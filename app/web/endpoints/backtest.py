"""Backtest web endpoint."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter()

# Set up templates
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/", response_class=HTMLResponse)
async def backtest_form(request: Request):
    """Backtest form page."""
    return templates.TemplateResponse(
        "backtest.html",
        {
            "request": request,
            "title": "Backtest Trading Strategy"
        }
    )
