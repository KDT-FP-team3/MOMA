# 팀원 E — 한국 음식 특화 YOLO + CLIP 플러그인

## 담당 범위
- `plugins/vision_korean/` 폴더 내 파일만 수정
- YOLO 한식 파인튜닝, CLIP 임베딩 개선, 식재료 인식 정확도 향상

## 구현해야 할 인터페이스
```python
class KoreanFoodAnalyzer:
    def analyze(self, image_bytes: bytes) -> dict[str, Any]:
        """반환 필수: {detected_items: list, confidence: float}
        선택: {nutrition_estimate: dict, korean_name: str}"""
```

## 사용 가능한 코어 모듈
- `backend.multimodal.clip_embedder` — OpenCLIP ViT-B-32 (참고용)
- `backend.multimodal.food_recognizer` — YOLOv8 기본 구현 (참고용)
- `backend.multimodal.photo_analyzer` — 통합 분석기 (참고용)
- `ultralytics` — YOLOv8 (설치 시)
- `open_clip` — OpenCLIP (설치 시)

## 제한사항
1. `plugins/vision_korean/` 밖의 파일 수정 금지
2. 모델 파일(.pt, .onnx)은 `plugins/vision_korean/models/`에 저장
3. 모델 파일은 `.gitignore`에 추가 (git에 커밋 금지)
4. CPU에서도 동작해야 함 (GPU는 선택사항)
5. 추론 시간 500ms 이하 목표
6. 이미지 입력 검증: jpeg/png/webp만 허용, 10MB 이하

## 참고 파일 (읽기 전용)
- `backend/multimodal/food_recognizer.py` — 현재 YOLO 구현
- `backend/multimodal/clip_embedder.py` — CLIP 임베딩
- `backend/core/interfaces.py` — ImageAnalyzer Protocol
- `backend/core/fallbacks.py` — BasicImageAnalyzer 폴백

## 완료 기준
1. `plugin.py`의 `register()` 주석 해제
2. `GET /api/plugins/status`에서 `image_analyzer: "plugin"` 표시
3. 한국 음식 사진 업로드 시 한국어 이름 + 영양정보 반환

## 에이전트 피드백 (자동)
- 점검 시각: 2026-03-30 01:28 UTC
- 인터페이스 점검: PASS
  - 모든 인터페이스 준수
- 플러그인 상태: active (KoreanFoodAnalyzer)
