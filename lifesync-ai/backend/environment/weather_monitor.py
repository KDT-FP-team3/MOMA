"""날씨 모니터 — 기상청 단기예보 + 에어코리아 대기오염 API 연동.

한국 공공데이터포털 API를 사용합니다.
- 기상청 초단기실황: 기온, 습도, 풍속, 강수형태
- 에어코리아: PM10, PM2.5, 오존, 일산화탄소 등

필요 환경변수:
    KMA_API_KEY       — 기상청 단기예보 인증키 (data.go.kr)
    AIRKOREA_API_KEY  — 에어코리아 대기오염 인증키 (data.go.kr)
"""

import datetime
import logging
import math
import os
import time
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)


# ── 위경도 → 기상청 격자 변환 ────────────────────────────
# 기상청 제공 Lambert Conformal Conic 투영 공식

_RE = 6371.00877       # 지구 반경 (km)
_GRID = 5.0            # 격자 간격 (km)
_SLAT1 = 30.0          # 투영 위도 1 (degree)
_SLAT2 = 60.0          # 투영 위도 2 (degree)
_OLON = 126.0          # 기준점 경도 (degree)
_OLAT = 38.0           # 기준점 위도 (degree)
_XO = 43               # 기준점 X좌표 (격자)
_YO = 136              # 기준점 Y좌표 (격자)


def _latlon_to_grid(lat: float, lon: float) -> tuple[int, int]:
    """위경도 → 기상청 격자좌표(nx, ny) 변환.

    기상청이 제공하는 Lambert Conformal Conic 투영 공식을 사용합니다.
    서울(37.5665, 126.9780) → (60, 127)

    Args:
        lat: 위도 (도 단위)
        lon: 경도 (도 단위)

    Returns:
        (nx, ny) 격자 좌표 튜플
    """
    deg_rad = math.pi / 180.0
    re = _RE / _GRID
    slat1 = _SLAT1 * deg_rad
    slat2 = _SLAT2 * deg_rad
    olon = _OLON * deg_rad
    olat = _OLAT * deg_rad

    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(
        math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    )
    sf = (math.tan(math.pi * 0.25 + slat1 * 0.5) ** sn) * math.cos(slat1) / sn
    ro = re * sf / (math.tan(math.pi * 0.25 + olat * 0.5) ** sn)

    ra = re * sf / (math.tan(math.pi * 0.25 + lat * deg_rad * 0.5) ** sn)
    theta = lon * deg_rad - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    nx = int(ra * math.sin(theta) + _XO + 0.5)
    ny = int(ro - ra * math.cos(theta) + _YO + 0.5)
    return nx, ny


# ── 하늘 상태 / 강수 형태 코드 → 한국어 ────────────────

_SKY_CODE = {
    "1": "맑음",
    "3": "구름많음",
    "4": "흐림",
}

_PTY_CODE = {
    "0": "없음",
    "1": "비",
    "2": "비/눈",
    "3": "눈",
    "5": "빗방울",
    "6": "빗방울눈날림",
    "7": "눈날림",
}


