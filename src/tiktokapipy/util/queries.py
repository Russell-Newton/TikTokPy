"""
API Queries
:autodoc-skip:
"""
import time
from typing import Literal, Union
from urllib.parse import quote, urlencode

from playwright.async_api import BrowserContext as AsyncContext
from playwright.sync_api import BrowserContext as SyncContext
from tiktokapipy import TikTokAPIError

from tiktokapipy.util.signing import (
    sign_and_get_request_async,
    sign_and_get_request_sync,
)

SUPPORTED_ENDPOINT = Literal[
    "comment/list/",
    "post/item_list/",
    "challenge/item_list/",
    "related/item_list/",
    "item/detail/",
    "challenge/detail/",
    "search/general/full/"
    # "user/detail/", # TODO - User detail requires msToken, X-Bogus, and _signature
    # "recommend/item_list/", # TODO - recommended list likely also requires msToken, X-Bogus, and _signature
]


TEMPLATE_QUERY_PARAMS_DICT = {
    "aid": 1988,
    "app_name": "tiktok_web",
    "browser_language": "en-US",  # TODO - Set dynamically?
    "browser_platform": "Win32",  # TODO - Set dynamically?
    "count": 30,
    "device_id": "",
    "device_platform": "web_pc",  # TODO - Set dynamically?
    "os": "windows",  # TODO - Set dynamically?
    "priority_region": "US",
    "referrer": "",
    "region": "US",  # TODO - Set dynamically?
    "screen_height": 0,
    "screen_width": 0,
}


ENDPOINT_ID_MAP = {
    "comment/list/": "aweme_id",
    "post/item_list/": "secUid",
    "challenge/item_list/": "challengeID",
    "related/item_list/": "itemID",
    "item/detail/": "itemId",
    "challenge/detail/": "challengeName",
    "search/general/full/": "keyword",
    # "user/detail/": "secUid",
}


# As of June 14, 2023, the following parameters are necessary to make comment API requests and don't seem to affect
# other API requests:
#
# * ``aid`` = 1988
# * ``app_name`` = tiktok_web
# * ``browser_language`` = en-US
# * ``browser_name`` = Mozilla
# * ``browser_platform`` = Win32
# * ``browser_version`` = Rest of UserAgent
# * ``count`` = 20
# * ``device_id`` (empty, but needed)
# * ``device_platform`` = web_pc
# * ``os`` = windows
# * ``priority_region`` (empty, but needed)
# * ``referer`` (empty, but needed)
# * ``region`` = US
# * ``screen_height`` (can be 0)
# * ``screen_width`` (can be 0)
#
# Unique to Video Detail (item/detail/):
# * ``itemId``
# * ``cursor`` and ``count`` don't seem to affect
#
# Unique to Challenge Detail (item/detail/):
# * ``challengeID``
# * ``challengeName``
# * ``cursor`` and ``count`` don't seem to affect
#
# Unique to Comments (comment/list/):
# * ``aweme_id``
# * ``cursor``
#
# Unique to Related Videos (related/item_list/):
# * ``itemID``
# * ``cursor``
#
# Unique to User Posts (post/item_list/):
# * ``secUid``
# * ``cursor`` is a Unix Timestamp. The retrieved videos are the newest ``count`` since before said timestamp
# * Next ``cursor`` is provided in response
# * Requires msToken cookie(s)
#
# Unique to Challenges (challenge/item_list/):
# * ``challengeID``
# * ``cursor``
#


async def get_necessary_query_params_async(
    context: AsyncContext, extra_params
) -> str:
    """

    :param context: Playwright Context retrieved from :class:`.AsyncTikTokAPI` with ``api.context``
    :return: a paramstring containing query parameters necessary for all API calls
    """

    page = await context.new_page()
    agent: str = await page.evaluate("navigator.userAgent")
    await page.close()
    browser_name, browser_version = agent.split("/", 1)
    query = dict(
        **TEMPLATE_QUERY_PARAMS_DICT,
        browser_name=browser_name,
        browser_version=browser_version,
    )
    query.update(**extra_params["extra_params"])
    return urlencode(query)


def get_necessary_query_params_sync(context: SyncContext, **extra_params) -> str:
    """
    :param context: Playwright Context retrieved from :class:`.AsyncTikTokAPI` with ``api.context``
    :return: a paramstring containing query parameters necessary for all API calls
    """

    page = context.new_page()
    agent: str = page.evaluate("navigator.userAgent")
    page.close()
    browser_name, browser_version = agent.split("/", 1)
    query = dict(
        **TEMPLATE_QUERY_PARAMS_DICT,
        browser_name=browser_name,
        browser_version=browser_version,
    )
    query.update(**extra_params)
    return urlencode(query, quote_via=quote)


