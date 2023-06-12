import numpy as np
import pytest
from libecalc.core.models.compressor.train.fluid import FluidStream
from libecalc.core.models.compressor.train.single_speed_compressor_train_common_shaft import (
    SingleSpeedCompressorTrainCommonShaft,
    calculate_single_speed_compressor_stage_given_target_discharge_pressure,
)
from libecalc.core.models.compressor.train.stage import CompressorTrainStage
from libecalc.core.models.results.compressor import (
    CompressorTrainCommonShaftFailureStatus,
)
from libecalc.dto.types import ChartAreaFlag, FixedSpeedPressureControl


@pytest.fixture
def single_speed_compressor_train_common_shaft_downstream_choking(
    single_speed_compressor_train,
) -> SingleSpeedCompressorTrainCommonShaft:
    return SingleSpeedCompressorTrainCommonShaft(
        data_transfer_object=single_speed_compressor_train,
    )


@pytest.fixture
def single_speed_compressor_train_common_shaft_downstream_choking_with_maximum_discharge_pressure(
    single_speed_compressor_train,
) -> SingleSpeedCompressorTrainCommonShaft:
    single_speed_compressor_train.maximum_discharge_pressure = 350.0
    return SingleSpeedCompressorTrainCommonShaft(
        data_transfer_object=single_speed_compressor_train,
    )


@pytest.fixture
def single_speed_compressor_train_common_shaft_upstream_choking(
    single_speed_compressor_train,
) -> SingleSpeedCompressorTrainCommonShaft:
    single_speed_compressor_train.pressure_control = FixedSpeedPressureControl.UPSTREAM_CHOKE
    return SingleSpeedCompressorTrainCommonShaft(
        data_transfer_object=single_speed_compressor_train,
    )


@pytest.fixture
def single_speed_compressor_train_common_shaft_common_asv(
    single_speed_compressor_train,
) -> SingleSpeedCompressorTrainCommonShaft:
    single_speed_compressor_train.pressure_control = FixedSpeedPressureControl.COMMON_ASV
    return SingleSpeedCompressorTrainCommonShaft(
        data_transfer_object=single_speed_compressor_train,
    )


@pytest.fixture
def single_speed_compressor_train_common_shaft_asv_rate_control(
    single_speed_compressor_train,
) -> SingleSpeedCompressorTrainCommonShaft:
    single_speed_compressor_train.pressure_control = FixedSpeedPressureControl.INDIVIDUAL_ASV_RATE
    return SingleSpeedCompressorTrainCommonShaft(
        data_transfer_object=single_speed_compressor_train,
    )


@pytest.fixture
def single_speed_compressor_train_common_shaft_asv_pressure_control(
    single_speed_compressor_train,
) -> SingleSpeedCompressorTrainCommonShaft:
    single_speed_compressor_train.pressure_control = FixedSpeedPressureControl.INDIVIDUAL_ASV_PRESSURE
    single_speed_compressor_train.stages[1].compressor_chart.rate_actual_m3_hour = [
        x / 2 for x in single_speed_compressor_train.stages[1].compressor_chart.rate_actual_m3_hour
    ]
    return SingleSpeedCompressorTrainCommonShaft(
        data_transfer_object=single_speed_compressor_train,
    )


