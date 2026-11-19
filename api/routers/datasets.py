"""
Dataset Management, Validation, and Ingestion Endpoints.
"""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from api.dependencies import get_current_user
from services.dataset_service import DatasetService

router = APIRouter(prefix="/api/datasets", tags=["Dataset Ingestion"])


@router.post("/validate")
async def validate_uploaded_dataset(
    file: UploadFile = File(...),
    dataset_type: str = Form(..., description="QUEUE_LOGS, STAFF_ROSTER, CUSTOMER_FEEDBACK, APPOINTMENTS"),
):
    """Parses and validates uploaded CSV/XLSX without writing to the database; returns preview and diagnostics."""
    content = await file.read()
    df, err = DatasetService.parse_file_to_dataframe(content, file.filename)
    if err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    report = DatasetService.validate_dataset(df, dataset_type, file.filename)
    return report


@router.post("/import")
async def import_uploaded_dataset(
    file: UploadFile = File(...),
    dataset_type: str = Form(...),
    skip_invalid: bool = Form(False),
    user=Depends(get_current_user),
):
    """Executes transactional database ingestion of validated spreadsheet records."""
    content = await file.read()
    df, err = DatasetService.parse_file_to_dataframe(content, file.filename)
    if err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    res = DatasetService.execute_import(
        df=df,
        dataset_type=dataset_type,
        filename=file.filename,
        file_size_bytes=len(content),
        imported_by=user.get("username", "API_USER"),
        skip_invalid=skip_invalid,
    )

    if not res["success"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=res["error"])

    return res
