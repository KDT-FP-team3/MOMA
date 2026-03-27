/**
 * 오프라인 추론 엔진 — 모델 동기화 + 로컬 추론
 *
 * 서버에서 최신 모델 가중치를 다운로드하여 IndexedDB에 캐싱하고,
 * 오프라인 시 로컬 가중치로 시뮬레이션 추론을 수행한다.
 */

const DB_NAME = "lifesync-offline";
const DB_VERSION = 1;
const MODEL_STORE = "models";
const STATE_STORE = "user_state";

/**
 * IndexedDB 초기화
 */
function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains(MODEL_STORE)) {
        db.createObjectStore(MODEL_STORE, { keyPath: "name" });
      }
      if (!db.objectStoreNames.contains(STATE_STORE)) {
        db.createObjectStore(STATE_STORE, { keyPath: "key" });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

/**
 * IndexedDB에 데이터 저장
 */
async function dbPut(storeName, data) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, "readwrite");
    tx.objectStore(storeName).put(data);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

/**
 * IndexedDB에서 데이터 조회
 */
async function dbGet(storeName, key) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, "readonly");
    const req = tx.objectStore(storeName).get(key);
    req.onsuccess = () => resolve(req.result || null);
    req.onerror = () => reject(req.error);
  });
}

// ============================================================
// 모델 동기화
// ============================================================

/**
 * 서버에서 모델 버전 확인 후 필요시 다운로드
 * @param {string} modelName - 모델 이름 (예: "ppo_policy")
 * @returns {Object} 동기화 결과
 */
export async function syncModel(modelName) {
  try {
    // 로컬 버전 확인
    const local = await dbGet(MODEL_STORE, modelName);
    const localVersion = local?.version || 0;

    // 서버 버전 확인
    const API_BASE = import.meta.env.VITE_API_BASE || "";
    const res = await fetch(`${API_BASE}/api/models/${modelName}/version`);
    if (!res.ok) {
      return { status: "offline", localVersion, serverVersion: 0 };
    }

    const serverInfo = await res.json();
    if (!serverInfo.available) {
      return { status: "not_available", localVersion };
    }

    // 버전 비교
    if (localVersion >= serverInfo.version) {
      return { status: "up_to_date", version: localVersion };
    }

    // 새 버전 다운로드
    const dlRes = await fetch(`${API_BASE}/api/models/${modelName}/download`);
    if (!dlRes.ok) {
      return { status: "download_failed", localVersion };
    }

    const blob = await dlRes.blob();
    const arrayBuffer = await blob.arrayBuffer();

    // IndexedDB에 저장
    await dbPut(MODEL_STORE, {
      name: modelName,
      version: serverInfo.version,
      checksum: serverInfo.checksum,
      weights: arrayBuffer,
      updatedAt: new Date().toISOString(),
    });

    return {
      status: "updated",
      oldVersion: localVersion,
      newVersion: serverInfo.version,
    };
  } catch (err) {
    console.warn("[OfflineEngine] 동기화 실패:", err.message);
    return { status: "offline", error: err.message };
  }
}

/**
 * 모든 모델 일괄 동기화
 */
export async function syncAllModels() {
  const modelNames = ["ppo_policy", "schedule_sim"];
  const results = {};
  for (const name of modelNames) {
    results[name] = await syncModel(name);
  }
  return results;
}

// ============================================================
// 오프라인 추론 (시뮬레이션)
// ============================================================

/** 활동별 시간당 효과 (서버 schedule_simulator.py와 동일) */
const ACTIVITY_EFFECTS = {
  sleep: { cal_burned: 50, sleep: 12, stress: -3, mood: 1, weight: -0.002 },
  meal_healthy: { cal_intake: 500, mood: 3, weight: -0.005, stress: -1 },
  meal_unhealthy: { cal_intake: 800, mood: 5, weight: 0.03, stress: 1.5 },
  meal_normal: { cal_intake: 600, mood: 2, weight: 0.005, stress: -0.5 },
  night_snack: { cal_intake: 400, sleep: -15, weight: 0.05, stress: 3, mood: 3 },
  exercise_cardio: { cal_burned: 500, sleep: 5, stress: -8, mood: 5, weight: -0.03 },
  exercise_strength: { cal_burned: 350, sleep: 3, stress: -5, mood: 4, weight: -0.01 },
  work: { cal_burned: 80, stress: 4, mood: -1 },
  hobby: { cal_burned: 60, stress: -6, mood: 6 },
  rest: { cal_burned: 50, stress: -2, mood: 2, sleep: 2 },
  commute: { cal_burned: 70, stress: 3, mood: -1 },
  other: { cal_burned: 60, stress: 0, mood: 0 },
};

const DEFAULT_STATE = {
  weight_kg: 75, bmi: 24.5, sleep_score: 60, stress_level: 50,
  mood_score: 50, hair_loss_risk: 20, blood_purity: 70,
  reactive_oxygen: 65, cholesterol_risk: 20,
};

const clamp = (v, min, max) => Math.min(max, Math.max(min, v));

/**
 * 오프라인 시뮬레이션 실행 (서버 불필요)
 * @param {Array} schedule - 스케줄 항목 배열
 * @param {number} days - 시뮬레이션 일수
 * @param {Object|null} initialState - 초기 상태
 * @returns {Object} 시뮬레이션 결과
 */
