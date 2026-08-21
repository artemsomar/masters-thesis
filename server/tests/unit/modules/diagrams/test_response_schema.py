import pytest

from app.modules.diagrams.schemas import DiagramGenerationOutput


@pytest.mark.unit
def test_diagram_generation_schema_uses_one_relation_object_shape() -> None:
    schema = DiagramGenerationOutput.model_json_schema()
    relation_items = schema["properties"]["relations"]["items"]
    relation = schema["$defs"]["DiagramRelation"]

    assert relation_items == {"$ref": "#/$defs/DiagramRelation"}
    assert relation["properties"]["type"]["$ref"] == "#/$defs/RelationType"
    assert "schema_version" not in schema["properties"]
