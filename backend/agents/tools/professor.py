from typing import List, Optional

from langchain_core.tools import tool


# TODO: ProfessorService 크롤링 마무리
def init_professor_tools():

    @tool
    async def search_professors(
        query: str,
        departments: Optional[List[str]] = None,
        include_schedule: bool = False,
        include_lab_info: bool = False,
        top_k: int = 5,
    ):
        """검색 쿼리를 바탕으로 관련된 교수님 정보를 검색합니다.

        Parameters:
            - query: 문맥 검색에 사용되는 쿼리. 문장 형태로 작성합니다.
            - departments: 검색 학과를 지정합니다. (default: null, 전체 학과 검색)
            - include_schedule: 교수님의 강의 시간표 포함 여부를 지정합니다. (default: false)
            - include_lab_info: 교수님의 연구실 정보 포함 여부를 지정합니다. (default: false)
            - top_k: 검색 결과를 몇개까지 반환할지. 유사도 높은 순 정렬
        """

        return {}

    @tool
    async def get_professor_info(
        name: str,
        department: str,
        include_schedule: bool = False,
        include_lab_info: bool = False,
    ):
        """교수님의 상세 정보를 불러옵니다.

        Parameters:
            - name: 교수님 성함.
            - department: 검색 학과를 지정합니다.
            - include_schedule: 교수님의 강의 시간표 포함 여부를 지정합니다. (default: false)
            - include_lab_info: 교수님의 연구실 정보 포함 여부를 지정합니다. (default: false)
        """

        return {}

    return [
        search_professors,
        get_professor_info,
    ]
