from typing import Literal, Optional, Union
from langchain_core.tools import tool


# TODO: 시설 정보 테이블 추가
def init_building_tools():

    @tool
    async def measure_distances(start: str, end: str):
        """건물간의 거리와 소요시간을 계산합니다.

        Parameters:
            - start: 출발 건물명 (또는 약어)
            - end: 도착 건물명 (또는 약어)
        """

        return {}

    @tool
    async def get_building_info(
        name: str,
        include_lecturerooms: bool = True,
        include_facilities: bool = True,
        floor: Union[Literal['ALL'], int] = 'ALL',
    ):
        """건물의 기본 정보를 조회합니다. (위치, 강의실, 시설, 운영시간, 연구실 등)

        Parameters:
            - name: 건물의 명칭 또는 약어 (ex: 통합기계관, 통기관, 기계관)
            - include_lecturerooms: 강의실 정보 포함 여부 (default: true)
            - include_facilities: 시설 정보 포함 여부 (default: true)
            - floor: 특정 층수에 대한 정보만 포함 (default: ALL)
        """

        return {}

    @tool
    async def search_facility(
        facility_query: str,
        from_building: Optional[str] = None,
        top_k: int = 5,
    ):
        """특정 시설(ex: '편의점', '프린터')이 있는 건물을 찾습니다.

        Parameters:
            - facility_query: 찾고자 하는 시설을 자연어로 입력합니다. (ex: '편의점', '프린터', '3D 프린터')
            - from_building: 기준이 되는 건물 이름(ex: '경통관', '기계관'). 지정하면 가장 가까운 건물과 그 거리를 반환합니다.
            - top_k: 검색 결과를 몇개까지 반환할지(거리순 정렬). from_building이 없다면 무시될 수 있습니다.
        """

        return {}

    return [
        measure_distances,
        get_building_info,
        search_facility,
    ]
