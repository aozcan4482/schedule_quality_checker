from datetime import date
from rdflib import Graph, URIRef
from graph.models import Activity, Project, Relationship, programme_to_graph
from graph.metrics import evaluate_checks_6_to_11_and_bei
from graph.validator import DEFAULT_SHAPES_PATH, load_check_definitions, load_shapes_graph, validate_programme_graph
from graph.vocabulary import PREDECESSOR, SCHED, SUCCESSOR


def test_relationship_links_emit_activity_uris_for_check1_compatibility():
    project = Project(
        name="URI Alignment Project",
        data_date=date(2026, 11, 1),
        activities=[
            Activity(id="A1", name="Start Task", status="Not Started", duration=5, resource="Crew"),
            Activity(id="A2", name="Next Task", status="In Progress", duration=5, resource="Crew"),
        ],
        relationships=[
            Relationship(predecessor="A1", successor="A2", relationship_type="FS", lag=0.0),
        ],
    )
    g = programme_to_graph(project)
    rel_uri = URIRef(f"{SCHED}relationship_1")
    assert g.value(rel_uri, PREDECESSOR) == URIRef(f"{SCHED}activity_A1")
    assert g.value(rel_uri, SUCCESSOR) == URIRef(f"{SCHED}activity_A2")


def test_project_level_data_date_turtle_compatibility():
    ttl_programme = """
    @prefix sched: <http://example.org/schedule#> .
    @prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .

    sched:project_main a sched:Project ;
        sched:projectName "External Turtle Programme" ;
        sched:dataDate "2026-11-01"^^xsd:date .

    sched:activity_T1 a sched:Activity ;
        sched:activityId "T1" ;
        sched:activityName "Completed Work" ;
        sched:activityType "Task" ;
        sched:status "Completed" ;
        sched:duration 10.0 ;
        sched:actualFinish "2026-10-20"^^xsd:date ;
        sched:baselineFinish "2026-10-25"^^xsd:date ;
        sched:totalFloat 0.0 ;
        sched:resource "Team 1" .

    sched:activity_T2 a sched:Activity ;
        sched:activityId "T2" ;
        sched:activityName "Delayed Work" ;
        sched:activityType "Task" ;
        sched:status "Not Started" ;
        sched:duration 50.0 ;
        sched:start "2026-10-25"^^xsd:date ;
        sched:finish "2026-12-20"^^xsd:date ;
        sched:baselineFinish "2026-10-28"^^xsd:date ;
        sched:totalFloat 60.0 .
    """
    data_graph = Graph().parse(data=ttl_programme, format="turtle")
    findings = validate_programme_graph(data_graph, DEFAULT_SHAPES_PATH)
    results = evaluate_checks_6_to_11_and_bei(data_graph)

    assert results[6].offending_count == 1
    assert results[8].offending_count == 1
    assert results[9].offending_count == 1
    assert results[10].offending_count == 1
    assert results[11].offending_count == 1
    for check_num in (6, 7, 8, 9, 10, 11):
        unique_shacl_targets = {f.target_id for f in findings if f.check_number == check_num}
        assert len(unique_shacl_targets) == results[check_num].offending_count


def test_check_metadata_definitions_cover_all_assigned_checks():
    shapes_graph = load_shapes_graph(DEFAULT_SHAPES_PATH)
    checks = load_check_definitions(shapes_graph)
    assert [c.number for c in checks] == [6, 7, 8, 9, 10, 11, 14]
    assert all(c.counting_rule for c in checks)