class TestSingleSpeedCompressorTrainCommonShaft:
    def test_evaluate_rate_ps_pd_downstream_choke_pressure_control(
        self, single_speed_compressor_train_common_shaft_downstream_choking
    ):
        target_discharge_pressures = np.asarray([300.0, 310.0, 300.0, 300.0])
        suction_pressures = 4 * [80.0]
        result = single_speed_compressor_train_common_shaft_downstream_choking.evaluate_rate_ps_pd(
            rate=np.asarray([5800000.0, 5800000.0, 1000.0, 8189000.0]),
            suction_pressure=np.asarray(suction_pressures),
            discharge_pressure=target_discharge_pressures,
        )
        np.testing.assert_almost_equal(
            result.outlet_stream.pressure,
            [300.0, 304.9383594594694, 300.0, 216.26124954299556],
            decimal=3,
        )
        assert list(result.outlet_stream.pressure_before_choking) == pytest.approx(
            [304.9384, 304.9384, 367.532, 216.2612]
        )
        assert result.inlet_stream.pressure == pytest.approx(suction_pressures)
        assert result.power == pytest.approx([14.54498, 14.54498, 16.05248, 14.6864])

        assert result.failure_status == [
            None,
            CompressorTrainCommonShaftFailureStatus.TARGET_DISCHARGE_PRESSURE_TOO_HIGH,
            None,
            CompressorTrainCommonShaftFailureStatus.ABOVE_MAXIMUM_FLOW_RATE,
        ]
        assert result.is_valid == [True, False, True, False]

    def test_adjust_energy_constant_mw(
        self,
        single_speed_compressor_train_common_shaft_downstream_choking,
    ):
        target_discharge_pressures = np.asarray([300.0, 310.0, 300.0, 300.0])
        suction_pressures = 4 * [80.0]
        energy_usage_adjustment_constant = 10  # MW

        result_comparison = single_speed_compressor_train_common_shaft_downstream_choking.evaluate_rate_ps_pd(
            rate=np.asarray([5800000.0, 5800000.0, 1000.0, 8189000.0]),
            suction_pressure=np.asarray(suction_pressures),
            discharge_pressure=target_discharge_pressures,
        )

        single_speed_compressor_train_common_shaft_downstream_choking.data_transfer_object.energy_usage_adjustment_constant = (
            energy_usage_adjustment_constant
        )
        result = single_speed_compressor_train_common_shaft_downstream_choking.evaluate_rate_ps_pd(
            rate=np.asarray([5800000.0, 5800000.0, 1000.0, 8189000.0]),
            suction_pressure=np.asarray(suction_pressures),
            discharge_pressure=target_discharge_pressures,
        )

        np.testing.assert_allclose(
            np.asarray(result_comparison.energy_usage) + energy_usage_adjustment_constant, result.energy_usage
        )

    def test_evaluate_rate_ps_pd_downstream_choke_pressure_control_and_maximum_discharge_pressure(
        self, single_speed_compressor_train_common_shaft_downstream_choking_with_maximum_discharge_pressure
    ):
        # In the previous test, we see that the third point (index=2) have a floating discharge pressure 367.5
        # Now, the maximum discharge pressure is set to 350.0, thus for this point, the discharge pressure shold be ~350
        # And the suction pressure and other relevant attributes in the result should have been changed accordingly
        target_discharge_pressures = np.asarray([300.0, 310.0, 300.0, 300.0])
        suction_pressures = 4 * [80.0]
        result = single_speed_compressor_train_common_shaft_downstream_choking_with_maximum_discharge_pressure.evaluate_rate_ps_pd(
            rate=np.asarray([5800000.0, 5800000.0, 1000.0, 8189000.0]),
            suction_pressure=np.asarray(suction_pressures),
            discharge_pressure=target_discharge_pressures,
        )
        np.testing.assert_almost_equal(
            result.outlet_stream.pressure,
            [300.0, 304.9383594594694, 300.0, 216.26124954299556],
            decimal=3,
        )
        np.testing.assert_almost_equal(
            result.outlet_stream.pressure_before_choking,
            [304.93835945946944, 304.93835945946944, 350.0, 216.26124954299556],
            decimal=3,
        )

        np.testing.assert_almost_equal(result.inlet_stream.pressure, [80.0, 80.0, 75.8132, 80.0], decimal=5)
        np.testing.assert_almost_equal(
            result.power,
            [14.544982226011612, 14.544982226011612, 15.185817372522788, 14.686402097735332],
            decimal=3,
        )

        assert result.failure_status == [
            None,
            CompressorTrainCommonShaftFailureStatus.TARGET_DISCHARGE_PRESSURE_TOO_HIGH,
            None,
            CompressorTrainCommonShaftFailureStatus.ABOVE_MAXIMUM_FLOW_RATE,
        ]
        assert result.is_valid == [True, False, True, False]

    @pytest.mark.slow
    def test_evaluate_rate_ps_pd_upstream_choke_pressure_control(
        self, single_speed_compressor_train_common_shaft_upstream_choking
    ):
        target_suction_pressures = np.asarray(5 * [80.0])
        suction_pressures_after_upstream_choking = np.asarray([79.34775, 80.67131, 64.52168, 85.95488, 49.11668])
        result = single_speed_compressor_train_common_shaft_upstream_choking.evaluate_rate_ps_pd(
            rate=np.asarray([5800000.0, 5800000.0, 1000.0, 8000000.0, 5800000.0]),
            suction_pressure=target_suction_pressures,
            discharge_pressure=np.asarray([300.0, 310.0, 300.0, 250.0, 100.0]),
        )
        np.testing.assert_almost_equal(
            suction_pressures_after_upstream_choking, result.inlet_stream.pressure, decimal=1
        )
        np.testing.assert_almost_equal(
            result.inlet_stream.pressure_before_choking,
            [80, 80.67130816793885, 80, 85.95489987691745, 80],
            decimal=1,
        )

        assert result.failure_status == [
            None,
            CompressorTrainCommonShaftFailureStatus.TARGET_DISCHARGE_PRESSURE_TOO_HIGH,
            None,
            CompressorTrainCommonShaftFailureStatus.ABOVE_MAXIMUM_FLOW_RATE,
            CompressorTrainCommonShaftFailureStatus.ABOVE_MAXIMUM_FLOW_RATE,
        ]
        assert result.is_valid == [True, False, True, False, False]

    def test_evaluate_rate_ps_pd_asv_rate_control(self, single_speed_compressor_train_common_shaft_asv_rate_control):
        target_discharge_pressures = np.asarray([100, 300.0, 310.0, 300.0, 250.0])
        result = single_speed_compressor_train_common_shaft_asv_rate_control.evaluate_rate_ps_pd(
            rate=np.asarray([5800000.0, 5800000.0, 5800000.0, 1000.0, 8000000.0]),
            suction_pressure=np.asarray(5 * [80.0]),
            discharge_pressure=target_discharge_pressures,
        )
        np.testing.assert_almost_equal(
            result.outlet_stream.pressure,
            [166.95, 300.00, 304.93, 300.00, 219.71],
            decimal=2,
        )
        np.testing.assert_almost_equal(
            result.outlet_stream.pressure_before_choking,
            [166.95, 300.00, 304.93, 300.00, 219.71],
            decimal=2,
        )

        assert result.failure_status == [
            CompressorTrainCommonShaftFailureStatus.TARGET_DISCHARGE_PRESSURE_TOO_LOW,
            None,
            CompressorTrainCommonShaftFailureStatus.TARGET_DISCHARGE_PRESSURE_TOO_HIGH,
            None,
            CompressorTrainCommonShaftFailureStatus.ABOVE_MAXIMUM_FLOW_RATE,
        ]
        assert result.is_valid == [False, True, False, True, False]

    def test_evaluate_rate_ps_pd_asv_pressure_control(
        self, single_speed_compressor_train_common_shaft_asv_pressure_control
    ):
        target_discharge_pressures = np.asarray([300.0, 310.0, 300.0, 250.0, 200.0])
        result = single_speed_compressor_train_common_shaft_asv_pressure_control.evaluate_rate_ps_pd(
            rate=np.asarray([6800000.0, 6200000.0, 7000000.0, 8000000.0, 7000000.0]),
            suction_pressure=np.asarray([100, 100, 100, 110, 110], dtype=float),
            discharge_pressure=target_discharge_pressures,
        )

        np.testing.assert_almost_equal(
            result.outlet_stream.pressure,
            [300.00, 310.00, 292.67, 240.38, 231.92],
            decimal=2,
        )
        assert result.failure_status == [
            None,
            None,
            CompressorTrainCommonShaftFailureStatus.TARGET_DISCHARGE_PRESSURE_TOO_HIGH,
            CompressorTrainCommonShaftFailureStatus.ABOVE_MAXIMUM_FLOW_RATE,
            CompressorTrainCommonShaftFailureStatus.TARGET_DISCHARGE_PRESSURE_TOO_LOW,
        ]
        assert result.is_valid == [True, True, False, False, False]

    def test_evaluate_rate_ps_pd_common_asv(self, single_speed_compressor_train_common_shaft_common_asv):
        target_discharge_pressures = np.asarray([200.0, 270.0, 350.0, 250.0])
        result = single_speed_compressor_train_common_shaft_common_asv.evaluate_rate_ps_pd(
            rate=np.asarray([5800000.0, 5800000.0, 1000.0, 8000000.0]),
            suction_pressure=np.asarray(4 * [80.0]),
            discharge_pressure=target_discharge_pressures,
        )

        np.testing.assert_almost_equal(
            result.outlet_stream.pressure,
            [238.25, 270.0, 277.23, 219.7185],
            decimal=2,
        )

        assert result.failure_status == [
            CompressorTrainCommonShaftFailureStatus.TARGET_DISCHARGE_PRESSURE_TOO_LOW,
            None,
            CompressorTrainCommonShaftFailureStatus.TARGET_DISCHARGE_PRESSURE_TOO_HIGH,
            CompressorTrainCommonShaftFailureStatus.ABOVE_MAXIMUM_FLOW_RATE,
        ]
        assert result.is_valid == [False, True, False, False]


