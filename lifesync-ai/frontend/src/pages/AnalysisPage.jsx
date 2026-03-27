/**
 * AnalysisPage — 사진 분석 전용 페이지
 */
import { useState, useRef, useCallback, useEffect } from "react";
import { Upload, User, Activity, ListChecks, CheckSquare, Camera, Image, X, CircleDot } from "lucide-react";
import axios from "axios";
import Layout from "../components/layout/Layout";

const domainColors = {
  exercise: { text: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/30" },
  food: { text: "text-orange-400", bg: "bg-orange-500/10", border: "border-orange-500/30" },
  health: { text: "text-green-400", bg: "bg-green-500/10", border: "border-green-500/30" },
  hobby: { text: "text-purple-400", bg: "bg-purple-500/10", border: "border-purple-500/30" },
};

export default function AnalysisPage() {
  const [preview, setPreview] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(new Set());
  const [dragOver, setDragOver] = useState(false);
  const [cameraMode, setCameraMode] = useState(false);
  const [guideMode, setGuideMode] = useState("face"); // "face" | "body"
  const [facingMode, setFacingMode] = useState("user"); // "user" = front, "environment" = back
  const fileRef = useRef(null);
  const cameraRef = useRef(null);
  const albumRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  // Start camera
  const startCamera = useCallback(async () => {
    setCameraMode(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode, width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
    } catch (err) {
      alert("카메라에 접근할 수 없습니다. 권한을 허용해주세요.");
      setCameraMode(false);
    }
  }, [facingMode]);

  // Stop camera
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setCameraMode(false);
  }, []);

  // Capture photo from video
  const capturePhoto = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    // Mirror front camera
    if (facingMode === "user") {
      ctx.translate(canvas.width, 0);
      ctx.scale(-1, 1);
    }
    ctx.drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], "camera-photo.jpg", { type: "image/jpeg" });
        stopCamera();
        handleFile(file);
      }
    }, "image/jpeg", 0.92);
  }, [facingMode, stopCamera]);

  // Switch front/back camera
  const flipCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
    }
    setFacingMode((prev) => prev === "user" ? "environment" : "user");
  }, []);

  // Restart camera when facingMode changes
  useEffect(() => {
    if (cameraMode) {
      startCamera();
    }
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, [facingMode]);

  const handleFile = async (file) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);

    setLoading(true);
    setResults(null);
    setSelected(new Set());
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await axios.post("/api/photo/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResults(res.data);
    } catch {
      console.error("분석 실패");
    } finally {
      setLoading(false);
    }
  };

  const toggleSelect = (id) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const face = results?.face_analysis;
  const body = results?.body_analysis;

  return (
    <Layout>
      <div className="p-4 md:p-6 space-y-6 max-w-6xl mx-auto">
        <div>
          <h1 className="text-xl font-bold">사진 분석</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            사진 한 장으로 얼굴 + 체형 분석 → 맞춤 Top-5 조언
          </p>
        </div>

        {/* 카메라 모드 */}
        {cameraMode && (
          <div className="relative bg-black rounded-xl overflow-hidden">
            {/* 비디오 */}
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full max-h-[480px] object-cover"
              style={facingMode === "user" ? { transform: "scaleX(-1)" } : {}}
            />
            {/* 캔버스 (촬영용, 숨김) */}
            <canvas ref={canvasRef} className="hidden" />

            {/* 얼굴 가이드라인 */}
            {guideMode === "face" && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="w-52 h-64 border-2 border-cyan-400/60 rounded-[50%] shadow-[0_0_30px_rgba(6,182,212,0.15)]" />
                <div className="absolute bottom-20 left-0 right-0 text-center">
                  <span className="bg-black/60 text-cyan-300 text-xs px-3 py-1 rounded-full">
                    얼굴을 원 안에 맞춰주세요
                  </span>
                </div>
              </div>
            )}

            {/* 전신 가이드라인 */}
            {guideMode === "body" && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="w-40 h-[400px] border-2 border-emerald-400/60 rounded-lg" />
                <div className="absolute bottom-20 left-0 right-0 text-center">
                  <span className="bg-black/60 text-emerald-300 text-xs px-3 py-1 rounded-full">
                    전신이 사각형 안에 들어오도록 맞춰주세요
                  </span>
                </div>
              </div>
            )}

            {/* 카메라 컨트롤 */}
            <div className="absolute bottom-4 left-0 right-0 flex items-center justify-center gap-4">
              {/* 가이드 모드 전환 */}
              <button onClick={() => setGuideMode((g) => g === "face" ? "body" : "face")}
                className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center text-white hover:bg-white/30 transition-all"
                title={guideMode === "face" ? "전신 모드" : "얼굴 모드"}
              >
                {guideMode === "face" ? <User size={18} /> : <CircleDot size={18} />}
              </button>

              {/* 촬영 버튼 */}
              <button onClick={capturePhoto}
                className="w-16 h-16 rounded-full bg-white border-4 border-gray-300 hover:scale-105 transition-transform shadow-xl"
              />

              {/* 전후면 전환 */}
              <button onClick={flipCamera}
                className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center text-white hover:bg-white/30 transition-all"
                title="카메라 전환"
              >
                <Camera size={18} />
              </button>
            </div>

            {/* 닫기 */}
            <button onClick={stopCamera}
              className="absolute top-3 right-3 w-8 h-8 rounded-full bg-black/50 flex items-center justify-center text-white hover:bg-black/70 transition-all"
            >
              <X size={16} />
            </button>
          </div>
        )}

        {/* 업로드 영역 (카메라 모드 아닐 때) */}
        {!cameraMode && (
        <div
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
            dragOver
              ? "border-cyan-400 bg-cyan-900/10"
              : "border-gray-700 hover:border-gray-500"
          }`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0]); }}
          onClick={() => fileRef.current?.click()}
        >
          <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={(e) => handleFile(e.target.files[0])} />
          <input ref={albumRef} type="file" accept="image/*" className="hidden" onChange={(e) => handleFile(e.target.files[0])} />

          {preview ? (
            <img src={preview} alt="Preview" className="max-h-56 mx-auto rounded-lg" />
          ) : (
            <div className="text-gray-500">
              <Upload size={40} className="mx-auto mb-3 text-gray-600" />
              <p className="font-medium">사진을 드래그하거나 클릭하여 업로드</p>
              <p className="text-sm mt-1">얼굴 + 전신이 보이는 사진을 권장합니다</p>
            </div>
          )}
        </div>
        )}

        {/* 촬영 / 앨범 버튼 */}
        {!cameraMode && (
        <div className="flex gap-3 justify-center">
          <button
            onClick={startCamera}
            className="flex items-center gap-2 px-6 py-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl font-medium transition-all shadow-lg shadow-cyan-600/20"
          >
            <Camera size={20} />
            촬영
          </button>
          <button
            onClick={() => albumRef.current?.click()}
            className="flex items-center gap-2 px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-xl font-medium transition-all"
          >
            <Image size={20} />
            앨범
          </button>
          {preview && (
            <button
              onClick={() => { setPreview(null); setResults(null); }}
              className="flex items-center gap-2 px-6 py-3 bg-red-900/30 hover:bg-red-900/50 text-red-300 rounded-xl font-medium transition-all"
            >
              다시 선택
            </button>
          )}
        </div>
        )}

        {/* 로딩 */}
        {loading && (
          <div className="flex items-center justify-center py-10">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-cyan-400" />
            <span className="ml-4 text-gray-400">AI가 분석 중입니다...</span>
          </div>
        )}

        {/* 분석 결과 3열 */}
        {results && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* 얼굴 분석 */}
              <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <User size={18} className="text-pink-400" />
                  <h3 className="font-semibold text-sm">얼굴 분석</h3>
                </div>
                <div className="space-y-3">
                  <Metric label="피부 상태" value={face?.skin_condition} />
                  <Metric label="피로도" value={face?.fatigue_level} invert />
                  <Metric label="스트레스 지표" value={face?.stress_indicator} invert />
                  <Metric label="건강 외관" value={face?.health_appearance} />
                </div>
              </div>

              {/* 체형 분석 */}
              <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Activity size={18} className="text-blue-400" />
                  <h3 className="font-semibold text-sm">체형 분석</h3>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">체형 유형</span>
                    <span className="font-medium">{body?.body_type || "분석 중"}</span>
                  </div>
                  <Metric label="자세 점수" value={body?.posture_score} />
                </div>
              </div>

              {/* Top-5 조언 */}
              <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <ListChecks size={18} className="text-cyan-400" />
                  <h3 className="font-semibold text-sm">Top-5 맞춤 조언</h3>
                </div>
                <p className="text-xs text-gray-500 mb-3">원하는 항목을 복수 선택하세요</p>
                <div className="space-y-2">
                  {(results.top_5 || []).map((item, idx) => {
                    const dc = domainColors[item.domain] || domainColors.health;
                    const checked = selected.has(item.id);
                    return (
                      <button
                        key={item.id}
                        onClick={() => toggleSelect(item.id)}
                        className={`w-full text-left flex items-start gap-2 p-2.5 rounded-lg border transition-all ${
                          checked
                            ? `${dc.border} ${dc.bg}`
                            : "border-gray-700 hover:border-gray-600"
                        }`}
                      >
                        <span className="text-sm font-bold text-cyan-400 mt-0.5 w-4">{idx + 1}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{item.title}</p>
                          <p className="text-[11px] text-gray-500">{item.description}</p>
                        </div>
                        <CheckSquare
                          size={16}
                          className={checked ? "text-cyan-400 flex-shrink-0" : "text-gray-600 flex-shrink-0"}
                        />
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* 로드맵 생성 CTA */}
            {selected.size > 0 && (
              <div className="bg-gradient-to-r from-cyan-900/30 to-blue-900/30 border border-cyan-700/30 rounded-xl p-5 text-center">
                <p className="text-sm text-gray-300 mb-3">
                  {selected.size}개 목표를 선택했습니다. 12주 로드맵을 생성하시겠습니까?
                </p>
                <button className="inline-flex items-center gap-2 bg-cyan-600 hover:bg-cyan-500 text-white font-medium px-6 py-2.5 rounded-lg transition-colors">
                  12주 로드맵 생성 →
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
}

function Metric({ label, value, invert = false }) {
  const v = Math.round(value || 0);
  const good = invert ? v < 40 : v > 60;
  const barColor = good ? "bg-green-500" : v > 40 && v < 60 ? "bg-yellow-500" : "bg-red-500";

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-400">{label}</span>
        <span className="font-medium">{v}/100</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-1.5">
        <div className={`${barColor} h-1.5 rounded-full transition-all`} style={{ width: `${v}%` }} />
      </div>
    </div>
  );
}
