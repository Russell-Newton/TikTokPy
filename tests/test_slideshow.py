import pytest
from tiktokapipy import TikTokAPIError
from tiktokapipy.models.video import video_link


async def test_slideshow_async(async_api_mobile, slideshow_id):
    link = video_link(slideshow_id)
    video = await async_api_mobile.video(link)
    assert video
    assert video.image_post
    assert video.image_post.images
    assert video.image_post.images[0].image_url.url_list
    assert await video.creator()


def test_slideshow_sync(sync_api_mobile, slideshow_id):
    link = video_link(slideshow_id)
    video = sync_api_mobile.video(link)
    assert video
    assert video.image_post
    assert video.image_post.images
    assert video.image_post.images[0].image_url.url_list
    assert video.creator()


@pytest.mark.skip("Slideshows now work on desktop")
async def test_slideshow_fails_on_desktop_async(async_api, slideshow_id):
    with pytest.raises(TikTokAPIError):
        await async_api.video(video_link(slideshow_id))


@pytest.mark.skip("Slideshows now work on desktop")
def test_slideshow_fails_on_desktop_sync(sync_api, slideshow_id):
    with pytest.raises(TikTokAPIError):
        sync_api.video(video_link(slideshow_id))
