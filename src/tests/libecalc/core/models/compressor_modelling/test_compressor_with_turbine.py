import numpy as np
import pytest

from libecalc import dto
from libecalc.core.models.compressor.base import CompressorWithTurbineModel


@pytest.fixture()
def compressor_train_variable_speed_multiple_streams_and_pressures_with_turbine_dto(
    variable_speed_compressor_train_two_compressors_one_stream_dto,
    turbine_dto,
) -> dto.CompressorWithTurbine:
    return dto.CompressorWithTurbine(
        compressor_train=variable_speed_compressor_train_two_compressors_one_stream_dto,
        turbine=turbine_dto,
        energy_usage_adjustment_constant=1.0,
        energy_usage_adjustment_factor=1.0,
    )


@pytest.fixture()
def compressor_train_variable_speed_multiple_streams_and_pressures_with_turbine(
    turbine,
    variable_speed_compressor_train_two_compressors_one_stream,
    compressor_train_variable_speed_multiple_streams_and_pressures_with_turbine_dto,
) -> CompressorWithTurbineModel:
    return CompressorWithTurbineModel(
        turbine_model=turbine,
        compressor_energy_function=variable_speed_compressor_train_two_compressors_one_stream,
        data_transfer_object=compressor_train_variable_speed_multiple_streams_and_pressures_with_turbine_dto,
    )


def test_variable_speed_multiple_streams_and_pressures_with_turbine(
    compressor_train_variable_speed_multiple_streams_and_pressures_with_turbine,
):
    result_with_turbine = (
        compressor_train_variable_speed_multiple_streams_and_pressures_with_turbine.evaluate_rate_ps_pd(
            rate=np.asarray([[3000000]]),
            suction_pressure=np.asarray([30]),
            discharge_pressure=np.asarray([100]),
        )
    )

    expected_load = (
        compressor_train_variable_speed_multiple_streams_and_pressures_with_turbine.data_transfer_object.energy_usage_adjustment_factor
        * sum([stage.power[0] for stage in result_with_turbine.stage_results])
        + compressor_train_variable_speed_multiple_streams_and_pressures_with_turbine.data_transfer_object.energy_usage_adjustment_constant
    )
    assert result_with_turbine.turbine_result.load[0] == expected_load
