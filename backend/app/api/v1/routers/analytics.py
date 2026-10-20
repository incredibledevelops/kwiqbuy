from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_admin
from app.crud import analytics as analytics_crud
from app.crud import review as review_crud
from app.schemas.analytics import (
    AdminAnalyticsOverview,
    AdminAnalyticsSummary,
    HourlyPoint,
    RevenuePoint,
    StatusCount,
    TopPromo,
    TopSeller,
    TopVendor,
    TopZone,
    WeeklyComparison,
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/overview", response_model=AdminAnalyticsOverview)
async def overview(days: int = Query(30, ge=1, le=365)):
    start, end = analytics_crud.default_range(days=days)
    summary = await analytics_crud.summary(start, end)
    daily = await analytics_crud.daily_series(start, end)
    status_bd = await analytics_crud.status_breakdown(start, end)
    top = await analytics_crud.top_sellers(start, end, limit=5)
    promos = await analytics_crud.top_promos(start, end, limit=5)
    zones = await analytics_crud.top_zones(start, end, limit=5)
    vendors = await analytics_crud.top_vendors(start, end, limit=5)

    return AdminAnalyticsOverview(
        summary=AdminAnalyticsSummary(**summary),
        daily=[RevenuePoint(**d) for d in daily],
        status_breakdown=[StatusCount(**s) for s in status_bd],
        top_sellers=[TopSeller(**t) for t in top],
        top_promos=[TopPromo(**p) for p in promos],
        top_zones=[TopZone(**z) for z in zones],
        top_vendors=[TopVendor(**v) for v in vendors],
    )


@router.get("/daily", response_model=list[RevenuePoint])
async def daily(days: int = Query(30, ge=1, le=365)):
    start, end = analytics_crud.default_range(days=days)
    return [RevenuePoint(**d) for d in await analytics_crud.daily_series(start, end)]


@router.get("/status-breakdown", response_model=list[StatusCount])
async def status_breakdown(days: int = Query(30, ge=1, le=365)):
    start, end = analytics_crud.default_range(days=days)
    return [
        StatusCount(**s)
        for s in await analytics_crud.status_breakdown(start, end)
    ]


@router.get("/top-vendors", response_model=list[TopVendor])
async def top_vendors(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(5, ge=1, le=50),
):
    start, end = analytics_crud.default_range(days=days)
    return [TopVendor(**v) for v in await analytics_crud.top_vendors(start, end, limit)]


@router.get("/top-sellers", response_model=list[TopSeller])
async def top_sellers(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(5, ge=1, le=50),
):
    start, end = analytics_crud.default_range(days=days)
    return [TopSeller(**t) for t in await analytics_crud.top_sellers(start, end, limit)]


@router.get("/reviews")
async def reviews_overview():
    return await review_crud.summary()