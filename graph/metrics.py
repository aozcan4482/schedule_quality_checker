from typing import Optional
from rdflib import Graph
from graph.models import CheckResult


PASS = "Pass"
FAIL = "Fail"
NOT_APPLICABLE = "Not Applicable"


def _query_single_int(graph: Graph, sparql: str) -> int:
    for row in graph.query(sparql):
        return int(row[0])
    return 0


def _decide(value: Optional[float], threshold: float, comparison: str) -> str:
    if value is None:
        return NOT_APPLICABLE
    if comparison == "<=":
        return PASS if value <= threshold else FAIL
    if comparison == ">=":
        return PASS if value >= threshold else FAIL
    raise ValueError(f"Unsupported comparison operator: {comparison!r}")


def calculate_check_6_high_float(
    graph: Graph,
    max_float: float = 44.0,
    threshold_percent: float = 5.0,
) -> CheckResult:
    total_query = """
    PREFIX sched: <http://example.org/schedule#>
    SELECT (COUNT(DISTINCT ?act) AS ?total)
    WHERE {
        ?act a sched:Activity ;
             sched:activityType ?type ;
             sched:status ?status .
        FILTER (LCASE(STR(?type)) = "task")
        FILTER (LCASE(STR(?status)) NOT IN ("complete", "completed"))
    }
    """
    offending_query = f"""
    PREFIX sched: <http://example.org/schedule#>
    SELECT (COUNT(DISTINCT ?act) AS ?offending)
    WHERE {{
        ?act a sched:Activity ;
             sched:activityType ?type ;
             sched:status ?status ;
             sched:totalFloat ?tf .
        FILTER (LCASE(STR(?type)) = "task")
        FILTER (LCASE(STR(?status)) NOT IN ("complete", "completed"))
        FILTER (?tf > {float(max_float)})
    }}
    """
    total = _query_single_int(graph, total_query)
    offending = _query_single_int(graph, offending_query)
    if total == 0:
        return CheckResult(6, "High Float", None, threshold_percent, NOT_APPLICABLE, 0, 0, "<=")
    percent = offending * 100.0 / total
    status = _decide(percent, threshold_percent, "<=")
    return CheckResult(6, "High Float", percent, threshold_percent, status, offending, total, "<=")


def calculate_check_7_negative_float(
    graph: Graph,
    threshold_percent: float = 0.0,
) -> CheckResult:
    total_query = """
    PREFIX sched: <http://example.org/schedule#>
    SELECT (COUNT(DISTINCT ?act) AS ?total)
    WHERE {
        ?act a sched:Activity ;
             sched:activityType ?type ;
             sched:status ?status .
        FILTER (LCASE(STR(?type)) = "task")
        FILTER (LCASE(STR(?status)) NOT IN ("complete", "completed"))
    }
    """
    offending_query = """
    PREFIX sched: <http://example.org/schedule#>
    SELECT (COUNT(DISTINCT ?act) AS ?offending)
    WHERE {
        ?act a sched:Activity ;
             sched:activityType ?type ;
             sched:status ?status ;
             sched:totalFloat ?tf .
        FILTER (LCASE(STR(?type)) = "task")
        FILTER (LCASE(STR(?status)) NOT IN ("complete", "completed"))
        FILTER (?tf < 0)
    }
    """
    total = _query_single_int(graph, total_query)
    offending = _query_single_int(graph, offending_query)
    if total == 0:
        return CheckResult(7, "Negative Float", None, threshold_percent, NOT_APPLICABLE, 0, 0, "<=")
    percent = offending * 100.0 / total
    status = _decide(percent, threshold_percent, "<=")
    return CheckResult(7, "Negative Float", percent, threshold_percent, status, offending, total, "<=")


def calculate_check_8_high_duration(
    graph: Graph,
    max_duration: float = 44.0,
    threshold_percent: float = 5.0,
) -> CheckResult:
    total_query = """
    PREFIX sched: <http://example.org/schedule#>
    SELECT (COUNT(DISTINCT ?act) AS ?total)
    WHERE {
        ?act a sched:Activity ;
             sched:activityType ?type ;
             sched:status ?status .
        FILTER (LCASE(STR(?type)) = "task")
        FILTER (LCASE(STR(?status)) NOT IN ("complete", "completed"))
    }
    """
    offending_query = f"""
    PREFIX sched: <http://example.org/schedule#>
    SELECT (COUNT(DISTINCT ?act) AS ?offending)
    WHERE {{
        ?act a sched:Activity ;
             sched:activityType ?type ;
             sched:status ?status ;
             sched:duration ?dur .
        FILTER (LCASE(STR(?type)) = "task")
        FILTER (LCASE(STR(?status)) NOT IN ("complete", "completed"))
        FILTER (?dur > {float(max_duration)})
    }}
    """
    total = _query_single_int(graph, total_query)
    offending = _query_single_int(graph, offending_query)
    if total == 0:
        return CheckResult(8, "High Duration", None, threshold_percent, NOT_APPLICABLE, 0, 0, "<=")
    percent = offending * 100.0 / total
    status = _decide(percent, threshold_percent, "<=")
    return CheckResult(8, "High Duration", percent, threshold_percent, status, offending, total, "<=")