class TestCalculateSingleSpeedCompressorStage:
    def test_rate_below_minimum_chart_rate(self, single_speed_compressor_train_stage, medium_fluid):
        mass_rate_kg_per_hour = 85500.0
        inlet_pressure_train_bara = 80.0

        inlet_stream = FluidStream(medium_fluid).get_fluid_streams(
            pressure_bara=np.array([inlet_pressure_train_bara]),
            temperature_kelvin=np.array([single_speed_compressor_train_stage.inlet_temperature_kelvin]),
        )[0]

        # stage.mass_rate_kg_per_hour = mass_rate_kg_per_hour
        result = single_speed_compressor_train_stage.evaluate(
            inlet_stream_stage=inlet_stream,
            mass_rate_kg_per_hour=mass_rate_kg_per_hour,
        )
        # Stability check
        assert result.inlet_actual_rate_m3_per_hour == pytest.approx(1148.7960837804026)
        assert result.inlet_actual_rate_asv_corrected_m3_per_hour == 1735.0
        assert result.chart_area_flag == ChartAreaFlag.BELOW_MINIMUM_FLOW_RATE
        assert result.power_megawatt == pytest.approx(4.832668696214711)
        assert result.outlet_stream.pressure_bara == pytest.approx(173.36439708753804)
        assert result.outlet_stream.temperature_kelvin == pytest.approx(374.72572136518033)
        assert result.outlet_stream.density_kg_per_m3 == pytest.approx(117.12528630719012)

    def test_rate_within_chart_curve_range(self, single_speed_compressor_train_stage, medium_fluid):
        mass_rate_kg_per_hour = 200000.0
        # stage.mass_rate_kg_per_hour = mass_rate_kg_per_hour
        inlet_pressure_train_bara = 80.0

        inlet_stream = FluidStream(medium_fluid).get_fluid_streams(
            pressure_bara=np.array([inlet_pressure_train_bara]),
            temperature_kelvin=np.array([single_speed_compressor_train_stage.inlet_temperature_kelvin]),
        )[0]

        result = single_speed_compressor_train_stage.evaluate(
            inlet_stream_stage=inlet_stream,
            mass_rate_kg_per_hour=mass_rate_kg_per_hour,
        )
        # Stability check
        assert result.inlet_actual_rate_m3_per_hour == pytest.approx(2687.242301240708)
        assert result.inlet_actual_rate_asv_corrected_m3_per_hour == pytest.approx(2687.242301240708)
        assert result.chart_area_flag == ChartAreaFlag.INTERNAL_POINT
        assert result.power_megawatt == pytest.approx(5.407217436940095)
        assert result.outlet_stream.pressure_bara == pytest.approx(140.10731313862553)
        assert result.outlet_stream.temperature_kelvin == pytest.approx(355.69497851991036)
        assert result.outlet_stream.density_kg_per_m3 == pytest.approx(103.14261057405868)


