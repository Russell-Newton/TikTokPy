import pytest


async def test_challenge_async(async_api, challenge_name):
    challenge = await async_api.challenge(challenge_name, video_limit=2)
    assert challenge
    assert challenge.videos
    async for video in challenge.videos:
        assert video
        assert video.comments


async def test_challenge_async_mobile(async_api_mobile, challenge_name):
    challenge = await async_api_mobile.challenge(challenge_name, video_limit=2)
    assert challenge
    assert challenge.videos
    async for video in challenge.videos:
        assert video
        assert video.comments


@pytest.mark.parametrize("api", ["sync_api", "sync_api_mobile"])
def test_challenge_sync(request, api, challenge_name):
    sync_api = request.getfixturevalue(api)
    challenge = sync_api.challenge(challenge_name, video_limit=2)
    assert challenge
    assert challenge.videos
    for video in challenge.videos:
        assert video
        assert video.comments
