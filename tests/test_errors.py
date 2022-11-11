import pytest
import tiktokapipy.async_api as a_api
import tiktokapipy.sync_api as s_api
from tiktokapipy import TikTokAPIError


async def test_error_on_browser_change_async(async_api):
    with pytest.raises(TikTokAPIError):
        async_api.browser = None


def test_error_on_browser_change_sync(sync_api):
    with pytest.raises(TikTokAPIError):
        sync_api.browser = None


async def test_init_error():
    with pytest.raises(ValueError):
        a_api.TikTokAPI(scroll_down_time=10, headless=True)

    with pytest.raises(ValueError):
        s_api.TikTokAPI(scroll_down_time=10, headless=True)
