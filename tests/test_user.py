import pytest


async def test_user_async(async_api, user_name):
    user = await async_api.user(user_name, video_limit=2)
    assert user
    assert user.videos
    i = 0
    async for video in user.videos:
        assert video
        i += 1
    assert i == 2


def test_user_sync(sync_api, user_name):
    user = sync_api.user(user_name, video_limit=2)
    assert user
    assert user.videos
    i = 0
    for video in user.videos:
        assert video
        i += 1
    assert i == 2


@pytest.mark.skip("Removed sorting")
def test_sort_user_videos(sync_api, user_name):
    user = sync_api.user(user_name)
    most_recent = -1
    for video in user.videos.sorted_by(lambda vid: vid.stats.play_count).light_models:
        assert video.stats.play_count >= most_recent
        most_recent = video.stats.play_count


@pytest.mark.skip("Removed sorting")
async def test_sort_user_videos_async(async_api, user_name):
    user = await async_api.user(user_name)
    most_recent = -1
    for video in user.videos.sorted_by(lambda vid: vid.stats.play_count).light_models:
        assert video.stats.play_count >= most_recent
        most_recent = video.stats.play_count
