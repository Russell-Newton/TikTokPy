import pytest
from tiktokapipy.api import TikTokAPI as SyncTikTokAPI
from tiktokapipy.async_api import AsyncTikTokAPI as AsyncTikTokAPI


@pytest.fixture(scope="session")
def navigation_timeout():
    return 120000


@pytest.fixture(scope="session")
def navigation_retries():
    return 2


@pytest.fixture(scope="function")
async def async_api(navigation_timeout, navigation_retries):
    async with AsyncTikTokAPI(
        navigation_timeout=navigation_timeout, navigation_retries=navigation_retries
    ) as api:
        yield api


@pytest.fixture(scope="function")
def sync_api(navigation_timeout, navigation_retries):
    with SyncTikTokAPI(
        navigation_timeout=navigation_timeout, navigation_retries=navigation_retries
    ) as api:
        yield api


@pytest.fixture(scope="function")
async def async_api_mobile(navigation_timeout, navigation_retries):
    async with AsyncTikTokAPI(
        emulate_mobile=True,
        navigation_timeout=navigation_timeout,
        navigation_retries=navigation_retries,
    ) as api:
        yield api


@pytest.fixture(scope="function")
def sync_api_mobile(navigation_timeout, navigation_retries):
    with SyncTikTokAPI(
        emulate_mobile=True,
        navigation_timeout=navigation_timeout,
        navigation_retries=navigation_retries,
    ) as api:
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
