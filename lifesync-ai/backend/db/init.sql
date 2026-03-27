-- LifeSync AI: Supabase 사용자 상태 테이블
-- Supabase 대시보드 > SQL Editor에서 실행

CREATE TABLE IF NOT EXISTS user_states (
    user_id        TEXT PRIMARY KEY,
    calorie_intake FLOAT DEFAULT 0,
    calorie_burned FLOAT DEFAULT 0,
    sleep_score    FLOAT DEFAULT 70,
    stress_level   FLOAT DEFAULT 50,
    weight_kg      FLOAT DEFAULT 70,
    bmi            FLOAT DEFAULT 23,
    blood_pressure_sys FLOAT DEFAULT 120,
    blood_pressure_dia FLOAT DEFAULT 80,
    mood_score     FLOAT DEFAULT 60,
    weekly_achievement FLOAT DEFAULT 0,
    extra          JSONB DEFAULT '{}',
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_updated_at ON user_states;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON user_states
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

-- 인덱스: updated_at 기준 조회 최적화
CREATE INDEX IF NOT EXISTS idx_user_states_updated
    ON user_states (updated_at DESC);
