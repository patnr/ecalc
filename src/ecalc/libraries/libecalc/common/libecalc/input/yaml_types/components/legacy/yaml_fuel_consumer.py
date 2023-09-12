from typing import Any, Dict, Type

from libecalc.dto.base import ConsumerUserDefinedCategoryType
from libecalc.input.yaml_types import YamlBase
from libecalc.input.yaml_types.components.category import CategoryField
from libecalc.input.yaml_types.placeholder_type import PlaceholderType
from libecalc.input.yaml_types.schema_helpers import (
    replace_temporal_placeholder_property_with_legacy_ref,
)
from libecalc.input.yaml_types.temporal_model import TemporalModel
from pydantic import Field


class YamlFuelConsumer(YamlBase):
    class Config:
        title = "FUEL_CONSUMER"

        @staticmethod
        def schema_extra(schema: Dict[str, Any], model: Type["YamlFuelConsumer"]) -> None:
            replace_temporal_placeholder_property_with_legacy_ref(
                schema=schema,
                property_key="ENERGY_USAGE_MODEL",
                property_ref="$SERVER_NAME/api/v1/schema-validation/energy-usage-model.json#properties/ENERGY_USAGE_MODEL",
            )

    name: str = Field(
        ...,
        title="NAME",
        description="Name of the consumer.\n\n$ECALC_DOCS_KEYWORDS_URL/NAME",
    )
    category: ConsumerUserDefinedCategoryType = CategoryField(...)
    energy_usage_model: TemporalModel[PlaceholderType] = Field(
        ...,
        title="ENERGY_USAGE_MODEL",
        description="Definition of the energy usage model for the consumer."
        "\n\n$ECALC_DOCS_KEYWORDS_URL/ENERGY_USAGE_MODEL",
    )

    fuel: TemporalModel[str] = Field(
        None,
        title="FUEL",
        description="The fuel used by the consumer." "\n\n$ECALC_DOCS_KEYWORDS_URL/FUEL",
    )
