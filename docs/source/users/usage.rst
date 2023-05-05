*****
Usage
*****

TikTokPy has both a synchronous and an asynchronous API. The interfaces are the same, but the asynchronous API
requires awaiting of certain functions and iterators. The following sections show example code for both.

API Context Managers
====================

The TikTokPy API should be used as a context manager in your program:

.. tabs::

    .. code-tab:: py TikTokAPI

            from tiktokapipy.api import TikTokAPI

            def do_something():
                with TikTokAPI() as api:
                    ...

    .. code-tab:: py AsyncTikTokAPI

            from tiktokapipy.async_api import AsyncTikTokAPI

            async def do_something():
                async with AsyncTikTokAPI() as api:
                    ...

Internally, the API uses a Playwright BrowserContext to scrape data from TikTok. The initialization of the
BrowserContext and corresponding Browser can be controlled by arguments passed to :ref:`TikTokAPI` or
:ref:`AsyncTikTokAPI`. This allows for use of a proxy, custom executable location, and more. See their documentation
for more information.

Examples
========

Get Video Information
---------------------

You can get information about a :ref:`Video` with a link.

.. tabs::

    .. code-tab:: py TikTokAPI

            from tiktokapipy.api import TikTokAPI

            def do_something():
                with TikTokAPI() as api:
                    video = api.video(video_url)
                    ...

    .. code-tab:: py AsyncTikTokAPI

            from tiktokapipy.async_api import AsyncTikTokAPI

            async def do_something():
                async with AsyncTikTokAPI() as api:
                    video = await api.video(video_url)
                    ...

Get Video Creator Information
-----------------------------

Given a :ref:`Video` object, you can get the :ref:`User` object corresponding to its creator.

.. tabs::

    .. code-tab:: py TikTokAPI

            from tiktokapipy.api import TikTokAPI

            def do_something():
                with TikTokAPI() as api:
                    video = api.video(video_url)
                    creator = video.creator()
                    ...

    .. code-tab:: py AsyncTikTokAPI

            from tiktokapipy.async_api import AsyncTikTokAPI

            async def do_something():
                async with AsyncTikTokAPI() as api:
                    video = await api.video(video_url)
                    creator = await video.creator()
                    ...

Iterate Over User Videos
------------------------

Given a :ref:`User` object, you can retrieve that creator's most recent videos.

.. tabs::

    .. code-tab:: py TikTokAPI

            from tiktokapipy.api import TikTokAPI

            def do_something():
                with TikTokAPI() as api:
                    user = api.user(user_tag)
                    for video in user.videos:
                        ...

    .. code-tab:: py AsyncTikTokAPI

            from tiktokapipy.async_api import AsyncTikTokAPI

            async def do_something():
                async with AsyncTikTokAPI() as api:
                    user = await api.user(user_tag)
                    async for video in user.videos:
                        ...

.. note::
    By default, the number of videos that can be iterated over is not limited. This can be changed by specifying a
    ``video_limit`` in the ``user()`` call. If a limit is not specified, every video link that was grabbed from the
    user page will be used for video data scraping. Specifying a limit can be useful if you only want the most
    recent videos.

Iterate Over Sorted Videos
--------------------------

Unfortunately, this strategy is not perfect. TikTok does not provide a direct way to sort :ref:`Video`, so you will
only be able to perform the sorting on videos that are picked up by TikTokPy during scraping. More can be retrieved by
setting ``scroll_down_time`` to something like 10 seconds in the API constructor. The ``videos`` (async) iterator that
exists on :ref:`User` and :ref:`Challenge` objects contains a function called ``sorted_by()`` that has the same
signature as the builtin ``sorted()`` but is faster if you want to sort on :ref:`VideoStats` or ``create_time``.

.. tabs::

    .. code-tab:: py TikTokAPI

            from tiktokapipy.api import TikTokAPI

            def do_something():
                with TikTokAPI() as api:
                    user = api.user(user_tag)
                    for video in user.videos.sorted_by(key=lambda vid: vid.stats.digg_count, reverse=True):
                        ...

    .. code-tab:: py AsyncTikTokAPI

            from tiktokapipy.async_api import AsyncTikTokAPI

            async def do_something():
                async with AsyncTikTokAPI() as api:
                    user = await api.user(user_tag)
                    async for video in user.videos.sorted_by(key=lambda vid: vid.stats.digg_count, reverse=True):
                        ...

.. note::
    All other video data besides the unique ID and stats are grabbed at iteration time, so if you would like to sort on
    something else you should just go with ``sorted()``. This helps keep the memory footprint low.

Iterate Over Popular Videos Tagged with a Challenge
---------------------------------------------------

TikTok refers to hashtags as "Challenges" internally. You can iterate over popular videos tagged with a specific
:ref:`Challenge`.

.. tabs::

    .. code-tab:: py TikTokAPI

            from tiktokapipy.api import TikTokAPI

            def do_something():
                with TikTokAPI() as api:
                    challenge = api.challenge(tag_name)
                    for video in challenge.videos:
                        ...

    .. code-tab:: py AsyncTikTokAPI

            from tiktokapipy.async_api import AsyncTikTokAPI

            async def do_something():
                async with AsyncTikTokAPI() as api:
                    challenge = await api.challenge(tag_name)
                    async for video in challenge.videos:
                        ...

You can also sort these by create time with ``challenge.videos.sorted_by(lambda vid: vid.create_time)``.

