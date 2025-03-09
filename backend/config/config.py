import json
from typing import Dict, List, NotRequired, Any, Optional, TypedDict, overload


class DepartmentURL(TypedDict):
    base: str
    notices: Dict[str, str]
    professors: List[str]


class Department(TypedDict):
    info: NotRequired[Any]
    urls: DepartmentURL


class University(TypedDict):
    info: NotRequired[Any]
    departments: Dict[str, Department]


class PNUData(TypedDict):
    info: NotRequired[Any]
    universities: Dict[str, University]


def load_data(path: str):
    with open(path, encoding="utf-8-sig") as f:
        raw = json.load(f)

    return PNUData(**raw)


_PNU = None


def get_pnudata(path: str = "config/base_info.json") -> PNUData:
    global _PNU
    if not _PNU:
        with open(path, encoding="utf-8-sig") as f:
            raw = json.load(f)
        _PNU = PNUData(**raw)

    return _PNU


def get_professor_urls(department: str) -> List[str]:

    data = get_pnudata()
    univs = [u["departments"] for u in data["universities"].values()]

    _data = None
    for univ in univs:
        if department in univ:
            _data = univ[department]["urls"]
            break

    if not _data:
        raise ValueError(f"존재하지 않는 학과입니다. ({department})")

    _data = [f"{_data['base']}{p}" for p in _data["professors"]]

    return _data


@overload
def get_notice_urls(department: str, category: str) -> str:
    pass


@overload
def get_notice_urls(department: str, category: None = None) -> Dict[str, str]:
    pass


def get_notice_urls(department: str,
                    category: Optional[str] = None) -> str | Dict[str, str]:

    data = get_pnudata()
    univs = [u["departments"] for u in data["universities"].values()]

    _data = None
    for univ in univs:
        if department in univ:
            _data = univ[department]["urls"]
            break

    if not _data:
        raise ValueError(f"존재하지 않는 학과입니다. ({department})")

    _data = {
        d: f"{_data['base']}{path}"
        for d, path in _data["notices"].items()
    }

    if category and category in _data:
        return _data[category]

    return _data


def get_universities() -> Dict[str, List[str]]:
    data = get_pnudata()
    univs = data["universities"]

    def parse_departments(x):
        return [name for name in x["departments"].keys()]

    return {k: parse_departments(v) for k, v in univs.items()}
