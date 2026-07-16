from datetime import UTC, datetime, timedelta

import pytest

from app.application.dto.commands import (
    CreateTaskDTO,
    CreateTeamDTO,
    JoinTeamDTO,
    PaymentDTO,
    UserUpsertDTO,
)
from app.application.exceptions.errors import LimitExceededError
from app.application.services.use_cases import (
    AnalyticsServiceImpl,
    PaymentService,
    SecureInviteTokenGenerator,
    TaskService,
    TeamService,
    UserService,
)
from app.domain.entities import SubscriptionPlan
from app.infrastructure.database.repositories.sqlalchemy import SqlAlchemyUnitOfWorkFactory
from app.infrastructure.redis.client import RedisCacheService, create_redis_client
from app.shared.enums import PlanCode, TaskPriority, TaskType
from app.shared.plans import DEFAULT_PLANS


@pytest.fixture
async def uow_factory(database_url):
    factory = SqlAlchemyUnitOfWorkFactory(database_url)
    yield factory
    await factory.dispose()


@pytest.fixture
async def seeded_uow(uow_factory):
    async with uow_factory() as uow:
        for plan_data in DEFAULT_PLANS:
            if await uow.plans.get_by_code(plan_data["code"]) is None:
                await uow.plans.add(SubscriptionPlan(**plan_data))
        await uow.commit()
    return uow_factory


@pytest.fixture
def cache_service(redis_url):
    redis = create_redis_client(redis_url)
    return RedisCacheService(redis)


@pytest.mark.asyncio
async def test_create_team(seeded_uow, cache_service):
    async with seeded_uow() as uow:
        await UserService(uow, cache_service, []).upsert(
            UserUpsertDTO(
                telegram_id=1001,
                username="owner",
                first_name="Owner",
                last_name=None,
                language_code="ru",
            )
        )
        await uow.commit()
    async with seeded_uow() as uow:
        team, token = await TeamService(
            uow, cache_service, SecureInviteTokenGenerator()
        ).create_team(
            CreateTeamDTO(
                name="Alpha", description="Team A", timezone="UTC", owner_telegram_id=1001
            )
        )
        await uow.commit()
    assert team.name == "Alpha"
    assert token


@pytest.mark.asyncio
async def test_join_by_invite(seeded_uow, cache_service):
    async with seeded_uow() as uow:
        await UserService(uow, cache_service, []).upsert(
            UserUpsertDTO(
                telegram_id=1001,
                username="owner",
                first_name="Owner",
                last_name=None,
                language_code="ru",
            )
        )
        await UserService(uow, cache_service, []).upsert(
            UserUpsertDTO(
                telegram_id=1002,
                username="member",
                first_name="Member",
                last_name=None,
                language_code="ru",
            )
        )
        team, token = await TeamService(
            uow, cache_service, SecureInviteTokenGenerator()
        ).create_team(
            CreateTeamDTO(name="Beta", description=None, timezone="UTC", owner_telegram_id=1001)
        )
        await uow.commit()
    async with seeded_uow() as uow:
        joined = await TeamService(uow, cache_service, SecureInviteTokenGenerator()).join_by_invite(
            JoinTeamDTO(token=token, telegram_id=1002)
        )
        await uow.commit()
    assert joined.name == "Beta"


@pytest.mark.asyncio
async def test_free_plan_team_limit(seeded_uow, cache_service):
    async with seeded_uow() as uow:
        await UserService(uow, cache_service, []).upsert(
            UserUpsertDTO(
                telegram_id=2001,
                username="owner",
                first_name="Owner",
                last_name=None,
                language_code="ru",
            )
        )
        service = TeamService(uow, cache_service, SecureInviteTokenGenerator())
        await service.create_team(
            CreateTeamDTO(name="One", description=None, timezone="UTC", owner_telegram_id=2001)
        )
        await uow.commit()
    async with seeded_uow() as uow:
        service = TeamService(uow, cache_service, SecureInviteTokenGenerator())
        with pytest.raises(LimitExceededError):
            await service.create_team(
                CreateTeamDTO(name="Two", description=None, timezone="UTC", owner_telegram_id=2001)
            )


