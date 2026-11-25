import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, UploadFile, status
from pydantic import BaseModel

from app.api.dependencies import Admin, dataset_service
from app.api.errors import documented_errors
from app.modules.datasets.application.service import DatasetService
from app.modules.datasets.infrastructure.records import DatasetRecord

router = APIRouter(prefix="/datasets", tags=["Datasets"])


class DatasetOut(BaseModel):
    id: uuid.UUID
    original_filename: str
    sha256: str
    row_count: int
    size_bytes: int
    validation_report: dict[str, Any]
    created_at: datetime

    @classmethod
    def of(cls, record: DatasetRecord) -> "DatasetOut":
        return cls.model_validate(record, from_attributes=True)


Service = Annotated[DatasetService, Depends(dataset_service)]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Subir un archivo de entrenamiento (admin)",
    description=(
        "Acepta un CSV con las columnas del dataset original. Se valida formato, tamaño, "
        "columnas, tipos y dominios ANTES de aceptarlo. Se guarda versionado por su SHA-256."
    ),
    response_model=DatasetOut,
    responses=documented_errors(401, 403, 409, 413, 415, 422),
)
async def upload(
    admin: Admin, service: Service, file: Annotated[UploadFile, File(description="Archivo .csv")]
) -> DatasetOut:
    # Se lee como máximo el límite + 1 byte: basta para detectar el exceso sin cargarlo entero.
    content = await file.read(service.max_bytes + 1)
    record = service.upload(file.filename or "", file.content_type, content, admin.id)
    return DatasetOut.of(record)


@router.get(
    "",
    summary="Listar datasets subidos (admin)",
    response_model=list[DatasetOut],
    responses=documented_errors(401, 403),
)
def list_datasets(_: Admin, service: Service) -> list[DatasetOut]:
    return [DatasetOut.of(record) for record in service.list()]
