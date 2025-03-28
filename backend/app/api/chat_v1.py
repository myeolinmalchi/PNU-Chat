import json
from typing import List
from dependency_injector.wiring import inject, Provide
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from app.schemas.chat import ChatRequest, ChatResponse, SearchHistory
from containers import AppContainer

from services.app import ApplicationService
from services.app.prompt import TEMPLATE, create_prompt_factory, init_search_history
from config.logger import _logger

import os

load_dotenv()

router = APIRouter()

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
client = AsyncOpenAI(
    api_key=UPSTAGE_API_KEY,
    base_url="https://api.upstage.ai/v1",
)

#client = AsyncOpenAI()

logger = _logger(__name__)


@router.post("/chat", response_model=ChatResponse)
@inject
async def chat(
    req: ChatRequest,
    app: ApplicationService = Depends(Provide[AppContainer.app]),
):

    now, semester = app.load_today_info()
    tools = app.load_tools(semester["year"], semester["type_"])

    create_prompt = create_prompt_factory(
        now.year,
        now.month,
        now.day,
        semester["year"],
        semester["type_"],
    )

    search_histories: List[SearchHistory] = [*req.contexts]

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_cached_prompt_tokens = 0

    for _ in range(3):

        history_contexts = [init_search_history(
            s.tool_name,
            "\n".join(s.content),
        ) for s in (search_histories)]

        context_dump = create_prompt(
            req.question,
            req.university,
            req.department,
            req.major,
            req.grade,
            history_contexts,
            req.messages,
        )
        prompt = TEMPLATE + "\n" + context_dump

        #reasoning_effort = "low" if req.model == "o3-mini" else NotGiven()
        messages: List[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": req.question
            },
        ]
        #tool_choice = "auto" if len(history_contexts) > 5 or idx > 0 else "required"

        completion = await client.chat.completions.create(
            model=req.model,
            tools=tools,
            messages=messages,
            tool_choice="auto",
        )

        #total_prompt_tokens += completion.usage.prompt_tokens                              # type: ignore
        #total_cached_prompt_tokens += completion.usage.prompt_tokens_details.cached_tokens # type: ignore
        #total_completion_tokens += completion.usage.completion_tokens                      # type: ignore

        result = await app.call_by_chat(completion)

        if not result:
            continue

        if isinstance(result, str):
            """
            filtered_contexts = await app.filter_relate_contexts_async(
                result,
                acc_histories + search_histories,
                threshold=0.3,
            )
            """
            return {
                "question": req.question,
                "answer": result,
                "contexts": search_histories,
                "messages": [
                    *req.messages, {
                        "role": "user",
                        "content": req.question
                    }, {
                        "role": "assistant",
                        "content": result
                    }
                ],
                "usage": {
                    "prompt_tokens": total_prompt_tokens,
                    "cached_prompt_tokens": total_cached_prompt_tokens,
                    "completion_tokens": total_completion_tokens,
                    "total_tokens": total_prompt_tokens + total_completion_tokens
                }
            }

        search_histories += [
            SearchHistory(**{
                "tool_name": tool_call.function.name,
                "content": content,
            }) for content, tool_call in result
        ]

    raise HTTPException(
        status_code=400,
        detail="답변 생성 중 일시적인 오류가 발생했습니다.",
    )
