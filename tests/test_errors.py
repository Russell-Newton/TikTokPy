import pytest
from tiktokapipy.api import TikTokAPI
from tiktokapipy.async_api import AsyncTikTokAPI


@pytest.mark.skip("Deprecated test")
async def test_init_error():
    with pytest.raises(ValueError):
        AsyncTikTokAPI(scroll_down_time=10, headless=True)

    with pytest.raises(ValueError):
        TikTokAPI(scroll_down_time=10, headless=True)