async def get_ms_token(context: AsyncContext) -> str | None:
    all_cookies = await context.cookies()
    if len(all_cookies) != 0:
        ms_token = {cookie['name']: cookie['value'] for cookie in all_cookies if cookie['name'] == 'msToken'}
        return ms_token["msToken"]
    else:
        return None


def get_id_type(endpoint: str) -> str:
    for k, v in ENDPOINT_ID_MAP.items():
        if k == endpoint:
            return v
    raise TikTokAPIError(f"Unsupported endpoint: {endpoint}")


async def continuous_request_async(
        endpoint: SUPPORTED_ENDPOINT,
        cursor_position: int,
        target_identifier: Union[int, str],
        async_context: AsyncContext,
        max_videos: int,
        **additional_params,
) -> list:

    BASE_URL = "https://www.tiktok.com/api/"
    VIDEO_TYPE = 1
    NO_MORE_DATA = 0
    collected_data = []  # List to store the concatenated data

    while True:
        query_params = await get_necessary_query_params_async(async_context, additional_params)
        identifier_type = get_id_type(endpoint)

        full_params = f"{query_params}&offset={cursor_position}&{identifier_type}={target_identifier}"

        response_data = await sign_and_get_request_async(
            f"{BASE_URL}{endpoint}?{full_params}", async_context
        )

        if 'data' in response_data:
            video_data = [item for item in response_data['data'] if item["type"] == VIDEO_TYPE]
            collected_data += video_data
            additional_params["extra_params"]["search_id"] = response_data["extra"]["logid"]

        more_data_available = response_data.get('has_more', NO_MORE_DATA)
        cursor_position = response_data.get('cursor', None)
        if more_data_available <= NO_MORE_DATA or cursor_position is None or (max_videos != -1 and len(collected_data) >= max_videos):
            break

    return collected_data

async def make_request_async(
    endpoint: SUPPORTED_ENDPOINT,
    cursor: int,
    target_id: Union[int, str],
    context: AsyncContext,
    **extra_params,
) -> dict:
    params = await get_necessary_query_params_async(context, **extra_params)
    id_type = get_id_type(endpoint)
    params += f"&cursor={cursor}&{id_type}={target_id}"
    return await sign_and_get_request_async(
        f"https://www.tiktok.com/api/{endpoint}?{params}", context
    )


def make_request_sync(
    endpoint: SUPPORTED_ENDPOINT,
    cursor: int,
    target_id: Union[int, str],
    context: SyncContext,
    **extra_params,
) -> dict:
    params = get_necessary_query_params_sync(context, **extra_params)
    id_type = get_id_type(endpoint)
    params += f"&cursor={cursor}&{id_type}={target_id}"
    return sign_and_get_request_sync(
        f"https://www.tiktok.com/api/{endpoint}?{params}", context
    )


async def get_challenge_detail_async(challenge_name: str, context: AsyncContext):
    return await make_request_async("challenge/detail/", 0, challenge_name, context)


def get_challenge_detail_sync(challenge_name: str, context: SyncContext):
    return make_request_sync("challenge/detail/", 0, challenge_name, context)


def get_video_detail_sync(video_id: int, context: SyncContext):
    return make_request_sync("item/detail/", 0, video_id, context)


async def get_video_detail_async(video_id: int, context: AsyncContext):
    return await make_request_async("item/detail/", 0, video_id, context)


async def get_search_results_async(search_term: str, context: AsyncContext,video_limit):
    extra_params = {
        "keyword": search_term,
        "from_page": "search",
        "web_search_code": """{"tiktok":{"client_params_x":{"search_engine":{"ies_mt_user_live_video_card_use_libra":1,"mt_search_general_user_live_card":1}},"search_server":{}}}""",

    }
    ms_token = await get_ms_token(context)
    # if ms_token is not None:
    #     extra_params["msToken"] = ms_token
    return await continuous_request_async("search/general/full/", 0, search_term, context, video_limit, extra_params=extra_params)

__all__ = [
    "get_search_results_async",
    "get_necessary_query_params_async",
    "get_necessary_query_params_sync",
    "make_request_async",
    "make_request_sync",
    "get_challenge_detail_async",
    "get_challenge_detail_sync",
    "get_video_detail_async",
    "get_video_detail_sync",
]
