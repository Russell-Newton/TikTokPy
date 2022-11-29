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

Examples
========

Get Video Information
---------------------

You can get information about videos with a link.

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

Given a Video object, you can get the User object corresponding to the video creator.

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

With a User object, you can retrieve their most recent Videos.

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

Iterate Over Recent Videos Tagged with a Challenge
--------------------------------------------------

TikTok refers to hashtags as "Challenges" internally. You can iterate over the most recent videos tagged with a specific
challenge.

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
