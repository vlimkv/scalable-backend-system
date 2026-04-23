import json
from typing import Any

from app.core.redis import redis_client


class CacheService:
    TASK_LIST_PREFIX = "tasks:list:"

    @classmethod
    def build_task_list_key(
        cls,
        *,
        page: int,
        size: int,
        status_filter: str | None,
        owner_id: int | None,
        assignee_id: int | None,
        mine: bool,
        current_user_id: int,
    ) -> str:
        return (
            f"{cls.TASK_LIST_PREFIX}"
            f"user={current_user_id}:page={page}:size={size}:"
            f"status={status_filter}:owner={owner_id}:assignee={assignee_id}:mine={mine}"
        )

    @classmethod
    async def get_json(cls, key: str) -> dict[str, Any] | None:
        data = await redis_client.get(key)
        if not data:
            return None
        return json.loads(data)

    @classmethod
    async def set_json(cls, key: str, value: dict[str, Any], ttl: int = 60) -> None:
        await redis_client.set(key, json.dumps(value), ex=ttl)

    @classmethod
    async def invalidate_task_lists(cls) -> None:
        keys = await redis_client.keys(f"{cls.TASK_LIST_PREFIX}*")
        if keys:
            await redis_client.delete(*keys)