import operator
import typing
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from functools import reduce
from typing import Dict, Generic, List, TypeVar

import numpy as np

from libecalc.common.priorities import Priorities, PriorityID
from libecalc.common.units import Unit
from libecalc.common.utils.rates import (
    TimeSeriesBoolean,
    TimeSeriesString,
)

TResult = TypeVar("TResult")
TPriority = TypeVar("TPriority")

ComponentID = str


@dataclass
class PriorityOptimizerResult(Generic[TResult]):
    priorities_used: TimeSeriesString
    priority_results: List[typing.Any]  # TODO: typing. This is the consumer results merged based on priorities used


@dataclass
class EvaluatorResult(Generic[TResult]):
    id: ComponentID
    result: TResult
    is_valid: TimeSeriesBoolean


class PriorityOptimizer(Generic[TResult, TPriority]):
    @staticmethod
    def get_component_ids(
        priority_results: Dict[datetime, Dict[PriorityID, Dict[ComponentID, TResult]]]
    ) -> List[ComponentID]:
        component_ids = []
        for timestep in priority_results:
            for priority in priority_results[timestep]:
                for component_id in priority_results[timestep][priority].keys():
                    if component_id not in component_ids:
                        component_ids.append(component_id)
        return component_ids

    def collect_consumer_results(
        self,
        priorities_used: TimeSeriesString,
        priority_results: Dict[datetime, Dict[PriorityID, Dict[ComponentID, TResult]]],
    ) -> List[typing.Any]:  # TODO: Any type since we don't have access to component_result within TResult
        """
        Merge consumer results into a single result per consumer based on the operational settings used. I.e. pick results
        from the correct operational setting result and merge into a single result per consumer.
        Args:
            priorities_used:
            priority_results:

        Returns: List of merged consumer results

        """
        component_ids = self.get_component_ids(priority_results)

        consumer_results: Dict[ComponentID, typing.Any] = {}
        for component_id in component_ids:
            for timestep_index, timestep in enumerate(priorities_used.timesteps):
                priority_used = priorities_used.values[timestep_index]
                prev_result = consumer_results.get(component_id)
                consumer_result_subset = priority_results[timestep][priority_used][
                    component_id
                ].component_result  # TODO: Accessing something the type does not make clear exists

                if prev_result is None:
                    consumer_results[component_id] = consumer_result_subset
                else:
                    consumer_results[component_id] = prev_result.merge(consumer_result_subset)

        return list(consumer_results.values())

    def optimize(
        self,
        timesteps: List[datetime],
        priorities: Priorities[TPriority],
        evaluator: typing.Callable[[datetime, TPriority], List[EvaluatorResult[TResult]]],
    ) -> PriorityOptimizerResult:
        """
        Given a list of priorities, evaluate each priority using the evaluator. If the result of an evaluation is valid
        the priority is selected, if invalid try the next priority.

        We process each timestep separately.

        It will default to the last priority if all settings fails

        Args:
            timesteps: The timesteps that we want to figure out which priority to use for.
            priorities: Dict of priorities, key is used to identify the priority in the results.
            evaluator: The evaluator function gives a list of results back, each result with its own unique id.

        Returns:
            PriorityOptimizerResult: result containing priorities used and a list of the results merged on priorities
            used,

        """
        is_valid = TimeSeriesBoolean(timesteps=timesteps, values=[False] * len(timesteps), unit=Unit.NONE)
        priorities_used = TimeSeriesString(
            timesteps=timesteps,
            values=[list(priorities.keys())[-1]] * len(timesteps),
            unit=Unit.NONE,
        )
        priority_results: Dict[datetime, Dict[PriorityID, Dict[str, TResult]]] = defaultdict(dict)

        for timestep_index, timestep in enumerate(timesteps):
            priority_results[timestep] = defaultdict(dict)
            for priority_name, priority_value in priorities.items():
                evaluator_results = evaluator(timestep, priority_value)
                for evaluator_result in evaluator_results:
                    priority_results[timestep][priority_name][evaluator_result.id] = evaluator_result.result

                # Check if consumers are valid for this operational setting, should be valid for all consumers
                all_evaluator_results_valid = reduce(
                    operator.mul, [evaluator_result.is_valid for evaluator_result in evaluator_results]
                )
                all_evaluator_results_valid_indices = np.nonzero(all_evaluator_results_valid.values)[0]
                all_evaluator_results_valid_indices_period_shifted = [
                    axis_indices + timestep_index for axis_indices in all_evaluator_results_valid_indices
                ]

                # Remove already valid indices, so we don't overwrite priority used with the latest valid
                new_valid_indices = [
                    i for i in all_evaluator_results_valid_indices_period_shifted if not is_valid.values[i]
                ]

                # Register the valid timesteps as valid and keep track of the operational setting used
                is_valid[new_valid_indices] = True
                priorities_used[new_valid_indices] = priority_name

                if all(is_valid.values):
                    # quit as soon as all time-steps are valid. This means that we do not need to test all settings.
                    break
        return PriorityOptimizerResult(
            priorities_used=priorities_used,
            priority_results=self.collect_consumer_results(
                priorities_used=priorities_used, priority_results=priority_results
            ),
        )
