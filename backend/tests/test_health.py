def test_health_does_not_call_solar(env):
    response = env.client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "changespec-reviewer",
        "version": "0.1.0",
    }
    assert env.solar.call_count == 0
    assert response.headers["X-Request-ID"]


def test_openapi_contains_required_paths(env):
    response = env.client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/health" in paths
    assert "/api/v1/change-specs/interpret" in paths
    assert "/api/v1/change-specs/{spec_id}/confirm" in paths
    assert "/api/v1/change-specs/{spec_id}/sql-pack/{artifact_name}" in paths
    assert "/api/v1/change-specs/{spec_id}/review" in paths