def test_calculate_single_speed_train(single_speed_compressor_train):
    mass_rate_kg_per_hour = 200000.0
    inlet_pressure_train_bara = 80.0
    inlet_temperature_kelvin = 303.15

    compressor_train = SingleSpeedCompressorTrainCommonShaft(
        data_transfer_object=single_speed_compressor_train,
    )

    inlet_streams = compressor_train.fluid.get_fluid_streams(
        pressure_bara=np.asarray([inlet_pressure_train_bara]),
        temperature_kelvin=np.asarray([inlet_temperature_kelvin]),
    )
    result = compressor_train.calculate_single_speed_train(
        train_inlet_stream=inlet_streams[0],
        mass_rate_kg_per_hour_per_stage=[mass_rate_kg_per_hour] * compressor_train.number_of_compressor_stages,
    )

    # Stability tests
    assert result.power_megawatt == pytest.approx(14.514685163666886)
    assert result.discharge_pressure == pytest.approx(304.09487589413385)
    assert result.stage_results[0].outlet_stream.pressure_bara == pytest.approx(140.10731313862553)
    assert result.stage_results[1].inlet_stream.pressure_bara == pytest.approx(140.1073131386256)
    assert result.stage_results[0].chart_area_flag == ChartAreaFlag.INTERNAL_POINT
    assert result.stage_results[1].chart_area_flag == ChartAreaFlag.BELOW_MINIMUM_FLOW_RATE


