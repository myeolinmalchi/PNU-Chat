from typing import List, Optional
from langgraph.prebuilt import create_react_agent


# TODO: ProfessorService 크롤링 마무리
def init_professor_tools():

    async def search_professors(
        query: str,
        departments: Optional[List[str]] = None,
        include_schedule: bool = False,
        include_lab_info: bool = False,
        top_k: int = 5,
    ):
        """검색 쿼리를 바탕으로 관련된 교수님 정보를 검색합니다."""
        return {
            "query": query,
            "results": [{
                "name": "김철수",
                "department": departments[0] if departments else "전자공학과",
                "title": "부교수",
                "email": "kimcs@university.ac.kr",
                "lab": "임베디드 시스템 연구실" if include_lab_info else None,
                "schedule": [
                    {
                        "course": "디지털회로",
                        "day": "월",
                        "time": "10:00~11:30"
                    },
                    {
                        "course": "마이크로프로세서",
                        "day": "수",
                        "time": "13:00~14:30"
                    },
                ] if include_schedule else None,
            }][:top_k]
        }

    async def get_professor_info(
        name: str,
        department: str,
        include_schedule: bool = False,
        include_lab_info: bool = False,
    ):
        """교수님의 상세 정보를 불러옵니다."""
        return {
            "name": name,
            "department": department,
            "position": "정교수",
            "email": "leejh@university.ac.kr",
            "phone": "02-1234-5678",
            "office": "공학관 402호",
            "lab": {
                "name": "지능형 로봇 연구실",
                "location": "공학관 501호",
                "website": "https://irobotlab.university.ac.kr"
            } if include_lab_info else None,
            "schedule": [
                {
                    "course": "로봇공학",
                    "day": "화",
                    "time": "09:00~10:30"
                },
                {
                    "course": "기계학습",
                    "day": "목",
                    "time": "14:00~15:30"
                },
            ] if include_schedule else None,
        }

    return [
        search_professors,
        get_professor_info,
    ]


def init_professor_agent():
    tools = init_professor_tools()
    agent = create_react_agent(
        model="openai:gpt-4.1",
        tools=tools,
        prompt=(""),
        name="professor_agent",
    )

    return agent
