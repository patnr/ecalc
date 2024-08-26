from __future__ import annotations

from copy import deepcopy
from typing import Any, List, Optional

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, model_validator

from libecalc.common.errors.exceptions import EcalcError, IncompatibleDataError
from libecalc.common.logger import logger
from libecalc.common.utils.rates import Rates
from libecalc.core.utils.array_type import PydanticNDArray
from libecalc.expression import Expression


class ConsumerSystemOperationalSettingExpressions(BaseModel):
    """Each index of a setting is aligned with a consumer. The first consumer has rate self.rates[0], etc.

    cross_overs: Defines what consumer to send exceeding rates to (Warning! index starts at 1!).
        - 0 means no cross-over.
        - 1 means send exceeding rate (above max rate) to the first consumer
        - 2 means send exceeding rate (above max rate) to the second consumer

    E.g. [3, 3, 0]: First and second consumer sends exceeding rate to the thirds consumer. Third consumer does not
        have the ability to send exceeding rates anywhere.

    Note that circular references is not possible.
    """

    rates: List[Expression]
    suction_pressures: List[Expression]
    discharge_pressures: List[Expression]
    cross_overs: Optional[List[int]] = None
    fluid_densities: Optional[List[Expression]] = None

    @property
    def number_of_consumers(self):
        return len(self.rates)

    @model_validator(mode="after")
    def check_list_length(self):
        def _log_error(field: str, field_values: List[Any], n_rates) -> None:
            msg = (
                f"All attributes in a consumer system operational setting must have the same number of elements"
                f"(corresponding to the number of consumers). The number of elements in {field} "
                f"({len(field_values)}) is not equal to the number of elements in rates ({n_rates})."
            )
            logger.error(msg)
            raise EcalcError(title="Invalid system", message=msg)

        rates = self.rates
        suction_pressures = self.suction_pressures
        discharge_pressures = self.discharge_pressures
        cross_overs = self.cross_overs
        n_rates = len(rates)

        if len(suction_pressures) != n_rates:
            _log_error(field="suction_pressures", field_values=suction_pressures, n_rates=n_rates)
        if len(discharge_pressures) != n_rates:
            _log_error(field="discharge_pressures", field_values=discharge_pressures, n_rates=n_rates)
        if cross_overs and len(cross_overs) != n_rates:
            _log_error(field="cross_overs", field_values=cross_overs, n_rates=n_rates)
        return self


class CompressorSystemOperationalSettingExpressions(ConsumerSystemOperationalSettingExpressions): ...


class PumpSystemOperationalSettingExpressions(ConsumerSystemOperationalSettingExpressions):
    fluid_densities: List[Expression]


class ConsumerSystemOperationalSetting(BaseModel):
    """Warning! The methods below are fragile to changes in attribute names and types."""

    rates: List[PydanticNDArray]
    suction_pressures: List[PydanticNDArray]
    discharge_pressures: List[PydanticNDArray]
    cross_overs: Optional[List[int]] = None
    fluid_densities: Optional[List[PydanticNDArray]] = None
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    @model_validator(mode="after")
    def check_list_length(self):
        def _log_error(field: str, field_values: List[Any], n_rates: int) -> None:
            error_message = (
                f"All attributes in a consumer system operational setting must have the same number of elements"
                f"(corresponding to the number of consumers). The number of elements in {field} "
                f"({len(field_values)}) is not equal to the number of elements in rates ({n_rates})."
            )
            logger.error(error_message)
            raise IncompatibleDataError(error_message)

        rates = self.rates
        suction_pressures = self.suction_pressures
        discharge_pressures = self.discharge_pressures
        cross_overs = self.cross_overs
        n_rates = len(rates)

        if len(suction_pressures) != n_rates:
            _log_error(field="suction_pressure", field_values=suction_pressures, n_rates=n_rates)
        if len(discharge_pressures) != n_rates:
            _log_error(field="discharge_pressures", field_values=discharge_pressures, n_rates=n_rates)
        if cross_overs and len(cross_overs) != n_rates:
            _log_error(field="cross_overs", field_values=cross_overs, n_rates=n_rates)

        return self

    def convert_rates_to_stream_day(self, regularity: List[float]) -> ConsumerSystemOperationalSetting:
        """If regularity is specified, interpret the rate in the operational setting
        as calendar day rate and compute the stream day rate. Return operational
        setting object where the rate is stream day.

        rate_stream_day = rate_calendar_day / regularity
        regularity is between 0 and 1 (fraction of "full time")


        Note: Hack because of Config allow_mutation = False - to avoid Pydantic faux immutability
            Refactor so that we do not need to do this at all.
        """
        operational_settings = deepcopy(self)
        stream_day_rates = [
            Rates.to_stream_day(
                calendar_day_rates=calendar_day_rate,
                regularity=regularity,
            )
            for calendar_day_rate in operational_settings.rates
        ]
        operational_settings.__dict__["rates"] = stream_day_rates  # Avoid Pydantic faux immutability

        return operational_settings

    def set_rates_after_cross_over(
        self,
        rates_after_cross_over: List[NDArray[np.float64]],
    ) -> ConsumerSystemOperationalSetting:
        """Note: Hack because of Config allow_mutation = False - to avoid Pydantic faux immutability
        Refactor so that we do not need to do this at all.
        """
        data = deepcopy(self.__dict__)
        data.update({"rates": rates_after_cross_over})
        return self.__class__(**data)


class CompressorSystemOperationalSetting(ConsumerSystemOperationalSetting): ...


class PumpSystemOperationalSetting(ConsumerSystemOperationalSetting):
    fluid_densities: List[PydanticNDArray]