def test_calculate_single_speed_train_zero_mass_rate(medium_fluid, single_speed_compressor_train):
    """We want to get a result object when rate is zero regardless of invalid/zero pressures. To ensure
    this we set pressure -> 1 when both rate and pressure is zero. This may happen when pressure is a function
    of rate.
    """
    compressor_train = SingleSpeedCompressorTrainCommonShaft(
        data_transfer_object=single_speed_compressor_train,
    )
    result = compressor_train.evaluate_rate_ps_pd(
        rate=np.array([0, 1, 1]), suction_pressure=np.array([0, 1, 1]), discharge_pressure=np.array([0, 2, 2])
    )

    # Ensuring that first stage returns zero energy usage and no failure.
    assert result.is_valid == [True, True, True]
    assert result.energy_usage == pytest.approx([0.0, 0.14898322782599177, 0.14898322782599177])

    assert result.mass_rate_kg_per_hr[0] == 0
    assert result.power[0] == 0
    assert np.isnan(result.inlet_stream.pressure[0])
    assert np.isnan(result.outlet_stream.pressure[0])


def test_calculate_single_speed_train_zero_pressure_non_zero_rate(medium_fluid, single_speed_compressor_train):
    """We would like to run the model regardless of some missing pressures. We will skip calculating these steps
    by setting rate to zero.
    """
    compressor_train = SingleSpeedCompressorTrainCommonShaft(
        data_transfer_object=single_speed_compressor_train,
    )

    # These inputs should all result in compressor not running. Zero pressure should return failure_status about invalid
    # pressure input. Zero rate and valid pressure input should just result in compressor not running.
    result = compressor_train.evaluate_rate_ps_pd(
        rate=np.array([0, 0, 1, 1]), suction_pressure=np.array([0, 1, 1, 0]), discharge_pressure=np.array([0, 1, 0, 1])
    )

    # Results with zero rate should be valid
    assert result.is_valid == [True, True, False, False]
    assert result.failure_status == [
        None,
        None,
        CompressorTrainCommonShaftFailureStatus.INVALID_DISCHARGE_PRESSURE_INPUT,
        CompressorTrainCommonShaftFailureStatus.INVALID_SUCTION_PRESSURE_INPUT,
    ]
    assert all([flag == ChartAreaFlag.NOT_CALCULATED for flag in result.stage_results[0].chart_area_flags])
    np.testing.assert_allclose(result.energy_usage, np.array([0, 0, 0, 0]))

    np.testing.assert_allclose(result.mass_rate_kg_per_hr, 0)
    np.testing.assert_allclose(result.energy_usage, 0)
    np.testing.assert_allclose(result.power, 0)


def test_calculate_single_speed_compressor_stage_given_target_discharge_pressure(
    single_speed_compressor_train_common_shaft_downstream_choking,
):
    inlet_pressure_train_bara = 80.0
    mass_rate_kg_per_hour = 200000.0
    stage: CompressorTrainStage = single_speed_compressor_train_common_shaft_downstream_choking.stages[0]
    inlet_stream_stage = single_speed_compressor_train_common_shaft_downstream_choking.fluid.get_fluid_streams(
        pressure_bara=np.asarray([inlet_pressure_train_bara]),
        temperature_kelvin=np.asarray([stage.inlet_temperature_kelvin]),
    )[0]
    target_outlet_pressure = 130

    result, failure_status = calculate_single_speed_compressor_stage_given_target_discharge_pressure(
        inlet_stream_stage=inlet_stream_stage,
        outlet_pressure_stage_bara=target_outlet_pressure,
        mass_rate_kg_per_hour=mass_rate_kg_per_hour,
        stage=stage,
    )
    np.testing.assert_allclose(result.outlet_stream.pressure_bara, target_outlet_pressure, rtol=0.01)


