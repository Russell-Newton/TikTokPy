import pytest


async def test_challenge_async(async_api, challenge_name):
    challenge = await async_api.challenge(challenge_name, video_limit=2)
    assert challenge
    assert challenge.videos
    async for video in challenge.videos:
        assert video


async def test_challenge_async_mobile(async_api_mobile, challenge_name):
    challenge = await async_api_mobile.challenge(challenge_name, video_limit=2)
    assert challenge
    assert challenge.videos
    async for video in challenge.videos:
        assert video


@pytest.mark.parametrize("api", ["sync_api", "sync_api_mobile"])
def test_challenge_sync(request, api, challenge_name):
    sync_api = request.getfixturevalue(api)
    challenge = sync_api.challenge(challenge_name, video_limit=2)
    assert challenge
    assert challenge.videos
    for video in challenge.videos:
        assert video


def test_sort_challenge_videos(sync_api, challenge_name):
    challenge = sync_api.challenge(challenge_name)
    most_recent = -1
    for video in challenge.videos.sorted_by(
        lambda vid: vid.stats.play_count
    ).light_models:
        assert video.stats.play_count >= most_recent
        most_recent = video.stats.play_count


async def test_sort_challenge_videos_async(async_api, challenge_name):
    challenge = await async_api.challenge(challenge_name)
    most_recent = -1
    for video in challenge.videos.sorted_by(
        lambda vid: vid.stats.play_count
    ).light_models:
        assert video.stats.play_count >= most_recent
        most_recent = video.stats.play_count
