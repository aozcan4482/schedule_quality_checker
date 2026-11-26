from pathlib import Path
from typing import Iterable, Optional
from pyshacl import validate
from rdflib import Graph, Namespace, URIRef
from graph.models import AuditReport, Check, Finding, Project, programme_to_graph
from graph.metrics import evaluate_checks_6_to_11_and_bei
from graph.vocabulary import ACTIVITY_ID, SCHED

SH = Namespace("http://www.w3.org/ns/shacl#")

DEFAULT_SHAPES_PATH = Path(__file__).resolve().parent.parent / "shapes" / "float_date_resource_shapes.ttl"

SHAPE_TO_CHECK_NUMBER = {
    str(SCHED.Check1_LogicShape): 1,
    str(SCHED.Check2_LeadsShape): 2,
    str(SCHED.Check3_LagsShape): 3,
    str(SCHED.Check4_RelationshipTypesShape): 4,
    str(SCHED.Check5_HardConstraintsShape): 5,
    str(SCHED.Check6_HighFloatShape): 6,
    str(SCHED.Check7_NegativeFloatShape): 7,
    str(SCHED.Check8_HighDurationShape): 8,
    str(SCHED.Check9_InvalidDatesShape): 9,
    str(SCHED.Check10_ResourceShape): 10,
    str(SCHED.Check11_MissedActivityShape): 11,
}


def load_shapes_graph(shapes_paths: Optional[str | Path | Iterable[str | Path]] = None) -> Graph:
    shapes_graph = Graph()
    if shapes_paths is None:
        paths: list[Path] = [DEFAULT_SHAPES_PATH]
    elif isinstance(shapes_paths, (str, Path)):
        paths = [Path(shapes_paths)]
    else:
        paths = [Path(p) for p in shapes_paths]

    for path in paths:
        shapes_graph.parse(str(path), format="turtle")
    return shapes_graph


def load_check_definitions(shapes_graph: Graph) -> list[Check]:
    query = """
    PREFIX sched: <http://example.org/schedule#>
    SELECT ?num ?name ?tp ?ti ?rule WHERE {
        ?c a sched:Check ;
           sched:checkNumber ?num ;
           sched:checkName ?name .
        OPTIONAL { ?c sched:thresholdPercent ?tp }
        OPTIONAL { ?c sched:thresholdIndex ?ti }
        OPTIONAL { ?c sched:countingRule ?rule }
    }
    ORDER BY ?num
    """
    checks: list[Check] = []
    for row in shapes_graph.query(query):
        threshold = float(row.tp) if row.tp is not None else (float(row.ti) if row.ti is not None else 0.0)
        rule = str(row.rule) if row.rule is not None else ""
        checks.append(Check(number=int(row.num), name=str(row.name), threshold=threshold, counting_rule=rule))
    return checks


def load_ratio_thresholds(shapes_graph: Graph) -> dict[int, float]:
    return {c.number: c.threshold for c in load_check_definitions(shapes_graph)}


def get_shape_threshold(
    shapes_graph: Graph,
    shape_uri: URIRef,
    constraint_predicate: URIRef = SH.maxInclusive,
    default_value: float = 44.0,
) -> float:
    query = f"""
    PREFIX sh: <http://www.w3.org/ns/shacl#>
    SELECT ?val
    WHERE {{
        <{shape_uri}> sh:property ?prop .
        ?prop <{constraint_predicate}> ?val .
    }}
    """
    for row in shapes_graph.query(query):
        return float(row[0])
    return default_value


def _resolve_check_number(results_graph: Graph, result_node, source_shape) -> int:
    shape_str = str(source_shape)
    if shape_str in SHAPE_TO_CHECK_NUMBER:
        return SHAPE_TO_CHECK_NUMBER[shape_str]

    for parent_shape, _, _ in results_graph.triples((None, SH.property, source_shape)):
        parent_str = str(parent_shape)
        if parent_str in SHAPE_TO_CHECK_NUMBER:
            return SHAPE_TO_CHECK_NUMBER[parent_str]

    local_name = shape_str.split("#")[-1]
    if local_name.startswith("Check"):
        digits = ""
        for ch in local_name[len("Check"):]:
            if ch.isdigit():
                digits += ch
            else:
                break
        if digits:
            return int(digits)

    msg_objs = list(results_graph.objects(result_node, SH.resultMessage))
    if msg_objs:
        msg = str(msg_objs[0])
        for num in range(14, 0, -1):
            if f"Check {num} " in msg or f"Check {num}(" in msg:
                return num
    return 0


def validate_programme_graph(
    data_graph: Graph,
    shapes_file_path: Optional[str | Path | Iterable[str | Path]] = None,
) -> list[Finding]:
    shapes_graph = load_shapes_graph(shapes_file_path)

    _, results_graph, _ = validate(
        data_graph=data_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        advanced=True,
    )

    combined_results = Graph()
    for triple in results_graph:
        combined_results.add(triple)
    for triple in shapes_graph:
        combined_results.add(triple)

    findings: list[Finding] = []
    for result_node in results_graph.subjects(predicate=SH.focusNode):
        focus_nodes = list(results_graph.objects(result_node, SH.focusNode))
        source_shapes = list(results_graph.objects(result_node, SH.sourceShape))
        messages = list(results_graph.objects(result_node, SH.resultMessage))
        values = list(results_graph.objects(result_node, SH.value))

        if not focus_nodes or not source_shapes:
            continue

        focus_node = focus_nodes[0]
        source_shape = source_shapes[0]
        message = str(messages[0]) if messages else ""
        measured_value = str(values[0]) if values else None

        act_ids = list(data_graph.objects(focus_node, ACTIVITY_ID))
        target_id = str(act_ids[0]) if act_ids else str(focus_node).split("#")[-1]
        if target_id.startswith("activity_"):
            target_id = target_id[len("activity_"):]
        check_num = _resolve_check_number(combined_results, result_node, source_shape)

        findings.append(
            Finding(
                check_number=check_num,
                target_id=target_id,
                measured_value=measured_value,
                message=message,
            )
        )

    findings.sort(key=lambda f: (f.check_number, f.target_id))
    return findings


def run_float_date_resource_audit(
    project: Project,
    shapes_file_path: Optional[str | Path | Iterable[str | Path]] = None,
) -> AuditReport:
    shapes_graph = load_shapes_graph(shapes_file_path)

    max_float = get_shape_threshold(shapes_graph, SCHED.Check6_HighFloatShape, SH.maxInclusive, 44.0)
    max_duration = get_shape_threshold(shapes_graph, SCHED.Check8_HighDurationShape, SH.maxInclusive, 44.0)
    ratio_thresholds = load_ratio_thresholds(shapes_graph)

    data_graph = programme_to_graph(project)
    findings = validate_programme_graph(data_graph, shapes_file_path)
    check_results = evaluate_checks_6_to_11_and_bei(
        data_graph,
        max_float=max_float,
        max_duration=max_duration,
        thresholds=ratio_thresholds,
    )

    return AuditReport(
        project=project,
        check_results=check_results,
        findings=findings,
    )
