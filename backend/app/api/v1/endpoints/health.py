from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Vérifier que l’API répond",
)
def get_health() -> HealthResponse:
    return HealthResponse(status="ok")