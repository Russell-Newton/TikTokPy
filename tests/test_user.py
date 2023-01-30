import pytest


async def test_user_async(async_api, user_name):
    user = await async_api.user(user_name, video_limit=2)
    assert user
    assert user.videos
    async for video in user.videos:
        assert video


async def test_user_async_mobile(async_api_mobile, user_name):
    user = await async_api_mobile.user(user_name, video_limit=2)
    assert user
    assert user.videos
    async for video in user.videos:
        assert video


@pytest.mark.parametrize("api", ["sync_api", "sync_api_mobile"])
def test_user_sync(request, api, user_name):
    sync_api = request.getfixturevalue(api)
    user = sync_api.user(user_name, video_limit=2)
    assert user
    assert user.videos
    for video in user.videos:
        assert video


def test_sort_user_videos(sync_api, user_name):
    user = sync_api.user(user_name)
    most_recent = -1
    for video in user.videos.sorted_by(lambda vid: vid.stats.play_count).light_models:
        assert video.stats.play_count >= most_recent
        most_recent = video.stats.play_count


async def test_sort_user_videos_async(async_api, user_name):
    user = await async_api.user(user_name)
    most_recent = -1
    for video in user.videos.sorted_by(lambda vid: vid.stats.play_count).light_models:
        assert video.stats.play_count >= most_recent
        most_recent = video.stats.play_count
