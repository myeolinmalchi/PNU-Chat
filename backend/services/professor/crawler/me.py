import asyncio
from typing import List

from bs4 import BeautifulSoup
import re

from services.professor import ProfessorDTO

import re

from .base import EDU_KEYWORDS, ProfessorCrawlerBase

LIST_URL = "https://me.pusan.ac.kr/new/sub01/sub04.asp?perPage=1000"
DETAIL_URL = "https://me.pusan.ac.kr/new/sub01/sub04_detail.asp"

SELECTORs = {
    "list": "#contents > div > div > div > div.professor-box",
    "detail": {
        "name": "#contents > div > div.professor-wrapper > div > p.name",
        "name_eng": "#contents > div > div.professor-wrapper > div > p.eng_name",
        "minor": "#professor-major > dd",
        "lab_addr": "#professor-lab > dd > span",
        "office_phone": "#professor-office > dd",
        "website": "#professor-website > dd",
        "email": "#professor-email > dd",
    },
}


class ProfessorMECrawler(ProfessorCrawlerBase):

    def scrape_seqs(self) -> List[int]:
        soup = self._scrape(LIST_URL)
        if soup is None:
            return []

        seqs = self._parse_seqs(soup)
        return seqs

    def _parse_seqs(self, soup: BeautifulSoup) -> List[int]:
        professor_boxes = soup.select(SELECTORs["list"])

        seqs: List[int] = []
        for box in professor_boxes:
            anchor = box.select_one("& > a:first-child")
            if anchor is None or not anchor.has_attr("href"):
                continue

            href = str(anchor["href"])
            seq_str = re.search(r"seq=(\d+)", href)

            if seq_str is not None:
                seq = int(seq_str.group(1))
                seqs.append(seq)

        return seqs

    async def _scrape_partial_async(self, session, **kwargs):
        seqs = kwargs.get("seqs")
        if not seqs:
            raise ValueError("'seqs' must be contained")
        _urls = [f"{DETAIL_URL}?seq={seq}" for seq in seqs]

        soups = await self._scrape_async(_urls, session=session)
        loop = asyncio.get_running_loop()
        tasks = [loop.run_in_executor(None, self._parse_detail, seq, soup) for seq, soup in zip(seqs, soups)]
        results = await asyncio.gather(*tasks)
        return results

    def _parse_detail(self, seq: int, soup: BeautifulSoup):
        elements = {key: soup.select_one(selector) for key, selector in SELECTORs["detail"].items()}

        basic_info = {k: v.get_text(separator="", strip=True) for k, v in elements.items() if v is not None}

        basic_info["major"] = "기계공학부"

        additional_info = {}
        contents_boxes = soup.select("#contents > div > div.contents-box")

        for box in contents_boxes:
            title_element = box.select_one("& > .title01")
            if title_element is None:
                continue

            title = title_element.get_text(strip=True)
            items = box.select(".ul-list01 > li")

            if "연구분야" in title:
                additional_info["fields"] = [{
                    "seq": idx + 1,
                    "name": field.get_text(strip=True)
                } for idx, field in enumerate(items)]

            elif "학력" in title:
                educations = []
                for idx, e in enumerate(items):
                    text = e.get_text(strip=True)
                    education = {"seq": idx + 1, "name": text}

                    for _type, keywords in EDU_KEYWORDS.items():
                        if any(keyword in text for keyword in keywords):
                            education["edu_type"] = _type
                            break

                    educations.append(education)

                additional_info["educations"] = educations

            elif "경력" in title:
                additional_info["fields"] = [{
                    "seq": idx + 1,
                    "name": career.get_text(strip=True)
                } for idx, career in enumerate(items)]

        for img in soup.select("img"):
            img.extract()

        result = ProfessorDTO(**{
            "seq": seq,
            "basic_info": basic_info,
            "additional_info": additional_info,
        })

        return result

    async def _scrape_all_async(self, interval, delay, session, **kwargs) -> List[ProfessorDTO]:
        seqs = self.scrape_seqs()
        results: List[ProfessorDTO] = []

        from tqdm import tqdm

        pbar = tqdm(range(0, len(seqs), interval), desc="Scraping Professors", total=len(seqs))
        for st_idx in pbar:
            ed_idx = st_idx + interval
            _seqs = seqs[st_idx:ed_idx]
            professors = await self.scrape_detail_async(session, seqs=_seqs)
            results += professors

            pbar.update(interval)

            await asyncio.sleep(delay)

        return results
