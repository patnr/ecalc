from datetime import datetime

import pandas as pd
import pytest
from libecalc import dto
from libecalc.common.units import Unit
from libecalc.common.utils.rates import RateType
from libecalc.fixtures.cases.ltp_export.installation_setup import (
    expected_boiler_fuel_consumption,
    expected_ch4_from_diesel,
    expected_co2_from_boiler,
    expected_co2_from_diesel,
    expected_co2_from_fuel,
    expected_co2_from_heater,
    expected_diesel_consumption,
    expected_fuel_consumption,
    expected_gas_turbine_compressor_el_consumption,
    expected_gas_turbine_el_generated,
    expected_heater_fuel_consumption,
    expected_nmvoc_from_diesel,
    expected_nox_from_diesel,
    expected_offshore_wind_el_consumption,
    expected_pfs_el_consumption,
    installation_boiler_heater_dto,
    installation_compressor_dto,
    installation_diesel_fixed_dto,
    installation_diesel_mobile_dto,
    installation_direct_consumer_dto,
    installation_offshore_wind_dto,
    no_el_consumption,
    simple_direct_el_consumer,
)
from libecalc.fixtures.cases.ltp_export.loading_storage_ltp_yaml import (
    ltp_oil_loaded_yaml_factory,
)
from libecalc.fixtures.cases.ltp_export.utilities import (
    get_consumption,
    get_consumption_asset_result,
    get_sum_ltp_column,
)
from libecalc.fixtures.cases.venting_emitters.venting_emitter_yaml import (
    venting_emitter_yaml_factory,
)
from libecalc.presentation.yaml.validation_errors import DtoValidationError
from libecalc.presentation.yaml.yaml_keywords import EcalcYamlKeywords

time_vector_installation = [
    datetime(2027, 1, 1),
    datetime(2027, 4, 10),
    datetime(2028, 1, 1),
    datetime(2028, 4, 10),
    datetime(2029, 1, 1),
]

time_vector_yearly = pd.date_range(datetime(2027, 1, 1), datetime(2029, 1, 1), freq="YS").to_pydatetime().tolist()


def test_emissions_diesel_fixed_and_mobile():
    """Test reporting of CH4 from diesel in LTP."""
    installation_fixed = installation_diesel_fixed_dto()
    installation_mobile = installation_diesel_mobile_dto()

    asset = dto.Asset(
        name="multiple_installations_asset",
        installations=[
            installation_fixed,
            installation_mobile,
        ],
    )

    variables = dto.VariablesMap(time_vector=time_vector_installation, variables={"RATE": [1, 1, 1, 1, 1, 1]})

    ltp_result = get_consumption(model=asset, variables=variables, time_vector=time_vector_yearly)

    co2_from_diesel_fixed = get_sum_ltp_column(ltp_result, installation_nr=0, ltp_column_nr=1)
    co2_from_diesel_mobile = get_sum_ltp_column(ltp_result, installation_nr=1, ltp_column_nr=1)

    nox_from_diesel_fixed = get_sum_ltp_column(ltp_result, installation_nr=0, ltp_column_nr=2)
    nox_from_diesel_mobile = get_sum_ltp_column(ltp_result, installation_nr=1, ltp_column_nr=2)

    nmvoc_from_diesel_fixed = get_sum_ltp_column(ltp_result, installation_nr=0, ltp_column_nr=3)
    nmvoc_from_diesel_mobile = get_sum_ltp_column(ltp_result, installation_nr=1, ltp_column_nr=3)

    ch4_from_diesel_fixed = get_sum_ltp_column(ltp_result, installation_nr=0, ltp_column_nr=4)
    ch4_from_diesel_mobile = get_sum_ltp_column(ltp_result, installation_nr=1, ltp_column_nr=4)

    assert co2_from_diesel_fixed == expected_co2_from_diesel()
    assert co2_from_diesel_mobile == expected_co2_from_diesel()
    assert nox_from_diesel_fixed == expected_nox_from_diesel()
    assert nox_from_diesel_mobile == expected_nox_from_diesel()
    assert nmvoc_from_diesel_fixed == expected_nmvoc_from_diesel()
    assert nmvoc_from_diesel_mobile == expected_nmvoc_from_diesel()
    assert ch4_from_diesel_fixed == expected_ch4_from_diesel()
    assert ch4_from_diesel_mobile == expected_ch4_from_diesel()


