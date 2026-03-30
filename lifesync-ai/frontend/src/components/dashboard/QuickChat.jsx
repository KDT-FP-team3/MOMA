/**
 * QuickChat — AI 어시스턴트 채팅 (자동 도메인 감지 + 멀티 도메인 응답)
 */
import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Mic, MicOff, Bot, User, AlertCircle, RefreshCw } from "lucide-react";
import axios from "axios";
import { useAppState } from "../../context/AppStateContext";

const DOMAIN_CONFIG = {
  food:     { label: "요리", color: "text-orange-400", border: "border-orange-500/30", bg: "bg-orange-500/5" },
  exercise: { label: "운동", color: "text-blue-400",   border: "border-blue-500/30",   bg: "bg-blue-500/5" },
  health:   { label: "건강", color: "text-green-400",  border: "border-green-500/30",  bg: "bg-green-500/5" },
  hobby:    { label: "취미", color: "text-purple-400", border: "border-purple-500/30", bg: "bg-purple-500/5" },
};

// 키워드 기반 도메인 자동 감지
const DOMAIN_KEYWORDS = {
  food: ["식사", "음식", "요리", "레시피", "칼로리", "식단", "먹", "밥", "메뉴", "영양", "다이어트", "라면", "치킨", "샐러드"],
  exercise: ["운동", "헬스", "달리기", "러닝", "근력", "유산소", "스트레칭", "걷기", "조깅", "헬스장", "PT"],
  health: ["건강", "검진", "혈압", "콜레스테롤", "수면", "체중", "BMI", "혈액", "병원", "약"],
  hobby: ["취미", "기타", "독서", "명상", "그림", "음악", "게임", "산책", "여행", "노래"],
};

function detectDomain(text) {
  const scores = {};
  for (const [domain, keywords] of Object.entries(DOMAIN_KEYWORDS)) {
    scores[domain] = keywords.filter((kw) => text.includes(kw)).length;
  }
  const best = Object.entries(scores).sort((a, b) => b[1] - a[1])[0];
  return best[1] > 0 ? best[0] : "food";
}

function formatResponse(domain, result, cascade) {
  const parts = [];

  if (domain === "food") {
    const recs = result.recommendations || [];
    if (recs.length) {
      parts.push(recs.map((r, i) => `${i + 1}. **${r.name}** — ${r.reason || ""} ${r.calories ? `(${r.calories}kcal)` : ""}`).join("\n"));
    }
    if (result.nutrition_summary) parts.push(`\n ${result.nutrition_summary}`);
  } else if (domain === "exercise") {
    const recs = result.recommendations || [];
    if (recs.length) {
      parts.push(recs.map((r, i) => `${i + 1}. **${r.name}** — ${r.duration_min || ""}분, ${r.reason || ""}`).join("\n"));
    }
  } else if (domain === "health") {
    if (result.summary) parts.push(result.summary);
    if (result.plan?.length) {
      parts.push("\n 건강 플랜:\n" + result.plan.map((p, i) => `${i + 1}. ${p}`).join("\n"));
    }
  } else if (domain === "hobby") {
    const recs = result.recommendations || [];
    if (recs.length) {
      parts.push(recs.map((r, i) => `${i + 1}. **${r.name}** — ${r.reason || ""}`).join("\n"));
    }
  }

  // 크로스 도메인 연쇄 효과
  if (cascade?.effects && Object.keys(cascade.effects).length > 0) {
    const effects = Object.entries(cascade.effects)
      .map(([d, e]) => `[${DOMAIN_CONFIG[d]?.label || d}] ${e.description}`)
      .join("\n");
    parts.push(`\n 연쇄 효과:\n${effects}`);
  }

  return parts.join("\n") || "요청을 처리했습니다.";
}

