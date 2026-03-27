"""사용자 상태 관리자 — 40+ 차원 State 벡터 관리.

Supabase PostgreSQL에 사용자별 상태 벡터를 영속화한다.
DATABASE_URL이 없으면 인메모리 모드로 폴백한다.
pg8000 (순수 Python 드라이버) 사용.
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import urlparse, unquote

logger = logging.getLogger(__name__)

DATABASE_URL: str = os.getenv("DATABASE_URL", "")

# DB 컬럼과 매핑되는 주요 필드 목록
_DB_FIELDS = [
    "calorie_intake", "calorie_burned", "sleep_score", "stress_level",
    "weight_kg", "bmi", "blood_pressure_sys", "blood_pressure_dia",
    "mood_score", "weekly_achievement",
]


@dataclass
class StateVector:
    """40차원 사용자 상태 벡터.

    주요 필드 10개를 명시하고, 나머지 30개는 extra dict로 관리한다.
    """

    # --- 주요 필드 (10개) ---
    calorie_intake: float = 0.0  # 일일 칼로리 섭취량
    calorie_burned: float = 0.0  # 일일 칼로리 소모량
    sleep_score: float = 70.0  # 수면 점수 (0~100)
    stress_level: float = 50.0  # 스트레스 수준 (0~100)
    weight_kg: float = 70.0  # 현재 체중 (kg)
    bmi: float = 23.0  # BMI 지수
    blood_pressure_sys: float = 120.0  # 수축기 혈압
    blood_pressure_dia: float = 80.0  # 이완기 혈압
    mood_score: float = 60.0  # 기분 점수 (0~100)
    weekly_achievement: float = 0.0  # 주간 달성률 (0~1)

    # --- 나머지 30개 필드 (extra dict로 관리) ---
    extra: dict[str, float] = field(default_factory=dict)


class UserStateManager:
    """사용자 상태 벡터 관리자.

    Supabase PostgreSQL에 사용자별 StateVector를 저장/조회한다.
    DATABASE_URL이 없으면 인메모리 캐시만 사용한다.
    """

    def __init__(self) -> None:
        self._db_url = os.getenv("DATABASE_URL", "")
        self._cache: dict[str, StateVector] = {}
        self._conn = None
        self._connect_db()

    def _parse_url(self) -> dict:
        """DATABASE_URL을 pg8000 연결 파라미터로 파싱."""
        parsed = urlparse(self._db_url)
        return {
            "host": parsed.hostname,
            "port": parsed.port or 6543,
            "database": parsed.path.lstrip("/"),
            "user": unquote(parsed.username or ""),
            "password": unquote(parsed.password or ""),
            "ssl_context": True,
        }

    def _get_conn(self):
        """pg8000 연결을 반환. 끊어졌으면 재연결."""
        if self._conn is None:
            import pg8000
            params = self._parse_url()
            self._conn = pg8000.connect(**params)
        return self._conn

    def _connect_db(self) -> None:
        """Supabase PostgreSQL 연결 초기화."""
        if not self._db_url:
            logger.warning("DATABASE_URL 미설정 — 인메모리 모드로 동작")
            return
        try:
            self._get_conn()
            self._ensure_table()
            logger.info("Supabase PostgreSQL 연결 완료 (pg8000)")
        except Exception as e:
            logger.error("DB 연결 실패, 인메모리 모드로 폴백: %s", e)
            self._conn = None

    def _ensure_table(self) -> None:
        """user_states 테이블이 없으면 생성."""
        conn = self._get_conn()
        try:
            conn.run("""
                CREATE TABLE IF NOT EXISTS user_states (
                    user_id TEXT PRIMARY KEY,
                    calorie_intake FLOAT DEFAULT 0,
                    calorie_burned FLOAT DEFAULT 0,
                    sleep_score FLOAT DEFAULT 70,
                    stress_level FLOAT DEFAULT 50,
                    weight_kg FLOAT DEFAULT 70,
                    bmi FLOAT DEFAULT 23,
                    blood_pressure_sys FLOAT DEFAULT 120,
                    blood_pressure_dia FLOAT DEFAULT 80,
                    mood_score FLOAT DEFAULT 60,
                    weekly_achievement FLOAT DEFAULT 0,
                    extra JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
        except Exception as e:
            logger.warning("테이블 생성 스킵 (이미 존재할 수 있음): %s", e)

    def get_state(self, user_id: str) -> StateVector:
        """사용자 상태 벡터 조회.

        Args:
            user_id: 사용자 식별자.

        Returns:
            해당 사용자의 StateVector. 없으면 기본값 생성.
        """
        if user_id in self._cache:
            return self._cache[user_id]

        # DB에서 조회 시도
        if self._conn is not None:
            try:
                conn = self._get_conn()
                rows = conn.run(
                    "SELECT calorie_intake, calorie_burned, sleep_score, "
                    "stress_level, weight_kg, bmi, blood_pressure_sys, "
                    "blood_pressure_dia, mood_score, weekly_achievement, "
                    "extra FROM user_states WHERE user_id = :uid",
                    uid=user_id,
                )
                if rows:
                    row = rows[0]
                    extra_data = row[10] if row[10] else {}
                    if isinstance(extra_data, str):
                        extra_data = json.loads(extra_data)
                    state = StateVector(
                        calorie_intake=row[0],
                        calorie_burned=row[1],
                        sleep_score=row[2],
                        stress_level=row[3],
                        weight_kg=row[4],
                        bmi=row[5],
                        blood_pressure_sys=row[6],
                        blood_pressure_dia=row[7],
                        mood_score=row[8],
                        weekly_achievement=row[9],
                        extra=extra_data,
                    )
                    self._cache[user_id] = state
                    return state
            except Exception as e:
                logger.error("DB 조회 실패 (user_id=%s): %s", user_id, e)

        state = StateVector()
        self._cache[user_id] = state
        return state

    def update_state(
        self, user_id: str, delta: dict[str, float]
    ) -> StateVector:
        """사용자 상태 벡터 업데이트 (UPSERT).

        Args:
            user_id: 사용자 식별자.
            delta: 변경할 필드와 값의 딕셔너리.

        Returns:
            업데이트된 StateVector.
        """
        state = self.get_state(user_id)

        for key, value in delta.items():
            if hasattr(state, key) and key != "extra":
                setattr(state, key, value)
            else:
                state.extra[key] = value

        self._cache[user_id] = state

        # DB UPSERT
        if self._conn is not None:
            try:
                conn = self._get_conn()
                conn.run(
                    """
                    INSERT INTO user_states (
                        user_id, calorie_intake, calorie_burned, sleep_score,
                        stress_level, weight_kg, bmi, blood_pressure_sys,
                        blood_pressure_dia, mood_score, weekly_achievement, extra
                    ) VALUES (
                        :uid, :ci, :cb, :ss, :sl, :wk, :bmi, :bps, :bpd, :ms, :wa, :ex
                    )
                    ON CONFLICT (user_id) DO UPDATE SET
                        calorie_intake = EXCLUDED.calorie_intake,
                        calorie_burned = EXCLUDED.calorie_burned,
                        sleep_score = EXCLUDED.sleep_score,
                        stress_level = EXCLUDED.stress_level,
                        weight_kg = EXCLUDED.weight_kg,
                        bmi = EXCLUDED.bmi,
                        blood_pressure_sys = EXCLUDED.blood_pressure_sys,
                        blood_pressure_dia = EXCLUDED.blood_pressure_dia,
                        mood_score = EXCLUDED.mood_score,
                        weekly_achievement = EXCLUDED.weekly_achievement,
                        extra = EXCLUDED.extra,
                        updated_at = NOW()
                    """,
                    uid=user_id,
                    ci=state.calorie_intake,
                    cb=state.calorie_burned,
                    ss=state.sleep_score,
                    sl=state.stress_level,
                    wk=state.weight_kg,
                    bmi=state.bmi,
                    bps=state.blood_pressure_sys,
                    bpd=state.blood_pressure_dia,
                    ms=state.mood_score,
                    wa=state.weekly_achievement,
                    ex=json.dumps(state.extra),
                )
            except Exception as e:
                logger.error("DB UPSERT 실패 (user_id=%s): %s", user_id, e)

        return state

    def to_dict(self, user_id: str) -> dict[str, Any]:
        """상태 벡터를 딕셔너리로 변환.

        Args:
            user_id: 사용자 식별자.

        Returns:
            StateVector의 딕셔너리 표현 (extra 필드 펼침).
        """
        state = self.get_state(user_id)
        result = asdict(state)
        extra = result.pop("extra", {})
        result.update(extra)
        return result

    def close(self) -> None:
        """연결 종료. FastAPI 종료 시 호출."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("DB 연결 종료 완료")
