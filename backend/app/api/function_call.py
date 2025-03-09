import os
import json
from dotenv import load_dotenv
from typing import Dict, List, Tuple

from fastapi import HTTPException

from openai.types.chat import ChatCompletionToolParam
from openai import OpenAI
import openai

from services.professor import create_professor_service
from db.repositories.calendar import CalendarRepository, SemesterRepository
from db.models.notice import NoticeModel
from db.models.support import SupportModel
from db.models.professor import ProfessorModel
from services.base.types.calendar import SemesterType

load_dotenv()


# OpenAI functioncalling 비동기 함수
async def function_calling(question: str) -> str:
    question = question
    openai.api_key = os.environ.get("OPENAI_KEY")

    tools = TOOLS
    prompt: str = prompt

    messages: List = [{"role": "system", "content": prompt}, {"role": "user", "content": f"{question}"}]

    while True:
        completion = await openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            functions=tools,
            function_call="auto",
        )
        try:
            choice = completion.get("choices")[0]
            if choice["finish_reason"] == "function_call":
                function_name = function_call["name"]
                function_args = json.loads(function_call["arguments"])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error during function call: {str(e)}")

        try:
            choice = completion.get("choices")[0]
            if choice["finish_reason"] == "function_call":
                function_call = choice["message"]["function_call"]
                function_name = function_call["name"]
                function_args = json.loads(function_call["arguments"])

                if function_name == "search_support":
                    support_search_result = await search_support(**function_args)
                    supports_info = []
                    for support, rrf_score in support_search_result:
                        support_info = (
                            f"Category: {support.category}\n"
                            f"SubCategory: {support.sub_category}\n"
                            f"Title: {support.title}\n"
                            f"URL: {support.url}\n"
                            f"Content: {support.content}\n"
                        )
                        supports_info.append(support_info)
                    supports_info_str = "\n\n".join(supports_info)
                    messages.append({"role": "function", "content": f"{supports_info_str}"})

                elif function_name == "search_notices":
                    notice_search_result = await search_notices(**function_args)
                    notices_info = []
                    for notice, rrf_score in notice_search_result:
                        notice_info = (
                            f"Title: {notice.title}\n"
                            f"Date: {notice.date}\n"
                            f"URL: {notice.url}\n"
                            f"Department: {notice.department}\n"
                            f"content: {notice.content}\n"
                        )
                        notices_info.append(notice_info)
                    notices_info_str = "\n\n".join(notices_info)
                    messages.append({{"role": "function", "content": f"{notices_info_str}"}})

                elif function_name == "search_calendar":
                    calendar_search_result = await search_calendar(**function_args)
                    calendars_info: List[Dict] = []
                    for calendar in calendar_search_result:
                        calendar_info = (f"기간: {calendar.period}\n"
                                         f"학사일정: {calendar.description}\n")
                        calendars_info.append(calendar_info)
                    calendar_info_str = "\n\n".join(calendars_info)
                    messages.append({"role": "function", "content": f"{calendar_info_str}"})

                elif function_name == "search_professor":
                    professor_search_result = await search_professor(**function_args)
                    professors_info = []
                    for professor, rrf_score in professor_search_result:
                        professor_info = (
                            f"Name: {professor.name}\n"
                            f"Office Phone: {professor.office_phone}\n"
                            f"Website: {professor.website}\n"
                            f"Email: {professor.email if professor.emial else 'N/A'}\n"
                            f"Department: {professor.department.name}\n"                     # department 객체의 name 필드 접근
                            f"Major: {professor.major.name if professor.major else 'N/A'}\n" # major가 없을 수 있으므로 체크
                            f"Detail: {professor.detail}"
                        )
                        professors_info.append(professor_info)
                    professor_info_str = "\n\n".join(professors_info)
                    messages.append({"role": "function", "content": f"{professor_info_str}"})
                else:
                    raise HTTPException(status_code=400, detail="Unknown function called")
            else:
                answer = choice["message"]["content"]
                messages.append({"role": "assistant", "content": answer})
                return choice["message"]["content"]                                          ##여기서 최종 답변 생성하고 리턴되는거임 !!

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error during function call: {str(e)}")

        continue


async def search_support(query: str) -> List[Tuple[SupportModel, float]]:
    support_service = create_support_service()
    search_result = support_service.search_supports_with_filter(query=query)

    return search_result


async def search_notices(query: str) -> List[Tuple[NoticeModel, float]]:
    notice_service = create_notice_service()
    search_result = notice_service.search_notices_with_filter(query=query)

    return search_result


## 날짜와 학사 일정에 대한 질문을 받으면 그걸 토대로 학기 데이터를 추출해서 이를 semestertype객체로서 전달
## semetsetertype객체를 이용해서 calendar table에서
async def search_calendar(query: str, semesters: List[SemesterType]):
    # 학사일정 searching function
    semester_repo = SemesterRepository()
    calendar_repo = CalendarRepository()
    calendar_service = CalendarService(semester_repo=semester_repo, calendar_repo=calendar_repo)

    search_result = calendar_service.get_calendars(semesters=semesters)

    return search_result


async def search_professor(query: str) -> List[Tuple[ProfessorModel, float]]:
    professor_service = create_professor_service()
    search_result = professor_service.search_professors(query=query)

    return search_result