def calculate_check_9_invalid_dates(
    graph: Graph,
    threshold_percent: float = 0.0,
) -> CheckResult:
    total_query = """
    PREFIX sched: <http://example.org/schedule#>
    SELECT (COUNT(DISTINCT ?act) AS ?total)
    WHERE {
        ?act a sched:Activity .
    }
    """
    offending_query = """
    PREFIX sched: <http://example.org/schedule#>
    SELECT (COUNT(DISTINCT ?act) AS ?offending)
    WHERE {
        ?act a sched:Activity .
        OPTIONAL { ?act sched:dataDate ?actDD }
        OPTIONAL {
            ?proj a sched:Project ;
                  sched:dataDate ?projDD .
        }
        BIND (COALESCE(?actDD, ?projDD) AS ?dataDate)
        FILTER (BOUND(?dataDate))
        {
            ?act sched:status ?status ;
                 sched:start ?value .
            FILTER (LCASE(STR(?status)) NOT IN ("complete", "completed"))
            BIND ("before" AS ?mode)
        }
        UNION
        {
            ?act sched:status ?status ;
                 sched:finish ?value .
            FILTER (LCASE(STR(?status)) NOT IN ("complete", "completed"))
            BIND ("before" AS ?mode)
        }
        UNION
        {
            ?act sched:actualStart ?value .
            BIND ("after" AS ?mode)
        }
        UNION
        {
            ?act sched:actualFinish ?value .
            BIND ("after" AS ?mode)
        }
        FILTER (
            (?mode = "before" && ?value < ?dataDate)
            || (?mode = "after" && ?value > ?dataDate)
        )
    }
    """
    total = _query_single_int(graph, total_query)
    offending = _query_single_int(graph, offending_query)
    if total == 0:
        return CheckResult(9, "Invalid Dates", None, threshold_percent, NOT_APPLICABLE, 0, 0, "<=")
    percent = offending * 100.0 / total
    status = _decide(percent, threshold_percent, "<=")
    return CheckResult(9, "Invalid Dates", percent, threshold_percent, status, offending, total, "<=")


def calculate_check_10_resources(
    graph: Graph,
    threshold_percent: float = 0.0,
) -> CheckResult:
    total_query = """
    PREFIX sched: <http://example.org/schedule#>
    SELECT (COUNT(DISTINCT ?act) AS ?total)
    WHERE {
        ?act a sched:Activity ;
             sched:activityType ?type ;
             sched:status ?status ;
             sched:duration ?dur .
        FILTER (LCASE(STR(?type)) = "task")
        FILTER (LCASE(STR(?status)) NOT IN ("complete", "completed"))
        FILTER (?dur > 0)
    }
    """
    offending_query = """
    PREFIX sched: <http://example.org/schedule#>
    SELECT (COUNT(DISTINCT ?act) AS ?offending)
    WHERE {
        ?act a sched:Activity ;
             sched:activityType ?type ;
             sched:status ?status ;
             sched:duration ?dur .
        FILTER (LCASE(STR(?type)) = "task")
        FILTER (LCASE(STR(?status)) NOT IN ("complete", "completed"))
        FILTER (?dur > 0)
        FILTER NOT EXISTS {
            ?act sched:resource ?res .
            FILTER (STRLEN(STR(?res)) > 0)
        }
    }
    """
    total = _query_single_int(graph, total_query)
    offending = _query_single_int(graph, offending_query)
    if total == 0:
        return CheckResult(10, "Resources", None, threshold_percent, NOT_APPLICABLE, 0, 0, "<=")
    percent = offending * 100.0 / total
    status = _decide(percent, threshold_percent, "<=")
    return CheckResult(10, "Resources", percent, threshold_percent, status, offending, total, "<=")


