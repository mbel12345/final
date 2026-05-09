from datetime import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from typing import Optional

from app.auth.dependencies import get_current_active_user
from app.database import get_db
from app.models.calculation import Calculation
from app.schemas.calculation import CalculationType
from app.schemas.statistics import TotalCalculations

router = APIRouter(prefix='/statistics', tags=['statistics'])

templates = Jinja2Templates(directory='templates')

# Page for statistics
@router.get('/', response_class=HTMLResponse, tags=['statistics'])
def statistics_page(request: Request):
    return templates.TemplateResponse('statistics.html', {
        'request': request,
    })

@router.get('/total-calculations', response_model=list[TotalCalculations], tags=['statistics'])
def get_total_calculations(
    request: Request,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    # Get number of calculations for each type
    stmt = (
        select(
            Calculation.type,
            func.count(Calculation.id).label('count'),
        )
        .where(Calculation.user_id == current_user.id)
        .group_by(Calculation.type)
    )
    if start_time is not None:
        stmt = stmt.where(Calculation.created_at >= start_time)
    if end_time is not None:
        stmt = stmt.where(Calculation.created_at <= end_time)
    counts = db.execute(stmt).mappings().all()

    # If a calc type has never been done, set its count to 0
    for calc_type in CalculationType:
        original_counts = list(counts)
        if calc_type.value not in [row['type'] for row in original_counts]:
            counts.append({
                'type': calc_type.value,
                'count': 0,
            })

    return counts

