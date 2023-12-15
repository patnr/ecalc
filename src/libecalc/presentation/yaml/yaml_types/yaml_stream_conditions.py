from typing import Optional

try:
    from pydantic.v1 import Field
except ImportError:
    from pydantic import Field

from libecalc.common.units import Unit
from libecalc.expression.expression import ExpressionType
from libecalc.presentation.yaml.yaml_types import YamlBase


class YamlTimeSeries(YamlBase):
    value: ExpressionType
    unit: Unit


class YamlRate(YamlTimeSeries):
    class Config:
        title = "Rate"

    unit: Unit = Unit.STANDARD_CUBIC_METER_PER_DAY


class YamlPressure(YamlTimeSeries):
    class Config:
        title = "Pressure"

    unit: Unit = Unit.BARA


class YamlTemperature(YamlTimeSeries):
    class Config:
        title = "Temperature"

    unit: Unit = Unit.KELVIN


class YamlDensity(YamlTimeSeries):
    class Config:
        title = "Density"

    unit: Unit = Unit.KG_SM3


class YamlStreamConditions(YamlBase):
    class Config:
        title = "Stream"

    rate: Optional[YamlRate] = Field(
        None,
        title="Rate",
        description="Rate...",
    )
    pressure: Optional[YamlPressure] = Field(
        None,
        title="Pressure",
        description="Pressure..",
    )
    temperature: Optional[YamlTemperature] = Field(
        None,
        title="Temperature",
        description="Temperature...",
    )
    fluid_density: Optional[YamlDensity] = Field(None, title="Fluid density", description="The fluid density...")
    # fluid model
    # At least one should be specified, rate or pressure? temperature, fluid model when multistream? fluid density for pumps?