class WeatherMonitor:
    """기상청 + 에어코리아 기반 날씨/대기질 모니터.

    10분 캐싱을 사용하여 API 호출 횟수를 절약합니다.
    API 키가 없거나 호출 실패 시 기본값을 반환합니다.
    """

    # 기상청 초단기실황 API
    KMA_URL = (
        "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"
        "/getUltraSrtNcst"
    )

    # 에어코리아 실시간 대기오염 API
    AIRKOREA_URL = (
        "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc"
        "/getMsrstnAcctoRltmMesureDnsty"
    )

    # 캐시 유효 시간 (초)
    _CACHE_TTL = 600  # 10분

    def __init__(self) -> None:
        self.kma_key = os.getenv("KMA_API_KEY", "")
        self.airkorea_key = os.getenv("AIRKOREA_API_KEY", "")

        # 캐시: {key: (timestamp, data)}
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}

    def _get_cached(self, key: str) -> dict[str, Any] | None:
        """캐시에서 데이터 조회. 만료되었으면 None."""
        if key in self._cache:
            ts, data = self._cache[key]
            if time.time() - ts < self._CACHE_TTL:
                return data
        return None

    def _set_cached(self, key: str, data: dict[str, Any]) -> None:
        """캐시에 데이터 저장."""
        self._cache[key] = (time.time(), data)

    # ── 기상청 날씨 조회 ────────────────────────────────

    async def get_weather(
        self, lat: float = 37.5665, lon: float = 126.9780
    ) -> dict[str, Any]:
        """기상청 초단기실황 조회.

        위경도를 격자좌표로 변환하여 기상청 API를 호출합니다.

        Args:
            lat: 위도 (기본: 서울 시청)
            lon: 경도 (기본: 서울 시청)

        Returns:
            {temperature, humidity, wind_speed, weather_main, weather_description}
        """
        # 캐시 확인
        cache_key = f"weather_{lat:.2f}_{lon:.2f}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        # API 키 확인
        if not self.kma_key:
            logger.warning("KMA_API_KEY 미설정 — 기본값 반환")
            return self._default_weather()

        # 위경도 → 격자 변환
        nx, ny = _latlon_to_grid(lat, lon)

        # 현재 시각에서 가장 가까운 정시 base_time 계산
        # 초단기실황은 매시 정각 생성, 10분 후 API 제공
        now = datetime.datetime.now()
        # 현재 분이 40분 이전이면 1시간 전 데이터 사용 (API 제공 지연 고려)
        if now.minute < 40:
            now = now - datetime.timedelta(hours=1)
        base_date = now.strftime("%Y%m%d")
        base_time = now.strftime("%H00")

        params = {
            "serviceKey": self.kma_key,
            "numOfRows": "10",
            "pageNo": "1",
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": str(nx),
            "ny": str(ny),
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.KMA_URL, params=params)
                response.raise_for_status()
                data = response.json()

            # 응답 파싱
            items = (
                data.get("response", {})
                .get("body", {})
                .get("items", {})
                .get("item", [])
            )

            if not items:
                logger.warning("기상청 응답 데이터 없음 (base_date=%s, base_time=%s)", base_date, base_time)
                return self._default_weather()

            # 카테고리별 값 추출
            values: dict[str, str] = {}
            for item in items:
                category = item.get("category", "")
                value = item.get("obsrValue", "")
                values[category] = value

            # T1H: 기온, REH: 습도, WSD: 풍속, PTY: 강수형태, RN1: 1시간 강수량
            temperature = float(values.get("T1H", "20"))
            humidity = float(values.get("REH", "50"))
            wind_speed = float(values.get("WSD", "3"))
            pty_code = values.get("PTY", "0")

            # 강수형태 → 날씨 설명
            weather_desc = _PTY_CODE.get(pty_code, "없음")
            if pty_code == "0":
                weather_main = "Clear"
                weather_desc = "맑음"
            elif pty_code in ("1", "5"):
                weather_main = "Rain"
            elif pty_code in ("3", "7"):
                weather_main = "Snow"
            else:
                weather_main = "Rain"

            result = {
                "temperature": temperature,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "weather_main": weather_main,
                "weather_description": weather_desc,
                "precipitation": values.get("RN1", "0"),
                "source": "기상청 초단기실황",
            }

            self._set_cached(cache_key, result)
            logger.info(
                "기상청 날씨 조회 성공: %.1f°C, %s (nx=%d, ny=%d)",
                temperature, weather_desc, nx, ny,
            )
            return result

        except Exception:
            logger.exception("기상청 API 호출 실패")
            return self._default_weather()

    # ── 에어코리아 대기질 조회 ──────────────────────────

    async def get_air_quality(
        self, station_name: str = "종로구"
    ) -> dict[str, Any]:
        """에어코리아 실시간 대기오염 조회.

        Args:
            station_name: 측정소 이름 (기본: 종로구)

        Returns:
            {pm10, pm25, o3, no2, co, so2, grade}
        """
        # 캐시 확인
        cache_key = f"air_{station_name}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        if not self.airkorea_key:
            logger.warning("AIRKOREA_API_KEY 미설정 — 기본값 반환")
            return self._default_air_quality()

        params = {
            "serviceKey": self.airkorea_key,
            "stationName": quote(station_name),
            "dataTerm": "DAILY",
            "returnType": "json",
            "numOfRows": "1",
            "pageNo": "1",
            "ver": "1.0",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.AIRKOREA_URL, params=params)
                response.raise_for_status()
                data = response.json()

            items = data.get("response", {}).get("body", {}).get("items", [])
            if not items:
                logger.warning("에어코리아 응답 데이터 없음 (station=%s)", station_name)
                return self._default_air_quality()

            item = items[0]
            result = {
                "pm10": float(item.get("pm10Value", 0) or 0),
                "pm25": float(item.get("pm25Value", 0) or 0),
                "o3": float(item.get("o3Value", 0) or 0),
                "no2": float(item.get("no2Value", 0) or 0),
                "co": float(item.get("coValue", 0) or 0),
                "so2": float(item.get("so2Value", 0) or 0),
                "grade": item.get("pm10Grade", ""),
                "source": "에어코리아",
            }

            self._set_cached(cache_key, result)
            logger.info(
                "에어코리아 대기질 조회 성공: PM10=%.0f, PM2.5=%.0f (측정소=%s)",
                result["pm10"], result["pm25"], station_name,
            )
            return result

        except Exception:
            logger.exception("에어코리아 API 호출 실패")
            return self._default_air_quality()

    # ── 통합 조회 ───────────────────────────────────────

    async def get_combined(
        self,
        lat: float = 37.5665,
        lon: float = 126.9780,
        station_name: str = "종로구",
    ) -> dict[str, Any]:
        """날씨 + 대기질 통합 조회.

        두 API를 각각 호출하고 결과를 합칩니다.
        하나가 실패해도 다른 하나는 정상 반환합니다.
        """
        weather = await self.get_weather(lat, lon)
        air = await self.get_air_quality(station_name)
        return {**weather, **air}

    # ── 기본값 (API 미연동 시) ──────────────────────────

    def _default_weather(self) -> dict[str, Any]:
        """기본 날씨 데이터."""
        return {
            "temperature": 20.0,
            "humidity": 50.0,
            "wind_speed": 3.0,
            "weather_main": "Clear",
            "weather_description": "맑음",
            "precipitation": "0",
            "source": "기본값",
        }

    def _default_air_quality(self) -> dict[str, Any]:
        """기본 대기질 데이터."""
        return {
            "pm10": 35.0,
            "pm25": 15.0,
            "o3": 0.03,
            "no2": 0.02,
            "co": 0.5,
            "so2": 0.003,
            "grade": "1",
            "source": "기본값",
        }
