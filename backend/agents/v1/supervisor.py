from langchain.chat_models import init_chat_model
from langgraph_supervisor import create_supervisor

from agents.v1.buildings import init_building_agent
from agents.v1.department import init_department_agent
from agents.v1.professor import init_professor_agent

from pprint import pprint

import asyncio


def init_supervisor():
    professor_agent = init_professor_agent()
    department_agent = init_department_agent()
    building_agent = init_building_agent()

    supervisor = create_supervisor(
        model=init_chat_model("openai:gpt-4.1"),
        agents=[
            professor_agent,
            department_agent,
            building_agent,
        ],
        add_handoff_back_messages=True,
        prompt="당신은 부산대학교의 FAQ 관련 검색 작업을 총괄하는 Supervisor Agent입니다. 정확한 정보를 검색하고, 사용자에게 최대한 자세하고 친절한 답변을 제공하세요."
    ).compile()

    return supervisor


async def run(query: str):
    supervisor = init_supervisor()

    result = await supervisor.ainvoke({"messages": {
        "role": "user",
        "content": query,
    }})

    pprint(result)


if __name__ == "__main__":
    asyncio.run(run("기계관에는 어떤 편의시설이 있나요?"))
