from typing import Union

from pydantic import BaseModel

from libecalc.core.models.compressor.base import CompressorModel
from libecalc.core.models.pump import PumpModel


class ConsumerSystemComponent(BaseModel):
    name: str
    facility_model: Union[PumpModel, CompressorModel]

    class Config:
        arbitrary_types_allowed = True
