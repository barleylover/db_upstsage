from tests.conftest import create_confirmed_pack


def _failed_rule_ids(review: dict) -> set[str]:
    return {check["ruleId"] for check in review["checks"] if check["status"] == "FAIL"}


def test_normal_pack_is_review_not_block(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)

    response = env.client.post(f"/api/v1/change-specs/{spec_id}/review", json={})

    assert response.status_code == 200
    review = response.json()
    assert review["verdict"] == "REVIEW"
    assert not _failed_rule_ids(review)
    assert {check["ruleId"] for check in review["checks"] if check["status"] == "REVIEW"} >= {
        "R001",
        "R002",
        "R003",
    }


def test_missing_tenant_predicate_is_b003_block(env, golden_request):
    spec_id, pack = create_confirmed_pack(env, golden_request)
    changed_sql = pack["executionSql"].replace(' AND\n  "tenant_id" = 42', "")
    env.client.put(
        f"/api/v1/change-specs/{spec_id}/sql-pack/executionSql",
        json={"sql": changed_sql},
    )

    review = env.client.post(f"/api/v1/change-specs/{spec_id}/review", json={}).json()

    assert review["verdict"] == "BLOCK"
    assert "B003" in _failed_rule_ids(review)
    check = next(item for item in review["checks"] if item["ruleId"] == "B003" and item["status"] == "FAIL")
    assert check["expected"] == "tenant_id = 42"
    assert check["actual"] == "missing"
    assert check["specField"] == "predicates[tenant_id]"
    assert check["sqlArtifact"] == "executionSql"
    assert check["suggestedFix"]


def test_where_removal_is_b001_block(env, golden_request):
    spec_id, pack = create_confirmed_pack(env, golden_request)
    sql_without_where = pack["executionSql"].split("\nWHERE ", 1)[0] + ";"
    env.client.put(
        f"/api/v1/change-specs/{spec_id}/sql-pack/executionSql",
        json={"sql": sql_without_where},
    )

    review = env.client.post(f"/api/v1/change-specs/{spec_id}/review", json={}).json()

    assert review["verdict"] == "BLOCK"
    assert "B001" in _failed_rule_ids(review)


def test_and_order_change_does_not_block(env, golden_request):
    spec_id, pack = create_confirmed_pack(env, golden_request)
    prefix, where = pack["executionSql"].split("\nWHERE ", 1)
    clauses = where.removesuffix(";").split(" AND\n  ")
    reordered = prefix + "\nWHERE " + " AND\n  ".join(reversed(clauses)) + ";"
    env.client.put(
        f"/api/v1/change-specs/{spec_id}/sql-pack/executionSql",
        json={"sql": reordered},
    )

    review = env.client.post(f"/api/v1/change-specs/{spec_id}/review", json={}).json()

    assert review["verdict"] == "REVIEW"
    assert not _failed_rule_ids(review)


def test_extra_predicate_and_mutation_change_block(env, golden_request):
    spec_id, pack = create_confirmed_pack(env, golden_request)
    changed = pack["executionSql"].replace("SET \"status\" = 'cancelled'", "SET \"status\" = 'completed'")
    changed = changed.replace("\nWHERE ", "\nWHERE \"id\" = 100 AND\n  ")
    env.client.put(
        f"/api/v1/change-specs/{spec_id}/sql-pack/executionSql",
        json={"sql": changed},
    )

    review = env.client.post(f"/api/v1/change-specs/{spec_id}/review", json={}).json()

    assert review["verdict"] == "BLOCK"
    assert {"B004", "B005"}.issubset(_failed_rule_ids(review))


def test_parse_error_is_b007_block(env, golden_request):
    spec_id, _ = create_confirmed_pack(env, golden_request)
    env.client.put(
        f"/api/v1/change-specs/{spec_id}/sql-pack/executionSql",
        json={"sql": "UPDATE ???"},
    )

    review = env.client.post(f"/api/v1/change-specs/{spec_id}/review", json={}).json()

    assert review["verdict"] == "BLOCK"
    assert "B007" in _failed_rule_ids(review)
