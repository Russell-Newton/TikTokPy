import pytest
from tiktokapipy.models.video import video_link


async def test_video_async(async_api, video_id):
    link = video_link(video_id)
    video = await async_api.video(link)
    assert video
    assert video.comments
    assert await video.creator()
    assert await video.comments[0].creator()


async def test_video_async_mobile(async_api_mobile, video_id):
    link = video_link(video_id)
    video = await async_api_mobile.video(link)
    assert video
    assert video.comments
    assert await video.creator()
    assert await video.comments[0].creator()


@pytest.mark.parametrize("api", ["sync_api", "sync_api_mobile"])
def test_video_sync(request, api, video_id):
    sync_api = request.getfixturevalue(api)
    link = video_link(video_id)
    video = sync_api.video(link)
    assert video
    assert video.comments
    assert video.creator()
    assert video.comments[0].creator()
