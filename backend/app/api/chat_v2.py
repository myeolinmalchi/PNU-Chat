import textwrap
from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI, NotGiven
from openai.types.chat import ChatCompletionMessageParam

from app.schemas.chat import ChatRequestV2, ChatResponseV2
from containers import AppContainer

from services.app import ApplicationService
from services.app.prompt import TEMPLATE_V2
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
    app: ApplicationService = Depends(Provide[AppContainer.app]),
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

    now, semester = app.load_today_info()
    tools = app.load_tools(semester["year"], semester["type_"])

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_cached_prompt_tokens = 0

    USER_PROMPT = textwrap.dedent(
        f"""\
        User Info:
            - 단과대학: {req.university}
            - 학과/학부: {req.department}
            - 학년: {req.grade}"""
    )

    DATE_PROMPT = textwrap.dedent(
        f"""\
        Date Info:
            - year: {now.year}
            - month: {now.month}
            - day: {now.day}
            - academic year: {semester["year"]}
            - semester type: {semester["type_"]}"""
    )

    SYSTEM_PROMPT = "\n".join((TEMPLATE_V2, USER_PROMPT, DATE_PROMPT))

    system_message: ChatCompletionMessageParam = {
        "role": "system",
        "content": SYSTEM_PROMPT,
    }

    messages = [*req.messages, {"role": "user", "content": req.question}]

    for idx in range(3):

        reasoning_effort = "low" if req.model == "o3-mini" else NotGiven()
        tool_choice = "auto" if len(req.messages) > 0 or idx > 0 else "required"
        temperature = 0.3 if req.model in ("gpt-4o-mini", "gpt-4o") else NotGiven()

        completion = await client.chat.completions.create(
            model=req.model,
            tools=tools,
            messages=[system_message, *messages],          # type: ignore
            tool_choice=tool_choice,
            reasoning_effort=reasoning_effort,
            parallel_tool_calls=True,
            temperature=temperature,
                                                           #max_completion_tokens=1024,
        )

        total_prompt_tokens += completion.usage.prompt_tokens                              # type: ignore
        total_cached_prompt_tokens += completion.usage.prompt_tokens_details.cached_tokens # type: ignore
        total_completion_tokens += completion.usage.completion_tokens                      # type: ignore

        result = await app.call_by_chat(completion)

        if not result:
            continue

        if isinstance(result, str):
            return {
                "title": title,
                "question": req.question,
                "answer": result,
                "messages": [*messages, {
                    "role": "assistant",
                    "content": result
                }],
                "contexts": [],
                "usage": {
                    "prompt_tokens": total_prompt_tokens,
                    "cached_prompt_tokens": total_cached_prompt_tokens,
                    "completion_tokens": total_completion_tokens,
                    "total_tokens": total_prompt_tokens + total_completion_tokens
                }
            }

        messages.append(completion.choices[0].message) # type: ignore

        for content, tool_call in result:
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": "\n".join(content),
            })

    raise HTTPException(
        status_code=400,
        detail="답변 생성 중 일시적인 오류가 발생했습니다.",
    )
