from typing import List, Optional
from openai import AsyncOpenAI
from pydantic import BaseModel, TypeAdapter
from mixins.asyncio import retry_async


class ValidationResult(BaseModel):
    valid: bool
    reasons: Optional[List[str]] = None


ValidationResultList = TypeAdapter(List[ValidationResult])


class Validator:
    """생성된 Query에 대해 규칙 준수 여부 판정"""

    def __init__(self, openai_client: AsyncOpenAI, domain: str):
        self.client = openai_client

        self.system_prompt = (
            f"당신은 {domain} 검색 데이터 구축을 위한 품질관리자입니다.\n"
            "다음 규칙을 모두 만족하는지 평가하세요:\n"
            "1) 자연스러운 한국어 질문이어야 함\n"
            "2) 문장은 너무 길어서는 안되며, '?' 로 끝나야 함\n"
            "3) 문서에서 문장을 그대로 복사하지 말 것\n"
            "4) 문장이 충분히 구체적이어야 함\n\n"
            "5) query에 대한 응답을 document에서 찾을 수 있어야 함\n\n"
            "각 query 대해 {valid: bool, reasons: [string]} 형태로 JSON 배열을 반환하세요.\n"
            "규칙을 위반했다면 valid=false로, 위반 사유를 한글로 기술하세요.\n"
            "규칙을 준수했다면 valid=true로, reasons는 빈 배열로 응답하세요."
        )

        self.response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "validation_results",
                "strict": True,
                "schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "valid": {
                                "type": "boolean"
                            },
                            "reasons": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                            },
                        },
                        "required": ["valid", "reasons"],
                        "additionalProperties": False,
                    },
                },
            },
        }

    @retry_async(times=10)
    async def validate(
        self,
        document_title: str,
        document_content: str,
        queries: List[str],
    ) -> List[ValidationResult]:

        joined_queries = "\n".join(f"{idx+1}. {query}" for idx, query in enumerate(queries))

        user_prompt = (
            f"Document Title:\n{document_title}\n\n"
            f"Document Content:\n{document_content}\n\n"
            f"Queries\n{joined_queries}"
        )

        res = await self.client.chat.completions.create(
            model="solar-pro",
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                },
            ],
            response_format=self.response_format,        # type: ignore
        )

        raw = res.choices[0].message.content
        if not raw:
            raise ValueError("Empty validation response")

        return ValidationResultList.validate_json(raw)
