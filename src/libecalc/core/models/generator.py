import numpy as np
from numpy.typing import NDArray
from scipy.interpolate import interp1d

from libecalc import dto
from libecalc.common.list.adjustment import transform_linear


class GeneratorModelSampled:
    def __init__(
        self,
        data_transfer_object: dto.GeneratorSetSampled,
    ):
        fuel_values = transform_linear(
            np.array(data_transfer_object.fuel_values),
            constant=data_transfer_object.energy_usage_adjustment_constant,
            factor=data_transfer_object.energy_usage_adjustment_factor,
        )

        self._func = interp1d(
            data_transfer_object.power_values,
            fuel_values.tolist(),
            fill_value=(min(fuel_values), max(fuel_values)),
            bounds_error=False,
        )

    def evaluate(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        """Ensure zero power consumption return zero fuel consumption. I.e. equipment is turned off."""
        return np.where(x > 0, self._func(x), 0.0)

    def evaluate_power_capacity_margin(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        """Calculate the capacity margin on the el2fuel function if using sampled data.
        If using el2fuel factor, there is no margin.

        E.g.
            max sampled power is 50, and you require 40 -> 50 - 40 = 10.
            max sampled power is 50, and you require 60 -> 50 - 60 = -10
        """
        return np.full_like(x, fill_value=self._func.x.max(), dtype=np.float64) - x
