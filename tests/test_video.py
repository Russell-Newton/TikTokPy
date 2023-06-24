from tiktokapipy.models.video import video_link


async def test_video_async(async_api, video_id):
    link = video_link(video_id)
    video = await async_api.video(link)
    assert video
    assert await video.creator()
    async for comment in video.comments.limit(5):
        assert comment
    async for tag in video.tags:
        assert tag


def test_video_sync(sync_api, video_id):
    link = video_link(video_id)
    video = sync_api.video(link)
    assert video
    assert video.creator()
    for comment in video.comments.limit(5):
        assert comment
    for tag in video.tags:
        assert tag
