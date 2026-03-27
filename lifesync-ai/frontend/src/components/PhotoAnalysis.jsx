/**
 * PhotoAnalysis — 사진 업로드 및 Top-5 분석 결과 UI
 * @param {{ onCascade?: function }} props
 * @returns {JSX.Element}
 */
import { useState, useRef } from "react";
import axios from "axios";

export default function PhotoAnalysis({ onCascade }) {
  const [preview, setPreview] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef(null);

  const handleFile = async (file) => {
    if (!file) return;

    // 미리보기
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);

    // 업로드
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await axios.post("/api/photo/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResults(res.data);
    } catch (err) {
      console.error("사진 분석 실패:", err);
    } finally {
      setLoading(false);
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  const domainColors = {
    exercise: "text-blue-400 bg-blue-900/30",
    food: "text-orange-400 bg-orange-900/30",
    health: "text-green-400 bg-green-900/30",
    hobby: "text-purple-400 bg-purple-900/30",
  };

  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <h2 className="text-lg font-semibold text-cyan-400 mb-4">
        사진 분석 — Top-5 맞춤 조언
      </h2>

      {/* 드래그앤드롭 영역 */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          dragOver
            ? "border-cyan-400 bg-cyan-900/20"
            : "border-gray-600 hover:border-gray-500"
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => fileRef.current?.click()}
      >
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => handleFile(e.target.files[0])}
        />
        {preview ? (
          <img
            src={preview}
            alt="Preview"
            className="max-h-48 mx-auto rounded-lg"
          />
        ) : (
          <div className="text-gray-400">
            <p className="text-4xl mb-2 text-gray-500">[+]</p>
            <p>사진을 드래그하거나 클릭하여 업로드</p>
            <p className="text-sm text-gray-500 mt-1">얼굴 + 전신 사진 권장</p>
          </div>
        )}
      </div>

      {/* 로딩 */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400" />
          <span className="ml-3 text-gray-400">분석 중...</span>
        </div>
      )}

      {/* Top-5 결과 */}
      {results?.top_5 && (
        <div className="mt-4 space-y-3">
          <h3 className="text-sm font-medium text-gray-400">Top-5 맞춤 조언</h3>
          {results.top_5.map((item, idx) => (
            <div
              key={item.id}
              className="flex items-center gap-4 bg-gray-700/50 rounded-lg p-4 hover:bg-gray-700 transition-colors"
            >
              <span className="text-2xl font-bold text-cyan-400 w-8">
                {idx + 1}
              </span>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{item.title}</span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      domainColors[item.domain] || "text-gray-400"
                    }`}
                  >
                    {item.domain}
                  </span>
                </div>
                <p className="text-sm text-gray-400 mt-1">{item.description}</p>
              </div>
              <div className="text-right">
                <div className="w-16 bg-gray-600 rounded-full h-2">
                  <div
                    className="bg-cyan-400 h-2 rounded-full"
                    style={{ width: `${item.similarity * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500">
                  {(item.similarity * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 얼굴/체형 분석 요약 */}
      {results?.face_analysis && (
        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="bg-gray-700/50 rounded-lg p-3">
            <span className="text-xs text-gray-400">피부 상태</span>
            <p className="text-lg font-bold">
              {results.face_analysis.skin_condition?.toFixed(0) || 0}/100
            </p>
          </div>
          <div className="bg-gray-700/50 rounded-lg p-3">
            <span className="text-xs text-gray-400">자세 점수</span>
            <p className="text-lg font-bold">
              {results.body_analysis?.posture_score?.toFixed(0) || 0}/100
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
