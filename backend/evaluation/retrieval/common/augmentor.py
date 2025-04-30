from typing import List, Optional
from openai import AsyncOpenAI
from pydantic import BaseModel, TypeAdapter
from mixins.asyncio import retry_async


class AugmentQueryPair(BaseModel):
    query: str
    paraphrase: str


AugmentQueryPairList = TypeAdapter(List[AugmentQueryPair])


class Augmentor:

    def __init__(self, openai_client: AsyncOpenAI, domain: str):

        self.client = openai_client

        self.system_prompt = (
            f"당신은 '{domain}'에 대한 정보를 찾고 있는 학생입니다.\n\n"
            "사용자의 문서를 읽고 다음을 수행하세요:\n\n"
            "1. 문서를 기반으로 학생이 검색창에 입력할 수 있을 만한 현실적인 질문 5개를 생성하세요.\n"
            "2. 각 질문에 대해 의미는 유지하되 다른 표현을 사용한 패러프레이즈 버전을 1개씩 생성하세요.\n\n"
            "가이드라인:\n"
            "1. 모든 질문과 패러프레이즈는 자연스럽고 대화체인 한국어 질문이어야 합니다.\n"
            "2. 각 문장은 반드시 물음표('?'로) 끝나야 합니다.\n"
            "3. 각 문장은 20자 이내로 작성하세요.\n"
            "4. 문서의 문장을 그대로 복사하지 마세요.\n"
            "5. 너무 포괄적인 질문은 피하고, 문서 내용에 구체적이고 관련 있는 질문을 작성하세요.\n"
            "6. 출력은 반드시 지정된 JSON 포맷으로 반환하세요.\n"
            "7. 반드시 한국어로 응답하세요."
        )
        self.response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "student_support_queries",
                "strict": True,
                "schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "학생이 문서를 검색하기 위해 입력할 수 있는 원본 질문입니다. 반드시 한국어로 작성하세요."
                            },
                            "paraphrase": {
                                "type": "string",
                                "description": "원본 질문과 의미는 같지만 다른 표현을 사용한 패러프레이즈 질문입니다. 반드시 한국어로 작성하세요."
                            }
                        },
                        "required": ["query", "paraphrase"],
                        "additionalProperties": False
                    }
                }
            }
        }

    @retry_async(times=10)
    async def generate(
        self,
        document_title: str,
        document_content: str,
        document_detail: Optional[str] = None,
        bad_example: Optional[str] = None,
        good_example: Optional[str] = None,
    ):

        user_prompt = f"Document Title: {document_title}\n\n"
        if document_detail:
            user_prompt += f"Document Info:\n{document_detail}\n\n"
        user_prompt += f"Document Content:\n{document_content}\n\n"
        if good_example:
            user_prompt += f"Good Examples:\n{good_example}\n\n"
        if bad_example:
            user_prompt += f"Bad Examples:\n{bad_example}\n\n"

        res = await self.client.chat.completions.create(
            model="solar-pro",
            messages=[{
                "role": "system",
                "content": self.system_prompt,
            }, {
                "role": "user",
                "content": user_prompt,
            }],
            response_format=self.response_format,        # type: ignore
        )

        raw = res.choices[0].message.content
        if not raw:
            raise ValueError

        parsed = AugmentQueryPairList.validate_json(raw)
        queries = [p.query for p in parsed] + [p.paraphrase for p in parsed]

        return queries
