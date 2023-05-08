import numpy as np
from libecalc import dto
from scipy.interpolate import interp1d


class GeneratorModelSampled:
    def __init__(
        self,
        data_transfer_object: dto.GeneratorSetSampled,
    ):
        self._func = interp1d(
            data_transfer_object.power_values,
            data_transfer_object.fuel_values,
            fill_value=(min(data_transfer_object.fuel_values), max(data_transfer_object.fuel_values)),
            bounds_error=False,
        )

    def evaluate(self, x: np.ndarray) -> np.ndarray:
        """Ensure zero power consumption return zero fuel consumption. I.e. equipment is turned off."""
        return np.where(x > 0, self._func(x), 0.0)

    def evaluate_power_capacity_margin(self, x: np.ndarray) -> np.ndarray:
        """Calculate the capacity margin on the el2fuel function if using sampled data.
        If using el2fuel factor, there is no margin.

        E.g.
            max sampled power is 50, and you require 40 -> 50 - 40 = 10.
            max sampled power is 50, and you require 60 -> 50 - 60 = -10
        """
        return self._func.x.max() - x