def calculate_check_11_missed_activities(
    graph: Graph,
    threshold_percent: float = 5.0,
) -> CheckResult:
    baseline_presence_query = """
    PREFIX sched: <http://example.org/schedule#>
    SELECT (COUNT(?act) AS ?cnt)
    WHERE {
        ?act a sched:Activity ;
             sched:baselineFinish ?bf .
    }
    """
    if _query_single_int(graph, baseline_presence_query) == 0:
        return CheckResult(11, "Missed Activities", None, threshold_percent, NOT_APPLICABLE, 0, 0, "<=")

    total_planned_query = """
    PREFIX sched: <http://example.org/schedule#>
    SELECT (COUNT(DISTINCT ?act) AS ?total)
    WHERE {
        ?act a sched:Activity ;
             sched:baselineFinish ?baselineFinish .
        OPTIONAL { ?act sched:dataDate ?actDD }
        OPTIONAL {
            ?proj a sched:Project ;
                  sched:dataDate ?projDD .
        }
        BIND (COALESCE(?actDD, ?projDD) AS ?dataDate)
        FILTER (BOUND(?dataDate))
        FILTER (?baselineFinish <= ?dataDate)
    }
    """
    offending_query = """
    PREFIX sched: <http://example.org/schedule#>
    SELECT (COUNT(DISTINCT ?act) AS ?offending)
    WHERE {
        ?act a sched:Activity ;
             sched:baselineFinish ?baselineFinish ;
             sched:status ?status .
        OPTIONAL { ?act sched:dataDate ?actDD }
        OPTIONAL {
            ?proj a sched:Project ;
                  sched:dataDate ?projDD .
        }
        BIND (COALESCE(?actDD, ?projDD) AS ?dataDate)
        FILTER (BOUND(?dataDate))
        FILTER (?baselineFinish <= ?dataDate)
        OPTIONAL { ?act sched:actualFinish ?actualFinish }
        OPTIONAL { ?act sched:finish ?finish }
        FILTER (
            LCASE(STR(?status)) NOT IN ("complete", "completed")
            || (BOUND(?actualFinish) && ?actualFinish > ?baselineFinish)
            || (BOUND(?finish) && ?finish > ?baselineFinish)
        )
    }
    """
    total_planned = _query_single_int(graph, total_planned_query)
    offending = _query_single_int(graph, offending_query)
    if total_planned == 0:
        return CheckResult(11, "Missed Activities", 0.0, threshold_percent, PASS, 0, 0, "<=")
    percent = offending * 100.0 / total_planned
    status = _decide(percent, threshold_percent, "<=")
    return CheckResult(11, "Missed Activities", percent, threshold_percent, status, offending, total_planned, "<=")


def calculate_check_14_bei(
    graph: Graph,
    min_bei: float = 0.95,
) -> CheckResult:
    baseline_presence_query = """
    PREFIX sched: <http://example.org/schedule#>
    SELECT (COUNT(?act) AS ?cnt)
    WHERE {
        ?act a sched:Activity ;
             sched:baselineFinish ?bf .
    }
    """
    if _query_single_int(graph, baseline_presence_query) == 0:
        return CheckResult(14, "Baseline Execution Index (BEI)", None, min_bei, NOT_APPLICABLE, 0, 0, ">=")

    planned_query = """
    PREFIX sched: <http://example.org/schedule#>
    SELECT (COUNT(DISTINCT ?act) AS ?planned)
    WHERE {
        ?act a sched:Activity ;
             sched:baselineFinish ?baselineFinish .
        OPTIONAL { ?act sched:dataDate ?actDD }
        OPTIONAL {
            ?proj a sched:Project ;
                  sched:dataDate ?projDD .
        }
        BIND (COALESCE(?actDD, ?projDD) AS ?dataDate)
        FILTER (BOUND(?dataDate))
        FILTER (?baselineFinish <= ?dataDate)
    }
    """
    completed_query = """
    PREFIX sched: <http://example.org/schedule#>
    SELECT (COUNT(DISTINCT ?act) AS ?completed)
    WHERE {
        ?act a sched:Activity ;
             sched:status ?status .
        FILTER (LCASE(STR(?status)) IN ("complete", "completed"))
    }
    """
    planned = _query_single_int(graph, planned_query)
    completed = _query_single_int(graph, completed_query)
    if planned == 0:
        return CheckResult(14, "Baseline Execution Index (BEI)", None, min_bei, NOT_APPLICABLE, 0, 0, ">=")
    bei = completed / planned
    status = _decide(bei, min_bei, ">=")
    offending = max(0, planned - completed)
    return CheckResult(14, "Baseline Execution Index (BEI)", bei, min_bei, status, offending, planned, ">=")


def evaluate_checks_6_to_11_and_bei(
    graph: Graph,
    max_float: float = 44.0,
    max_duration: float = 44.0,
    thresholds: Optional[dict[int, float]] = None,
) -> dict[int, CheckResult]:
    t = thresholds or {}
    return {
        6: calculate_check_6_high_float(graph, max_float=max_float, threshold_percent=t.get(6, 5.0)),
        7: calculate_check_7_negative_float(graph, threshold_percent=t.get(7, 0.0)),
        8: calculate_check_8_high_duration(graph, max_duration=max_duration, threshold_percent=t.get(8, 5.0)),
        9: calculate_check_9_invalid_dates(graph, threshold_percent=t.get(9, 0.0)),
        10: calculate_check_10_resources(graph, threshold_percent=t.get(10, 0.0)),
        11: calculate_check_11_missed_activities(graph, threshold_percent=t.get(11, 5.0)),
        14: calculate_check_14_bei(graph, min_bei=t.get(14, 0.95)),
    }
