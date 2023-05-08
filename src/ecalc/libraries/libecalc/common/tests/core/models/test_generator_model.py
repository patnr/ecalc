import numpy as np
import pandas as pd
from libecalc import dto
from libecalc.core.models.generator import GeneratorModelSampled


class TestGeneratorModelSampled:
    def test_evaluate(self):
        df = pd.DataFrame(
            [
                [0, 0],
                [0.1, 50400],
                [5, 50400],
                [10, 76320],
                [15, 99888],
                [20, 123480],
                [21, 129000],
                [21.5, 160080],
                [25, 176640],
                [30, 199800],
            ],
            columns=["power", "fuel"],
        )

        power_values = df["power"].tolist()
        fuel_values = df["fuel"].tolist()

        el2fuel = GeneratorModelSampled(
            data_transfer_object=dto.GeneratorSetSampled(
                data=[power_values, fuel_values],
                headers=["POWER", "FUEL"],
                energy_usage_adjustment_factor=1,
                energy_usage_adjustment_constant=0,
            )
        )

        x_input = np.asarray([-1, 0, 5, 7, 10, 30, 31])
        expected = np.asarray([0, 0, 50400.0, 60768.0, 76320.0, 199800, 199800])
        np.testing.assert_allclose(el2fuel.evaluate(x_input), expected)

    def test_capacity_margin(self):
        # Testing the capacity factor when using sampled genset.
        el2fuel_function = GeneratorModelSampled(
            data_transfer_object=dto.GeneratorSetSampled(
                data=[[1, 2, 3], [1, 2, 3]],
                headers=["FUEL", "POWER"],
                energy_usage_adjustment_factor=1,
                energy_usage_adjustment_constant=0,
            )
        )
        capacity_margin = el2fuel_function.evaluate_power_capacity_margin(np.array([0, 1, 2, 3, 4, 5]))
        np.testing.assert_allclose(capacity_margin, np.asarray([3, 2, 1, 0, -1, -2]))
