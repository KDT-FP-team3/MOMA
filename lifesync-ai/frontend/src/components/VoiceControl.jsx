/**
 * VoiceControl — 음성 입력 및 TTS 응답 컴포넌트
 *
 * Web Speech API (SpeechRecognition) 사용
 * 마이크 버튼 UI (녹음 중 / 대기 중 상태)
 * 인식 결과를 WebSocket으로 전송
 * TTS: 응답 텍스트를 음성으로 재생 (한국어)
 * WebSocket 자동 재연결 (최대 5회, 3초 간격)
 */
import { useState, useRef, useCallback, useEffect } from "react";

const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

const MAX_RETRIES = 5;
const RETRY_DELAY = 3000;

export default function VoiceControl() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [wsStatus, setWsStatus] = useState("disconnected");
  const recognitionRef = useRef(null);
  const wsRef = useRef(null);
  const retryCountRef = useRef(0);
  const retryTimerRef = useRef(null);

  // TTS 재생
  const speakText = useCallback(
    (text) => {
      if (!ttsEnabled || !text || !window.speechSynthesis) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "ko-KR";
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    },
    [ttsEnabled]
  );

  // WebSocket 연결 (자동 재연결)
  useEffect(() => {
    function connectWebSocket() {
      const wsUrl =
        (window.location.protocol === "https:" ? "wss://" : "ws://") +
        window.location.host +
        "/ws";

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setWsStatus("connected");
          retryCountRef.current = 0;
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            if (message.type === "voice_result" && message.data) {
              const text = message.data.text || "";
              setResponse(text);
              speakText(text);
            }
          } catch {
            // JSON 파싱 실패 무시
          }
        };

        ws.onclose = () => {
          setWsStatus("disconnected");
          scheduleReconnect();
        };

        ws.onerror = () => {
          setWsStatus("error");
        };
      } catch {
        setWsStatus("error");
        scheduleReconnect();
      }
    }

    function scheduleReconnect() {
      if (retryCountRef.current >= MAX_RETRIES) return;
      retryCountRef.current += 1;
      retryTimerRef.current = setTimeout(connectWebSocket, RETRY_DELAY);
    }

    connectWebSocket();

    return () => {
      clearTimeout(retryTimerRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [speakText]);

  // TTS 토글
  const toggleTts = useCallback(() => {
    setTtsEnabled((prev) => {
      if (prev) window.speechSynthesis?.cancel();
      return !prev;
    });
  }, []);

  // 음성 인식 시작
  const startRecording = useCallback(() => {
    if (!SpeechRecognition) {
      alert("이 브라우저는 음성 인식을 지원하지 않습니다.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "ko-KR";
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      const result = event.results[event.results.length - 1];
      const text = result[0].transcript;
      setTranscript(text);

      if (result.isFinal && wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({ type: "voice", data: { text, lang: "ko" } })
        );
      }
    };

    recognition.onend = () => setIsRecording(false);
    recognition.onerror = (event) => {
      console.error("음성 인식 오류:", event.error);
      setIsRecording(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
    setIsRecording(true);
    setTranscript("");
    setResponse("");
  }, []);

  // 음성 인식 중지
  const stopRecording = useCallback(() => {
    if (recognitionRef.current) recognitionRef.current.stop();
    setIsRecording(false);
  }, []);

  const statusColor =
    wsStatus === "connected" ? "#10b981" : wsStatus === "error" ? "#ef4444" : "#6b7280";

  return (
    <div className="voice-control">
      <h2>Voice Control</h2>

      {/* 상태 표시 */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
        <span
          style={{
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            backgroundColor: statusColor,
            display: "inline-block",
          }}
        />
        <span style={{ fontSize: "12px", color: "#999" }}>
          {wsStatus === "connected" ? "연결됨" : wsStatus === "error" ? "오류" : "연결 대기"}
        </span>
      </div>

      {/* 버튼 그룹 */}
      <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
        {/* 마이크 버튼 */}
        <button
          onClick={isRecording ? stopRecording : startRecording}
          style={{
            width: "64px",
            height: "64px",
            borderRadius: "50%",
            border: "none",
            cursor: "pointer",
            fontSize: "24px",
            backgroundColor: isRecording ? "#ff6b6b" : "#228be6",
            color: "#fff",
            transition: "background-color 0.2s",
          }}
          aria-label={isRecording ? "녹음 중지" : "녹음 시작"}
        >
          {isRecording ? "\u23F9" : "\uD83C\uDF99"}
        </button>

        {/* TTS 토글 버튼 */}
        <button
          onClick={toggleTts}
          style={{
            padding: "8px 14px",
            borderRadius: "8px",
            border: "none",
            cursor: "pointer",
            fontSize: "12px",
            fontWeight: 600,
            backgroundColor: ttsEnabled ? "#10b981" : "#4b5563",
            color: "#fff",
            transition: "background-color 0.2s",
          }}
        >
          {ttsEnabled ? "TTS ON" : "TTS OFF"}
        </button>
      </div>

      <p style={{ fontSize: "14px", color: "#666", marginTop: "8px" }}>
        {isRecording ? "녹음 중..." : "마이크를 눌러 시작하세요"}
      </p>

      {/* 인식 결과 */}
      {transcript && (
        <div
          style={{
            marginTop: "16px",
            padding: "12px",
            backgroundColor: "#f1f3f5",
            borderRadius: "8px",
          }}
        >
          <strong>인식:</strong> {transcript}
        </div>
      )}

      {/* AI 응답 */}
      {response && (
        <div
          style={{
            marginTop: "8px",
            padding: "12px",
            backgroundColor: "#e7f5ff",
            borderRadius: "8px",
          }}
        >
          <strong>응답:</strong> {response}
        </div>
      )}
    </div>
  );
}
