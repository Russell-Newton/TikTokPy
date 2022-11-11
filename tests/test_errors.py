import pytest
from tiktokapipy.api import TikTokAPI, TikTokAPIError


async def test_error_on_browser_change(api):
    with pytest.raises(TikTokAPIError):
        api.browser = None


async def test_init_error():
    with pytest.raises(ValueError):
        TikTokAPI(10, True)
