import json
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanUpdate


class PlanService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_plan_by_id(self, plan_id: int) -> Optional[Plan]:
        result = await self.db.execute(select(Plan).where(Plan.id == plan_id))
        return result.scalar_one_or_none()

    async def get_all_plans(self, active_only: bool = True) -> List[Plan]:
        query = select(Plan)
        if active_only:
            query = query.where(Plan.is_active == True)
        result = await self.db.execute(query.order_by(Plan.price))
        return list(result.scalars().all())

    async def create_plan(self, plan_data: PlanCreate) -> Plan:
        features_str = None
        if plan_data.features:
            features_str = json.dumps(plan_data.features)

        db_plan = Plan(
            name=plan_data.name,
            description=plan_data.description,
            price=plan_data.price,
            currency=plan_data.currency,
            interval=plan_data.interval,
            features=features_str,
            stripe_price_id=plan_data.stripe_price_id,
            stripe_product_id=plan_data.stripe_product_id,
        )
        self.db.add(db_plan)
        await self.db.commit()
        await self.db.refresh(db_plan)
        return db_plan

    async def update_plan(self, plan: Plan, plan_data: PlanUpdate) -> Plan:
        update_data = plan_data.model_dump(exclude_unset=True)
        if "features" in update_data and update_data["features"] is not None:
            update_data["features"] = json.dumps(update_data["features"])
        for field, value in update_data.items():
            setattr(plan, field, value)
        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def update_stripe_ids(
        self, plan: Plan, stripe_price_id: str, stripe_product_id: str
    ) -> Plan:
        plan.stripe_price_id = stripe_price_id
        plan.stripe_product_id = stripe_product_id
        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def delete_plan(self, plan: Plan) -> None:
        plan.is_active = False
        await self.db.commit()
