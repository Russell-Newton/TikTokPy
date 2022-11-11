async def test_user_async(async_api, challenge_name):
    challenge = await async_api.challenge(challenge_name, video_limit=2)
    assert challenge
    assert challenge.videos
    async for video in challenge.videos:
        assert video
        assert video.comments


def test_user_sync(sync_api, challenge_name):
    challenge = sync_api.challenge(challenge_name, video_limit=2)
    assert challenge
    assert challenge.videos
    for video in challenge.videos:
        assert video
        assert video.comments
