from app.domain.enums import Operation, Operator, ValueType
from app.domain.models import ChangeSpecDraft, Mutation, Predicate
from app.services.solar_client import FakeSolarClient


def test_interpret_and_confirm_flow(env, golden_request):
    interpreted = env.client.post("/api/v1/change-specs/interpret", json=golden_request)
    assert interpreted.status_code == 201
    draft = interpreted.json()
    assert draft["status"] == "DRAFT"
    assert draft["targetTable"] == "orders"
    assert draft["contentHash"]

    confirmed = env.client.post(
        f"/api/v1/change-specs/{draft['specId']}/confirm",
        json={"expectedRowCount": 18},
    )
    assert confirmed.status_code == 200
    result = confirmed.json()
    assert result["status"] == "CONFIRMED"
    assert result["version"] == 2
    assert result["expectedRowCount"] == 18


def test_confirm_rejects_unresolved_questions(env, golden_request):
    env.client.app.state.solar_client = FakeSolarClient(
        ChangeSpecDraft(
            targetTable="orders",
            identityKeyColumns=["id"],
            operation=Operation.UPDATE,
            predicates=[
                Predicate(column="tenant_id", operator=Operator.EQ, value=42, valueType=ValueType.NUMBER)
            ],
            mutations=[Mutation(column="status", value="cancelled", valueType=ValueType.STRING)],
            unresolvedQuestions=["What is the cutoff time?"],
        )
    )
    interpreted = env.client.post("/api/v1/change-specs/interpret", json=golden_request)
    spec_id = interpreted.json()["specId"]

    response = env.client.post(f"/api/v1/change-specs/{spec_id}/confirm", json={})

    assert response.status_code == 409
    assert response.json()["code"] == "UNRESOLVED_QUESTIONS"
    assert response.json()["requestId"]


def test_second_confirm_is_conflict(env, golden_request):
    draft = env.client.post("/api/v1/change-specs/interpret", json=golden_request).json()
    path = f"/api/v1/change-specs/{draft['specId']}/confirm"
    assert env.client.post(path, json={}).status_code == 200

    response = env.client.post(path, json={})

    assert response.status_code == 409
    assert response.json()["code"] == "SPEC_NOT_DRAFT"


def test_not_found_and_validation_errors_use_common_shape(env):
    missing = env.client.get("/api/v1/change-specs/not-found")
    invalid = env.client.post("/api/v1/change-specs/interpret", json={})

    assert missing.status_code == 404
    assert set(missing.json()) == {"code", "message", "details", "requestId"}
    assert invalid.status_code == 422
    assert set(invalid.json()) == {"code", "message", "details", "requestId"}


def test_value_types_are_corrected_by_schema_input(env, golden_request):
    fake_solar = FakeSolarClient(
        ChangeSpecDraft(
            targetTable="orders",
            identityKeyColumns=["id"],
            operation=Operation.UPDATE,
            predicates=[
                Predicate(column="tenant_id", operator=Operator.EQ, value=42, valueType=ValueType.STRING),
                Predicate(column="status", operator=Operator.EQ, value="pending", valueType=ValueType.STRING),
                Predicate(column="created_at", operator=Operator.LT, value="2026-09-01T00:00:00+09:00", valueType=ValueType.STRING),
            ],
            mutations=[Mutation(column="status", value="cancelled", valueType=ValueType.STRING)],
            unresolvedQuestions=[],
        )
    )
    env.client.app.state.solar_client = fake_solar

    interpreted = env.client.post("/api/v1/change-specs/interpret", json=golden_request)
    assert interpreted.status_code == 201
    draft = interpreted.json()

    predicates_by_column = {p["column"]: p for p in draft["predicates"]}
    assert predicates_by_column["tenant_id"]["valueType"] == "NUMBER"
    assert predicates_by_column["status"]["valueType"] == "STRING"
    assert predicates_by_column["created_at"]["valueType"] == "TIMESTAMP"

    mutations_by_column = {m["column"]: m for m in draft["mutations"]}
    assert mutations_by_column["status"]["valueType"] == "STRING"
