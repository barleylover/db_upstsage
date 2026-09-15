from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from openai import APIConnectionError, APIError, APITimeoutError, OpenAI, RateLimitError
from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import SolarError
from app.domain.enums import DBMS, Operation, Operator, ValueType
from app.domain.models import ChangeSpecDraft, InterpretChangeRequest, Mutation, Predicate


class SolarClient(Protocol):
    def interpret(self, request: InterpretChangeRequest) -> ChangeSpecDraft: ...


class UpstageSolarClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.upstage_api_key:
            raise SolarError("SOLAR_KEY_MISSING", "UPSTAGE_API_KEY is not configured")
        self._model = settings.upstage_model
        self._client = OpenAI(
            api_key=settings.upstage_api_key,
            base_url=settings.upstage_base_url,
            timeout=settings.upstage_timeout_seconds,
            max_retries=2,
        )
        prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "interpret_change_request.md"
        self._system_prompt = prompt_path.read_text(encoding="utf-8")

    def interpret(self, request: InterpretChangeRequest) -> ChangeSpecDraft:
        safe_payload = {
            "originalRequest": request.original_request,
            "schemaInput": request.schema_input.model_dump(by_alias=True, mode="json"),
        }
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": json.dumps(safe_payload, ensure_ascii=False)},
                ],
                reasoning_effort="medium",
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "change_spec_draft",
                        "strict": True,
                        "schema": ChangeSpecDraft.model_json_schema(),
                    },
                },
            )
        except APITimeoutError as exc:
            raise SolarError("SOLAR_TIMEOUT", "Solar request timed out") from exc
        except RateLimitError as exc:
            raise SolarError("SOLAR_RATE_LIMIT", "Solar rate limit was exceeded") from exc
        except APIConnectionError as exc:
            raise SolarError("SOLAR_CONNECTION_ERROR", "Could not connect to Solar") from exc
        except APIError as exc:
            raise SolarError("SOLAR_API_ERROR", "Solar returned an API error") from exc

        if not response.choices or not response.choices[0].message.content:
            raise SolarError("SOLAR_EMPTY_RESPONSE", "Solar returned an empty response")
        try:
            data = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as exc:
            raise SolarError("SOLAR_INVALID_JSON", "Solar returned invalid JSON") from exc
        try:
            return ChangeSpecDraft.model_validate(data)
        except ValidationError as exc:
            raise SolarError(
                "SOLAR_SCHEMA_MISMATCH",
                "Solar response did not match ChangeSpecDraft",
                details=exc.errors(include_input=False),
            ) from exc


class FakeSolarClient:
    """Deterministic client used by tests and the local demo."""

    def __init__(self, draft: ChangeSpecDraft | None = None) -> None:
        self._draft = draft
        self.call_count = 0

    def interpret(self, request: InterpretChangeRequest) -> ChangeSpecDraft:
        self.call_count += 1
        if self._draft is not None:
            return self._draft.model_copy(deep=True)
        return ChangeSpecDraft(
            dbms=DBMS.POSTGRESQL,
            environment="production",
            database=request.schema_input.database,
            schema=request.schema_input.schema,
            target_table="orders",
            identity_key_columns=["id"],
            operation=Operation.UPDATE,
            predicates=[
                Predicate(column="tenant_id", operator=Operator.EQ, value=42, value_type=ValueType.NUMBER),
                Predicate(column="status", operator=Operator.EQ, value="pending", value_type=ValueType.STRING),
                Predicate(
                    column="created_at",
                    operator=Operator.LT,
                    value="2026-09-01T00:00:00+09:00",
                    value_type=ValueType.TIMESTAMP,
                ),
            ],
            mutations=[
                Mutation(column="status", value="cancelled", value_type=ValueType.STRING)
            ],
            assumptions=[],
            unresolved_questions=[],
        )