export function offlineSimulate(schedule, days = 30, initialState = null) {
  const state = { ...DEFAULT_STATE, ...(initialState || {}) };
  const initial = { ...state };
  const history = [];
  let weeklyExercise = 0;

  for (let day = 1; day <= days; day++) {
    let dailyCalIn = 0, dailyCalOut = 0, dailySleep = 0, dailyExercise = 0;

    for (const entry of schedule) {
      if ((day - 1) % (entry.repeat_cycle || 1) !== 0) continue;
      const duration = entry.end_hour > entry.start_hour
        ? entry.end_hour - entry.start_hour
        : entry.end_hour + 24 - entry.start_hour;
      if (duration <= 0) continue;

      const fx = ACTIVITY_EFFECTS[entry.activity] || ACTIVITY_EFFECTS.other;

      dailyCalIn += (fx.cal_intake || 0) * duration;
      dailyCalOut += (fx.cal_burned || 0) * duration;
      state.stress_level = clamp(state.stress_level + (fx.stress || 0) * duration, 0, 100);
      state.mood_score = clamp(state.mood_score + (fx.mood || 0) * duration, 0, 100);
      state.weight_kg += (fx.weight || 0) * duration;

      if (entry.activity === "sleep") dailySleep += duration;
      if (entry.activity.startsWith("exercise")) dailyExercise += duration;
      if ((fx.sleep || 0) > 0) state.sleep_score = clamp(state.sleep_score + fx.sleep * duration * 0.1, 0, 100);
    }

    const netCal = dailyCalIn - dailyCalOut;
    state.weight_kg += netCal * 0.0001;
    state.bmi = +(state.weight_kg / (1.75 ** 2)).toFixed(1);

    if (dailySleep < 6) {
      state.stress_level = clamp(state.stress_level + 3, 0, 100);
      state.mood_score = clamp(state.mood_score - 2, 0, 100);
    }

    weeklyExercise += dailyExercise;
    if (day % 7 === 0) {
      if (weeklyExercise < 2.5) {
        state.blood_purity = clamp(state.blood_purity - 2, 0, 100);
        state.reactive_oxygen = clamp(state.reactive_oxygen + 1, 0, 100);
      } else {
        state.blood_purity = clamp(state.blood_purity + 1, 0, 100);
        state.reactive_oxygen = clamp(state.reactive_oxygen - 1, 0, 100);
      }
      weeklyExercise = 0;
    }

    history.push({
      day,
      weight_kg: +state.weight_kg.toFixed(2),
      bmi: state.bmi,
      sleep_score: +state.sleep_score.toFixed(1),
      stress_level: +state.stress_level.toFixed(1),
      mood_score: +state.mood_score.toFixed(1),
      calorie_intake: Math.round(dailyCalIn),
      calorie_burned: Math.round(dailyCalOut),
      sleep_hours: +dailySleep.toFixed(1),
      exercise_hours: +dailyExercise.toFixed(1),
    });
  }

  return {
    days,
    initial_state: initial,
    final_state: { ...state },
    daily_history: history,
    analysis: generateAnalysis(initial, state, history, days),
    source: "offline",
  };
}

function generateAnalysis(initial, final, history, days) {
  const problems = [];
  const advice = [];

  const avgSleep = history.reduce((s, d) => s + d.sleep_hours, 0) / days;
  const avgExercise = history.reduce((s, d) => s + d.exercise_hours, 0) / (days / 7);

  if (avgSleep < 6) {
    problems.push({ category: "수면", severity: "high", message: `평균 수면 ${avgSleep.toFixed(1)}시간 — 만성 수면 부족입니다.` });
    advice.push({ category: "수면", message: "최소 7시간 수면을 확보하세요." });
  }
  if (final.stress_level > 60) {
    problems.push({ category: "스트레스", severity: "high", message: `스트레스 ${final.stress_level.toFixed(0)}/100 — 매우 높은 수준입니다.` });
    advice.push({ category: "스트레스", message: "취미 활동을 하루 30분 이상 추가하세요." });
  }
  if (avgExercise < 2.5) {
    problems.push({ category: "운동", severity: "medium", message: `주간 운동 ${avgExercise.toFixed(1)}시간 — WHO 권장 미달입니다.` });
    advice.push({ category: "운동", message: "주 3회 이상 유산소 운동 30분을 추가하세요." });
  }

  return { problems, advice, source: "offline" };
}

// ============================================================
// 온라인/오프라인 자동 전환
// ============================================================

/**
 * 네트워크 상태에 따라 서버/오프라인 자동 선택 시뮬레이션
 * @param {Array} schedule
 * @param {number} days
 * @param {Object|null} initialState
 * @returns {Object} 시뮬레이션 결과 (source: "server" | "offline")
 */
export async function smartSimulate(schedule, days = 30, initialState = null) {
  // 온라인이면 서버 사용 시도
  if (navigator.onLine) {
    try {
      const axios = (await import("axios")).default;
      const res = await axios.post("/api/schedule/simulate", { schedule, days, initial_state: initialState });
      return { ...res.data, source: "server" };
    } catch (err) {
      console.warn("[SmartSimulate] 서버 실패, 오프라인 폴백:", err.message);
    }
  }

  // 오프라인 추론
  return offlineSimulate(schedule, days, initialState);
}

// ============================================================
// 상태 캐싱 (오프라인 시 최근 상태 사용)
// ============================================================

export async function cacheUserState(userId, state) {
  await dbPut(STATE_STORE, { key: `state_${userId}`, state, cachedAt: new Date().toISOString() });
}

export async function getCachedState(userId) {
  return dbGet(STATE_STORE, `state_${userId}`);
}
