from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends
from openai import AsyncOpenAI

from app.schemas.chat import ChatRequestV2, ChatResponseV2
from containers import AppContainer

from services.app.assistant import BaseAssistantService
from config.logger import _logger

from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api")

client = AsyncOpenAI()

logger = _logger(__name__)


@router.get("/health_check")
def health_check():
    return {"message": "good"}


@router.post("/chat", response_model=ChatResponseV2)
@inject
async def chat(
    req: ChatRequestV2,
    assistant: BaseAssistantService = Depends(Provide[AppContainer.assistant_package.assistant_service]),
):
    title = None
    if not req.messages:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": "당신은 사용자의 첫 질문을 바탕으로 채팅의 제목을 생성하는 assistant입니다. 10글자 내외의 짧은 제목을 작성하세요."
            }, {
                "role": "user",
                "content": req.question
            }]
        )
        title = completion.choices[0].message.content

    answer = await assistant.pipeline(
        req.question,
        req.university,
        req.department,
        history=req.messages,
    )

    messages = [*req.messages, {
        "role": "user",
        "content": req.question,
    }, {
        "role": "assistant",
        "content": answer,
    }]

    return {
        "title": title,
        "answer": answer,
        "question": req.question,
        "messages": messages,
        "usage": {
            "prompt_tokens": 0,
            "cached_prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }
