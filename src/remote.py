from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Self, Union, Tuple, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, Literal
from pyrocko.gf import LocalEngine

from fastapi import FastAPI

if TYPE_CHECKING:
    from pyrocko.gf import Request as PyrockoRequest
    from pyrocko.gf import Response as PyrockoResponse
    from pyrocko.gf import Source as PyrockoSource
    from pyrocko.gf import Target as PyrockoTarget


class CommunicationTarget(BaseModel):
    lat: float | 0.
    lon: float | 0.
    north_shift: float | 0.
    east_shift: float | 0.
    depth: float | 0.
    elevation: float | 0.
    store_id: str
    sample_rate: Union[float, None]
    azimuth: float
    dip: float
    tmin: Union[float, None]
    tmax: Union[float, None]
    codes: Tuple[str] | ('', 'STA', '', 'Z')
    interpolation: Literal['nearest_neighbor', 'multilinear']
    quantity: Literal[
        'displacement',
        'velocity',
        'acceleration',
        'rotation_displacement',
        'rotation_velocity',
        'rotation_acceleration',
        'pressure',
        'tilt',
        'pore_pressure',
        'darcy_velocity',
        'vertical_tilt']

    @classmethod
    def from_pyrocko(cls, target: PyrockoTarget) -> Self:
        attributes = target.__dict__
        attributes.pop('_latlon')
        attributes.pop('filter')
        return cls(**attributes)

    def to_pyrocko(self) -> PyrockoTarget:
        return PyrockoTarget(**self.__dict__)

class Source(BaseModel):
    @classmethod
    def from_pyrocko(cls, source: PyrockoSource) -> Self:
        ...

    def to_pyrocko(self) -> PyrockoSource:
        ...


class GFRequest(BaseModel):
    uid: UUID = Field(default_factory=uuid4)

    sources: list[Source]
    targets: list[CommunicationTarget]

    @classmethod
    def from_pyrocko(cls, request: PyrockoRequest) -> Self:
        ...

    def to_pyrocko(self) -> PyrockoRequest:
        ...


class GFResponse(BaseModel):
    uid: UUID = Field(default_factory=uuid4)

    @classmethod
    def from_pyrocko(cls, response: PyrockoResponse) -> Self:
        ...

    def to_pyrocko(self) -> PyrockoResponse:
        ...


app = FastAPI()


@app.post("/request", respone_model=GFResponse)
async def request(request: GFRequest):
    pyrocko_request = request.to_pyrocko()
    pyrocko_response = await asyncio.to_thread(LocalEngine.process, pyrocko_request)
    return GFResponse.from_pyrocko(pyrocko_response)
