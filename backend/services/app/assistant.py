from abc import abstractmethod
import asyncio
from itertools import chain
import json
from typing import Dict, List, Optional

from aiohttp import ClientSession
from openai.types.chat import ChatCompletionMessageParam
from services.app.search import AppSearchService
from services.base.embedder import embed_async
from services.base.service import BaseService

from services.app.agents import p0

from config.logger import _logger

import inspect

logger = _logger("AssistantService")


class BaseAssistantService(BaseService):

    def __init__(self, search_service: AppSearchService, **kwargs):
        self.search_service = search_service
        self.__dict__.update(kwargs)

    @abstractmethod
    async def pipeline_async(
        self,
        question: str,
        university: str,
        department: str,
        history: List[ChatCompletionMessageParam] = [],
        session: Optional[ClientSession] = None,
    ) -> str:
        pass


class P0AssistantServiceV1(BaseAssistantService):

    def __init__(
        self,
        p0: p0.P0,
        p0_1: p0.P0_1,
        p0_2: p0.P0_2,
        p0_3: p0.P0_3,
        p0_4: p0.P0_4,
        search_service: AppSearchService,
    ):
        self.p0 = p0
        self.p0_1 = p0_1
        self.p0_2 = p0_2
        self.p0_3 = p0_3
        self.p0_4 = p0_4
        self.search_service = search_service

    async def call_by_name(self, tool_name: str, **args) -> List[str]:
        func = getattr(self.search_service, tool_name)
        if inspect.iscoroutinefunction(func):
            return await func(**args)
        return func(**args)

    async def pipeline_async(
        self,
        question,
        university,
        department,
        history=[],
        session=None,
    ):
        if session is None:
            raise ValueError("'session' must be provided.")

        today, semester = self.search_service.load_today_info()
        base_info = (
            f"Date: {today.year}년 {today.month}월 {today.day}일\n"
            f"Semester: {semester['year']}학년도 {semester['type_'].value}\n"
            f"User: {university} {department} 학부생\n"
            "---\n"
        )

        usage = {
            "input": 0,
            "output": 0,
            "input_cached": 0,
        }

        def add_usage(_usage: Dict[str, int]):
            usage["input"] += _usage["input"]
            usage["input_cached"] += _usage["input_cached"]
            usage["output"] += _usage["output"]

        logger("before extract sub questions...")
        p0_1_response, usage1 = await self.p0_1.inference(base_info + question, history)

        if not p0_1_response:
            raise ValueError

        sub_questions = p0_1_response.sub_questions
        add_usage(usage1)

        logger("embed sub questions...")
        sub_question_embeddings = await embed_async(
            sub_questions,
            session=session,
            chunking=False,
            html=False,
        )

        logger("choose search tools...")
        p0_2_futures = [self.p0_2.inference(base_info + q, history) for q in sub_questions]
        p0_2_responses = await asyncio.gather(*p0_2_futures)
        tools = [res.tools for res, _ in p0_2_responses if res is not None]
        usage2 = [_usage for res, _usage in p0_2_responses if res is not None]

        for _usage in usage2:
            add_usage(_usage)

        #logger("choose search parameters...")
        #p0_3_futures = [self.p0_3.inference(base_info + q) for q in sub_questions]
        #p0_3_responses = await asyncio.gather(*p0_3_futures)
        #tool_params = [res for res in p0_3_responses if res is not None]

        #if not tools or not tool_params:
        #    raise ValueError

        logger("run tools...")
        tool_result_futures = [
            asyncio.gather(
                *[
                    self.call_by_name(
                        tool_name=_tool.value, **{
                            "departments": [department],
                            "query": q,
                            "embeddings": es,
                        }
                    ) for _tool in tool
                ]
            ) for tool, q, es in zip(tools, sub_questions, sub_question_embeddings)
        ]

        tool_results = await asyncio.gather(*tool_result_futures)

        logger("extract essential infos...")

        p0_4_futures = [
            self.p0_4.inference(base_info + q, history, context="\n".join(_tool_result))
            for q, tool_result in zip(sub_questions, tool_results) for _tool_result in tool_result
        ]

        p0_4_responses = await asyncio.gather(*p0_4_futures)
        documents = [res.documents for res, _ in p0_4_responses if res is not None]
        usage4 = [_usage for res, _usage in p0_4_responses if res is not None]

        for _usage in usage4:
            add_usage(_usage)

        if not documents:
            raise ValueError

        flattened_documents = list(chain(*documents))
        flattened_documents = [doc.model_dump() for doc in flattened_documents]

        document_strs = json.dumps(flattened_documents, ensure_ascii=False)

        logger("create final answer...")
        p0_response, usage5 = await self.p0.inference(question, history, context=document_strs)

        if not p0_response:
            raise ValueError

        add_usage(usage5)

        url2md = lambda url: f"[FILE]({url})" if "download" in url else f"[URL]({url})"
        final_answer = "\n\n".join([
            answer.paragraph + " " + "".join(map(url2md, answer.urls)) for answer in p0_response.answers
        ])

        print(usage5)

        return final_answer
