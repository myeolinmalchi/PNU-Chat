from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageParam
from pydantic import BaseModel
from typing import Any, Dict, Literal, List, Optional


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class SearchHistory(BaseModel):
    tool_name: str
    tool_args: Dict[str, Any]
    content: str | List[str]


class ChatRequest(BaseModel):
    question: str
    university: str
    department: str
    major: Optional[str] = None
    grade: int = 1
    model: Literal["gpt-4o", "o3-mini", "gpt-4o-mini"] = "o3-mini"
    messages: List[Message] = []
    contexts: List[SearchHistory] = []


class ChatRequestV2(BaseModel):
    question: str
    university: str
    department: str
    major: Optional[str] = None
    grade: int = 1
    model: Literal["gpt-4o", "o3-mini", "gpt-4o-mini"] = "gpt-4o-mini"
    messages: List[ChatCompletionMessageParam] = []


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    cached_prompt_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    answer: str
    question: str
    messages: List[Message] = []
    contexts: List[SearchHistory]
    usage: Usage


class ChatResponseV2(BaseModel):
    title: Optional[str] = None
    answer: str
    question: str
    messages: List[ChatCompletionMessageParam | ChatCompletionMessage] = []
    usage: Usage
