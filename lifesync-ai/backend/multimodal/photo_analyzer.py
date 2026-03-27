"""사진 분석기 — 얼굴 및 체형 분석, Top-5 맞춤 조언 생성."""

import logging
from typing import Any

from backend.multimodal.clip_embedder import CLIPEmbedder
from backend.multimodal.pose_analyzer import PoseAnalyzer

logger = logging.getLogger(__name__)

# Top-5 조언 템플릿 (분석 결과에 따라 선택)
ADVICE_TEMPLATES: list[dict[str, Any]] = [
    {"id": 1, "domain": "exercise", "title": "HIIT + 근력 운동 (주 3회)", "description": "12주 내 체지방 -5% 목표", "condition": "bmi_high"},
    {"id": 2, "domain": "food", "title": "고단백 식단 플랜", "description": "근손실 방지하며 건강한 감량", "condition": "bmi_high"},
    {"id": 3, "domain": "health", "title": "수면 최적화 (7시간 이상)", "description": "코르티솔 감소로 지방 감소 촉진", "condition": "stress_high"},
    {"id": 4, "domain": "hobby", "title": "주말 등산 취미", "description": "스트레스 해소 + 추가 유산소 효과", "condition": "stress_high"},
    {"id": 5, "domain": "health", "title": "건강검진 (혈액/간)", "description": "진행 추적을 위한 기준값 확보", "condition": "general"},
    {"id": 6, "domain": "exercise", "title": "자세 교정 스트레칭", "description": "라운드숄더 및 거북목 교정", "condition": "posture_bad"},
    {"id": 7, "domain": "food", "title": "항산화 식단 강화", "description": "비타민 C/E 풍부한 레시피 추천", "condition": "skin_concern"},
    {"id": 8, "domain": "exercise", "title": "유산소 + 요가 병행", "description": "항노화 운동으로 활력 증진", "condition": "general"},
    {"id": 9, "domain": "hobby", "title": "명상 습관 형성", "description": "스트레스 -15%, 폭식 충동 -40%", "condition": "stress_high"},
    {"id": 10, "domain": "food", "title": "칼로리 목표 설정", "description": "탄단지 비율 맞춤 식단 설계", "condition": "bmi_high"},
]