def test_temporal_models_detailed():
    """Test various queries for LTP reporting. Purpose: ensure that variations in temporal models are captured.

    Detailed temporal models (variations within one year) for:
    - Fuel type
    - Generator set user defined category
    - Generator set model
    """
    variables = dto.VariablesMap(time_vector=time_vector_installation, variables={"RATE": [1, 1, 1, 1, 1, 1]})

    ltp_result = get_consumption(
        model=installation_direct_consumer_dto(), variables=variables, time_vector=time_vector_yearly
    )

    turbine_fuel_consumption = get_sum_ltp_column(ltp_result, installation_nr=0, ltp_column_nr=0)
    engine_diesel_consumption = get_sum_ltp_column(ltp_result, installation_nr=0, ltp_column_nr=1)

    gas_turbine_el_generated = get_sum_ltp_column(ltp_result, installation_nr=0, ltp_column_nr=4)
    pfs_el_consumption = get_sum_ltp_column(ltp_result, installation_nr=0, ltp_column_nr=5)

    co2_from_fuel = get_sum_ltp_column(ltp_result, installation_nr=0, ltp_column_nr=2)
    co2_from_diesel = get_sum_ltp_column(ltp_result, installation_nr=0, ltp_column_nr=3)

    # FuelQuery: Check that turbine fuel consumption is included,
    # even if the temporal model starts with diesel every year
    assert turbine_fuel_consumption != 0

    # FuelQuery: Check that turbine fuel consumption is correct
    assert turbine_fuel_consumption == expected_fuel_consumption()

    # FuelQuery: Check that turbine fuel gas is not categorized as diesel,
    # even if the temporal model starts with diesel every year
    assert engine_diesel_consumption != expected_diesel_consumption() + expected_fuel_consumption()

    # FuelQuery: Check that diesel consumption is correct
    assert engine_diesel_consumption == pytest.approx(expected_diesel_consumption(), 0.00001)

    # ElectricityGeneratedQuery: Check that turbine power generation is correct.
    assert gas_turbine_el_generated == pytest.approx(expected_gas_turbine_el_generated(), 0.00001)

    # ElectricityGeneratedQuery: Check that power from shore el consumption is correct.
    assert pfs_el_consumption == pytest.approx(expected_pfs_el_consumption(), 0.00001)

    # EmissionQuery. Check that co2 from fuel is correct.
    assert co2_from_fuel == expected_co2_from_fuel()

    # EmissionQuery: Emissions. Check that co2 from diesel is correct.
    assert co2_from_diesel == expected_co2_from_diesel()


def test_temporal_models_offshore_wind():
    """Test ElConsumerPowerConsumptionQuery for calculating offshore wind el-consumption, LTP.

    Detailed temporal models (variations within one year) for:
    - El-consumer user defined category
    - El-consumer energy usage model
    """
    variables = dto.VariablesMap(time_vector=time_vector_installation, variables={"RATE": [1, 1, 1, 1, 1, 1]})

    ltp_result = get_consumption(
        model=installation_offshore_wind_dto(), variables=variables, time_vector=time_vector_yearly
    )

    offshore_wind_el_consumption = get_sum_ltp_column(ltp_result, installation_nr=0, ltp_column_nr=3)

    # ElConsumerPowerConsumptionQuery: Check that offshore wind el-consumption is correct.
    assert offshore_wind_el_consumption == expected_offshore_wind_el_consumption()


def test_temporal_models_compressor():
    """Test FuelConsumerPowerConsumptionQuery for calculating gas turbine compressor el-consumption, LTP.

    Detailed temporal models (variations within one year) for:
    - Fuel consumer user defined category
    """
    variables = dto.VariablesMap(time_vector=time_vector_installation, variables={})

    ltp_result = get_consumption(
        model=installation_compressor_dto([no_el_consumption()]), variables=variables, time_vector=time_vector_yearly
    )

    gas_turbine_compressor_el_consumption = get_sum_ltp_column(ltp_result, installation_nr=0, ltp_column_nr=3)

    # FuelConsumerPowerConsumptionQuery. Check gas turbine compressor el consumption.
    assert gas_turbine_compressor_el_consumption == expected_gas_turbine_compressor_el_consumption()


def test_boiler_heater_categories():
    variables = dto.VariablesMap(time_vector=time_vector_installation, variables={})

    ltp_result = get_consumption(
        model=installation_boiler_heater_dto(), variables=variables, time_vector=time_vector_yearly
    )

    boiler_fuel_consumption = get_sum_ltp_column(ltp_result, installation_nr=0, ltp_column_nr=0)
    heater_fuel_consumption = get_sum_ltp_column(ltp_result, installation_nr=0, ltp_column_nr=1)
    co2_from_boiler = get_sum_ltp_column(ltp_result, installation_nr=0, ltp_column_nr=2)
    co2_from_heater = get_sum_ltp_column(ltp_result, installation_nr=0, ltp_column_nr=3)

    # FuelConsumerPowerConsumptionQuery. Check gas turbine compressor el consumption.
    assert boiler_fuel_consumption == expected_boiler_fuel_consumption()
    assert heater_fuel_consumption == expected_heater_fuel_consumption()
    assert co2_from_boiler == expected_co2_from_boiler()
    assert co2_from_heater == expected_co2_from_heater()


