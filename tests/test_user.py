async def test_user_async(async_api, user_name):
    user = await async_api.user(user_name, video_limit=2)
    assert user
    assert user.videos
    async for video in user.videos:
        assert video
        assert video.comments


def test_user_sync(sync_api, user_name):
    user = sync_api.user(user_name, video_limit=2)
    assert user
    assert user.videos
    for video in user.videos:
        assert video
        assert video.comments
