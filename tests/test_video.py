from tiktokapipy.models.video import video_link


async def test_video_async(async_api, video_id):
    link = video_link(video_id)
    video = await async_api.video(link)
    assert video
    assert video.comments
    assert await video.creator()
    assert await video.comments[0].creator()


def test_video_sync(sync_api, video_id):
    link = video_link(video_id)
    video = sync_api.video(link)
    assert video
    assert video.comments
    assert video.creator()
    assert video.comments[0].creator()