def test_venting_emitters():
    """Test venting emitters for LTP export.

    Verify correct behaviour if input rate is given in different units and rate types (sd and cd).
    """
    time_vector = [
        datetime(2027, 1, 1),
        datetime(2028, 1, 1),
    ]
    regularity = 0.2
    emission_rate = 10

    variables = dto.VariablesMap(time_vector=time_vector, variables={})

    installation_sd_kg_per_day = venting_emitter_yaml_factory(
        emission_rates=[emission_rate],
        regularity=regularity,
        units=[Unit.KILO_PER_DAY],
        emission_names=["ch4"],
        rate_types=[RateType.STREAM_DAY],
        names=["Venting emitter 1"],
    )

    installation_sd_tons_per_day = venting_emitter_yaml_factory(
        emission_rates=[emission_rate],
        regularity=regularity,
        rate_types=[RateType.STREAM_DAY],
        units=[Unit.TONS_PER_DAY],
        emission_names=["ch4"],
        names=["Venting emitter 1"],
    )

    installation_cd_kg_per_day = venting_emitter_yaml_factory(
        emission_rates=[emission_rate],
        regularity=regularity,
        rate_types=[RateType.CALENDAR_DAY],
        units=[Unit.KILO_PER_DAY],
        emission_names=["ch4"],
        names=["Venting emitter 1"],
    )

    ltp_result_input_sd_kg_per_day = get_consumption(
        model=installation_sd_kg_per_day, variables=variables, time_vector=time_vector_yearly
    )

    ltp_result_input_sd_tons_per_day = get_consumption(
        model=installation_sd_tons_per_day, variables=variables, time_vector=time_vector_yearly
    )

    ltp_result_input_cd_kg_per_day = get_consumption(
        model=installation_cd_kg_per_day, variables=variables, time_vector=time_vector_yearly
    )

    emission_input_sd_kg_per_day = get_sum_ltp_column(
        ltp_result_input_sd_kg_per_day, installation_nr=0, ltp_column_nr=0
    )
    emission_input_sd_tons_per_day = get_sum_ltp_column(
        ltp_result_input_sd_tons_per_day, installation_nr=0, ltp_column_nr=0
    )
    emission_input_cd_kg_per_day = get_sum_ltp_column(
        ltp_result_input_cd_kg_per_day, installation_nr=0, ltp_column_nr=0
    )

    # Verify correct emissions when input is kg per day. Output should be in tons per day - hence dividing by 1000
    assert emission_input_sd_kg_per_day == (emission_rate / 1000) * 365 * regularity

    # Verify correct emissions when input is tons per day.
    assert emission_input_sd_tons_per_day == emission_rate * 365 * regularity

    # Verify that input calendar day vs input stream day is linked correctly through regularity
    assert emission_input_cd_kg_per_day == emission_input_sd_kg_per_day / regularity

    # Verify that results is independent of regularity, when input rate is in calendar days
    assert emission_input_cd_kg_per_day == (emission_rate / 1000) * 365


def test_only_venting_emitters_no_fuelconsumers():
    """
    Test that it is possible with only venting emitters, without fuelconsumers.
    """
    time_vector = [
        datetime(2027, 1, 1),
        datetime(2028, 1, 1),
    ]
    regularity = 0.2
    emission_rate = 10

    variables = dto.VariablesMap(time_vector=time_vector, variables={})

    installation_venting_emitters = venting_emitter_yaml_factory(
        emission_rates=[emission_rate],
        regularity=regularity,
        units=[Unit.KILO_PER_DAY],
        emission_names=["ch4"],
        rate_types=[RateType.STREAM_DAY],
        include_emitters=True,
        include_fuel_consumers=False,
        names=["Venting emitter 1"],
    )
    venting_emitter_results = get_consumption(
        model=installation_venting_emitters, variables=variables, time_vector=time_vector_yearly
    )
    emissions_ch4 = get_sum_ltp_column(venting_emitter_results, installation_nr=0, ltp_column_nr=0)
    assert emissions_ch4 == (emission_rate / 1000) * 365 * regularity


