import pytest
from tiktokapipy.models.video import video_link


@pytest.fixture(scope="session")
def video_id():
    return 7109512307918621995


async def test_video(api, video_id):
    link = video_link(video_id)
    assert await api.video(link)
