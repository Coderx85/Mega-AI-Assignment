import pytest
from app.services.frame_cache import FrameCache


@pytest.fixture
def cache():
    return FrameCache()


@pytest.mark.asyncio
async def test_put_and_latest(cache):
    await cache.put("s1", b"data1")
    assert await cache.latest("s1") == b"data1"


@pytest.mark.asyncio
async def test_session_isolation(cache):
    await cache.put("s1", b"data1")
    await cache.put("s2", b"data2")
    assert await cache.latest("s1") == b"data1"
    assert await cache.latest("s2") == b"data2"


@pytest.mark.asyncio
async def test_miss_returns_none(cache):
    assert await cache.latest("ghost") is None


@pytest.mark.asyncio
async def test_clear_removes_session(cache):
    await cache.put("s1", b"data1")
    await cache.clear("s1")
    assert await cache.latest("s1") is None


@pytest.mark.asyncio
async def test_latest_any_returns_most_recent(cache):
    await cache.put("s1", b"data1")
    await cache.put("s2", b"data2")
    assert await cache.latest_any() == b"data2"


@pytest.mark.asyncio
async def test_latest_any_empty(cache):
    assert await cache.latest_any() is None
