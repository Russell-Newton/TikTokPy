import pytest
from tiktokapipy.api import TikTokAPI
from tiktokapipy.async_api import AsyncTikTokAPI


@pytest.fixture(scope="session")
def navigation_timeout():
    return 30


@pytest.fixture(scope="session")
def navigation_retries():
    return 0


@pytest.fixture(scope="session")
def headless_browsing():
    return True


@pytest.fixture(scope="function")
async def async_api(
    navigation_timeout, navigation_retries, headless_browsing
) -> AsyncTikTokAPI:
    async with AsyncTikTokAPI(
        navigation_timeout=navigation_timeout,
        navigation_retries=navigation_retries,
        headless=headless_browsing,
    ) as api:
        yield api


@pytest.fixture(scope="function")
def sync_api(navigation_timeout, navigation_retries, headless_browsing) -> TikTokAPI:
    with TikTokAPI(
        navigation_timeout=navigation_timeout,
        navigation_retries=navigation_retries,
        headless=headless_browsing,
    ) as api:
        yield api


@pytest.fixture(scope="function")
async def async_api_mobile(
    navigation_timeout, navigation_retries, headless_browsing
) -> AsyncTikTokAPI:
    async with AsyncTikTokAPI(
        emulate_mobile=True,
        navigation_timeout=navigation_timeout,
        navigation_retries=navigation_retries,
        headless=headless_browsing,
    ) as api:
        yield api


@pytest.fixture(scope="function")
def sync_api_mobile(
    navigation_timeout, navigation_retries, headless_browsing
) -> TikTokAPI:
    with TikTokAPI(
        emulate_mobile=True,
        navigation_timeout=navigation_timeout,
        navigation_retries=navigation_retries,
        headless=headless_browsing,
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
