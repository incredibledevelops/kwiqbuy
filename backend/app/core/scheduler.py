"""
Background jobs.
"""
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _job_expire_applications():
    try:
        from app.crud import vendor_application as va_crud
        count = await va_crud.expire_stale_applications()
        if count:
            logger.info("[scheduler] expired %d vendor applications", count)
    except Exception:
        logger.exception("[scheduler] expire applications failed")


async def _job_purge_idempotency():
    try:
        from app.crud import idempotency as idem_crud
        deleted = await idem_crud.purge_expired()
        if deleted:
            logger.info("[scheduler] purged %d idempotency records", deleted)
    except Exception:
        logger.exception("[scheduler] purge idempotency failed")


async def _job_expire_subscriptions():
    """
    Checks for active subscriptions whose period has ended,
    and reverts the vendor back to the Free tier.
    """
    try:
        from app.crud import subscription as sub_crud
        from app.models.subscription_tier import SubscriptionStatus, VendorSubscription
        from app.models.vendor import Vendor
        
        now = datetime.now(timezone.utc)
        expired_subs = await VendorSubscription.find(
            VendorSubscription.status == SubscriptionStatus.ACTIVE,
            VendorSubscription.current_period_end < now
        ).to_list()

        if not expired_subs:
            return

        # Get the default free tier
        free_tier = await sub_crud.get_tier_by_slug("free")
        
        for sub in expired_subs:
            sub.status = SubscriptionStatus.EXPIRED
            sub.expired_at = now
            await sub.save()

            # Auto-downgrade to Free
            if free_tier:
                vendor = await Vendor.get(sub.vendor_id)
                if vendor:
                    await sub_crud.subscribe_vendor(vendor, free_tier)
                    logger.info("[scheduler] expired sub for vendor %s, reverted to Free", vendor.id)

    except Exception:
        logger.exception("[scheduler] expire subscriptions failed")


async def _job_auto_payouts():
    try:
        from app.crud import payout as payout_crud
        from app.crud import platform_settings as ps_crud
        from app.crud import vendor as vendor_crud
        from app.models.payout import PayoutMethod
        from app.models.vendor import VendorStatus

        plat = await ps_crud.get_settings()
        if plat.payout_schedule not in ("weekly", "monthly"):
            return

        vendors = await vendor_crud.list_vendors(status=VendorStatus.ACTIVE, limit=500)
        created = 0
        for v in vendors:
            if v.available_balance < plat.min_payout_ghs:
                continue
            if not v.payout_recipient_code:
                continue
            try:
                await payout_crud.request_payout(v, requested_by="system:auto", method=PayoutMethod.PAYSTACK_TRANSFER)
                created += 1
            except ValueError:
                continue
        if created:
            logger.info("[scheduler] created %d auto payouts", created)
    except Exception:
        logger.exception("[scheduler] auto payouts failed")


async def _job_webhook_retry():
    try:
        from app.core.webhooks import retry_pending
        n = await retry_pending()
        if n:
            logger.info("[scheduler] retried %d webhook deliveries", n)
    except Exception:
        logger.exception("[scheduler] webhook retry failed")


def start_scheduler() -> None:
    global _scheduler
    if not settings.SCHEDULER_ENABLED:
        logger.info("[scheduler] disabled via SCHEDULER_ENABLED=false")
        return
    if _scheduler is not None:
        return

    _scheduler = AsyncIOScheduler(timezone="UTC")

    _scheduler.add_job(_job_expire_applications, trigger=IntervalTrigger(hours=6), id="expire_applications", replace_existing=True)
    _scheduler.add_job(_job_purge_idempotency, trigger=IntervalTrigger(hours=1), id="purge_idempotency", replace_existing=True)
    
    # Run subscription check every hour
    _scheduler.add_job(_job_expire_subscriptions, trigger=IntervalTrigger(hours=1), id="expire_subscriptions", replace_existing=True)
    
    _scheduler.add_job(_job_auto_payouts, trigger=CronTrigger(day_of_week="mon", hour=settings.PAYOUT_SCHEDULE_HOUR, minute=0), id="auto_payouts_weekly", replace_existing=True)
    _scheduler.add_job(_job_auto_payouts, trigger=CronTrigger(day=1, hour=settings.PAYOUT_SCHEDULE_HOUR, minute=0), id="auto_payouts_monthly", replace_existing=True)
    _scheduler.add_job(_job_webhook_retry, trigger=IntervalTrigger(seconds=settings.WEBHOOK_RETRY_INTERVAL_SECONDS), id="webhook_retry", replace_existing=True)

    _scheduler.start()
    logger.info("[scheduler] started")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        try:
            _scheduler.shutdown(wait=False)
        except Exception:
            pass
        _scheduler = None
        logger.info("[scheduler] stopped")