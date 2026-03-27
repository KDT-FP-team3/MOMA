/**
 * QuickChat — 빠른 질문 채팅 + 음성 입력
 */
import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Mic, MicOff } from "lucide-react";
import axios from "axios";

const domainColors = {
  food: "border-orange-500/30 bg-orange-500/5",
  exercise: "border-blue-500/30 bg-blue-500/5",
  health: "border-green-500/30 bg-green-500/5",
  hobby: "border-purple-500/30 bg-purple-500/5",
};

const domainLabels = {
  food: "요리",
  exercise: "운동",
  health: "건강",
  hobby: "취미",
};

export default function QuickChat() {
  const [messages, setMessages] = useState([
    {
      role: "ai",
      text: "안녕하세요! 저는 LifeSync AI입니다. 요리, 운동, 건강, 취미에 대해 물어보세요.",
      domain: null,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const messagesEnd = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Web Speech API 초기화
  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
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

    setMessages((prev) => [...prev, { role: "user", text, domain: null }]);
    setInput("");
    setLoading(true);

    try {
      const res = await axios.post("/api/query", {
        domain: "food",
        action: { query: text, meal_type: "", preference: text },
        user_id: "default",
      });

      const domain = res.data.domain || "food";
      const result = res.data.result || {};

      let responseText = "요청을 처리했습니다.";
      if (domain === "food") {
        const recs = result.recommendations || [];
        responseText = recs.length
          ? recs.map((r) => `${r.name}: ${r.reason || ""}`).join("\n")
          : result.query
          ? `"${result.query}" 검색 결과를 분석중입니다.`
          : responseText;
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          text: responseText,
          domain,
          cascade: res.data.cascade_effects,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: "응답을 받지 못했습니다. 서버 연결을 확인해주세요.", domain: null },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 flex flex-col h-[420px]">
      <div className="px-4 py-3 border-b border-gray-700">
        <h3 className="font-semibold text-sm text-cyan-400">AI 어시스턴트</h3>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-xl px-3.5 py-2.5 text-sm ${
                msg.role === "user"
                  ? "bg-cyan-600 text-white"
                  : msg.domain
                  ? `border ${domainColors[msg.domain] || "bg-gray-700"}`
                  : "bg-gray-700"
              }`}
            >
              {msg.domain && (
                <span className="text-[10px] font-medium text-gray-400 block mb-1">
                  {domainLabels[msg.domain] || msg.domain}
                </span>
              )}
              <p className="whitespace-pre-wrap">{msg.text}</p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
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

      {/* Input */}
      <div className="px-3 py-3 border-t border-gray-700">
        <div className="flex items-center gap-2">
          <button
            onClick={toggleRecording}
            className={`p-2 rounded-lg transition-colors flex-shrink-0 ${
              isRecording
                ? "bg-red-500/20 text-red-400"
                : "bg-gray-700 text-gray-400 hover:text-gray-200"
            }`}
          >
            {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="질문을 입력하세요..."
            className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500 placeholder:text-gray-500"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="p-2 rounded-lg bg-cyan-600 text-white hover:bg-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex-shrink-0"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
