"""API 에러 핸들링 테스트."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


class TestQueryErrors:
    """POST /api/query 에러 케이스 테스트."""

    def test_query_invalid_domain(self) -> None:
        """유효하지 않은 도메인 → 400 응답, 크래시 방지."""
        response = client.post(
            "/api/query",
            json={"domain": "invalid_domain", "action": {}, "user_id": "test"},
        )
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_query_missing_fields(self) -> None:
        """필수 필드 누락 → 422 Validation Error."""
        response = client.post("/api/query", json={})
        assert response.status_code == 422
        assert "detail" in response.json()


class TestScheduleSimulateErrors:
    """POST /api/schedule/simulate 에러 케이스 테스트."""

    def test_schedule_simulate_empty(self) -> None:
        """빈 스케줄 → 정상 처리 (크래시 방지)."""
        response = client.post(
            "/api/schedule/simulate",
            json={"schedule": [], "days": 7},
        )
        assert response.status_code in (200, 400, 422)

    def test_schedule_simulate_invalid_cycle(self) -> None:
        """repeat_cycle=0 → 정상 처리 (크래시 방지)."""
        response = client.post(
            "/api/schedule/simulate",
            json={
                "schedule": [
                    {"activity": "sleep", "start_hour": 0, "end_hour": 6, "repeat_cycle": 0}
                ],
                "days": 7,
            },
        )
        assert response.status_code in (200, 400, 422)


class TestHealthEndpoint:
    """GET /health 엔드포인트 테스트."""

    def test_health_endpoint(self) -> None:
        """헬스체크 → 200 응답."""
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