.. note::
    By default, the number of videos that can be iterated over is not limited. This can be changed by specifying a
    ``video_limit`` in the ``challenge()`` call. If a limit is not specified, every video link that was grabbed from the
    challenge page will be used for video data scraping. Specifying a limit can be useful if you only want the most
    recent videos.

Get Video Statistics for a User
-------------------------------

:ref:`Video` statistics are saved in a :ref:`VideoStats` object under the ``stats`` property.

.. tabs::

    .. code-tab:: py TikTokAPI

            from tiktokapipy.api import TikTokAPI

            def do_something():
                with TikTokAPI() as api:
                    user = api.user(username)
                    for video in user.videos:
                        num_comments = video.stats.comment_count
                        num_likes = video.stats.digg_count
                        num_views = video.stats.play_count
                        num_shares = video.stats.share_count
                        ...

    .. code-tab:: py AsyncTikTokAPI

            from tiktokapipy.async_api import AsyncTikTokAPI

            async def do_something():
                async with AsyncTikTokAPI() as api:
                    user = await api.user(username)
                    async for video in user.videos:
                        num_comments = video.stats.comment_count
                        num_likes = video.stats.digg_count
                        num_views = video.stats.play_count
                        num_shares = video.stats.share_count
                        ...

.. note::
    You can get similar data for users and challenges with the :ref:`UserStats` and :ref:`ChallengeStats` models.

Download Videos and Slideshows
------------------------------

If all you want to do is download a video or slideshow from TikTok, go no further. Because slideshows are saved as
images with a sound, you'll need to join these images together with the sound. I'd suggest using `ffmpeg`_ for this:

.. code-block:: py

    import asyncio
    import io
    import glob
    import os
    import urllib.request
    from os import path

    import aiohttp
    from tiktokapipy.async_api import AsyncTikTokAPI
    from tiktokapipy.models.video import Video

    link = ...
    directory = ...

    async def save_slideshow(video: Video):
        # this filter makes sure the images are padded to all the same size
        vf = "\"scale=iw*min(1080/iw\,1920/ih):ih*min(1080/iw\,1920/ih)," \
             "pad=1080:1920:(1080-iw)/2:(1920-ih)/2," \
             "format=yuv420p\""

        for i, image_data in enumerate(video.image_post.images):
            url = image_data.image_url.url_list[-1]
            # this step could probably be done with asyncio, but I didn't want to figure out how
            urllib.request.urlretrieve(url, path.join(directory, f"temp_{video.id}_{i:02}.jpg"))

        urllib.request.urlretrieve(video.music.play_url, path.join(directory, f"temp_{video.id}.mp3"))

        # use ffmpeg to join the images and audio
        command = [
            "ffmpeg",
            "-r 2/5",
            f"-i {directory}/temp_{video.id}_%02d.jpg",
            f"-i {directory}/temp_{video.id}.mp3",
            "-r 30",
            f"-vf {vf}",
            "-acodec copy",
            f"-t {len(video.image_post.images) * 2.5}",
            f"{directory}/temp_{video.id}.mp4",
            "-y"
        ]
        ffmpeg_proc = await asyncio.create_subprocess_shell(
            " ".join(command),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await ffmpeg_proc.communicate()
        generated_files = glob.glob(path.join(directory, f"temp_{video.id}*"))

        if not path.exists(path.join(directory, f"temp_{video.id}.mp4")):
            # optional ffmpeg logging step
            # logging.error(stderr.decode("utf-8"))
            for file in generated_files:
                os.remove(file)
            raise Exception("Something went wrong with piecing the slideshow together")

        with open(path.join(directory, f"temp_{video.id}.mp4"), "rb") as f:
            ret = io.BytesIO(f.read())

        for file in generated_files:
            os.remove(file)

        return ret

    async def save_video(video: Video):
        async with aiohttp.ClientSession() as session:
            async with session.get(video.video.download_addr) as resp:
                return io.BytesIO(await resp.read())

    async def download_video():
        # mobile emulation is necessary to retrieve slideshows
        # if you don't want this, you can set emulate_mobile=False and skip if the video has an image_post property
        async with AsyncTikTokAPI(emulate_mobile=True) as api:
            video: Video = await api.video(link)
            if video.image_post:
                downloaded = await save_slideshow(video)
            else:
                downloaded = await save_video(video)

            # do something with the downloaded video (save it, send it, whatever you want).
            ...

This entire process could also be done with the synchronous API, but it probably makes less sense.

.. warning::

    If this gives you 403 errors, you will likely need to carry over a cookie and a header when you make the HTTP GET
    request:

    .. code-block:: py

        async def save_video(video: Video, api: AsyncTikTokAPI):
            # Carrying over this cookie tricks TikTok into thinking this ClientSession was the Playwright instance
            # used by the AsyncTikTokAPI instance
            async with aiohttp.ClientSession(cookies={cookie["name"]: cookie["value"] for cookie in await api.context.cookies() if cookie["name"] == "tt_chain_token"}) as session:
                # Creating this header tricks TikTok into thinking it made the request itself
                async with session.get(video.video.download_addr, headers={"referer": "https://www.tiktok.com/"}) as resp:
                    return io.BytesIO(await resp.read())

    Note that this does require you to pass the api instance to this function, and you will likely also need to update
    the slideshow function as well.

    Credit to `@papayyg <https://github.com/papayyg>`_ for identifying a solution to this issue in issue `Issue #35 <https://github.com/Russell-Newton/TikTokPy/issues/35#issuecomment-1502976477>`_

.. _ffmpeg: https://ffmpeg.org/download.html
