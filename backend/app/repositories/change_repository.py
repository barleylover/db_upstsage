from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Protocol

from app.core.errors import NotFoundError
from app.domain.models import ChangeSpec, ReviewResult, SchemaInput, SqlPack


class ChangeRepository(Protocol):
    def create_spec(self, spec: ChangeSpec, schema_input: SchemaInput) -> None: ...

    def get_spec(self, spec_id: str) -> ChangeSpec: ...

    def get_schema(self, spec_id: str) -> SchemaInput: ...

    def replace_spec(self, spec: ChangeSpec) -> None: ...

    def save_sql_pack(self, sql_pack: SqlPack) -> None: ...

    def get_sql_pack(self, spec_id: str) -> SqlPack: ...

    def save_review(self, review: ReviewResult) -> None: ...

    def get_review(self, spec_id: str) -> ReviewResult | None: ...

    def mark_review_stale(self, spec_id: str) -> None: ...


class InMemoryChangeRepository:
    """Thread-safe demo repository. Contents are lost on process restart."""

    def __init__(self) -> None:
        self._specs: dict[str, ChangeSpec] = {}
        self._schemas: dict[str, SchemaInput] = {}
        self._sql_packs: dict[str, SqlPack] = {}
        self._reviews: dict[str, ReviewResult] = {}
        self._lock = RLock()

    def create_spec(self, spec: ChangeSpec, schema_input: SchemaInput) -> None:
        with self._lock:
            self._specs[spec.spec_id] = deepcopy(spec)
            self._schemas[spec.spec_id] = deepcopy(schema_input)

    def get_spec(self, spec_id: str) -> ChangeSpec:
        with self._lock:
            try:
                return deepcopy(self._specs[spec_id])
            except KeyError as exc:
                raise NotFoundError("ChangeSpec", spec_id) from exc

    def get_schema(self, spec_id: str) -> SchemaInput:
        with self._lock:
            try:
                return deepcopy(self._schemas[spec_id])
            except KeyError as exc:
                raise NotFoundError("SchemaInput", spec_id) from exc

    def replace_spec(self, spec: ChangeSpec) -> None:
        with self._lock:
            if spec.spec_id not in self._specs:
                raise NotFoundError("ChangeSpec", spec.spec_id)
            self._specs[spec.spec_id] = deepcopy(spec)

    def save_sql_pack(self, sql_pack: SqlPack) -> None:
        with self._lock:
            self._sql_packs[sql_pack.spec_id] = deepcopy(sql_pack)

    def get_sql_pack(self, spec_id: str) -> SqlPack:
        with self._lock:
            try:
                return deepcopy(self._sql_packs[spec_id])
            except KeyError as exc:
                raise NotFoundError("SqlPack", spec_id) from exc

    def save_review(self, review: ReviewResult) -> None:
        with self._lock:
            self._reviews[review.spec_id] = deepcopy(review)

    def get_review(self, spec_id: str) -> ReviewResult | None:
        with self._lock:
            review = self._reviews.get(spec_id)
            return deepcopy(review) if review else None

    def mark_review_stale(self, spec_id: str) -> None:
        with self._lock:
            review = self._reviews.get(spec_id)
            if review:
                self._reviews[spec_id] = review.model_copy(update={"is_stale": True})
