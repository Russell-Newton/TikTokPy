import pytest
from tiktokapipy.api import TikTokAPI


@pytest.fixture(scope="function")
async def api():
    async with TikTokAPI(
        scroll_down_time=5, data_dump_file="examples/test_data.json"
    ) as api:
        yield api
