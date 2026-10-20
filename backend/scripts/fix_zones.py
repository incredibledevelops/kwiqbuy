"""
One-off migration: inspect zone→branch linking and optionally fix orphans.

Usage:
    python -m scripts.fix_zones                  # just show what's linked
    python -m scripts.fix_zones accra            # assign all orphans to 'accra'
"""
import asyncio
import sys

from app.core.database import close_db, init_db
from app.crud import branch as branch_crud
from app.crud import delivery_zone as zone_crud
from app.models import ALL_DOCUMENTS


async def report():
    await init_db(ALL_DOCUMENTS)

    print("\n📍 Current delivery zone → branch mapping\n")
    print(f"{'Zone':<30} {'Fee':>6}   {'Branch':<30} {'Shared?':<8}")
    print("-" * 80)

    zones = await zone_crud.list_zones()
    branches_by_id = {str(b.id): b.name for b in await branch_crud.list_branches()}

    for z in zones:
        branch_name = "— shared (all branches) —" if z.branch_id is None else branches_by_id.get(str(z.branch_id), "⚠️  UNKNOWN")
        shared = "✓" if z.branch_id is None else ""
        print(f"{z.name:<30} {z.delivery_fee:>6.2f}   {branch_name:<30} {shared:<8}")

    orphans = await zone_crud.list_orphans()
    print(f"\nSummary: {len(zones)} zones total, {len(orphans)} orphan(s) (shared across all branches)\n")

    if len(sys.argv) > 1:
        target_slug = sys.argv[1].strip().lower()
        branch = await branch_crud.get_by_slug(target_slug)
        if not branch:
            print(f"❌ Branch '{target_slug}' not found.")
            await close_db()
            return
        count = await zone_crud.assign_all_orphans(str(branch.id))
        print(f"✅ Assigned {count} orphan zone(s) to '{branch.name}'.\n")
    else:
        print("ℹ️  To link all orphans to a branch, run:")
        print("      python -m scripts.fix_zones accra")
        print("   (or 'kumasi', or any branch slug)\n")

    await close_db()


if __name__ == "__main__":
    asyncio.run(report())