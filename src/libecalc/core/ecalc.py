from typing import Dict

import numpy as np

import libecalc.dto.components
from libecalc import dto
from libecalc.common.list.list_utils import elementwise_sum
from libecalc.common.priority_optimizer import PriorityOptimizer
from libecalc.common.utils.rates import TimeSeriesInt
from libecalc.core.consumers.consumer_system import ConsumerSystem
from libecalc.core.consumers.direct_emitter import DirectEmitter
from libecalc.core.consumers.generator_set import Genset
from libecalc.core.consumers.legacy_consumer.component import Consumer
from libecalc.core.models.fuel import FuelModel
from libecalc.core.result import EcalcModelResult
from libecalc.core.result.emission import EmissionResult
from libecalc.dto.component_graph import ComponentGraph
from libecalc.dto.types import ConsumptionType


class EnergyCalculator:
    def __init__(
        self,
        graph: ComponentGraph,
    ):
        self._graph = graph

    def evaluate_energy_usage(self, variables_map: dto.VariablesMap) -> Dict[str, EcalcModelResult]:
        component_ids = list(reversed(self._graph.sorted_node_ids))
        component_dtos = [self._graph.get_node(component_id) for component_id in component_ids]

        consumer_results: Dict[str, EcalcModelResult] = {}

        for component_dto in component_dtos:
            if isinstance(component_dto, (dto.ElectricityConsumer, dto.FuelConsumer)):
                consumer = Consumer(consumer_dto=component_dto)
                consumer_results[component_dto.id] = consumer.evaluate(variables_map=variables_map)
            elif isinstance(component_dto, dto.GeneratorSet):
                fuel_consumer = Genset(component_dto)

                power_requirement = elementwise_sum(
                    *[
                        consumer_results[consumer_id].component_result.power.values
                        for consumer_id in self._graph.get_successors(component_dto.id)
                    ],
                    timesteps=variables_map.time_vector,
                )

                consumer_results[component_dto.id] = EcalcModelResult(
                    component_result=fuel_consumer.evaluate(
                        variables_map=variables_map,
                        power_requirement=power_requirement,
                    ),
                    models=[],
                    sub_components=[],
                )
            elif isinstance(component_dto, libecalc.dto.components.ConsumerSystem):
                consumer_system = ConsumerSystem(
                    id=component_dto.id,
                    consumers=component_dto.consumers,
                    component_conditions=component_dto.component_conditions,
                )

                evaluated_stream_conditions = component_dto.evaluate_stream_conditions(
                    variables_map=variables_map,
                )
                optimizer = PriorityOptimizer()

                optimizer_result = optimizer.optimize(
                    timesteps=variables_map.time_vector,
                    priorities=evaluated_stream_conditions,
                    evaluator=consumer_system.evaluator,
                )

                # Convert to legacy compatible operational_settings_used
                priorities_to_int_map = {
                    priority_name: index + 1 for index, priority_name in enumerate(evaluated_stream_conditions.keys())
                }
                operational_settings_used = TimeSeriesInt(
                    timesteps=optimizer_result.priorities_used.timesteps,
                    values=[
                        priorities_to_int_map[priority_name]
                        for priority_name in optimizer_result.priorities_used.values
                    ],
                    unit=optimizer_result.priorities_used.unit,
                )

                system_result = consumer_system.get_system_result(
                    consumer_results=optimizer_result.priority_results,
                    operational_settings_used=operational_settings_used,
                )
                consumer_results[component_dto.id] = system_result
                for consumer_result in optimizer_result.priority_results:
                    consumer_results[consumer_result.id] = EcalcModelResult(
                        component_result=consumer_result,
                        sub_components=[],
                        models=[],
                    )

        return consumer_results

    def evaluate_emissions(
        self, variables_map: dto.VariablesMap, consumer_results: Dict[str, EcalcModelResult]
    ) -> Dict[str, Dict[str, EmissionResult]]:
        """
        Calculate emissions for fuel consumers and emitters

        Args:
            variables_map:
            consumer_results:

        Returns: a mapping from consumer_id to emissions
        """
        emission_results: Dict[str, Dict[str, EmissionResult]] = {}
        for consumer_dto in self._graph.nodes.values():
            if isinstance(consumer_dto, (dto.FuelConsumer, dto.GeneratorSet)):
                fuel_model = FuelModel(consumer_dto.fuel)
                energy_usage = consumer_results[consumer_dto.id].component_result.energy_usage
                emission_results[consumer_dto.id] = fuel_model.evaluate_emissions(
                    variables_map=variables_map,
                    fuel_rate=np.asarray(energy_usage.values),
                )
            elif isinstance(consumer_dto, dto.components.ConsumerSystem):
                if consumer_dto.consumes == ConsumptionType.FUEL:
                    fuel_model = FuelModel(consumer_dto.fuel)
                    energy_usage = consumer_results[consumer_dto.id].component_result.energy_usage
                    emission_results[consumer_dto.id] = fuel_model.evaluate_emissions(
                        variables_map=variables_map, fuel_rate=np.asarray(energy_usage.values)
                    )
            elif isinstance(consumer_dto, dto.DirectEmitter):
                emission_results[consumer_dto.id] = DirectEmitter(consumer_dto).evaluate(variables_map=variables_map)
        return emission_results
