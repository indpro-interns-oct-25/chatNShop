"""
Visual Cost Dashboard (HTML + Chart.js)
"""
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.ai.cost_monitor.usage_tracker import UsageTracker
import os

# ✅ Router with prefix ensures endpoint = /dashboard/cost
router = APIRouter(prefix="/dashboard", tags=["Cost Dashboard"])

# ✅ Template directory — matches your project’s folder structure
# If templates folder is inside app/, update this:
templates = Jinja2Templates(directory=os.path.join("app", "templates"))

# ✅ Initialize tracker
tracker = UsageTracker()

# ✅ Dashboard route
@router.get("/cost", response_class=HTMLResponse)
async def show_cost_dashboard(request: Request):
    """Renders the cost dashboard page"""
    daily = tracker.get_daily()
    monthly = tracker.get_monthly()

    return templates.TemplateResponse(
        "cost_dashboard.html",
        {
            "request": request,
            "daily": daily,
            "monthly": monthly,
        },
    )
