"""날씨 모니터 — AirKorea + OpenWeather API 연동."""

import logging
import os
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)


class WeatherMonitor:
    """AirKorea + OpenWeather 기반 날씨/대기질 모니터."""

    OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
    AIRKOREA_URL = (
        "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc"
        "/getMsrstnAcctoRltmMesureDnsty"
    )

    def __init__(self) -> None:
        self.airkorea_key = os.getenv("AIRKOREA_API_KEY", "")
        self.openweather_key = os.getenv("OPENWEATHER_API_KEY", "")

    async def get_weather(
        self, lat: float = 37.5665, lon: float = 126.9780
    ) -> dict[str, Any]:
        """현재 날씨 조회.

        Args:
            lat: 위도 (기본: 서울).
            lon: 경도 (기본: 서울).

        Returns:
            날씨 정보 딕셔너리.
        """
        if not self.openweather_key:
            logger.warning("OPENWEATHER_API_KEY 미설정 — 기본값 반환")
            return self._default_weather()

        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.openweather_key,
            "units": "metric",
            "lang": "kr",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.OPENWEATHER_URL, params=params)
                response.raise_for_status()
                data = response.json()

            return {
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "weather_main": data["weather"][0]["main"],
                "weather_description": data["weather"][0]["description"],
                "wind_speed": data["wind"]["speed"],
            }
        except Exception:
            logger.exception("날씨 API 호출 실패")
            return self._default_weather()

    async def get_air_quality(
        self, station_name: str = "종로구"
    ) -> dict[str, Any]:
        """대기질 정보 조회.

        Args:
            station_name: 측정소 이름 (기본: 종로구).

        Returns:
            대기질 정보 딕셔너리.
        """
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
                return self._default_air_quality()

            item = items[0]
            return {
                "pm10": float(item.get("pm10Value", 0) or 0),
                "pm25": float(item.get("pm25Value", 0) or 0),
                "o3": float(item.get("o3Value", 0) or 0),
                "no2": float(item.get("no2Value", 0) or 0),
                "co": float(item.get("coValue", 0) or 0),
                "so2": float(item.get("so2Value", 0) or 0),
                "grade": item.get("pm10Grade", ""),
            }
        except Exception:
            logger.exception("대기질 API 호출 실패")
            return self._default_air_quality()

    async def get_combined(
        self,
        lat: float = 37.5665,
        lon: float = 126.9780,
        station_name: str = "종로구",
    ) -> dict[str, Any]:
        """날씨 + 대기질 통합 조회.

        Args:
            lat: 위도.
            lon: 경도.
            station_name: 대기질 측정소 이름.

        Returns:
            통합된 환경 정보.
        """
        weather = await self.get_weather(lat, lon)
        air = await self.get_air_quality(station_name)
        return {**weather, **air}

    def _default_weather(self) -> dict[str, Any]:
        """기본 날씨 데이터 (API 미연동 시)."""
        return {
            "temperature": 20.0,
            "humidity": 50.0,
            "weather_main": "Clear",
            "weather_description": "맑음",
            "wind_speed": 3.0,
        }

    def _default_air_quality(self) -> dict[str, Any]:
        """기본 대기질 데이터 (API 미연동 시)."""
        return {
            "pm10": 35.0,
            "pm25": 15.0,
            "o3": 0.03,
            "no2": 0.02,
            "co": 0.5,
            "so2": 0.003,
            "grade": "1",
        }
