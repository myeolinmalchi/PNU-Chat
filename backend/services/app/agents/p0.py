from mixins.asyncio import retry_async
from services.base.service import BaseService

from .schemas import (
    P0_1_ResponseFormat,
    P0_2_ResponseFormat,
    P0_3_ResponseFormat,
    P0_4_ResponseFormat,
    P0_ResponseFormat,
)

from typing import Dict, Generic, List, Optional, Tuple

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
    ) -> Tuple[Optional[ResponseFormatT], Dict[str, int]]:
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

        usage = {}
        if completion.usage:
            usage["input"] = completion.usage.prompt_tokens
            usage["output"] = completion.usage.completion_tokens
            if completion.usage.prompt_tokens_details:
                usage["input_cached"] = completion.usage.prompt_tokens_details.cached_tokens

        return parsed, usage


class P0_1(P0_Base[P0_1_ResponseFormat]):

    def __init__(self, client, model, temperature):
        system_prompt = (
            "당신은 부산대학교 AI 어시스턴트 p0의 조수 역할을 하는 Agent p0_1입니다.\n"
            "당신의 임무는 사용자의 원본 질문을 바탕으로 의미를 확장하고 명확화하기 위해 하위 질문을 생성하는 것입니다.\n"
            "\n"
            "instructions:\n"
            "- 하위 질문은 원본 질문을 정확히 이해하고 답변하기 위해 반드시 필요한 전제나 세부 사항을 분해한 것입니다.\n"
            "- 중복되지 않는 최대 두 개의 하위 질문을 생성하세요.\n"
            "- 원본 질문의 맥락에서 생략되었을 수 있는 요소(대상, 범위, 조건, 시간 등)를 보완하세요.\n"
            "- 유사어, 상위 개념, 제도적 용어를 활용하여 검색 가능성을 확장하세요.\n"
            "- 각각의 질문은 명확하고 독립적인 문장이어야 하며, 최대한 많은 정보를 포함해야 합니다."
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
            "도구는 3개까지 선택 가능합니다.\n"
            "최대한 다양한 도구를 사용하세요.\n"
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
            "`extracted`: \n"
            "참고한 웹문서 또는 첨부파일에서 질문과 연관된 핵심 정보를 정리합니다.\n"
            "각각의 문서들은 출처가 상이하며, 내용이 일관되지 않을 수 있습니다. 이점에 유의하세요."
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
            "  - 질문과 관련되지 않은 추가 정보는 임의로 작성하지 마세요.\n"
            "`urls`: 문단과 직접적으로 연관이 있는 출처의 url 목록입니다.\n"
            "\n"
            "instructions:\n"
            "context에 포함된 정보만 참고하여 답변합니다.\n"
            "context에 없는 정보는 임의로 지어내지 마세요.\n"
            "context에 질문과 관련된 정보가 부족하다면 사용자에게 이를 알립니다.\n"
            "context에서 관련 정보를 찾을 수 없다면, 이를 사용자에게 알리고 사과하세요.\n"
            "마크다운 문서 구조를 유지한채로 문단을 최대한 잘게 쪼개세요.\n"
            "각 paragraph의 내용은 일관되어야 하며, 모순이 있어서는 안됩니다.\n"
            "Context의 각 내용은 출처가 상이하며, 내용이 일관되지 않을 수 있습니다. 이점에 유의하세요."
        )

        super().__init__(
            client=client,
            system_prompt=system_prompt,
            temperature=temperature,
            response_format=P0_ResponseFormat,
            model=model,
            store=True,
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
