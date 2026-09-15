# ChangeSpec Reviewer Backend

운영 PostgreSQL 데이터 변경 요청을 구조화하고, 확인·백업·실행·검증·롤백 SQL 사이의 의미적 정합성을 실행 전에 검토하는 FastAPI 백엔드입니다.

## 현재 지원 범위

- PostgreSQL 단일 테이블 `UPDATE` / `DELETE`
- 자연어 요청을 ChangeSpec 초안으로 구조화
- 결정론적 SQL 5종 생성
- SQLGlot 기반 정적 검토
- `READY` / `REVIEW` / `BLOCK` 판정과 B001~B008, R001~R004 근거 제공
- 실제 DB 연결·SQL 실행은 하지 않음
- 데이터는 인메모리 저장소에 보관되므로 서버 재시작 시 사라짐

## 로컬 실행

Python 3.11 이상을 권장합니다.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

기본값인 `SOLAR_MODE=fake`에서는 API 키 없이 골든 데모 요청을 사용할 수 있습니다. 실제 Solar API를 사용할 때만 셸이나 배포 환경에 `UPSTAGE_API_KEY`를 설정하고 `SOLAR_MODE=real`로 변경하세요. `.env.example`은 필요한 환경변수 목록을 보여주는 참고 파일이며, 실제 키는 저장소에 커밋하지 않습니다.

## 테스트

```bash
cd backend
PYTHONPATH=. python -m pytest tests -q
```

현재 기준 검증 결과는 `15 passed`입니다.

## 주요 API

- `GET /health`
- `POST /api/v1/change-specs/interpret`
- `POST /api/v1/change-specs/{specId}/confirm`
- `GET /api/v1/change-specs/{specId}`
- `POST /api/v1/change-specs/{specId}/sql-pack`
- `PUT /api/v1/change-specs/{specId}/sql-pack/{artifactName}`
- `POST /api/v1/change-specs/{specId}/review`

서버 실행 후 Swagger UI는 `http://localhost:8000/docs`, OpenAPI JSON은 `http://localhost:8000/openapi.json`에서 확인할 수 있습니다.

## 선택적 Solar 연결 확인

```bash
cd backend
UPSTAGE_API_KEY=... SOLAR_MODE=real PYTHONPATH=. python scripts/solar_smoke.py
```

키가 없으면 스크립트는 실제 API를 호출하지 않고 안전하게 종료합니다.

## 판정 해석

- `BLOCK`: 실행 SQL이 확정 명세와 충돌하거나 안전 필수조건을 위반함
- `REVIEW`: 치명적 불일치는 없지만 롤백 데이터, 실행계획 등 사람이 확인해야 할 항목이 남음
- `READY`: 현재 정적 규칙에서 차단·검토 항목이 모두 해소됨

판정은 정적 검토 결과이며 실제 실행 승인이나 무사 실행을 보장하지 않습니다.
