"""환경변수 검증 스크립트 — 서버 시작 전 필수 키 확인.

사용법:
    python scripts/check_env.py

출력:
    각 환경변수의 설정 상태를 표시하고,
    필수 키가 누락되면 경고를 출력합니다.
"""

import os
import sys
from pathlib import Path

# .env 파일 로드 (dotenv 설치 시)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path, encoding="utf-8")
        print(f"[OK] .env 파일 로드: {env_path}")
    else:
        print(f"[!!] .env 파일 없음: {env_path}")
        print("     .env.example을 복사하여 .env를 생성하세요.")
except ImportError:
    print("[--] python-dotenv 미설치 (시스템 환경변수만 확인)")

print()

# 환경변수 정의: (이름, 필수 여부, 설명)
ENV_VARS = [
    ("OPENAI_API_KEY",      True,  "OpenAI API 키 (GPT-4o-mini)"),
    ("DATABASE_URL",        True,  "Supabase PostgreSQL 연결 URL"),
    ("JWT_SECRET",          True,  "JWT 토큰 서명 키"),
    ("KMA_API_KEY",         False, "기상청 단기예보 API 키"),
    ("AIRKOREA_API_KEY",    False, "에어코리아 대기오염 API 키"),
    ("KAKAO_CLIENT_ID",     False, "카카오 REST API 키"),
    ("KAKAO_CLIENT_SECRET", False, "카카오 Client Secret"),
    ("KAKAO_REDIRECT_URI",  False, "카카오 OAuth 리다이렉트 URI"),
    ("CHROMA_PATH",         False, "ChromaDB 저장 경로"),
    ("ENV",                 False, "실행 환경 (development/production)"),
    ("CORS_ORIGINS",        False, "허용 CORS 도메인"),
    ("AWS_ACCESS_KEY_ID",   False, "AWS S3 접근 키"),
    ("AWS_SECRET_ACCESS_KEY", False, "AWS S3 비밀 키"),
    ("S3_BUCKET_NAME",      False, "S3 버킷 이름"),
    ("FORCE_CPU",           False, "GPU 대신 CPU 강제 사용 (1=강제)"),
]

# 검증 실행
required_missing = []
optional_missing = []

print("=" * 60)
print("  LifeSync AI — 환경변수 검증")
print("=" * 60)
print()

for name, required, desc in ENV_VARS:
    value = os.getenv(name, "")
    has_value = bool(value.strip())
    tag = "필수" if required else "선택"

    if has_value:
        # 키 값의 일부만 표시 (보안)
        masked = value[:4] + "..." + value[-4:] if len(value) > 12 else "****"
        print(f"  [OK] {name:<25} = {masked:<20} ({desc})")
    else:
        marker = "!!" if required else "--"
        print(f"  [{marker}] {name:<25} = (미설정)              ({desc})")
        if required:
            required_missing.append(name)
        else:
            optional_missing.append(name)

print()
print("-" * 60)

if required_missing:
    print(f"\n  [경고] 필수 키 {len(required_missing)}개 미설정:")
    for name in required_missing:
        print(f"         - {name}")
    print()
    print("  .env 파일에 위 키들을 추가하세요.")
    print("  참고: .env.example 파일을 확인하세요.")
    sys.exit(1)
else:
    print(f"\n  [완료] 필수 키 모두 설정됨")
    if optional_missing:
        print(f"  [참고] 선택 키 {len(optional_missing)}개 미설정 (기능 제한 가능)")
    print()
    sys.exit(0)
