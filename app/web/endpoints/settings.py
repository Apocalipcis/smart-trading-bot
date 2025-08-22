"""Settings web endpoint for API key management."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter()

# Set up templates
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page for API key management."""
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "title": "Settings - API Key Management"
        }
    )
