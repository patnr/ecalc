import math
import operator
from datetime import datetime
from functools import reduce
from typing import Dict, List

import libecalc
from libecalc import dto
from libecalc.common.component_info.component_level import ComponentLevel
from libecalc.common.component_info.compressor import CompressorPressureType
from libecalc.common.exceptions import ProgrammingError
from libecalc.common.temporal_model import TemporalExpression, TemporalModel
from libecalc.common.units import Unit
from libecalc.common.utils.calculate_emission_intensity import (
    compute_emission_intensity_by_yearly_buckets,
)
from libecalc.common.utils.rates import (
    TimeSeriesBoolean,
    TimeSeriesFloat,
    TimeSeriesRate,
)
from libecalc.core.result import ComponentResult, EcalcModelResult
from libecalc.core.result.emission import EmissionResult
from libecalc.dto.base import ComponentType
from libecalc.dto.graph import Graph
from libecalc.dto.models import EnergyUsageModel
from libecalc.dto.result.emission import EmissionIntensityResult
from libecalc.dto.result.results import CompressorResult
from libecalc.dto.types import RateType
from libecalc.dto.utils.aggregators import aggregate_emissions, aggregate_is_valid
from libecalc.expression import Expression
from pydantic import BaseModel, parse_obj_as


class EnergyCalculatorResult(BaseModel):
    consumer_results: Dict[str, EcalcModelResult]
    emission_results: Dict[str, Dict[str, EmissionResult]]
    variables_map: dto.VariablesMap


