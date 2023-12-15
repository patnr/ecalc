# from libecalc.presentation.yaml.yaml_types import YamlTemporalModel
from libecalc.presentation.yaml.yaml_types.yaml_temporal_model import YamlTemporalModel

try:
    from pydantic.v1 import schema_of
except ImportError:
    from pydantic import schema_of


class TestSchema:
    def test_temporal_model_schema(self):
        """
        Test to make sure temporal model creates the correct schema. We could improve TemporalModel to generate
        patternProperties, we would also need to change schema_helpers.replace_temporal_placeholder_property_with_legacy_ref
        """
        assert schema_of(YamlTemporalModel[str], title="TemporalModel") == {
            "title": "TemporalModel",
            "anyOf": [
                {
                    "type": "string",
                },
                {
                    "type": "object",
                    # "patternProperties": {
                    #     "^\\d{4}\\-(0?[1-9]|1[012])\\-(0?[1-9]|[12][0-9]|3[01])$": {"type": "string"}
                    # },
                    "additionalProperties": {"type": "string"},
                },
            ],
        }