def test_single_speed_compressor_train_vs_unisim_methane(single_speed_compressor_train_unisim_methane):
    compressor_train = single_speed_compressor_train_unisim_methane

    result = compressor_train.evaluate_rate_ps_pd(
        rate=np.asarray([5305771.971, 3890899.445, 6013208.233, 5305771.971, 5305771.971]),
        suction_pressure=np.asarray([40, 40, 40, 35, 60]),
        discharge_pressure=np.asarray([200, 200, 200, 200, 200]),  # Dummy values.
    )

    expected_power = np.array([7.577819961, 6.440134787, 7.728668854, 6.687897402, 9.620088576])

    # Note: Given data was meter liquid column. We need to compare against kJ/kg
    # expected_head = Unit.POLYTROPIC_HEAD_METER_LIQUID_COLUMN.to(Unit.POLYTROPIC_HEAD_KILO_JOULE_PER_KG)(
    #     np.array([16129.34382, 15530.2335, 15595.82912, 17449.38821, 8944.004374])
    # )
    expected_efficiency = np.array([0.723876159, 0.7469255823, 0.7254063622, 0.7449794342, 0.7090675589])  # [-]
    expected_act_gas_rate = np.array([5305.395, 3890.623, 6012.781, 6115.773, 3422.705])  # [m3/h]
    expected_inlet_temperature = np.array([20, 20, 20, 20, 20]) + 273.15  # [K]
    expected_inlet_mass_rate = np.array([150000, 110000, 170000, 150000, 150000])  # [kg/h]
    expected_inlet_mass_density = np.array([28.27311, 28.27311, 28.27311, 24.52675, 43.82499])  # [kg/m3]
    expected_inlet_z = np.array([0.931221, 0.931221, 0.931221, 0.939278, 0.901147065266633])  # [-]
    # expected_inlet_kappa = np.array([1.44187, 1.44187, 1.44187, 1.42216, 1.52606])  # [-]
    # expected_outlet_mass_density = np.array([48.40811, 50.49946, 44.97294, 38.62820, 72.89670])  # [kg/m3]
    # expected_outlet_kappa = np.array([1.39929, 1.38925, 1.40124, 1.38569, 1.42486])  # [-]
    expected_outlet_temperature = np.array([103.43398, 115.16061, 95.05306341, 93.22515, 122.12128]) + 273.15  # [K]
    expected_outlet_pressure = np.array([91.33181, 98.96722, 82.60081, 70.74829, 146.64472])  # [bar]

    np.testing.assert_allclose(result.power, expected_power, rtol=0.05)
    np.testing.assert_allclose(result.inlet_stream.actual_rate_before_asv_m3_per_hr, expected_act_gas_rate, rtol=0.05)
    np.testing.assert_allclose(result.inlet_stream.temperature_kelvin, expected_inlet_temperature, rtol=0.05)
    np.testing.assert_allclose(result.mass_rate_kg_per_hr, expected_inlet_mass_rate, rtol=0.05)
    np.testing.assert_allclose(result.inlet_stream.density_kg_per_m3, expected_inlet_mass_density, rtol=0.05)
    np.testing.assert_allclose(result.inlet_stream.z, expected_inlet_z, rtol=0.05)
    # np.testing.assert_allclose(result.inlet_kappa, expected_inlet_kappa, rtol=0.05)
    # np.testing.assert_allclose(result.outlet_density_kg_per_m3, expected_outlet_mass_density, rtol=0.05)
    # np.testing.assert_allclose(result.outlet_kappa, expected_outlet_kappa, rtol=0.16)
    np.testing.assert_allclose(result.outlet_stream.temperature_kelvin, expected_outlet_temperature, rtol=0.05)
    np.testing.assert_allclose(result.outlet_stream.pressure, expected_outlet_pressure, rtol=0.05)

    # np.testing.assert_allclose(result.polytropic_head_kJ_per_kg, expected_head, rtol=0.01)  # Test is failing
    np.testing.assert_allclose(result.stage_results[0].polytropic_efficiency, expected_efficiency, rtol=0.05)
