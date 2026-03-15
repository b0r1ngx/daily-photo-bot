"""Unit tests for ScheduleService."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.service.schedule_service import ScheduleService
from src.types.exceptions import BotError
from src.types.schedule import ScheduleConfig, ScheduleType


@pytest.fixture
def schedule_repo():
    return AsyncMock()


@pytest.fixture
def service(schedule_repo):
    return ScheduleService(schedule_repo=schedule_repo)


@pytest.mark.asyncio
async def test_set_interval_schedule(service: ScheduleService, schedule_repo):
    schedule_repo.create_or_update.return_value = ScheduleConfig(
        id=1, topic_id=1, schedule_type=ScheduleType.INTERVAL, value="3600"
    )
    result = await service.set_interval_schedule(topic_id=1, seconds=3600)
    assert result.schedule_type == ScheduleType.INTERVAL
    assert result.value == "3600"


@pytest.mark.asyncio
async def test_set_interval_invalid(service: ScheduleService):
    with pytest.raises(BotError, match="Invalid interval"):
        await service.set_interval_schedule(topic_id=1, seconds=999)


@pytest.mark.asyncio
async def test_set_fixed_time_schedule(service: ScheduleService, schedule_repo):
    schedule_repo.create_or_update.return_value = ScheduleConfig(
        id=1, topic_id=1, schedule_type=ScheduleType.FIXED_TIME, value="09:30"
    )
    result = await service.set_fixed_time_schedule(topic_id=1, hour=9, minute=30)
    assert result.value == "09:30"


@pytest.mark.asyncio
async def test_set_fixed_time_invalid_hour(service: ScheduleService):
    with pytest.raises(BotError, match="Invalid hour"):
        await service.set_fixed_time_schedule(topic_id=1, hour=25, minute=0)


@pytest.mark.asyncio
async def test_set_fixed_time_invalid_minute(service: ScheduleService):
    with pytest.raises(BotError, match="Invalid minute"):
        await service.set_fixed_time_schedule(topic_id=1, hour=9, minute=61)


@pytest.mark.asyncio
async def test_get_all_active_schedules(service: ScheduleService, schedule_repo):
    schedule_repo.get_all_active.return_value = [
        ScheduleConfig(id=1, topic_id=1, schedule_type=ScheduleType.INTERVAL, value="300"),
    ]
    result = await service.get_all_active_schedules()
    assert len(result) == 1
