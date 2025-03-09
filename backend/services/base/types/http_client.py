from typing import NotRequired, TypedDict, Unpack

from aiohttp import ClientSession


class _SessionMethodParamType(TypedDict):
    session: NotRequired[ClientSession]


SessionArgsType = Unpack[_SessionMethodParamType]
