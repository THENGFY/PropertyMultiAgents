from fastapi import APIRouter
from fastapi.responses import FileResponse
from app.config import settings

router = APIRouter(tags=["UI Views"])


@router.get("/", response_class=FileResponse)
@router.get("/dashboard", response_class=FileResponse)
@router.get("/portal", response_class=FileResponse)
async def serve_dashboard():
    """Serve the Developer Test Dashboard UI."""
    index_path = settings.STATIC_DIR / "index.html"
    return FileResponse(str(index_path))
