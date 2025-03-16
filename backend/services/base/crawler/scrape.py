import asyncio
from typing import Callable, Dict, List, Optional, Tuple, overload, TypeVar, Any
from bs4 import BeautifulSoup
from mixins.asyncio import retry_async
import random

import aiohttp

T = TypeVar("T")


@overload
async def scrape_async(
    url: List[str],
    session: aiohttp.ClientSession,
    post_process: Optional[Callable[[BeautifulSoup], T]] = None,
    retry_delay: float = 5.0,
    delay_range: Tuple[float, float] = (0, 1)
) -> List[T]:
    pass


@overload
async def scrape_async(
    url: str,
    session: aiohttp.ClientSession,
    post_process: Optional[Callable[[BeautifulSoup], T]] = None,
    retry_delay: float = 5.0,
    delay_range: Tuple[float, float] = (0, 1)
) -> T:
    pass


async def scrape_async(
    url: str | List[str],
    session: aiohttp.ClientSession,
    post_process: Optional[Callable[[BeautifulSoup], T]] = None,
    retry_delay: float = 5.0,
    delay_range: Tuple[float, float] = (0, 1)
) -> T | List[T]:

    @retry_async(delay=retry_delay, times=25)
    async def help(_url: str) -> Any:
        await asyncio.sleep(random.uniform(*delay_range))
        async with session.get(_url) as res:
            if res.ok:
                html = await res.text(errors="ignore")
                soup = BeautifulSoup(html, "html5lib")
                result = post_process(soup) if post_process else soup
                return result

            raise aiohttp.ClientError

    if isinstance(url, str):
        return await help(url)

    return await asyncio.gather(*[help(url) for url in url])


import os

DOCUMENT_PARSER_URL = os.getenv("DOCUMENT_PARSER_URL")


@retry_async(delay=3)
async def parse_document_async(
    url: str | List[str],
    session: aiohttp.ClientSession,
) -> List[Dict[int, str]]:
    if isinstance(url, list) and not url:
        return []

    body = {"url": url}

    async with session.post(f"{DOCUMENT_PARSER_URL}/extract_text", json=body) as res:
        if res.ok:
            data = await res.json()
            return data

        raise Exception("Failed parse document")
