from tests.conftest import create_confirmed_pack


def test_sql_pack_requires_confirmed_spec(env, golden_request):
    draft = env.client.post("/api/v1/change-specs/interpret", json=golden_request).json()

    response = env.client.post(f"/api/v1/change-specs/{draft['specId']}/sql-pack")

    assert response.status_code == 409
    assert response.json()["code"] == "SPEC_NOT_CONFIRMED"


def test_generates_five_deterministic_sql_artifacts(env, golden_request):
    spec_id, pack = create_confirmed_pack(env, golden_request)

    assert pack["specId"] == spec_id
    assert pack["rollbackStatus"] == "TEMPLATE_REQUIRES_BACKUP_ROWS"
    for name in ("precheckSql", "backupSql", "executionSql", "verificationSql", "rollbackSql"):
        assert pack[name].strip()
    assert 'UPDATE "public"."orders"' in pack["executionSql"]
    assert '"tenant_id" = 42' in pack["executionSql"]
    assert '"status" = \'pending\'' in pack["executionSql"]
    assert '"created_at" < \'2026-09-01T00:00:00+09:00\'' in pack["executionSql"]


def test_sql_edit_increments_revision_and_stales_previous_review(env, golden_request):
    spec_id, pack = create_confirmed_pack(env, golden_request)
    reviewed = env.client.post(f"/api/v1/change-specs/{spec_id}/review", json={})
    assert reviewed.status_code == 200
    assert env.repository.get_review(spec_id).is_stale is False

    updated = env.client.put(
        f"/api/v1/change-specs/{spec_id}/sql-pack/executionSql",
        json={"sql": pack["executionSql"] + "\n-- reviewed by user"},
    )

    assert updated.status_code == 200
    assert updated.json()["revision"] == 2
    assert env.repository.get_review(spec_id).is_stale is True
