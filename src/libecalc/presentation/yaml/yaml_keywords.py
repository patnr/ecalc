"""Module for all input keys."""


class EcalcYamlKeywords:
    """All ecalc specific yaml keywords."""

    name = "NAME"

    direct_consumer_consumption_rate_type = "CONSUMPTION_RATE_TYPE"

    energy_usage_model = "ENERGY_USAGE_MODEL"
    energy_usage_model_type_direct = "DIRECT"
    energy_usage_model_type_pump_system = "PUMP_SYSTEM"
    energy_usage_model_type_compressor_system = "COMPRESSOR_SYSTEM"
    energy_usage_model_type_tabulated = "TABULATED"
    energy_usage_model_type_compressor = "COMPRESSOR"

    energy_usage_model_type_pump = "PUMP"
    energy_usage_model_type_variable_speed_compressor_train_multiple_streams_and_pressures = (
        "VARIABLE_SPEED_COMPRESSOR_TRAIN_MULTIPLE_STREAMS_AND_PRESSURES"
    )
    fuel = "FUEL"
    fuel_types = "FUEL_TYPES"
    fuel_lower_heating_value = "LOWER_HEATING_VALUE"

    consumer_system_total_system_rate = "TOTAL_SYSTEM_RATE"
    consumer_system_operational_settings = "OPERATIONAL_SETTINGS"
    consumer_system_operational_settings_rate_fractions = "RATE_FRACTIONS"
    consumer_system_operational_settings_rates = "RATES"
    consumer_system_operational_settings_suction_pressures = "SUCTION_PRESSURES"
    consumer_system_operational_settings_discharge_pressures = "DISCHARGE_PRESSURES"
    consumer_system_operational_settings_suction_pressure = "SUCTION_PRESSURE"
    consumer_system_operational_settings_discharge_pressure = "DISCHARGE_PRESSURE"
    consumer_system_operational_settings_crossover = "CROSSOVER"

    pump_system_pumps = "PUMPS"
    pump_system_pump_model = "CHART"
    pump_system_head_margin = "HEAD_MARGIN"
    pump_system_fluid_density = "FLUID_DENSITY"
    pump_system_operational_settings_fluid_densities = "FLUID_DENSITIES"

    compressor_system_compressors = "COMPRESSORS"
    compressor_system_compressor_sampled_data = "COMPRESSOR_MODEL"

    consumer_function_rate = "RATE"
    consumer_function_suction_pressure = "SUCTION_PRESSURE"
    consumer_function_discharge_pressure = "DISCHARGE_PRESSURE"
    pump_function_fluid_density = "FLUID_DENSITY"

    variable_expression = "EXPRESSION"
    user_defined_tag = "CATEGORY"
    file = "FILE"
    type = "TYPE"
    composition = "COMPOSITION"
    composition_H2O = "H2O"
    composition_water = "water"

    condition = "CONDITION"
    conditions = "CONDITIONS"
    consumers = "CONSUMERS"
    el2fuel = "ELECTRICITY2FUEL"
    emission_factor = "FACTOR"
    emissions = "EMISSIONS"
    energy_model = "ENERGYFUNCTION"
    facility_inputs = "FACILITY_INPUTS"
    fuel_consumers = "FUELCONSUMERS"
    fuel_rate = "FUELRATE"
    generator_sets = "GENERATORSETS"
    installation_venting_emitters = "VENTING_EMITTERS"
    installation_venting_emitter_emission_name = "EMISSION_NAME"
    installation_venting_emitter_emission_rate = "EMISSION_RATE"
    installation_venting_emitter_model = "EMITTER_MODEL"
    hydrocarbon_export = "HCEXPORT"
    installations = "INSTALLATIONS"
    load = "LOAD"
    power_loss_factor = "POWERLOSSFACTOR"

    consumer_tabular_power = "POWER"
    consumer_tabular_fuel = "FUEL"
    regularity = "REGULARITY"
    variables = "VARIABLES"
    facility_type_tabular = "TABULAR"
    facility_type_electricity2fuel = "ELECTRICITY2FUEL"
    facility_type_compressor_tabular = "COMPRESSOR_TABULAR"
    facility_type_pump_chart_single_speed = "PUMP_CHART_SINGLE_SPEED"
    facility_type_pump_chart_variable_speed = "PUMP_CHART_VARIABLE_SPEED"

    calculate_max_rate = "CALCULATE_MAX_RATE"
    maximum_discharge_pressure = "MAXIMUM_DISCHARGE_PRESSURE"

    # Compressor and compressor train
    models_type_compressor_chart = "COMPRESSOR_CHART"
    models_type_compressor_train_simplified = "SIMPLIFIED_VARIABLE_SPEED_COMPRESSOR_TRAIN"
    models_type_compressor_train_variable_speed = "VARIABLE_SPEED_COMPRESSOR_TRAIN"
    models_type_compressor_train_single_speed = "SINGLE_SPEED_COMPRESSOR_TRAIN"
    models_type_compressor_train_variable_speed_multiple_streams_and_pressures = (
        "VARIABLE_SPEED_COMPRESSOR_TRAIN_MULTIPLE_STREAMS_AND_PRESSURES"
    )
    models_type_compressor_train = "COMPRESSOR_TRAIN"
    models_type_compressor_train_stages = "STAGES"
    models_type_compressor_train_compressor_chart = "COMPRESSOR_CHART"
    models_type_compressor_train_maximum_pressure_ratio_per_stage = "MAXIMUM_PRESSURE_RATIO_PER_STAGE"
    models_type_compressor_train_inlet_temperature = "INLET_TEMPERATURE"
    models_type_compressor_train_pressure_drop_ahead_of_stage = "PRESSURE_DROP_AHEAD_OF_STAGE"
    models_type_compressor_train_stage_control_margin = "CONTROL_MARGIN"
    models_type_compressor_train_stage_control_margin_unit = "CONTROL_MARGIN_UNIT"
    models_type_compressor_train_stage_control_margin_unit_factor = "FRACTION"
    models_type_compressor_train_stage_control_margin_unit_percentage = "PERCENTAGE"
    models_type_compressor_train_chart_predefined = "PREDEFINED"

    models_type_compressor_train_rate_per_stream = "RATE_PER_STREAM"
    models_type_compressor_train_compressor_train_model = "COMPRESSOR_TRAIN_MODEL"
    models_type_compressor_train_streams = "STREAMS"
    models_type_compressor_train_stream = "STREAM"

    # Compressor train interstage pressure control
    models_type_compressor_train_interstage_control_pressure = "INTERSTAGE_CONTROL_PRESSURE"
    models_type_compressor_train_upstream_pressure_control = "UPSTREAM_PRESSURE_CONTROL"
    models_type_compressor_train_downstream_pressure_control = "DOWNSTREAM_PRESSURE_CONTROL"

    # Compressor train pressure control
    models_type_compressor_train_pressure_control = "PRESSURE_CONTROL"
    models_type_compressor_train_pressure_control_downstream_choke = "DOWNSTREAM_CHOKE"
    models_type_compressor_train_pressure_control_none = "NONE"

    # Fluids
    models_type_fluid = "FLUID"
    models_type_fluid_model = "FLUID_MODEL"
    models_type_fluid_model_type = "FLUID_MODEL_TYPE"
    models_type_fluid_predefined_gas_type = "GAS_TYPE"
    models_type_fluid_predefined_gas_ultra_dry = "ULTRA_DRY"
    models_type_fluid_predefined_gas_type_dry = "DRY"
    models_type_fluid_predefined_gas_type_medium = "MEDIUM"
    models_type_fluid_predefined_gas_type_rich = "RICH"
    models_type_fluid_predefined_gas_ultra_rich = "ULTRA_RICH"
    models_type_fluid_eos_model = "EOS_MODEL"
    models_type_fluid_eos_model_srk = "SRK"
    models_type_fluid_eos_model_pr = "PR"
    models_type_fluid_eos_model_gerg_srk = "GERG_SRK"
    models_type_fluid_eos_model_gerg_pr = "GERG_PR"

    # Pump and Compressor charts
    consumer_chart_type = "CHART_TYPE"
    consumer_chart_type_variable_speed = "VARIABLE_SPEED"
    consumer_chart_type_single_speed = "SINGLE_SPEED"
    consumer_chart_type_generic_from_design_point = "GENERIC_FROM_DESIGN_POINT"
    consumer_chart_type_generic_from_input = "GENERIC_FROM_INPUT"
    consumer_chart_units = "UNITS"
    consumer_chart_curves = "CURVES"
    consumer_chart_curve = "CURVE"
    consumer_chart_polytropic_efficiency = "POLYTROPIC_EFFICIENCY"
    consumer_chart_design_rate = "DESIGN_RATE"
    consumer_chart_design_head = "DESIGN_HEAD"
    consumer_chart_rate = "RATE"
    consumer_chart_head = "HEAD"
    consumer_chart_speed = "SPEED"
    consumer_chart_efficiency = "EFFICIENCY"
    consumer_chart_rate_unit_actual_volume_rate = "AM3_PER_HOUR"
    consumer_chart_head_unit_kj_per_kg = "KJ_PER_KG"
    consumer_chart_head_unit_joule_per_kg = "JOULE_PER_KG"
    consumer_chart_head_unit_m = "M"
    consumer_chart_efficiency_unit_factor = "FRACTION"
    consumer_chart_efficiency_unit_percentage = "PERCENTAGE"

    models = "MODELS"
    models_compressor_model = "COMPRESSOR_MODEL"
    models_turbine_model = "TURBINE_MODEL"
    models_type_turbine = "TURBINE"
    models_turbine_efficiency_table_load_values = "TURBINE_LOADS"
    models_turbine_efficiency_table_efficiency_values = "TURBINE_EFFICIENCIES"
    models_type_compressor_with_turbine = "COMPRESSOR_WITH_TURBINE"
    models_power_adjustment_constant_mw = "POWER_ADJUSTMENT_CONSTANT"
    models_maximum_power = "MAXIMUM_POWER"

    facility_adjustment = "ADJUSTMENT"
    facility_adjustment_factor = "FACTOR"
    facility_adjustment_constant = "CONSTANT"

    time_series = "TIME_SERIES"
    time_series_influence_time_vector = "INFLUENCE_TIME_VECTOR"
    time_series_extrapolate_outside_defined = "EXTRAPOLATION"
    time_series_interpolation_type = "INTERPOLATION_TYPE"

    start = "START"
    end = "END"
    date = "DATE"
