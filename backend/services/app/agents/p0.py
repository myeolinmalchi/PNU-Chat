from mixins.asyncio import retry_async
from services.base.service import BaseService

from .schemas import (
    P0_1_ResponseFormat,
    P0_2_ResponseFormat,
    P0_3_ResponseFormat,
    P0_4_ResponseFormat,
    P0_ResponseFormat,
)

from typing import Generic, List

import openai
from openai.lib import ResponseFormatT
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat_model import ChatModel
from services.base.service import BaseService


class P0_Base(BaseService, Generic[ResponseFormatT]):

    def __init__(
        self,
        client: openai.AsyncOpenAI,
        system_prompt: str,
        model: ChatModel = "gpt-4o-mini",
        temperature: float | openai.NotGiven = openai.NotGiven(),
        response_format: type[ResponseFormatT] | openai.NotGiven = openai.NotGiven(),
        store: bool = False,
        repeat_penalty: float | openai.NotGiven = openai.NotGiven(),
    ):
        self.client = client
        self.model = model
        self.temperature = temperature
        self.response_format = response_format
        self._system_prompt = system_prompt
        self.store = store
        self.repeat_penalty = repeat_penalty

    @property
    def system_prompt(self) -> ChatCompletionMessageParam:
        return {
            "role": "system",
            "content": self._system_prompt,
        }

    @retry_async(is_success=lambda res: res is not None)
    async def inference(
        self,
        question: str,
        history: List[ChatCompletionMessageParam] = [],
        context: str | None = None,
    ) -> ResponseFormatT | None:
        context_prompt = ("\n\n---\n\n"
                          "context:\n"
                          f"{context}") if context is not None else ""
        user_prompt = question + context_prompt
        messages = [self.system_prompt, *history, {"role": "user", "content": user_prompt}]

        completion = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            response_format=self.response_format,
            store=self.store,
        )

        parsed = completion.choices[0].message.parsed

        return parsed


class P0_1(P0_Base[P0_1_ResponseFormat]):

    def __init__(self, client, model, temperature):
        system_prompt = (
            "당신은 부산대학교 AI 어시스턴트 p0의 조수 역할을 하는 Agent p0_1입니다.\n"
            "당신의 역할은 주어진 사용자의 질문을 토대로 두 개 이상의 하위 질문을 생성하는 것입니다.\n"
            "\n"
            "instructions:\n"
            "하위 질문은 원본 질문을 답변하기 위해 먼저 해결해야 하는 내용을 포함합니다.\n"
            "중복되지 않아야 하며, 최대 세 개의 질문을 생성합니다.\n"
            "상위어와 유의어를 활용하여 보다 포괄적이고 일반적인 질문을 생성하세요.\n"
            "질문에 최대한 많은 정보를 포함하세요."
        )

        super().__init__(
            client=client,
            system_prompt=system_prompt,
            temperature=temperature,
            response_format=P0_1_ResponseFormat,
            model=model,
        )


class P0_2(P0_Base[P0_2_ResponseFormat]):

    def __init__(self, client, model, temperature):
        system_prompt = (
            "당신은 부산대학교 AI 어시스턴트 p0의 조수 역할을 하는 Agent p0_2입니다.\n"
            "당신의 역할은 사용자의 질문에 답하기 위해 적절한 검색 도구를 선택하는 것입니다.\n"
            "\n"
            "instructions:\n"
            "최대한 다양한 도구를 선택하세요.\n"
            "최대한 다양한 도구를 선택하세요.\n"
            "최대한 다양한 도구를 선택하세요.\n"
            "\n"
            "tools:\n"
            "- `search_supports`: 학생지원시스템에서 학교 생활과 관련된 일반적인 정보를 검색합니다.\n"
            "- `search_notices`: 학과 공지사항에서 학교 생활 및 학과 생활과 관련된 구체적인 정보를 검색합니다.\n"
            "- `search_pnu_notices`: 학교 공통 공지사항에서 학교 생활 및 공모전 등과 관련된 구체적인 정보를 검색합니다."
        )

        super().__init__(
            client=client,
            system_prompt=system_prompt,
            temperature=temperature,
            response_format=P0_2_ResponseFormat,
            model=model,
        )


