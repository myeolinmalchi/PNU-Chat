import asyncio
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from services.base.crawler.preprocess import clean_html


async def run():
    async with ClientSession() as session:
        async with session.get(
            "https://cse.pusan.ac.kr/cse/14651/subview.do?enc=Zm5jdDF8QEB8JTJGYmJzJTJGY3NlJTJGMjYwNSUyRjE3MDg5MTElMkZhcnRjbFZpZXcuZG8lM0ZiYnNPcGVuV3JkU2VxJTNEJTI2aXNWaWV3TWluZSUzRGZhbHNlJTI2c3JjaENvbHVtbiUzRCUyNnBhZ2UlM0QxJTI2c3JjaFdyZCUzRCUyNnJnc0JnbmRlU3RyJTNEJTI2YmJzQ2xTZXElM0QlMjZwYXNzd29yZCUzRCUyNnJnc0VuZGRlU3RyJTNEJTI2"
        ) as res:
            if not res.ok:
                raise ValueError

            html = await res.text(encoding="utf-8", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")

    content_element = soup.select_one("div.artclView")
    if not content_element:
        raise ValueError

    soup = clean_html(content_element)
    print(str(soup.prettify()))


if __name__ == "__main__":
    asyncio.run(run())
