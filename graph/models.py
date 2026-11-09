from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from rdflib import Graph, Literal, RDF, URIRef, XSD
from graph.vocabulary import (
    ACTIVITY,
    ACTIVITY_ID,
    ACTIVITY_NAME,
    ACTIVITY_TYPE,
    ACTUAL_FINISH,
    ACTUAL_START,
    BASELINE_FINISH,
    CONSTRAINT_TYPE,
    DATA_DATE,
    DURATION,
    FINISH_DATE,
    INCOMPLETE_ACTIVITY,
    LAG,
    POSITIVE_DURATION_ACTIVITY,
    PREDECESSOR,
    PROJECT,
    PROJECT_NAME,
    RELATIONSHIP,
    RELATIONSHIP_TYPE,
    RESOURCE,
    SCHED,
    START_DATE,
    STATUS,
    SUCCESSOR,
    TOTAL_FLOAT,
)


@dataclass
class Activity:
    id: str
    name: str
    activity_type: str = "Task"
    status: str = "Incomplete"
    duration: float = 0.0
    start: Optional[date] = None
    finish: Optional[date] = None
    actual_start: Optional[date] = None
    actual_finish: Optional[date] = None
    total_float: Optional[float] = None
    constraint_type: Optional[str] = None
    baseline_finish: Optional[date] = None
    resource: Optional[str] = None


@dataclass
class Relationship:
    predecessor: str
    successor: str
    relationship_type: str = "FS"
    lag: float = 0.0


@dataclass
class Project:
    name: str
    data_date: date
    activities: list[Activity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)


@dataclass
class Check:
    number: int
    name: str
    threshold: float
    counting_rule: str


@dataclass
class CheckResult:
    check_number: int
    check_name: str
    measured_value: Optional[float]
    threshold: float
    status: str
    offending_count: int = 0
    total_applicable: int = 0


@dataclass
class Finding:
    check_number: int
    target_id: str
    measured_value: Optional[str]
    message: str


@dataclass
class AuditReport:
    project: Project
    check_results: dict[int, CheckResult] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)


def programme_to_graph(project: Project) -> Graph:
    graph = Graph()
    graph.bind("sched", SCHED)

    project_uri = URIRef(f"{SCHED}project_main")
    graph.add((project_uri, RDF.type, PROJECT))
    graph.add((project_uri, PROJECT_NAME, Literal(project.name, datatype=XSD.string)))
    graph.add((project_uri, DATA_DATE, Literal(project.data_date, datatype=XSD.date)))

    for act in project.activities:
        act_uri = URIRef(f"{SCHED}activity_{act.id}")
        graph.add((act_uri, RDF.type, ACTIVITY))
        graph.add((act_uri, ACTIVITY_ID, Literal(act.id, datatype=XSD.string)))
        graph.add((act_uri, ACTIVITY_NAME, Literal(act.name, datatype=XSD.string)))
        graph.add((act_uri, ACTIVITY_TYPE, Literal(act.activity_type, datatype=XSD.string)))
        graph.add((act_uri, STATUS, Literal(act.status, datatype=XSD.string)))
        graph.add((act_uri, DURATION, Literal(float(act.duration), datatype=XSD.decimal)))
        graph.add((act_uri, DATA_DATE, Literal(project.data_date, datatype=XSD.date)))

        is_incomplete = act.status.strip().lower() != "complete"
        if is_incomplete:
            graph.add((act_uri, RDF.type, INCOMPLETE_ACTIVITY))
            if act.duration > 0 and act.activity_type.strip().lower() not in ("milestone", "summary"):
                graph.add((act_uri, RDF.type, POSITIVE_DURATION_ACTIVITY))

        if act.total_float is not None:
            graph.add((act_uri, TOTAL_FLOAT, Literal(float(act.total_float), datatype=XSD.decimal)))
        if act.start is not None:
            graph.add((act_uri, START_DATE, Literal(act.start, datatype=XSD.date)))
        if act.finish is not None:
            graph.add((act_uri, FINISH_DATE, Literal(act.finish, datatype=XSD.date)))
        if act.actual_start is not None:
            graph.add((act_uri, ACTUAL_START, Literal(act.actual_start, datatype=XSD.date)))
        if act.actual_finish is not None:
            graph.add((act_uri, ACTUAL_FINISH, Literal(act.actual_finish, datatype=XSD.date)))
        if act.baseline_finish is not None:
            graph.add((act_uri, BASELINE_FINISH, Literal(act.baseline_finish, datatype=XSD.date)))
        if act.constraint_type is not None and act.constraint_type.strip():
            graph.add((act_uri, CONSTRAINT_TYPE, Literal(act.constraint_type.strip(), datatype=XSD.string)))
        if act.resource is not None and act.resource.strip():
            graph.add((act_uri, RESOURCE, Literal(act.resource.strip(), datatype=XSD.string)))

    for idx, rel in enumerate(project.relationships, start=1):
        rel_uri = URIRef(f"{SCHED}relationship_{idx}")
        graph.add((rel_uri, RDF.type, RELATIONSHIP))
        graph.add((rel_uri, PREDECESSOR, Literal(rel.predecessor, datatype=XSD.string)))
        graph.add((rel_uri, SUCCESSOR, Literal(rel.successor, datatype=XSD.string)))
        graph.add((rel_uri, RELATIONSHIP_TYPE, Literal(rel.relationship_type, datatype=XSD.string)))
        graph.add((rel_uri, LAG, Literal(float(rel.lag), datatype=XSD.decimal)))

    return graph
