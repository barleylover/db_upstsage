from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Request

from app.domain.enums import ArtifactName
from app.domain.models import (
    ChangeDocument,
    ChangeSpec,
    ConfirmSpecRequest,
    DocumentReviewResult,
    GenerateChangeDocumentRequest,
    InterpretChangeRequest,
    ReviewChangeDocumentRequest,
    ReviewRequest,
    ReviewResult,
    SqlPack,
    UpdateSqlArtifactRequest,
)



from app.repositories.change_repository import ChangeRepository
from app.services.change_document_review_service import review_change_document
from app.services.change_document_service import generate_change_document
from app.services.review_service import review_change
from app.services.solar_client import SolarClient
from app.services.spec_service import SpecService
from app.services.sql_pack_service import generate_sql_pack, update_sql_artifact


api_router = APIRouter(prefix="/change-specs", tags=["change-specs"])


def get_repository(request: Request) -> ChangeRepository:
    return request.app.state.change_repository


def get_solar_client(request: Request) -> SolarClient:
    return request.app.state.solar_client


@api_router.post(
    "/interpret",
    response_model=ChangeSpec,
    status_code=201,
    summary="Interpret a natural-language change request",
)
def interpret_change_request(
    payload: InterpretChangeRequest,
    repository: ChangeRepository = Depends(get_repository),
    solar_client: SolarClient = Depends(get_solar_client),
) -> ChangeSpec:
    return SpecService(repository, solar_client).interpret(payload)


@api_router.post(
    "/{spec_id}/confirm",
    response_model=ChangeSpec,
    summary="Apply optional corrections and confirm a draft",
)
def confirm_change_spec(
    spec_id: str,
    payload: ConfirmSpecRequest,
    repository: ChangeRepository = Depends(get_repository),
    solar_client: SolarClient = Depends(get_solar_client),
) -> ChangeSpec:
    return SpecService(repository, solar_client).confirm(spec_id, payload)


@api_router.get("/{spec_id}", response_model=ChangeSpec, summary="Get the current ChangeSpec")
def get_change_spec(
    spec_id: str,
    repository: ChangeRepository = Depends(get_repository),
) -> ChangeSpec:
    return repository.get_spec(spec_id)


@api_router.post(
    "/{spec_id}/sql-pack",
    response_model=SqlPack,
    status_code=201,
    summary="Generate five deterministic SQL artifacts",
)
def create_sql_pack(
    spec_id: str,
    repository: ChangeRepository = Depends(get_repository),
) -> SqlPack:
    spec = repository.get_spec(spec_id)
    sql_pack = generate_sql_pack(spec, repository.get_schema(spec_id))
    repository.save_sql_pack(sql_pack)
    return sql_pack


@api_router.put(
    "/{spec_id}/sql-pack/{artifact_name}",
    response_model=SqlPack,
    summary="Replace one SQL artifact and invalidate the prior review",
)
def replace_sql_artifact(
    payload: UpdateSqlArtifactRequest,
    spec_id: str,
    artifact_name: ArtifactName = Path(),
    repository: ChangeRepository = Depends(get_repository),
) -> SqlPack:
    repository.get_spec(spec_id)
    return update_sql_artifact(repository, spec_id, artifact_name, payload.sql)


@api_router.post(
    "/{spec_id}/review",
    response_model=ReviewResult,
    summary="Review SQL intent preservation without executing SQL",
)
def review_sql_pack(
    spec_id: str,
    payload: ReviewRequest,
    repository: ChangeRepository = Depends(get_repository),
) -> ReviewResult:
    result = review_change(
        repository.get_spec(spec_id),
        repository.get_schema(spec_id),
        repository.get_sql_pack(spec_id),
        payload.evidence,
    )
    repository.save_review(result)
    return result


@api_router.post(
    "/{spec_id}/change-document",
    response_model=ChangeDocument,
    status_code=201,
    summary="Generate a change document from a confirmed spec and SQL pack",
)
def create_change_document(
    spec_id: str,
    payload: GenerateChangeDocumentRequest,
    repository: ChangeRepository = Depends(get_repository),
) -> ChangeDocument:
    return generate_change_document(repository, spec_id, payload)


@api_router.post(
    "/{spec_id}/change-document/review",
    response_model=DocumentReviewResult,
    summary="Review a submitted change document against the current spec and SQL pack",
)
def review_change_document_api(
    spec_id: str,
    payload: ReviewChangeDocumentRequest,
    repository: ChangeRepository = Depends(get_repository),
) -> DocumentReviewResult:
    return review_change_document(repository, spec_id, payload)