export default function QuickChat() {
  const { updateState } = useAppState();
  const [messages, setMessages] = useState([
    {
      role: "ai",
      text: "안녕하세요! 저는 LifeSync AI입니다.\n요리, 운동, 건강, 취미에 대해 자유롭게 물어보세요.\n\n예시:\n• \"저칼로리 저녁 메뉴 추천해줘\"\n• \"스트레스 해소 운동 알려줘\"\n• \"혈압이 높은데 어떻게 해야 해?\"\n• \"주말에 할 취미 추천\"",
      domain: null,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState(null);
  const messagesEnd = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 마운트 시 input에 포커스
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Web Speech API 초기화 + cleanup
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = "ko-KR";
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsRecording(false);
      };
      recognition.onerror = () => setIsRecording(false);
      recognition.onend = () => setIsRecording(false);
      recognitionRef.current = recognition;
    }
    return () => {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch { /* ignore */ }
        recognitionRef.current = null;
      }
    };
  }, []);

  const toggleRecording = useCallback(() => {
    if (!recognitionRef.current) return;
    if (isRecording) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
      setIsRecording(true);
    }
  }, [isRecording]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setError(null);
    setMessages((prev) => [...prev, { role: "user", text, domain: null }]);
    setInput("");
    setLoading(true);

    // 자동 도메인 감지
    const domain = detectDomain(text);

    try {
      const res = await axios.post("/api/query", {
        domain,
        action: { query: text, meal_type: "", preference: text },
        user_id: "default",
      }, { timeout: 15000 });

      const resDomain = res.data.domain || domain;
      const result = res.data.result || {};
      const cascade = res.data.cascade_effects || {};
      const responseText = formatResponse(resDomain, result, cascade);

      setMessages((prev) => [
        ...prev,
        { role: "ai", text: responseText, domain: resDomain, cascade },
      ]);

      // ── 연결: cascade_effects → 대시보드 게이지 업데이트 ──
      if (cascade?.effects) {
        updateState("lastCascade", cascade);
        // cascade.gauge_updates가 있으면 게이지에 반영
        if (res.data.updated_gauges) {
          updateState("gauges", (prev) => ({ ...prev, ...res.data.updated_gauges }));
        }
      }
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || "알 수 없는 오류";
      setError(detail);
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: ` 응답 실패: ${detail}\n\n서버가 실행 중인지 확인해주세요.`, domain: null, isError: true },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      { role: "ai", text: "대화가 초기화되었습니다. 새로운 질문을 해주세요!", domain: null },
    ]);
    setError(null);
  };

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 flex flex-col h-[420px]">
      {/* 헤더 */}
      <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot size={16} className="text-cyan-400" />
          <h3 className="font-semibold text-sm text-cyan-400">AI 어시스턴트</h3>
        </div>
        <button onClick={clearChat} className="text-white hover:text-white transition-colors" title="대화 초기화">
          <RefreshCw size={14} />
        </button>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} gap-2`}>
            {msg.role === "ai" && (
              <div className="w-6 h-6 rounded-full bg-cyan-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                <Bot size={12} className="text-cyan-400" />
              </div>
            )}
            <div
              className={`max-w-[80%] rounded-xl px-3.5 py-2.5 text-sm ${
                msg.role === "user"
                  ? "bg-cyan-600 text-white"
                  : msg.isError
                  ? "bg-red-500/10 border border-red-500/30"
                  : msg.domain
                  ? `border ${DOMAIN_CONFIG[msg.domain]?.border || "border-gray-600"} ${DOMAIN_CONFIG[msg.domain]?.bg || "bg-gray-700"}`
                  : "bg-gray-700"
              }`}
            >
              {msg.domain && DOMAIN_CONFIG[msg.domain] && (
                <span className={`text-[10px] font-medium ${DOMAIN_CONFIG[msg.domain].color} block mb-1`}>
                  {DOMAIN_CONFIG[msg.domain].label}
                </span>
              )}
              <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
            </div>
            {msg.role === "user" && (
              <div className="w-6 h-6 rounded-full bg-gray-600 flex items-center justify-center flex-shrink-0 mt-1">
                <User size={12} className="text-white" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex justify-start gap-2">
            <div className="w-6 h-6 rounded-full bg-cyan-500/20 flex items-center justify-center flex-shrink-0">
              <Bot size={12} className="text-cyan-400" />
            </div>
            <div className="bg-gray-700 rounded-xl px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:0.15s]" />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:0.3s]" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEnd} />
      </div>

      {/* 입력 영역 */}
      <div className="px-3 py-3 border-t border-gray-700">
        <div className="flex items-center gap-2">
          <button
            onClick={toggleRecording}
            className={`p-2 rounded-lg transition-colors flex-shrink-0 ${
              isRecording
                ? "bg-red-500/20 text-red-400 animate-pulse"
                : "bg-gray-700 text-white hover:text-gray-200"
            }`}
            title={isRecording ? "녹음 중지" : "음성 입력"}
          >
            {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
          </button>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isRecording ? "듣고 있습니다..." : "질문을 입력하세요..."}
            disabled={loading}
            className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 placeholder:text-white disabled:opacity-50"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="p-2 rounded-lg bg-cyan-600 text-white hover:bg-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex-shrink-0"
            title="전송"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
