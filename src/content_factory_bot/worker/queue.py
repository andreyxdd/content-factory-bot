import json
import uuid
from typing import Any

import redis.asyncio as redis


class JobQueue:
    def __init__(self, redis_url: str, *, queue_name: str = "cfbot:jobs") -> None:
        self._redis_url = redis_url
        self._queue_name = queue_name
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        self._client = redis.from_url(self._redis_url, decode_responses=True)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def enqueue(self, kind: str, payload: dict[str, Any]) -> str:
        if not self._client:
            raise RuntimeError("JobQueue not connected")
        job_id = str(uuid.uuid4())
        body = json.dumps({"id": job_id, "kind": kind, "payload": payload})
        await self._client.lpush(self._queue_name, body)
        return job_id

    async def dequeue(self, timeout: int = 5) -> dict[str, Any] | None:
        if not self._client:
            raise RuntimeError("JobQueue not connected")
        result = await self._client.brpop(self._queue_name, timeout=timeout)
        if not result:
            return None
        _, raw = result
        return json.loads(raw)
