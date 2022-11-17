import pytest
from tiktokapipy.api import TikTokAPI as SyncTikTokAPI
from tiktokapipy.async_api import AsyncTikTokAPI as AsyncTikTokAPI


@pytest.fixture(scope="function")
async def async_api():
    async with AsyncTikTokAPI(navigation_timeout=90000) as api:
        yield api


@pytest.fixture(scope="function")
def sync_api():
    with SyncTikTokAPI(navigation_timeout=90000) as api:
        yield api


@pytest.fixture(scope="function")
async def async_api_mobile():
    async with AsyncTikTokAPI(emulate_mobile=True, navigation_timeout=90000) as api:
        yield api


@pytest.fixture(scope="function")
def sync_api_mobile():
    with SyncTikTokAPI(emulate_mobile=True, navigation_timeout=90000) as api:
        yield api


@pytest.fixture(scope="session")
def video_id():
    return 7109512307918621995


@pytest.fixture(scope="session")
def slideshow_id():
    return 7165629307656670506


@pytest.fixture(scope="session")
def user_name():
    return "tiktok"


@pytest.fixture(scope="session")
def challenge_name():
    return "fyp"
