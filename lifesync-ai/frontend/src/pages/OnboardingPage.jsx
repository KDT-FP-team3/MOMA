/**
 * OnboardingPage — 3단계 온보딩 위저드
 *
 * Step 1: 기본 정보 (나이대, 키, 몸무게)
 * Step 2: 생활 패턴 (활동량, 수면, 스트레스)
 * Step 3: 목표 설정 (체크박스)
 */
import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../components/layout/Layout";
import AvatarBody from "../components/AvatarBody";

const AGE_OPTIONS = [
  { label: "10대", emoji: "", value: "10s" },
  { label: "20대", emoji: "", value: "20s" },
  { label: "30대", emoji: "", value: "30s" },
  { label: "40대", emoji: "", value: "40s" },
  { label: "50대+", emoji: "", value: "50s+" },
];

const ACTIVITY_OPTIONS = [
  { label: "비활동적", emoji: "", value: "sedentary" },
  { label: "보통", emoji: "", value: "moderate" },
  { label: "활동적", emoji: "", value: "active" },
  { label: "매우 활동적", emoji: "", value: "very_active" },
];

const SLEEP_OPTIONS = [
  { label: "올빼미", emoji: "🦉", value: "night_owl" },
  { label: "보통", emoji: "😊", value: "normal" },
  { label: "아침형", emoji: "🌅", value: "morning" },
];

const STRESS_OPTIONS = [
  { label: "낮음", emoji: "😌", value: "low" },
  { label: "보통", emoji: "😐", value: "moderate" },
  { label: "높음", emoji: "😰", value: "high" },
  { label: "매우높음", emoji: "🤯", value: "very_high" },
];

const GOAL_OPTIONS = [
  { label: "체중 감량", emoji: "⚖️", value: "weight_loss" },
  { label: "근력 증가", emoji: "💪", value: "strength" },
  { label: "스트레스 관리", emoji: "🧘", value: "stress_mgmt" },
  { label: "수면 개선", emoji: "😴", value: "sleep" },
  { label: "식습관 개선", emoji: "🥗", value: "diet" },
  { label: "체력 향상", emoji: "🏃", value: "stamina" },
];