def test_no_emitters_or_fuelconsumers():
    """
    Test that eCalc returns error when neither fuelconsumers or venting emitters are specified.
    """

    regularity = 0.2
    emission_rate = 10

    with pytest.raises(DtoValidationError) as ee:
        venting_emitter_yaml_factory(
            emission_rates=[emission_rate],
            regularity=regularity,
            units=[Unit.KILO_PER_DAY],
            emission_names=["ch4"],
            rate_types=[RateType.STREAM_DAY],
            include_emitters=False,
            include_fuel_consumers=False,
            names=["Venting emitter 1"],
        )

    assert (
        f"\nminimal_installation:\n:\tValue error, Keywords are missing:\n It is required to specify at least one of the keywords "
        f"{EcalcYamlKeywords.fuel_consumers}, {EcalcYamlKeywords.generator_sets} or {EcalcYamlKeywords.installation_venting_emitters} "
        f"in the model."
    ) in str(ee.value)


def test_total_oil_loaded_old_method():
    """Test total oil loaded/stored for LTP export. Using original method where direct/venting emitters are
    modelled as FUELSCONSUMERS using DIRECT.

    Verify correct volume when model includes emissions related to both storage and loading of oil,
    and when model includes only loading.
    """
    time_vector = [
        datetime(2027, 1, 1),
        datetime(2028, 1, 1),
    ]
    variables = dto.VariablesMap(time_vector=time_vector, variables={})

    regularity = 0.6
    emission_factor = 2
    fuel_rate = 100

    # Create model with both loading and storage
    asset_loading_storage = ltp_oil_loaded_yaml_factory(
        emission_factor=emission_factor,
        rate_types=[RateType.STREAM_DAY, RateType.STREAM_DAY],
        fuel_rates=[fuel_rate, fuel_rate],
        emission_name="ch4",
        regularity=regularity,
        categories=["LOADING", "STORAGE"],
        consumer_names=["loading", "storage"],
    )

    # Create model with only loading, not storage
    asset_loading_only = ltp_oil_loaded_yaml_factory(
        emission_factor=emission_factor,
        rate_types=[RateType.STREAM_DAY],
        fuel_rates=[fuel_rate],
        emission_name="ch4",
        regularity=regularity,
        categories=["LOADING"],
        consumer_names=["loading"],
    )

    ltp_result_loading_storage = get_consumption(
        model=asset_loading_storage, variables=variables, time_vector=time_vector_yearly
    )
    ltp_result_loading_only = get_consumption(
        model=asset_loading_only, variables=variables, time_vector=time_vector_yearly
    )

    loaded_and_stored_oil_loading_and_storage = get_sum_ltp_column(
        ltp_result_loading_storage, installation_nr=0, ltp_column_nr=2
    )
    loaded_and_stored_oil_loading_only = get_sum_ltp_column(ltp_result_loading_only, installation_nr=0, ltp_column_nr=1)

    # Verify output for total oil loaded/stored, if only loading is specified.
    assert loaded_and_stored_oil_loading_only is not None

    # Verify correct volume for oil loaded/stored
    assert loaded_and_stored_oil_loading_and_storage == fuel_rate * 365 * regularity

    # Verify that total oil loaded/stored is the same if only loading is specified,
    # compared to a model with both loading and storage.
    assert loaded_and_stored_oil_loading_and_storage == loaded_and_stored_oil_loading_only


def test_electrical_and_mechanical_power_installation():
    """Check that new total power includes the sum of electrical- and mechanical power at installation level"""
    variables = dto.VariablesMap(time_vector=time_vector_installation, variables={})
    asset = dto.Asset(
        name="Asset 1",
        installations=[
            installation_compressor_dto([simple_direct_el_consumer()]),
        ],
    )

    asset_result = get_consumption_asset_result(model=asset, variables=variables)
    power_fuel_driven_compressor = asset_result.get_component_by_name(
        "single_1d_compressor_sampled"
    ).power_cumulative.values[-1]
    power_generator_set = asset_result.get_component_by_name("genset").power_cumulative.values[-1]

    # Extract cumulative electrical-, mechanical- and total power.
    power_electrical_installation = asset_result.get_component_by_name(
        "INSTALLATION_A"
    ).power_electrical_cumulative.values[-1]

    power_mechanical_installation = asset_result.get_component_by_name(
        "INSTALLATION_A"
    ).power_mechanical_cumulative.values[-1]

    power_total_installation = asset_result.get_component_by_name("INSTALLATION_A").power_cumulative.values[-1]

    # Verify that total power is correct
    assert power_total_installation == power_electrical_installation + power_mechanical_installation

    # Verify that electrical power equals genset power, and mechanical power equals power from gas driven compressor:
    assert power_generator_set == power_electrical_installation
    assert power_fuel_driven_compressor == power_mechanical_installation