class PhotoAnalyzer:
    """얼굴 + 체형 분석기.

    CLIP 임베딩과 MediaPipe 자세 분석을 결합하여
    사진 기반 맞춤 Top-5 조언을 생성한다.
    """

    def __init__(self) -> None:
        self._clip = CLIPEmbedder()
        self._pose = PoseAnalyzer()

    def analyze_face(self, image_bytes: bytes) -> dict[str, Any]:
        """얼굴 분석 (CLIP 기반 건강 상태 추정).

        Args:
            image_bytes: 이미지 바이트 데이터.

        Returns:
            얼굴 분석 결과 (skin_condition, fatigue, stress_indicator 등).
        """
        # CLIP 유사도를 이용한 건강 상태 추정
        image_emb = self._clip.embed_image(image_bytes)

        prompts = {
            "healthy_skin": "a person with healthy, clear, glowing skin",
            "tired_face": "a person looking very tired and exhausted",
            "stressed_face": "a person looking stressed and anxious",
            "healthy_face": "a person looking healthy and energetic",
        }

        scores: dict[str, float] = {}
        for key, prompt in prompts.items():
            text_emb = self._clip.embed_text(prompt)
            scores[key] = self._clip.compute_similarity(image_emb, text_emb)

        # 점수 기반 상태 추정
        skin_score = scores.get("healthy_skin", 0.5) * 100
        fatigue = scores.get("tired_face", 0.3) * 100
        stress = scores.get("stressed_face", 0.3) * 100

        return {
            "skin_condition": min(100, max(0, skin_score)),
            "fatigue_level": min(100, max(0, fatigue)),
            "stress_indicator": min(100, max(0, stress)),
            "health_appearance": min(100, max(0, scores.get("healthy_face", 0.5) * 100)),
            "raw_scores": scores,
        }

    def analyze_body(self, image_bytes: bytes) -> dict[str, Any]:
        """체형 분석 (MediaPipe + CLIP).

        Args:
            image_bytes: 이미지 바이트 데이터.

        Returns:
            체형 분석 결과 (posture, estimated_bmi_range 등).
        """
        pose_result = self._pose.analyze(image_bytes)

        # CLIP으로 체형 추정
        image_emb = self._clip.embed_image(image_bytes)
        body_prompts = {
            "athletic": "an athletic, fit person with good muscle tone",
            "overweight": "an overweight person",
            "slim": "a slim, lean person",
            "average": "an average body type person",
        }

        body_scores: dict[str, float] = {}
        for key, prompt in body_prompts.items():
            text_emb = self._clip.embed_text(prompt)
            body_scores[key] = self._clip.compute_similarity(image_emb, text_emb)

        # 체형 추정
        best_type = max(body_scores, key=body_scores.get)  # type: ignore[arg-type]

        return {
            "posture": pose_result,
            "body_type_estimate": best_type,
            "body_scores": body_scores,
            "posture_score": pose_result.get("posture_score", 50.0),
        }

    def get_top_k_similar(
        self, image_bytes: bytes, k: int = 5
    ) -> list[dict[str, Any]]:
        """사진 분석 + LLM 기반 개인화 Top-K 조언 생성.

        CLIP/MediaPipe 분석 결과를 LLM에 전달하여
        사용자별 맞춤 조언을 생성한다.

        Args:
            image_bytes: 이미지 바이트 데이터.
            k: 반환할 조언 수.

        Returns:
            Top-K 개인화 조언 리스트.
        """
        face = self.analyze_face(image_bytes)
        body = self.analyze_body(image_bytes)

        # LLM 개인화 조언 시도
        llm_advice = self._generate_llm_advice(face, body, k)
        if llm_advice:
            return llm_advice

        # LLM 실패 시 기존 템플릿 기반 폴백
        return self._template_based_advice(face, body, k)

    def _generate_llm_advice(
        self,
        face: dict[str, Any],
        body: dict[str, Any],
        k: int,
    ) -> list[dict[str, Any]]:
        """LLM 기반 개인화 조언 생성."""
        try:
            import os
            import json
            from openai import OpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return []

            client = OpenAI(api_key=api_key)

            prompt = f"""사진 분석 결과를 기반으로 맞춤형 건강/생활 개선 Top-{k} 조언을 생성해주세요.

[분석 결과]
- 피부 상태: {face.get('skin_condition', 50):.0f}/100
- 피로도: {face.get('fatigue_level', 50):.0f}/100
- 스트레스 지표: {face.get('stress_indicator', 50):.0f}/100
- 건강 외관: {face.get('health_appearance', 50):.0f}/100
- 체형 추정: {body.get('body_type_estimate', 'average')}
- 자세 점수: {body.get('posture_score', 50):.0f}/100

[응답 형식] JSON 배열로 반환:
[{{"domain": "food|exercise|health|hobby", "title": "제목(20자 이내)", "description": "설명(50자 이내)", "priority": 0.0~1.0}}]

우선순위가 높은 순서로 {k}개만 반환하세요. 한국어로 작성하세요."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500,
            )

            content = response.choices[0].message.content or ""
            # JSON 파싱 (마크다운 코드블록 제거)
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("```", 1)[0]

            items = json.loads(content)
            result = []
            for i, item in enumerate(items[:k]):
                result.append({
                    "id": i + 1,
                    "domain": item.get("domain", "health"),
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "similarity": round(item.get("priority", 0.5), 3),
                    "source": "llm",
                })
            return result

        except Exception:
            logger.exception("LLM 개인화 조언 생성 실패, 템플릿으로 폴백")
            return []

    def _template_based_advice(
        self,
        face: dict[str, Any],
        body: dict[str, Any],
        k: int,
    ) -> list[dict[str, Any]]:
        """기존 템플릿 기반 조언 (폴백)."""
        scored_advice: list[dict[str, Any]] = []

        for advice in ADVICE_TEMPLATES:
            score = 0.5
            condition = advice["condition"]

            if condition == "bmi_high" and body.get("body_type_estimate") == "overweight":
                score = 0.9
            elif condition == "stress_high" and face.get("stress_indicator", 0) > 50:
                score = 0.85
            elif condition == "posture_bad" and body.get("posture_score", 100) < 60:
                score = 0.8
            elif condition == "skin_concern" and face.get("skin_condition", 100) < 50:
                score = 0.75
            elif condition == "general":
                score = 0.6

            scored_advice.append({
                "id": advice["id"],
                "domain": advice["domain"],
                "title": advice["title"],
                "description": advice["description"],
                "similarity": round(score, 3),
                "source": "template",
            })

        scored_advice.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_advice[:k]