function OptionCard({ emoji, label, selected, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex flex-col items-center justify-center gap-2 p-4 rounded-xl border-2 transition-all duration-200 cursor-pointer min-w-[100px]
        ${
          selected
            ? "border-blue-500 bg-blue-500/15 shadow-lg shadow-blue-500/10"
            : "border-gray-700 bg-gray-800/60 hover:border-gray-500 hover:bg-gray-800"
        }`}
    >
      <span className="text-2xl">{emoji}</span>
      <span className={`text-sm font-medium ${selected ? "text-blue-300" : "text-gray-300"}`}>
        {label}
      </span>
    </button>
  );
}

function SliderField({ label, value, min, max, step, unit, onChange }) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <span className="text-gray-300 text-sm">{label}</span>
        <span className="text-blue-400 font-bold text-lg">
          {value}
          <span className="text-sm text-gray-400 ml-1">{unit}</span>
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
      />
      <div className="flex justify-between text-xs text-gray-500">
        <span>{min}{unit}</span>
        <span>{max}{unit}</span>
      </div>
    </div>
  );
}

export default function OnboardingPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);

  // Step 1
  const [age, setAge] = useState("");
  const [height, setHeight] = useState(170);
  const [weight, setWeight] = useState(65);

  // Step 2
  const [activity, setActivity] = useState("");
  const [sleepPattern, setSleepPattern] = useState("");
  const [stressLevel, setStressLevel] = useState("");

  // Step 3
  const [goals, setGoals] = useState([]);

  const toggleGoal = (val) => {
    setGoals((prev) =>
      prev.includes(val) ? prev.filter((g) => g !== val) : [...prev, val]
    );
  };

  // Derive avatar props from inputs
  const avatarProps = useMemo(() => {
    const heightM = height / 100;
    const bmi = weight / (heightM * heightM);

    const energyMap = {
      sedentary: 25,
      moderate: 50,
      active: 75,
      very_active: 95,
    };
    const energy = energyMap[activity] ?? 50;

    const stressMap = {
      low: 15,
      moderate: 40,
      high: 70,
      very_high: 95,
    };
    const stress = stressMap[stressLevel] ?? 40;

    const sleepMap = {
      night_owl: 35,
      normal: 65,
      morning: 85,
    };
    const sleep = sleepMap[sleepPattern] ?? 60;

    const mood = Math.max(10, Math.min(95, 60 + (energy - 50) * 0.3 - stress * 0.3));
    const health = Math.max(20, Math.min(95, 70 - (bmi > 25 ? (bmi - 25) * 3 : 0) - stress * 0.2 + sleep * 0.15));

    return { bmi, mood, energy, stress, sleep, health };
  }, [height, weight, activity, stressLevel, sleepPattern]);

  const stepTitles = ["기본 정보", "생활 패턴", "목표 설정"];
  const progressPercent = (step / 3) * 100;

  return (
    <Layout>
      <div className="flex flex-col lg:flex-row min-h-full">
        {/* Left: form area */}
        <div className="flex-1 p-6 md:p-10 overflow-y-auto">
          {/* Progress bar */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-400">
                Step {step} / 3
              </span>
              <span className="text-sm text-gray-500">
                {Math.round(progressPercent)}%
              </span>
            </div>
            <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-600 to-blue-400 rounded-full transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* Step number + title */}
          <div className="mb-8">
            <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-blue-600 text-white font-bold text-lg mb-3">
              {step}
            </div>
            <h1 className="text-2xl md:text-3xl font-bold text-white">
              {stepTitles[step - 1]}
            </h1>
          </div>

          {/* Step content */}
          {step === 1 && (
            <div className="space-y-8 max-w-xl">
              {/* Age range */}
              <div>
                <h3 className="text-gray-300 font-medium mb-3">나이대</h3>
                <div className="flex flex-wrap gap-3">
                  {AGE_OPTIONS.map((opt) => (
                    <OptionCard
                      key={opt.value}
                      emoji={opt.emoji}
                      label={opt.label}
                      selected={age === opt.value}
                      onClick={() => setAge(opt.value)}
                    />
                  ))}
                </div>
              </div>

              {/* Height slider */}
              <SliderField
                label="키"
                value={height}
                min={140}
                max={200}
                step={1}
                unit="cm"
                onChange={setHeight}
              />

              {/* Weight slider */}
              <SliderField
                label="몸무게"
                value={weight}
                min={40}
                max={120}
                step={1}
                unit="kg"
                onChange={setWeight}
              />
            </div>
          )}

          {step === 2 && (
            <div className="space-y-8 max-w-xl">
              {/* Activity level */}
              <div>
                <h3 className="text-gray-300 font-medium mb-3">활동량</h3>
                <div className="flex flex-wrap gap-3">
                  {ACTIVITY_OPTIONS.map((opt) => (
                    <OptionCard
                      key={opt.value}
                      emoji={opt.emoji}
                      label={opt.label}
                      selected={activity === opt.value}
                      onClick={() => setActivity(opt.value)}
                    />
                  ))}
                </div>
              </div>

              {/* Sleep pattern */}
              <div>
                <h3 className="text-gray-300 font-medium mb-3">수면 패턴</h3>
                <div className="flex flex-wrap gap-3">
                  {SLEEP_OPTIONS.map((opt) => (
                    <OptionCard
                      key={opt.value}
                      emoji={opt.emoji}
                      label={opt.label}
                      selected={sleepPattern === opt.value}
                      onClick={() => setSleepPattern(opt.value)}
                    />
                  ))}
                </div>
              </div>

              {/* Stress level */}
              <div>
                <h3 className="text-gray-300 font-medium mb-3">스트레스 수준</h3>
                <div className="flex flex-wrap gap-3">
                  {STRESS_OPTIONS.map((opt) => (
                    <OptionCard
                      key={opt.value}
                      emoji={opt.emoji}
                      label={opt.label}
                      selected={stressLevel === opt.value}
                      onClick={() => setStressLevel(opt.value)}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-6 max-w-xl">
              <p className="text-gray-400 text-sm">
                달성하고 싶은 목표를 모두 선택해주세요.
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {GOAL_OPTIONS.map((opt) => (
                  <OptionCard
                    key={opt.value}
                    emoji={opt.emoji}
                    label={opt.label}
                    selected={goals.includes(opt.value)}
                    onClick={() => toggleGoal(opt.value)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Navigation buttons */}
          <div className="flex gap-4 mt-10 max-w-xl">
            {step > 1 && (
              <button
                type="button"
                onClick={() => setStep((s) => s - 1)}
                className="px-6 py-3 rounded-xl border border-gray-600 text-gray-300 hover:bg-gray-800 transition-colors"
              >
                이전
              </button>
            )}
            {step < 3 ? (
              <button
                type="button"
                onClick={() => setStep((s) => s + 1)}
                className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium transition-colors ml-auto"
              >
                다음
              </button>
            ) : (
              <button
                type="button"
                onClick={() => navigate("/avatar")}
                className="px-8 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold transition-all ml-auto shadow-lg shadow-blue-500/25"
              >
                시작하기
              </button>
            )}
          </div>
        </div>

        {/* Right: Avatar preview */}
        <div className="hidden lg:flex flex-col items-center justify-center w-80 xl:w-96 border-l border-gray-800 bg-gray-900/50 p-8">
          <h3 className="text-gray-400 text-sm font-medium mb-6 tracking-wide uppercase">
            Avatar Preview
          </h3>
          <div className="bg-gray-800/40 rounded-2xl p-8 border border-gray-700/50">
            <AvatarBody
              bmi={avatarProps.bmi}
              mood={avatarProps.mood}
              energy={avatarProps.energy}
              stress={avatarProps.stress}
              sleep={avatarProps.sleep}
              health={avatarProps.health}
              size={200}
              animate
            />
          </div>
          <div className="mt-6 space-y-2 text-xs text-gray-500 w-full">
            <div className="flex justify-between">
              <span>BMI</span>
              <span className="text-gray-300">{avatarProps.bmi.toFixed(1)}</span>
            </div>
            <div className="flex justify-between">
              <span>기분</span>
              <span className="text-gray-300">{Math.round(avatarProps.mood)}</span>
            </div>
            <div className="flex justify-between">
              <span>에너지</span>
              <span className="text-gray-300">{Math.round(avatarProps.energy)}</span>
            </div>
            <div className="flex justify-between">
              <span>스트레스</span>
              <span className="text-gray-300">{Math.round(avatarProps.stress)}</span>
            </div>
            <div className="flex justify-between">
              <span>수면</span>
              <span className="text-gray-300">{Math.round(avatarProps.sleep)}</span>
            </div>
            <div className="flex justify-between">
              <span>건강</span>
              <span className="text-gray-300">{Math.round(avatarProps.health)}</span>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
