from datetime import datetime

import numpy as np
from libecalc import dto
from libecalc.common.units import Unit
from libecalc.common.utils.rates import TimeSeriesRate
from libecalc.core.models.fuel import FuelModel
from libecalc.dto import VariablesMap
from libecalc.expression import Expression


def test_fuel_model():
    fuel_model = FuelModel(
        {
            datetime(2000, 1, 1): dto.FuelType(
                name="fuel_gas",
                price=Expression.setup_from_expression(10.0),
                emissions=[
                    dto.Emission(
                        name="CO2",
                        factor=Expression.setup_from_expression(1.0),
                        tax=Expression.setup_from_expression(1.0),
                        quota=Expression.setup_from_expression(0.0),
                    )
                ],
            )
        }
    )
    timesteps = [datetime(2000, 1, 1), datetime(2001, 1, 1), datetime(2002, 1, 1)]
    emissions = fuel_model.evaluate_emissions(
        variables_map=VariablesMap(time_vector=timesteps),
        fuel_rate=np.asarray([1, 2, 3]),
    )

    emission_names = [emission.name for emission in emissions]
    emission_result = emissions[emission_names.index("co2")]

    assert emission_result.name == "co2"
    assert emission_result.rate == TimeSeriesRate(
        timesteps=timesteps,
        values=[0.001, 0.002, 0.003],
        unit=Unit.TONS_PER_DAY,
    )
    assert emission_result.tax == TimeSeriesRate(
        timesteps=timesteps,
        values=[1.0, 2.0, 3.0],
        unit=Unit.NORWEGIAN_KRONER_PER_DAY,
    )
    assert emission_result.quota == TimeSeriesRate(
        timesteps=timesteps,
        values=[0.0] * 3,
        unit=Unit.NORWEGIAN_KRONER_PER_DAY,
    )


def test_temporal_fuel_model():
    """Assure that emissions are concatenated correctly when the emission name changes in a temporal model."""
    fuel_model = FuelModel(
        {
            datetime(2000, 1, 1): dto.FuelType(
                name="fuel_gas",
                price=Expression.setup_from_expression(1.0),
                emissions=[
                    dto.Emission(
                        name="CO2",
                        factor=Expression.setup_from_expression(1.0),
                        tax=Expression.setup_from_expression(1.0),
                        quota=Expression.setup_from_expression(1.0),
                    ),
                ],
            ),
            datetime(2001, 1, 1): dto.FuelType(
                name="fuel_gas",
                price=Expression.setup_from_expression(2.0),
                emissions=[
                    dto.Emission(
                        name="CH4",
                        factor=Expression.setup_from_expression(2.0),
                        tax=Expression.setup_from_expression(2.0),
                        quota=Expression.setup_from_expression(2.0),
                    ),
                ],
            ),
        }
    )

    emissions = fuel_model.evaluate_emissions(
        variables_map=VariablesMap(time_vector=[datetime(2000, 1, 1), datetime(2001, 1, 1), datetime(2002, 1, 1)]),
        fuel_rate=np.asarray([1, 2, 3]),
    )

    # We should have both CO2 and CH4 as emissions
    assert len(emissions) == 2

    # And they should cover the whole time index of 3 steps.
    for emission in emissions:
        assert len(emission.rate) == 3
