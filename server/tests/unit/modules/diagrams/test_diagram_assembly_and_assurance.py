import asyncio

from app.modules.diagrams.contracts.provenance import SourceSpan
from app.modules.diagrams.contracts.requirements import RequirementFrame
from app.modules.diagrams.contracts.results import PipelineVersions, RawDiagram
from app.modules.diagrams.diagram_assembly import DiagramAssembler, DiagramAssemblySettings
from app.modules.diagrams.diagram_assurance import DiagramAssuranceService
from app.modules.diagrams.enums import ActorType, RelationType
from app.modules.diagrams.requirement_graph import RequirementGraphBuilder
from app.modules.diagrams.schemas import Actor, Diagram, DiagramRelation, DiagramSystem, UseCase


DESCRIPTION = "Customer books a service."
SPAN = SourceSpan(start_offset=0, end_offset=len(DESCRIPTION), text=DESCRIPTION, origin="extracted")
VERSIONS = PipelineVersions(
    frame_extraction_prompt="1.0", defect_rules="1.0", assurance_rules="1.0"
)


def test_assembler_deterministically_builds_actors_use_cases_and_associations() -> None:
    graph = asyncio.run(
        RequirementGraphBuilder().build(
            [
                _frame("f2", actor="Customer", action="books", object_name="service"),
                _frame("f1", actor="Customer", action="books", object_name="service"),
            ]
        )
    )

    diagram = DiagramAssembler(DiagramAssemblySettings(system_name="Booking system")).assemble(
        graph
    )

    assert diagram.system.name == "Booking system"
    assert [(actor.name, actor.origin) for actor in diagram.actors] == [("Customer", "extracted")]
    assert [(use_case.name, use_case.origin) for use_case in diagram.use_cases] == [
        ("books service", "extracted")
    ]
    assert [
        (relation.type, relation.source_id, relation.target_id) for relation in diagram.relations
    ] == [(RelationType.ASSOCIATION, diagram.actors[0].id, diagram.use_cases[0].id)]


def test_assembler_keeps_each_action_object_pair() -> None:
    graph = asyncio.run(
        RequirementGraphBuilder().build(
            [
                _frame("f1", actor="Customer", action="books", object_name="service"),
                _frame("f2", actor="Customer", action="books", object_name="consultation"),
            ]
        )
    )

    diagram = DiagramAssembler().assemble(graph)

    assert {item.name for item in diagram.use_cases} == {
        "books service",
        "books consultation",
        "books",
    }
    assert len([item for item in diagram.relations if item.type is RelationType.ASSOCIATION]) == 2


def test_assembler_creates_include_for_an_action_shared_by_distinct_objects() -> None:
    graph = asyncio.run(
        RequirementGraphBuilder().build(
            [
                _frame("f1", actor="Customer", action="books", object_name="service"),
                _frame("f2", actor="Customer", action="books", object_name="consultation"),
            ]
        )
    )

    diagram = DiagramAssembler().assemble(graph)

    shared = next(item for item in diagram.use_cases if item.name == "books")
    includes = [item for item in diagram.relations if item.type is RelationType.INCLUDE]
    assert len(includes) == 2
    assert {item.target_id for item in includes} == {shared.id}


def test_assembler_creates_extend_for_one_conditional_sibling_use_case() -> None:
    graph = asyncio.run(
        RequirementGraphBuilder().build(
            [
                _frame("f1", actor="Customer", action="books", object_name="service"),
                _frame(
                    "f2",
                    actor="Customer",
                    action="cancels",
                    object_name="service",
                    condition="when the booking exists",
                ),
            ]
        )
    )

    diagram = DiagramAssembler().assemble(graph)

    extend = next(item for item in diagram.relations if item.type is RelationType.EXTEND)
    assert extend.source_id == next(
        item.id for item in diagram.use_cases if item.name == "cancels service"
    )
    assert extend.target_id == next(
        item.id for item in diagram.use_cases if item.name == "books service"
    )


