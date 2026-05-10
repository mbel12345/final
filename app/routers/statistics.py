from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from typing import Optional

from app.auth.dependencies import get_current_active_user
from app.database import get_db
from app.models import CalcsPerDay
from app.models import Calculation
from app.schemas import CalcsPerDayResponse
from app.schemas import CalculationType
from app.schemas import TotalCalculations

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


@router.get('/calculations-per-day', response_model=list[CalcsPerDayResponse], tags=['statistics'])
def get_calculations_per_day(
    calc_type: Optional[CalculationType] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    '''
    Get number of calculations for each type for each day
    '''

    # Clean up parameters
    if start_time is not None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time is not None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    # Get as much from the cache table as possible (calcs_per_day)

    stmt = (
        select(
            CalcsPerDay,
        )
        .where(
            CalcsPerDay.user_id == current_user.id,
        )
        .order_by(
            CalcsPerDay.calc_date,
        )
    )
    if calc_type is not None:
        stmt = stmt.where(CalcsPerDay.type == calc_type)
    if start_time is not None:
        stmt = stmt.where(CalcsPerDay.calc_date >= start_time)
    if end_time is not None:
        stmt = stmt.where(CalcsPerDay.calc_date <= end_time)
    counts = db.execute(stmt).scalars().all()
    count_dates = {row.calc_date: row for row in counts}

    # The earliest date will be from the user's first calc if start_time is undefined
    if start_time is None:
        stmt = (
            select(
                func.min(Calculation.created_at),
            )
            .where(Calculation.user_id == current_user.id)
        )
        if calc_type is not None:
            stmt = stmt.where(Calculation.type == calc_type)
        start_time = db.execute(stmt).scalar_one_or_none()
        if start_time is None:
            return []

    # The latest date will be from the user's last calc if end_time is undefined
    if end_time is None:
        stmt = (
            select(
                func.max(Calculation.created_at),
            )
            .where(Calculation.user_id == current_user.id)
        )
        if calc_type is not None:
            stmt = stmt.where(Calculation.type == calc_type)
        end_time = db.execute(stmt).scalar_one_or_none()

    # Loop through the relevant dates, and update the calcs_per_day table if there is no row for that date

    start = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    end = end_time.replace(hour=0, minute=0, second=0, microsecond=0)

    results = []
    current = start
    while current <= end:
        now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(7)
        now = now.replace(tzinfo=timezone.utc)
        # Cache miss, or it is the current week and data should be refreshed.
        # Ideally, there would be a periodic job that updates the cache for old data, so it doesn't have to be recomputed every time.
        # This caching could be disabled by setting timedelta above to a very large number, but I left it in to illustrate how the calcs_per_day table can save on computations.
        if current.date() not in count_dates or current >= now:
            stmt = (
                select(
                    func.count(Calculation.id).label('count'),
                )
                .where(
                    Calculation.user_id == current_user.id,
                    Calculation.created_at.between(current, current.replace(hour=23, minute=59, second=59, microsecond=999999)),
                )
            )
            if calc_type is not None:
                stmt = stmt.where(Calculation.type == calc_type)
            count = db.execute(stmt).scalar_one_or_none()
            result_row = {
                'type': calc_type,
                'calc_date': current.date(),
                'count': count if count is not None else 0,
            }
            results.append(dict(result_row))
            result_row['user_id'] = current_user.id
            if current.date() in count_dates:
                existing = count_dates[current.date()]
                for k, v in result_row.items():
                    setattr(existing, k, v)
                db.commit()
                db.refresh(existing)
            else: # current not in count_dates
                calcs_per_day = CalcsPerDay(**result_row)
                db.add(calcs_per_day)
                db.commit()
                db.refresh(calcs_per_day)
        else: # Cache hit
            results.append({
                'type': calc_type,
                'calc_date': current.date(),
                'count': count_dates[current.date()].count,
            })
        current += timedelta(days=1)

    return results
