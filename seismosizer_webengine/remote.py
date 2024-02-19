from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Self, Union, Tuple, List, Literal, Dict
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from pyrocko.gf import LocalEngine

from fastapi import FastAPI
from numpy import ndarray, array

# if TYPE_CHECKING:
from pyrocko.gf import Request as PyrockoRequest
from pyrocko.gf import Response as PyrockoResponse

from pyrocko.gf.seismosizer import source_classes
from pyrocko.gf.seismosizer import stf_classes

from pyrocko.gf import Target as PyrockoTarget
from pyrocko.gf import Source as PyrockoSource


stf_name_to_class = {stf.__name__: stf for stf in stf_classes}
STF_CLASS_NAMES = tuple(stf_name_to_class.keys())

source_name_to_class = {source.__name__: source for source in source_classes}
SOURCE_CLASS_NAMES = tuple(source_name_to_class.keys())


def attr_as_list(attributes: Dict) -> Dict:
    
    for key, val in attributes.items():
        if isinstance(val, ndarray):
            attributes[key] = val.tolist()
    
    return attributes


def convert_attributes(attributes: Dict) -> Dict:

    new_attr = {}
    for key, val in attributes.items():
        if key[-2::] == '__':   # for cached arguments
            key = key[0:-2]

        if isinstance(val, list):
            val = array(val)
        
        new_attr[key] = val
    
    return new_attr


class CommunicationTarget(BaseModel):
    lat: float = 0.
    lon: float = 0.
    north_shift: float = 0.
    east_shift: float = 0.
    depth: float = 0.
    elevation: float = 0.
    store_id: Union[str, None]
    sample_rate: Union[float, None]
    azimuth: Union[float, None]
    dip: Union[float, None]
    tmin: Union[float, None]
    tmax: Union[float, None]
    codes: Tuple[str, ...] = ('', 'STA', '', 'Z')
    interpolation: Literal['nearest_neighbor', 'multilinear']
    quantity: Union[Literal[
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
        'vertical_tilt'], None]

    @classmethod
    def from_pyrocko(cls, target: PyrockoTarget) -> Self:
        attributes = target.__dict__
        attributes.pop('_latlon')
        attributes.pop('filter')
        return cls(**attributes)

    def to_pyrocko(self) -> PyrockoTarget:
        return PyrockoTarget(**self.__dict__)


class CommunicationSource(BaseModel):

    source_class_name: Literal[SOURCE_CLASS_NAMES]
    source_attributes: Dict[str, Union[float, int, str, bool, None, List]]

    stf_class_name: Union[Literal[STF_CLASS_NAMES], None]
    stf_attributes: Union[Dict[str, float], None]

    @classmethod
    def from_pyrocko(cls, source: PyrockoSource) -> Self:
        source_attributes = attr_as_list(source.__dict__)
        source_attributes.pop('_latlon')
        source_attributes.pop('_interpolators', None)

        stf = source_attributes.pop('stf', None)
        if stf:
            stf_attributes = stf.__dict__
            stf_class_name = stf.__class__.__name__
        else:
            stf_attributes = stf_class_name = None

        kwargs = {
            "source_class_name": source.__class__.__name__,
            "source_attributes": source_attributes,
            "stf_attributes": stf_attributes,
            "stf_class_name": stf_class_name,
            }

        return cls(**kwargs)

    def to_pyrocko(self) -> PyrockoSource:
        source_attributes = convert_attributes(self.source_attributes)

        if self.stf_class_name is not None:
            stf = stf_name_to_class[self.stf_class_name](**self.stf_attributes)
        else:
            stf = None

        return source_name_to_class[self.source_class_name](
            stf=stf, **source_attributes)


class GFRequest(BaseModel):
    uid: UUID = Field(default_factory=uuid4)

    sources: list[CommunicationSource]
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


@app.post("/request", response_model=GFResponse)
async def request(request: GFRequest):
    pyrocko_request = request.to_pyrocko()
    pyrocko_response = await asyncio.to_thread(LocalEngine.process, pyrocko_request)
    return GFResponse.from_pyrocko(pyrocko_response)
