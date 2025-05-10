from typing import Literal, Optional, Union
from langgraph.prebuilt import create_react_agent


# TODO: 시설 정보 테이블 추가
def init_building_tools():

    async def measure_distances(start: str, end: str):
        """건물간의 거리와 소요시간을 계산합니다."""
        return {
            "start": start,
            "end": end,
            "distance_meters": 320,
            "estimated_time_minutes": 5,
            "path_description": f"{start}에서 {end}까지 도보 기준 약 5분 소요됩니다."
        }

    async def get_building_info(
        name: str,
        include_lecturerooms: bool = True,
        include_facilities: bool = True,
        floor: Union[Literal['ALL'], int] = 'ALL',
    ):
        """건물의 기본 정보를 조회합니다."""
        return {
            "name": name,
            "location": "캠퍼스 남측",
            "floors": 5,
            "operating_hours": "08:00 ~ 22:00",
            "lecturerooms": [
                {
                    "room": "101",
                    "type": "강의실",
                    "capacity": 50
                },
                {
                    "room": "102",
                    "type": "컴퓨터실",
                    "capacity": 40
                },
            ] if include_lecturerooms else [],
            "facilities": [
                {
                    "name": "카페",
                    "floor": 1
                },
                {
                    "name": "복사실",
                    "floor": 2
                },
            ] if include_facilities else [],
            "research_labs": [{
                "lab": "기계설계연구실",
                "floor": 4
            }, {
                "lab": "로봇지능연구실",
                "floor": 5
            }]
        }

    async def search_facility(
        facility_query: str,
        from_building: Optional[str] = None,
        top_k: int = 5,
    ):
        """특정 시설이 있는 건물을 찾습니다."""
        return {
            "query": facility_query,
            "results": [{
                "building": "기계관",
                "facility_name": facility_query,
                "floor": 1,
                "distance_from_reference": 120 if from_building else None,
                "estimated_time_minutes": 2 if from_building else None,
            }, {
                "building": "전산관",
                "facility_name": facility_query,
                "floor": 2,
                "distance_from_reference": 350 if from_building else None,
                "estimated_time_minutes": 6 if from_building else None,
            }][:top_k]
        }

    return [
        measure_distances,
        get_building_info,
        search_facility,
    ]


def init_building_agent():
    tools = init_building_tools()
    agent = create_react_agent(
        model="openai:gpt-4.1-nano",
        tools=tools,
        prompt=(""),
        name="building_agent",
    )

    return agent