class P0_3(P0_Base[P0_3_ResponseFormat]):

    def __init__(self, client, model, temperature):
        system_prompt = (
            "당신은 부산대학교 AI 어시스턴트 p0의 조수 역할을 하는 Agent p0_3입니다.\n"
            "당신의 역할은 사용자의 질문에 답하기 위해 검색 도구에 사용될 파라미터를 설정하는 것입니다.\n"
            "\n"
            "tools:\n"
            "- `semesters`: 문서가 등록된 학기를 지정합니다. 특정 시기에 대한 언급이 없다면 빈 배열로 둡니다."
            "- `query`:\n"
            "  - 검색에 사용되는 자연어 쿼리입니다.\n"
            "  - 구체적인 질문을 위해 원본 질문을 더욱 구체화 합니다.\n"
            "  - 의문문이어야 합니다.\n"
            "- `departments`: 검색 학과를 지정합니다. 직접적으로 언급된 학과만 포함합니다."
        )

        super().__init__(
            client=client,
            system_prompt=system_prompt,
            temperature=temperature,
            response_format=P0_3_ResponseFormat,
            model=model,
        )


class P0_4(P0_Base[P0_4_ResponseFormat]):

    def __init__(self, client, model, temperature):
        system_prompt = (
            "당신은 부산대학교 AI 어시스턴트 p0의 조수 역할을 하는 Agent p0_4입니다.\n"
            "당신의 역할은 사용자의 질문에 답하기 전에 주어진 context로부터 핵심 정보를 요약하는 것입니다.\n"
            "\n"
            "parameters:\n"
            "`urls`: 참고한 웹문서 또는 첨부파일의 url 주소입니다. url이 없는 문서의 경우 빈 배열로 출력합니다.\n"
            "`extracted`: 참고한 웹문서 또는 첨부파일에서 질문과 연관된 핵심 정보를 정리합니다."
        )

        super().__init__(
            client=client,
            system_prompt=system_prompt,
            temperature=temperature,
            response_format=P0_4_ResponseFormat,
            model=model,
        )


class P0(P0_Base[P0_ResponseFormat]):

    def __init__(self, client, model, temperature):
        system_prompt = (
            "당신은 부산대학교의 AI 어시스턴트 p0입니다.\n"
            "당신은 주어진 Context를 참고하여 사용자의 질문에 친절하게 답해야 합니다.\n"
            "\n"
            "properties:\n"
            "`paragraph`: "
            "  - 답변의 일부로, 문단 단위로 작성하세요."
            "  - 마크다운 포맷으로 작성해야하며, 각 문단의 내용이 중복되어서는 안됩니다.\n"
            "  - 각 문단의 내용은 일관되어야 하며, 모순이 있어서는 안됩니다.\n"
            "`urls`: 문단과 직접적으로 연관이 있는 문서의 url 목록입니다.\n"
            "\n"
            "instructions:\n"
            "context에 포함된 정보만 참고하여 답변합니다.\n"
            "context에 질문과 관련된 정보가 부족하다면 사용자에게 이를 알립니다.\n"
            "마크다운 문서 구조를 유지한채로 문단을 최대한 잘게 쪼개세요."
            "질문에 대해 맥락을 벗어나지 않으면서, 명료하게 답변합니다.\n"
        )

        super().__init__(
            client=client,
            system_prompt=system_prompt,
            temperature=temperature,
            response_format=P0_ResponseFormat,
            model=model,
            store=True,
                                               #repeat_penalty=0.1
        )

    """
    @retry_async(is_success=lambda res: res is not None)
    async def inference(self, question, history=[], context=None):
        context_prompt = ("\n\n---\n\n"
                          "context:\n"
                          f"{context}") if context is not None else ""
        user_prompt = question + context_prompt
        messages = [self.system_prompt, *history, {"role": "user", "content": user_prompt}]

        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )

        answer = completion.choices[0].message.content

        return answer
    """
