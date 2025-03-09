"""미사용"""

from abc import ABC, abstractmethod
import asyncio
import nest_asyncio
from typing import Callable, Generic, List, Optional, overload, Dict
import re

from aiohttp import ClientSession
import aiohttp

from mixins.asyncio import retry_async, retry_sync
from mixins.http_client import HTTPMetaclass
from bs4 import BeautifulSoup
from services.base.dto import DTO
import requests

from urllib.parse import urljoin
from dotenv import load_dotenv
import os
import json
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from playwright.async_api import async_playwright

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


class DetailModel(BaseModel):
    url: str = Field(..., description="Url of the current crawled site.")
    detail: str = Field(..., description="All the details for the lab.")


class PageNameModel(BaseModel):
    detail_model: DetailModel
    page_name: str = Field(..., description="Name of current page view.")


class _BaseCrawler(ABC, Generic[DTO], metaclass=HTTPMetaclass):

    async def scrape_detail_async(
        self, dtos: List[DTO], session: Optional[ClientSession] = None, **kwargs
    ) -> List[DTO]:
        if session is None:
            raise ValueError("parameter 'session' cannot be None.")

        return await self._scrape_detail_async(dtos, session=session, **kwargs)

    async def _scrape_detail_async(self, dtos: List[DTO], session: ClientSession,
                                   **kwargs) -> List[DTO]:
        urls = [dto["url"] for dto in dtos]
        soups = await self._scrape_async(urls, session=session)

        loop = asyncio.get_running_loop()
        tasks = [
            loop.run_in_executor(None, self._parse_detail, dto, soup)
            for soup, dto in zip(soups, dtos)
        ]

        dtos_ = await asyncio.gather(*tasks)
        dtos_ = [dto for dto in dtos_ if dto]

        return dtos_

    @abstractmethod
    def _parse_detail(self, dto: DTO, soup: BeautifulSoup) -> Optional[DTO]:
        pass

    @overload
    async def _scrape_async(
        self, url: str, session: ClientSession, retry_delay: float = 5.0
    ) -> BeautifulSoup:
        ...

    @overload
    async def _scrape_async(self,
                            url: List[str],
                            session: ClientSession,
                            retry_delay: float = 5.0) -> List[BeautifulSoup]:
        ...

    async def _scrape_async(
        self,
        url: str | List[str],
        session: ClientSession,
        retry_delay: float = 5.0
    ) -> BeautifulSoup | List[BeautifulSoup]:

        @retry_async(delay=retry_delay)
        async def scrape_coroutine(_url):
            async with session.get(_url) as res:
                if res.status == 200:
                    html = await res.read()
                    soup = BeautifulSoup(html, "html5lib")
                    return soup

                raise aiohttp.ClientError

        if isinstance(url, str):
            return await scrape_coroutine(url)
        return await asyncio.gather(*[scrape_coroutine(_url) for _url in url])

    @overload
    def _scrape(self, url: str, timeout: int = 600, is_success=lambda _: True) -> BeautifulSoup:
        ...

    @overload
    def _scrape(self,
                url: List[str],
                timeout: int = 600,
                is_success=lambda _: True) -> List[BeautifulSoup]:
        ...

    def _scrape(
        self,
        url: str | List[str],
        timeout: int = 600,
        is_success: Callable[[BeautifulSoup], bool] = lambda _: True
    ):

        @retry_sync(is_success=is_success)
        def scrape(_url):
            response = requests.get(_url, timeout=timeout)
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, "html5lib")
                return soup

            raise requests.ConnectionError()

        if isinstance(url, str):
            return scrape(url)

        soups = []
        for _url in url:
            result = scrape(_url)
            soups.append(result)

        return soups

    def _preprocess_text(self, text: str):
        """텍스트 전처리"""
        text = re.sub(r"\\+", " ", text)
        text = re.sub(r"\n+", "\n", text)
        text = re.sub(r"\t", " ", text)
        text = re.sub(r"\r", " ", text)
        exclude_base64 = re.compile(r"data:image/[a-zA-Z]+;base64,[^\"']+")
        text = re.sub(exclude_base64, "", text)
        re.sub(r"\s+", " ", text).strip()
        return text

    def extract_links(self, url: str) -> List[str]:
        try:
            headers = {
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            links = []
            for a_tag in soup.find_all('a'):
                href = a_tag.get('href')
                if href:
                    absolute_url = urljoin(url, href)
                    links.append(absolute_url)
            unique_links = sorted(list(set(links)))
            return unique_links
        except requests.RequestException as e:
            print(f"Error fetching URL: {e}")
            return []

    def extract_links_filter(self, url: str) -> List[str]:

        exclude_keywords = [
            'sitemap', 'sites', 'subLogin', 'userSbscrb', 'onestop', 'cmmCon', 'go', 'hrd', 'job',
            'lib', 'plato', 'certpia', 'webmail', '@', 'https://www.pusan.ac.kr',
            'http://www.pusan.ac.kr'
        ]

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            links = []

            for a_tag in soup.find_all('a'):
                href = a_tag.get('href')
                if href:
                    absolute_url = urljoin(url, href)
                    if not any(keyword in absolute_url for keyword in exclude_keywords):
                        links.append(absolute_url)

            unique_links = sorted(list(set(links)))
            return unique_links

        except requests.RequestException as e:
            print(f"Error fetching URL: {e}")
            return []

    async def crawl_details(
        self,
        url_addr: str,
        chunk_token_threshold: int = 3000,
        overlap_rate: float = 0.1,
        max_tokens: int = 1000,
        end_point: Optional[str] = None,
        llm_model: Optional[str] = "openai/gpt-4o-mini",
        api: Optional[str] = OPENAI_API_KEY
    ):
        prompt = "Extract one 'page_name', 'url' and 'detail' from the content. Set url as None. page_name must be uniform through the response. Include as many details ABOUT THE LAB as possible. If no information about the lab found, just return None in detail. Don't crawl any detail for contact like address, email, or office phone number. Don't crwal any url. Don't crawl any detail that is not related to the lab."

        strategy = {
            "schema": PageNameModel.model_json_schema(),
            "extraction_type": "schema",
            "instruction": prompt,
            "chunk_token_threshold": chunk_token_threshold,
            "overlap_rate": overlap_rate,
            "apply_chunking": True,
            "input_format": "markdown",
            "extra_args": {
                "temperature": 0.0,
                "max_tokens": max_tokens
            }
        }

        if llm_model:
            strategy["provider"] = llm_model
            if api:
                strategy["api_token"] = api
        elif end_point:
            strategy["api_base"] = end_point

        llm_strategy = LLMExtractionStrategy(**strategy)

        crawl_config = CrawlerRunConfig(
            extraction_strategy=llm_strategy, cache_mode=CacheMode.BYPASS
        )

        browser_cfg = BrowserConfig(headless=True)

        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            results = await crawler.arun(url=url_addr, config=crawl_config)

            if results.success:
                print("Current URL:", url_addr)
                llm_strategy.show_usage()

            else:
                print("Error URL", url_addr)
                print("Error Message:", results.error_message)

            return results

    def combine_details(self, results: List[str]) -> List[Dict]:
        combined_details = []
        for result in results:
            if isinstance(result, Exception):
                combined_details.append({})
                continue
            try:
                page_name_models = json.loads(result.extracted_content)
            except:
                continue
            if not page_name_models:
                combined_details.append({})
                continue
            detail = []
            detail = ""
            for file in page_name_models:
                if "detail_model" in file.keys():
                    content = file["detail_model"]["detail"]
                else:
                    content = None
                if content != "None" and content != None:
                    detail += str(file["detail_model"]["detail"])
                    detail += "\n"
                temp_detail = page_name_models[0]
                temp_detail["detail_model"]["detail"] = str(detail)
                combined_details.append(temp_detail)
        return combined_details

    def write_urls(self, urls: List[str], combined_details: List[Dict]) -> List[Dict]:
        for index, combined_detail in enumerate(combined_details):
            if 'detail_model' not in combined_detail.keys():
                continue
            combined_detail['detail_model']['url'] = urls[index]
        return combined_details

    def filter_empty_detail(self, details: List[Dict]) -> List[Dict]:
        filtered_details = []
        for detail in details:
            if "detail_model" in detail.keys() and detail['detail_model']['detail']:
                filtered_details.append(detail)
        return filtered_details

    def filter_unique_details(self, details: List[Dict]) -> List[int]:
        string_list = [detail['detail_model']['detail'] for detail in details]
        string_indices = {}
        for index, string in enumerate(string_list):
            if string in string_indices:
                string_indices[string].append(index)
            else:
                string_indices[string] = [index]
        result = []
        for string in string_indices:
            indices = string_indices[string]
            if len(indices) == 1:
                result.append(indices[0])
            else:
                result.append(min(indices))
        unique_details = [detail for index, detail in enumerate(details) if index in sorted(result)]
        return unique_details

    async def custom_crawl4ai(
        self,
        url: str,
        n_urls: int = None,
        chunk_token_threshold: int = 3000,
        overlap_rate: float = 0.1,
        max_tokens: int = 1000,
        end_point: Optional[str] = None,
        llm_model: Optional[str] = "openai/gpt-4o-mini",
        api: Optional[str] = OPENAI_API_KEY
    ) -> List[Dict]:
        target_url = url
        found_links = self.extract_links_filter(target_url)
        if n_urls is None:
            urls = found_links
        else:
            urls = found_links[:n_urls]
        results = await asyncio.gather(
            *[
                self.crawl_details(
                    url,
                    chunk_token_threshold=chunk_token_threshold,
                    overlap_rate=overlap_rate,
                    max_tokens=max_tokens,
                    end_point=end_point,
                    llm_model=llm_model,
                    api=api
                ) for url in urls if url
            ],
            return_exceptions=True
        )
        combined_details = self.combine_details(results)
        details = self.write_urls(urls, combined_details)
        filled_details = self.filter_empty_detail(details)
        unique_details = self.filter_unique_details(filled_details)
        return unique_details


if __name__ == "__main__":
    base_crawler = BaseCrawler()
    url = "url"
    details = asyncio.run(base_crawler.custom_crawl4ai(url, 10))
    print(details)