class GraphResult:
    def __init__(
        self,
        graph: Graph,
        consumer_results: Dict[str, EcalcModelResult],
        emission_results: Dict[str, Dict[str, EmissionResult]],
        variables_map: dto.VariablesMap,
    ):
        self.graph = graph
        self.consumer_results = consumer_results
        self.emission_results = emission_results
        self.variables_map = variables_map

    @staticmethod
    def _compute_intensity(
        hydrocarbon_export_rate: TimeSeriesRate,
        emissions: Dict[str, EmissionResult],
    ):
        hydrocarbon_export_cumulative = hydrocarbon_export_rate.to_volumes().cumulative()
        emission_intensities = []
        for key in emissions:
            cumulative_rate_kg = emissions[key].rate.to_volumes().to_unit(Unit.KILO).cumulative()
            intensity_sm3 = cumulative_rate_kg / hydrocarbon_export_cumulative
            intensity_yearly_sm3 = compute_emission_intensity_by_yearly_buckets(
                emission_cumulative=cumulative_rate_kg,
                hydrocarbon_export_cumulative=hydrocarbon_export_cumulative,
            )
            emission_intensities.append(
                EmissionIntensityResult(
                    name=emissions[key].name,
                    timesteps=emissions[key].timesteps,
                    intensity_sm3=intensity_sm3,
                    intensity_boe=intensity_sm3.to_unit(Unit.KG_BOE),
                    intensity_yearly_sm3=intensity_yearly_sm3,
                    intensity_yearly_boe=intensity_yearly_sm3.to_unit(Unit.KG_BOE),
                )
            )
        return emission_intensities

    def _evaluate_installations(self, variables_map: dto.VariablesMap) -> List[libecalc.dto.result.InstallationResult]:
        asset_id = self.graph.root
        asset = self.graph.get_component(asset_id)
        installation_results = []
        for installation in asset.installations:
            regularity = TemporalExpression.evaluate(
                temporal_expression=TemporalModel(installation.regularity),
                variables_map=variables_map,
            )
            hydrocarbon_export_rate = TemporalExpression.evaluate(
                temporal_expression=TemporalModel(installation.hydrocarbon_export),
                variables_map=variables_map,
            )
            hydrocarbon_export_rate = TimeSeriesRate(
                timesteps=variables_map.time_vector,
                values=hydrocarbon_export_rate,
                unit=Unit.STANDARD_CUBIC_METER_PER_DAY,
                regularity=regularity,
                typ=RateType.CALENDAR_DAY,
            )

            sub_components = [
                self.consumer_results[component_id].component_result
                for component_id in self.graph.get_successors(installation.id, recursively=True)
                if component_id in self.consumer_results
            ]

            installation_node_info = self.graph.get_node_info(installation.id)
            power = reduce(
                operator.add,
                [
                    component.power
                    for component in sub_components
                    if self.graph.get_node_info(component.id).component_type == ComponentType.GENERATOR_SET
                ],
                TimeSeriesRate(
                    values=[0.0] * self.variables_map.length,
                    timesteps=self.variables_map.time_vector,
                    unit=Unit.MEGA_WATT,
                    regularity=regularity,
                ),  # Initial value, handle no power output from components
            )

            energy_usage = reduce(
                operator.add,
                [
                    component.energy_usage
                    for component in sub_components
                    if component.energy_usage.unit == Unit.STANDARD_CUBIC_METER_PER_DAY
                ],
            )

            aggregated_emissions = aggregate_emissions(
                [
                    self.emission_results[fuel_consumer_id]
                    for fuel_consumer_id in self.graph.get_successors(installation.id)
                ]
            )

            installation_results.append(
                libecalc.dto.result.InstallationResult(
                    id=installation.id,
                    name=installation_node_info.name,
                    parent=asset.id,
                    component_level=installation_node_info.component_level,
                    componentType=installation_node_info.component_type,
                    timesteps=variables_map.time_vector,
                    is_valid=TimeSeriesBoolean(
                        timesteps=variables_map.time_vector,
                        values=aggregate_is_valid(sub_components),
                        unit=Unit.NONE,
                    ),
                    power=power,
                    power_cumulative=power.to_volumes().to_unit(Unit.GIGA_WATT_HOURS).cumulative(),
                    energy_usage=energy_usage,
                    energy_usage_cumulative=energy_usage.to_volumes().cumulative(),
                    hydrocarbon_export_rate=hydrocarbon_export_rate,
                    emissions=self._parse_emissions(aggregated_emissions),
                    emission_intensities=self._compute_intensity(
                        hydrocarbon_export_rate=hydrocarbon_export_rate,
                        emissions=aggregated_emissions,
                    ),
                )
            )
        return installation_results

    def get_subgraph(self, node_id: str) -> "GraphResult":
        subgraph = self.graph.get_component(node_id).get_graph()

        return GraphResult(
            graph=subgraph,
            variables_map=self.variables_map,
            consumer_results={
                component_id: consumer_result
                for component_id, consumer_result in self.consumer_results.items()
                if component_id in subgraph
            },
            emission_results={
                component_id: emissions
                for component_id, emissions in self.emission_results.items()
                if component_id in subgraph
            },
        )

    def get_energy_result(self, component_id: str) -> ComponentResult:
        return self.consumer_results[component_id].component_result

    @property
    def timesteps(self):
        return self.variables_map.time_vector

    @staticmethod
    def _parse_emissions(emissions: Dict[str, EmissionResult]) -> Dict[str, libecalc.dto.result.EmissionResult]:
        return {
            key: libecalc.dto.result.EmissionResult(
                name=key,
                timesteps=emissions[key].timesteps,
                rate=emissions[key].rate,
                quota=emissions[key].quota,
                tax=emissions[key].tax,
                cumulative=emissions[key].rate.to_volumes().cumulative(),
                quota_cumulative=emissions[key].quota.to_volumes().cumulative(),
                tax_cumulative=emissions[key].tax.to_volumes().cumulative(),
            )
            for key in emissions
        }

    @staticmethod
    def extract_requested_pressures_from_model(
        energy_usage_model: Dict[datetime, EnergyUsageModel],
        pressure_type: CompressorPressureType,
    ) -> TemporalModel[Expression]:
        """Get compressor inlet- and outlet pressures.
        The pressures are the requested pressures defined by user in input.

        :param energy_usage_model: Temporal energy usage model
        :param pressure_type: Compressor pressure type, inlet- or outlet
        :return: Temporal model with pressures as expressions
        """
        evaluated_temporal_energy_usage_models = {}
        for period, model in TemporalModel(energy_usage_model).items():
            if pressure_type.value == CompressorPressureType.OUTLET_PRESSURE:
                pressures = getattr(model, "discharge_pressure", None)
            else:
                pressures = getattr(model, "suction_pressure", None)

            if pressures is None:
                # Handle when pressure attribute does not exist and if pressure attribute is None
                pressures = math.nan

            if not isinstance(pressures, Expression):
                pressures = Expression.setup_from_expression(value=pressures)

            evaluated_temporal_energy_usage_models[period.start] = pressures
        return TemporalModel(evaluated_temporal_energy_usage_models)

    def get_asset_result(self) -> libecalc.dto.result.EcalcModelResult:
        asset_id = self.graph.root
        asset = self.graph.get_component(asset_id)

        if not isinstance(asset, dto.Asset):
            raise ProgrammingError("Need an asset graph to get asset result")

        installation_results = self._evaluate_installations(variables_map=self.variables_map)

        models = []
        sub_components = [*installation_results]
        for consumer_result in self.consumer_results.values():
            consumer_id = consumer_result.component_result.id
            consumer_node_info = self.graph.get_node_info(consumer_id)

            models.extend(
                [
                    parse_obj_as(
                        libecalc.dto.result.ConsumerModelResult,
                        {
                            **model.dict(),
                            "parent": consumer_id,
                            "componentType": model.component_type,
                            "component_level": ComponentLevel.MODEL,
                            "energy_usage_cumulative": model.energy_usage.to_volumes().cumulative().dict(),
                            "power_cumulative": (
                                model.power.to_volumes().to_unit(Unit.GIGA_WATT_HOURS).cumulative().dict()
                                if model.power is not None
                                else None
                            ),
                        },
                    )
                    for model in consumer_result.models
                ]
            )

            if self.graph.get_component(consumer_id).component_type == ComponentType.COMPRESSOR:
                component = self.graph.get_component(consumer_id)

                # Get temporal expression for inlet- and outlet pressures
                inlet_pressure_eval = GraphResult.extract_requested_pressures_from_model(
                    energy_usage_model=component.energy_usage_model,
                    pressure_type=CompressorPressureType.INLET_PRESSURE,
                )

                outlet_pressure_eval = GraphResult.extract_requested_pressures_from_model(
                    energy_usage_model=component.energy_usage_model,
                    pressure_type=CompressorPressureType.OUTLET_PRESSURE,
                )

                # Evaluate pressures in temporal expression
                requested_inlet_pressure = TimeSeriesFloat(
                    timesteps=self.timesteps,
                    values=TemporalExpression.evaluate(inlet_pressure_eval, self.variables_map),
                    unit=Unit.BARA,
                )

                requested_outlet_pressure = TimeSeriesFloat(
                    timesteps=self.timesteps,
                    values=TemporalExpression.evaluate(outlet_pressure_eval, self.variables_map),
                    unit=Unit.BARA,
                )

                sub_components.append(
                    CompressorResult(
                        parent=self.graph.get_predecessor(consumer_id),
                        componentType=consumer_node_info.component_type,
                        component_level=consumer_node_info.component_level,
                        name=consumer_node_info.name,
                        timesteps=self.timesteps,
                        is_valid=consumer_result.component_result.is_valid,
                        energy_usage=consumer_result.component_result.energy_usage,
                        energy_usage_cumulative=consumer_result.component_result.energy_usage.to_volumes().cumulative(),
                        id=consumer_id,
                        power=consumer_result.component_result.power
                        if consumer_result.component_result.power is not None
                        else None,
                        power_cumulative=consumer_result.component_result.power.to_volumes()
                        .to_unit(Unit.GIGA_WATT_HOURS)
                        .cumulative()
                        if consumer_result.component_result.power is not None
                        else None,
                        emissions=self._parse_emissions(self.emission_results[consumer_id])
                        if consumer_id in self.emission_results
                        else [],
                        recirculation_loss=consumer_result.component_result.recirculation_loss,
                        rate_exceeds_maximum=consumer_result.component_result.rate_exceeds_maximum,
                        outlet_pressure_before_choking=consumer_result.component_result.outlet_pressure_before_choking,
                        requested_inlet_pressure=requested_inlet_pressure,
                        requested_outlet_pressure=requested_outlet_pressure,
                    )
                )
            else:
                sub_components.append(
                    parse_obj_as(
                        libecalc.dto.result.ComponentResult,
                        {
                            **consumer_result.component_result.dict(),
                            "name": consumer_node_info.name,
                            "parent": self.graph.get_predecessor(consumer_id),
                            "component_level": consumer_node_info.component_level,
                            "componentType": consumer_node_info.component_type,
                            "emissions": self._parse_emissions(self.emission_results[consumer_id])
                            if consumer_id in self.emission_results
                            else [],
                            "energy_usage_cumulative": consumer_result.component_result.energy_usage.to_volumes()
                            .cumulative()
                            .dict(),
                            "power_cumulative": consumer_result.component_result.power.to_volumes()
                            .to_unit(Unit.GIGA_WATT_HOURS)
                            .cumulative()
                            .dict()
                            if consumer_result.component_result.power is not None
                            else None,
                        },
                    )
                )

        for installation in asset.installations:
            for direct_emitter in installation.direct_emitters:
                energy_usage = TimeSeriesRate(
                    timesteps=self.variables_map.time_vector,
                    values=[0.0] * self.variables_map.length,
                    regularity=[1] * self.variables_map.length,
                    unit=Unit.STANDARD_CUBIC_METER_PER_DAY,
                )
                sub_components.append(
                    libecalc.dto.result.DirectEmitterResult(
                        id=direct_emitter.id,
                        name=direct_emitter.name,
                        componentType=direct_emitter.component_type,
                        component_level=ComponentLevel.CONSUMER,
                        parent=installation.id,
                        emissions=self._parse_emissions(self.emission_results[direct_emitter.id]),
                        timesteps=self.variables_map.time_vector,
                        is_valid=TimeSeriesBoolean(
                            timesteps=self.variables_map.time_vector,
                            values=[True] * self.variables_map.length,
                            unit=Unit.NONE,
                        ),
                        energy_usage=energy_usage,
                        energy_usage_cumulative=energy_usage.to_volumes().cumulative(),
                    )
                )

        # dto timeseries
        asset_hydrocarbon_export_rate_core = reduce(
            operator.add,
            [installation.hydrocarbon_export_rate for installation in installation_results],
        )

        asset_aggregated_emissions = aggregate_emissions(self.emission_results.values())

        asset_power_core = reduce(
            operator.add,
            [installation.power for installation in installation_results if installation.power is not None],
        )

        asset_power_cumulative = asset_power_core.to_volumes().to_unit(Unit.GIGA_WATT_HOURS).cumulative()

        asset_energy_usage_core = reduce(
            operator.add,
            [installation.energy_usage for installation in installation_results],
        )

        asset_energy_usage_cumulative = asset_energy_usage_core.to_volumes().cumulative()

        asset_node_info = self.graph.get_node_info(asset_id)
        asset_result_dto = libecalc.dto.result.AssetResult(
            id=asset.id,
            name=asset_node_info.name,
            component_level=asset_node_info.component_level,
            componentType=asset_node_info.component_level,
            timesteps=self.variables_map.time_vector,
            is_valid=TimeSeriesBoolean(
                timesteps=self.variables_map.time_vector,
                values=aggregate_is_valid(installation_results),
                unit=Unit.NONE,
            ),
            power=asset_power_core,
            power_cumulative=asset_power_cumulative,
            energy_usage=asset_energy_usage_core,
            energy_usage_cumulative=asset_energy_usage_cumulative,
            hydrocarbon_export_rate=asset_hydrocarbon_export_rate_core,
            emissions=self._parse_emissions(asset_aggregated_emissions),
            emission_intensities=self._compute_intensity(
                hydrocarbon_export_rate=asset_hydrocarbon_export_rate_core,
                emissions=asset_aggregated_emissions,
            ),
        )

        return libecalc.dto.result.EcalcModelResult(
            component_result=asset_result_dto,
            sub_components=sub_components,
            models=models,
        )

    def get_emissions(self, component_id: str) -> Dict[str, EmissionResult]:
        return self.emission_results[component_id]

    def get_results(self) -> EnergyCalculatorResult:
        return EnergyCalculatorResult(
            consumer_results=self.consumer_results,
            emission_results=self.emission_results,
            variables_map=self.variables_map,
        )
