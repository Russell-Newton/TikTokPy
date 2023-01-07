<h1 align="center">TikTokPy</h1>
<div align="center">
    <a href="https://pypi.org/project/tiktokapipy/">
        <img src="https://img.shields.io/pypi/v/tiktokapipy?style=flat-square&logo=pypi" alt="PyPI">
    </a>
    <a href="https://www.python.org">
        <img src="https://img.shields.io/badge/python-3.8+-blue.svg?style=flat-square&logo=python" alt="Python Version 3.8+">
    </a>
    <a href="https://pypi.org/project/tiktokapipy/">
        <img alt="License" src="https://img.shields.io/github/license/Russell-Newton/TikTokPy?style=flat-square">
    </a>
    <br>
    <a href="https://github.com/Russell-Newton/TikTokPy/actions/workflows/tox.yml">
        <img src="https://img.shields.io/github/actions/workflow/status/Russell-Newton/TikTokPy/tox.yml?branch=main&label=Unit%20Tests&logo=github&style=flat-square" alt="Unit Tests Status">
    </a>
    <a href='https://tiktokpy.readthedocs.io/en/stable/'>
        <img src='https://readthedocs.org/projects/tiktokpy/badge/?version=stable&style=flat-square' alt='Documentation Status' />
    </a>
</div>

**Extract data from TikTok without needing any login information or API keys.**

## Table of Contents

* [Getting Started](#getting-started)
    * [Installation](#installation)
    * [Quick Start Guide](#quick-start-guide)
* [Documentation](#documentation)

## Getting Started

### Installation

Install the ``tiktokapipy`` package (or add it to your project requirements) and set up Playwright:

```shell
pip install tiktokapipy
python -m playwright install
```

### Quick Start Guide

TikTokPy has both a synchronous and an asynchronous API. The interfaces are the same, but the asynchronous API
requires awaiting of certain functions and iterators.

Both APIs must be used as context managers. To get video information in both APIs:

<table>
<tr>
<th>Synchronous</th>
<th>Asynchronous</th>
</tr>
<tr>
<td>

```py
from tiktokapipy.api import TikTokAPI

with TikTokAPI() as api:
    video = api.video(video_link)
    ...
```

</td>
<td>

```py
from tiktokapipy.async_api import AsyncTikTokAPI

async with AsyncTikTokAPI() as api:
    video = await api.video(video_link)
    ...
```

</td>
</tr>
</table>

More examples, including how to download videos and slideshows, can be found in the
[documentation](https://tiktokpy.readthedocs.io/en/latest/users/usage.html#examples).

## Documentation

You can view the full documentation on [Read the Docs](https://tiktokpy.readthedocs.io/en/latest/).
