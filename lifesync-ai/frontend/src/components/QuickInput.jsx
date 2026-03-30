/**
 * QuickInput — Natural language input that auto-classifies to closest choice
 * Shows at bottom of screen, user types text, we keyword-match to closest CHOICES item
 */
import { useState, useRef } from "react";
import { Send, Sparkles } from "lucide-react";

// Keyword mapping for auto-classification
const KEYWORD_MAP = [
  { keywords: ["한식", "비빔밥", "된장", "김치", "밥", "국"], match: "균형 잡힌 한식" },
  { keywords: ["에어프라이어", "구이"], match: "에어프라이어 요리" },
  { keywords: ["야식", "라면", "늦게", "밤"], match: "야식 라면 (23시)" },
  { keywords: ["치킨", "튀김", "피자", "햄버거", "패스트"], match: "튀김 치킨" },
  { keywords: ["과일", "사과", "바나나", "간식"], match: "과일 간식" },
  { keywords: ["폭식", "많이", "스트레스 먹"], match: "폭식 (스트레스)" },
  { keywords: ["조깅", "달리기", "러닝", "뛰"], match: "30분 조깅" },
  { keywords: ["헬스", "근력", "웨이트", "gym"], match: "헬스장 근력운동" },
  { keywords: ["요가", "스트레칭", "명상"], match: "요가 / 스트레칭" },
  { keywords: ["운동 안", "쉬었", "안 했", "귀찮"], match: "운동 안 함 (하루)" },
  { keywords: ["미세먼지", "황사"], match: "미세먼지 속 러닝" },
  { keywords: ["숙면", "잘 잤", "푹 잤", "7시간", "8시간"], match: "7~8시간 숙면" },
  { keywords: ["일찍", "규칙", "기상"], match: "규칙적 기상" },
  { keywords: ["못 잤", "4시간", "잠 부족", "뜬눈"], match: "4시간 수면" },
  { keywords: ["새벽", "늦게 잤", "밤새"], match: "새벽 3시 취침" },
  { keywords: ["기타", "악기", "음악", "피아노"], match: "기타 연주 30분" },
  { keywords: ["독서", "책", "읽"], match: "독서 1시간" },
  { keywords: ["산책", "공원", "자연", "걸"], match: "자연 산책" },
  { keywords: ["sns", "인스타", "유튜브", "틱톡", "스크롤"], match: "SNS 3시간+" },
  { keywords: ["술", "소주", "맥주", "음주", "와인"], match: "음주 (소주 1병)" },
  { keywords: ["검진", "병원", "건강검진"], match: "건강검진 이행" },
  { keywords: ["물", "수분", "마셨"], match: "충분한 수분 섭취" },
  { keywords: ["약", "거부", "안 먹"], match: "약 복용 거부" },
  { keywords: ["무시", "안 갔"], match: "검진 결과 무시" },
];

export default function QuickInput({ allChoices, onMatch }) {
  const [text, setText] = useState("");
  const [suggestion, setSuggestion] = useState(null);
  const inputRef = useRef(null);

  const findMatch = (input) => {
    const lower = input.toLowerCase();
    for (const entry of KEYWORD_MAP) {
      if (entry.keywords.some((k) => lower.includes(k))) {
        // Find the actual choice item
        for (const cat of allChoices) {
          const found = cat.items.find((item) => item.label === entry.match);
          if (found) return { ...found, category: cat.category };
        }
      }
    }
    return null;
  };

  const handleChange = (e) => {
    const val = e.target.value;
    setText(val);
    if (val.length >= 2) {
      setSuggestion(findMatch(val));
    } else {
      setSuggestion(null);
    }
  };

  const handleSubmit = () => {
    if (suggestion) {
      onMatch(suggestion);
      setText("");
      setSuggestion(null);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="fixed bottom-16 lg:bottom-4 left-1/2 -translate-x-1/2 w-[90%] max-w-lg z-40">
      {/* Suggestion preview */}
      {suggestion && (
        <div className="mb-2 mx-2 px-4 py-2.5 rounded-xl bg-gray-800/95 border border-cyan-800/50 backdrop-blur-sm flex items-center gap-3 shadow-xl">
          <span className="text-lg">{suggestion.icon}</span>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-white font-medium">{suggestion.label}</p>
            <p className="text-[10px] text-white">{suggestion.category}</p>
          </div>
          <span className={`text-xs px-2 py-0.5 rounded-full ${suggestion.type === "positive" ? "bg-emerald-900/40 text-emerald-400" : "bg-red-900/40 text-red-400"}`}>
            {suggestion.type === "positive" ? "긍정" : "부정"}
          </span>
          <button onClick={handleSubmit} className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium">
            적용
          </button>
        </div>
      )}
      {/* Input bar */}
      <div className="flex items-center gap-2 px-4 py-3 rounded-2xl bg-gray-800/95 border border-gray-600 backdrop-blur-sm shadow-xl">
        <Sparkles size={18} className="text-cyan-400 flex-shrink-0" />
        <input
          ref={inputRef}
          type="text"
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder='오늘 뭐 했어요? (예: "점심에 비빔밥 먹었어")'
          className="flex-1 bg-transparent text-sm text-white placeholder-gray-500 outline-none"
        />
        <button
          onClick={handleSubmit}
          disabled={!suggestion}
          className="p-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-30 disabled:cursor-not-allowed text-white transition-all"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