@pytest.mark.asyncio
async def test_create_common_task(seeded_uow, cache_service):
    async with seeded_uow() as uow:
        owner = await UserService(uow, cache_service, []).upsert(
            UserUpsertDTO(
                telegram_id=3001,
                username="owner",
                first_name="Owner",
                last_name=None,
                language_code="ru",
            )
        )
        await UserService(uow, cache_service, []).upsert(
            UserUpsertDTO(
                telegram_id=3002,
                username="member",
                first_name="Member",
                last_name=None,
                language_code="ru",
            )
        )
        team_service = TeamService(uow, cache_service, SecureInviteTokenGenerator())
        team, token = await team_service.create_team(
            CreateTeamDTO(name="Gamma", description=None, timezone="UTC", owner_telegram_id=3001)
        )
        await uow.commit()
    async with seeded_uow() as uow:
        await TeamService(uow, cache_service, SecureInviteTokenGenerator()).join_by_invite(
            JoinTeamDTO(token=token, telegram_id=3002)
        )
        await uow.commit()
    async with seeded_uow() as uow:
        assert owner.id is not None
        task = await TaskService(uow).create_task(
            CreateTaskDTO(
                team_id=team.id,  # type: ignore[arg-type]
                creator_id=owner.id,
                title="Deploy",
                description="Release",
                task_type=TaskType.COMMON,
                priority=TaskPriority.HIGH,
                deadline=datetime.now(UTC) + timedelta(days=1),
                assignee_ids=[],
                attachments=[],
                reminder_types=[],
            )
        )
        assignments = await uow.assignments.list_for_task(task.id)  # type: ignore[arg-type]
        await uow.commit()
    assert len(assignments) == 2


@pytest.mark.asyncio
async def test_payment_idempotency(seeded_uow, cache_service):
    async with seeded_uow() as uow:
        user = await UserService(uow, cache_service, []).upsert(
            UserUpsertDTO(
                telegram_id=4001,
                username="owner",
                first_name="Owner",
                last_name=None,
                language_code="ru",
            )
        )
        team, _ = await TeamService(uow, cache_service, SecureInviteTokenGenerator()).create_team(
            CreateTeamDTO(name="PayTeam", description=None, timezone="UTC", owner_telegram_id=4001)
        )
        await uow.commit()
    assert user.id is not None and team.id is not None
    payload = "payload-123"
    dto = PaymentDTO(
        user_id=user.id,
        team_id=team.id,
        plan_code=PlanCode.PREMIUM,
        payload=payload,
        telegram_payment_charge_id="chg-1",
        provider_payment_charge_id="prov-1",
        amount_stars=250,
        currency="XTR",
    )
    async with seeded_uow() as uow:
        payment_service = PaymentService(uow, cache_service)
        first = await payment_service.process_successful_payment(dto)
        second = await payment_service.process_successful_payment(dto)
        await uow.commit()
    assert first.id == second.id
    assert first.status == "paid"


@pytest.mark.asyncio
async def test_analytics_summary(seeded_uow, cache_service):
    async with seeded_uow() as uow:
        owner = await UserService(uow, cache_service, []).upsert(
            UserUpsertDTO(
                telegram_id=5001,
                username="owner",
                first_name="Owner",
                last_name=None,
                language_code="ru",
            )
        )
        team, _ = await TeamService(uow, cache_service, SecureInviteTokenGenerator()).create_team(
            CreateTeamDTO(
                name="Analytics", description=None, timezone="UTC", owner_telegram_id=5001
            )
        )
        assert owner.id is not None and team.id is not None
        await TaskService(uow).create_task(
            CreateTaskDTO(
                team_id=team.id,
                creator_id=owner.id,
                title="Task",
                description=None,
                task_type=TaskType.COMMON,
                priority=TaskPriority.MEDIUM,
                deadline=None,
                assignee_ids=[],
                attachments=[],
                reminder_types=[],
            )
        )
        summary = await AnalyticsServiceImpl(uow).team_summary(team.id)
        await uow.commit()
    assert summary["total_tasks"] == 1