def test_assurance_corrects_formal_rules_but_never_deletes_unverified_elements() -> None:
    diagram = _diagram(
        actors=[_actor("verified"), _actor("unverified", origin="unverified", spans=[])],
        use_cases=[
            _use_case("goal", "Book service"),
            _use_case("duplicate", " book service "),
            _use_case("orphan", "Cancel service"),
            _use_case("unverified-goal", "Select plan", origin="unverified", spans=[]),
        ],
        relations=[
            _relation(RelationType.ASSOCIATION, "verified", "goal"),
            _relation(RelationType.ASSOCIATION, "missing", "goal"),
            _relation(RelationType.INCLUDE, "goal", "duplicate"),
            _relation(RelationType.INCLUDE, "duplicate", "goal"),
            _relation(RelationType.EXTEND, "goal", "goal"),
            _relation(
                RelationType.ASSOCIATION,
                "unverified",
                "unverified-goal",
                origin="unverified",
                spans=[],
            ),
        ],
    )

    result = DiagramAssuranceService().assure(_raw(diagram), DESCRIPTION)

    assert [item.id for item in result.final.diagram.use_cases] == ["goal", "unverified-goal"]
    assert [item.id for item in result.final.diagram.actors] == ["verified", "unverified"]
    assert (
        len([item for item in result.final.diagram.relations if item.type is RelationType.INCLUDE])
        == 1
    )
    assert {fix.rule for fix in result.report.automatic_fixes} >= {
        "invalid_relation",
        "include_cycle",
        "duplicate_name",
        "use_case_without_actor",
    }
    assert {warning.rule for warning in result.report.assurance_warnings} >= {"action_step"}
    assert {item.element_id for item in result.report.unverified_elements} >= {
        "unverified",
        "unverified-goal",
    }
    assert result.raw.diagram == diagram


def test_assurance_marks_crud_and_scenario_steps_without_merging_them() -> None:
    diagram = _diagram(
        actors=[_actor("customer")],
        use_cases=[_use_case("create", "Create account"), _use_case("select", "Select plan")],
        relations=[
            _relation(RelationType.ASSOCIATION, "customer", "create"),
            _relation(RelationType.ASSOCIATION, "customer", "select"),
        ],
    )

    result = DiagramAssuranceService().assure(_raw(diagram), DESCRIPTION)

    assert [item.id for item in result.final.diagram.use_cases] == ["create", "select"]
    assert {warning.rule for warning in result.report.assurance_warnings} == {
        "excessive_crud",
        "action_step",
    }


def _raw(diagram: Diagram) -> RawDiagram:
    return RawDiagram(diagram=diagram, pipeline_versions=VERSIONS)


def _diagram(
    *, actors: list[Actor], use_cases: list[UseCase], relations: list[DiagramRelation]
) -> Diagram:
    return Diagram(
        schema_version="1.0",
        system=DiagramSystem(id="system", name="System", spans=[SPAN], origin="extracted"),
        actors=actors,
        use_cases=use_cases,
        relations=relations,
        assumptions=[],
        warnings=[],
    )


def _actor(
    identifier: str, *, origin: str = "extracted", spans: list[SourceSpan] | None = None
) -> Actor:
    return Actor(
        id=identifier,
        name=identifier.title(),
        type=ActorType.PRIMARY,
        origin=origin,
        spans=[SPAN] if spans is None else spans,
    )


def _use_case(
    identifier: str, name: str, *, origin: str = "extracted", spans: list[SourceSpan] | None = None
) -> UseCase:
    return UseCase(
        id=identifier, name=name, origin=origin, spans=[SPAN] if spans is None else spans
    )


def _relation(
    relation_type: RelationType,
    source_id: str,
    target_id: str,
    *,
    origin: str = "extracted",
    spans: list[SourceSpan] | None = None,
) -> DiagramRelation:
    return DiagramRelation(
        type=relation_type,
        source_id=source_id,
        target_id=target_id,
        origin=origin,
        spans=[SPAN] if spans is None else spans,
    )


def _frame(
    identifier: str,
    *,
    actor: str,
    action: str,
    object_name: str,
    condition: str | None = None,
) -> RequirementFrame:
    return RequirementFrame(
        id=identifier,
        actor=actor,
        action=action,
        object=object_name,
        condition=condition,
        spans=[SPAN],
        origin="extracted",
    )
