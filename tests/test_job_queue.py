import pytest

from content_factory_bot.worker.queue import JobQueue


@pytest.mark.integration
@pytest.mark.asyncio
async def test_enqueue_and_dequeue_roundtrip() -> None:
    q = JobQueue("redis://localhost:6379/15", queue_name="cfbot:test")
    try:
        await q.connect()
        job_id = await q.enqueue("ping", {"x": 1})
        assert job_id
        job = await q.dequeue(timeout=1)
        assert job is not None
        assert job["kind"] == "ping"
        assert job["payload"]["x"] == 1
    finally:
        await q.close()
