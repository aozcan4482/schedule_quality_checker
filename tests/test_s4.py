from datetime import date
from graph.models import Activity, Project, programme_to_graph
from graph.metrics import (
    NOT_APPLICABLE,
    calculate_check_6_high_float,
    calculate_check_7_negative_float,
    calculate_check_8_high_duration,
    calculate_check_9_invalid_dates,
    calculate_check_10_resources,
    calculate_check_11_missed_activities,
    calculate_check_14_bei,
)
from graph.validator import run_float_date_resource_audit


def test_s4_float_duration_date_resource_and_bei_checks():
    project = Project(
        name="Synthetic Programme S4",
        data_date=date(2026, 11, 1),
        activities=[
            Activity(
                id="A100",
                name="Site Mobilisation",
                status="Complete",
                duration=10,
                start=date(2026, 10, 1),
                finish=date(2026, 10, 12),
                actual_start=date(2026, 10, 1),
                actual_finish=date(2026, 10, 12),
                total_float=0,
                baseline_finish=date(2026, 10, 15),
                resource="Crew A",
            ),
            Activity(
                id="A101",
                name="Excavation",
                status="Incomplete",
                duration=20,
                start=date(2026, 11, 2),
                finish=date(2026, 11, 25),
                total_float=61,
                baseline_finish=date(2026, 11, 25),
                resource="Excavator Team",
            ),
            Activity(
                id="A102",
                name="Foundation Formwork",
                status="In Progress",
                duration=50,
                start=date(2026, 11, 5),
                finish=date(2026, 12, 30),
                total_float=-4,
                baseline_finish=date(2026, 12, 20),
                resource=None,
            ),
            Activity(
                id="A103",
                name="Substructure Concrete",
                status="Not Started",
                duration=15,
                start=date(2026, 10, 20),
                finish=date(2026, 11, 10),
                total_float=10,
                baseline_finish=date(2026, 10, 28),
                resource="Concrete Team",
            ),
            Activity(
                id="A104",
                name="Project Milestone",
                activity_type="Milestone",
                status="Not Started",
                duration=0,
                start=date(2026, 11, 2),
                finish=date(2026, 11, 2),
                total_float=80,
                resource=None,
            ),
            Activity(
                id="A105",
                name="Site Management",
                activity_type="LOE",
                status="In Progress",
                duration=120,
                start=date(2026, 11, 2),
                finish=date(2027, 4, 1),
                total_float=60,
                resource=None,
            ),
        ],
    )

    report = run_float_date_resource_audit(project)

    check6_findings = [f for f in report.findings if f.check_number == 6]
    assert [f.target_id for f in check6_findings] == ["A101"]
    assert float(check6_findings[0].measured_value) == 61.0

    check7_findings = [f for f in report.findings if f.check_number == 7]
    assert [f.target_id for f in check7_findings] == ["A102"]

    check8_findings = [f for f in report.findings if f.check_number == 8]
    assert [f.target_id for f in check8_findings] == ["A102"]

    check9_findings = [f for f in report.findings if f.check_number == 9]
    assert [f.target_id for f in check9_findings] == ["A103"]

    check10_findings = [f for f in report.findings if f.check_number == 10]
    assert [f.target_id for f in check10_findings] == ["A102"]

    check11_findings = [f for f in report.findings if f.check_number == 11]
    assert [f.target_id for f in check11_findings] == ["A103"]

    assert report.check_results[6].status == "Fail"
    assert report.check_results[7].status == "Fail"
    assert report.check_results[8].status == "Fail"
    assert report.check_results[9].status == "Fail"
    assert report.check_results[10].status == "Fail"
    assert report.check_results[11].status == "Fail"
    assert report.check_results[14].status == "Fail"
    assert report.check_results[14].measured_value == 0.5


def test_boundary_float_44_passes_and_45_fails():
    project = Project(
        name="Boundary Float Programme",
        data_date=date(2026, 11, 1),
        activities=[
            Activity(
                id="A1",
                name="Boundary 44 Days",
                status="Incomplete",
                duration=10,
                start=date(2026, 11, 2),
                finish=date(2026, 11, 12),
                total_float=44,
                resource="Crew 1",
            ),
            Activity(
                id="A2",
                name="Boundary 45 Days",
                status="Incomplete",
                duration=10,
                start=date(2026, 11, 2),
                finish=date(2026, 11, 12),
                total_float=45,
                resource="Crew 2",
            ),
        ],
    )

    report = run_float_date_resource_audit(project)
    check6_targets = [f.target_id for f in report.findings if f.check_number == 6]
    assert "A1" not in check6_targets
    assert "A2" in check6_targets


def test_absent_baseline_marks_check_11_and_14_not_applicable():
    project = Project(
        name="No Baseline Programme",
        data_date=date(2026, 11, 1),
        activities=[
            Activity(
                id="A1",
                name="Normal Task",
                status="Incomplete",
                duration=10,
                start=date(2026, 11, 2),
                finish=date(2026, 11, 12),
                total_float=5,
                baseline_finish=None,
                resource="Crew 1",
            )
        ],
    )

    graph = programme_to_graph(project)
    res11 = calculate_check_11_missed_activities(graph)
    res14 = calculate_check_14_bei(graph)

    assert res11.status == NOT_APPLICABLE
    assert res11.measured_value is None
    assert res14.status == NOT_APPLICABLE
    assert res14.measured_value is None


def test_all_completed_tasks_return_not_applicable():
    project = Project(
        name="Completed Programme",
        data_date=date(2026, 11, 1),
        activities=[
            Activity(
                id="A1",
                name="Done Task",
                status="Completed",
                duration=10,
                start=date(2026, 10, 1),
                finish=date(2026, 10, 10),
                actual_start=date(2026, 10, 1),
                actual_finish=date(2026, 10, 10),
                total_float=0,
                resource="Crew 1",
            )
        ],
    )
    graph = programme_to_graph(project)
    assert calculate_check_6_high_float(graph).status == NOT_APPLICABLE
    assert calculate_check_7_negative_float(graph).status == NOT_APPLICABLE
    assert calculate_check_8_high_duration(graph).status == NOT_APPLICABLE
    assert calculate_check_10_resources(graph).status == NOT_APPLICABLE
    assert calculate_check_9_invalid_dates(graph).status == "Pass"


def test_check9_in_progress_activity_past_start_is_valid():
    project = Project(
        name="In Progress Programme",
        data_date=date(2026, 11, 1),
        activities=[
            Activity(
                id="A1",
                name="Active Excavation",
                status="In Progress",
                duration=30,
                start=date(2026, 10, 20),
                actual_start=date(2026, 10, 20),
                finish=date(2026, 11, 20),
                total_float=5,
                resource="Crew 1",
            )
        ],
    )
    report = run_float_date_resource_audit(project)
    check9_findings = [f for f in report.findings if f.check_number == 9]
    assert check9_findings == []
    assert report.check_results[9].offending_count == 0
    assert report.check_results[9].status == "Pass"


def test_check11_and_bei_exclude_summary_and_loe():
    project = Project(
        name="Summary And LOE Filter Programme",
        data_date=date(2026, 11, 1),
        activities=[
            Activity(
                id="T1",
                name="Completed Task",
                activity_type="Task",
                status="Completed",
                duration=10,
                start=date(2026, 10, 1),
                finish=date(2026, 10, 10),
                actual_start=date(2026, 10, 1),
                actual_finish=date(2026, 10, 10),
                baseline_finish=date(2026, 10, 10),
                resource="Crew 1",
            ),
            Activity(
                id="T2",
                name="Missed Task",
                activity_type="Task",
                status="Not Started",
                duration=10,
                start=date(2026, 11, 5),
                finish=date(2026, 11, 15),
                baseline_finish=date(2026, 10, 20),
                resource="Crew 1",
            ),
            Activity(
                id="S1",
                name="Phase Summary",
                activity_type="Summary",
                status="Completed",
                duration=20,
            ),
            Activity(
                id="L1",
                name="Project Management LOE",
                activity_type="LOE",
                status="In Progress",
                duration=60,
                start=date(2026, 10, 1),
                actual_start=date(2026, 10, 1),
                finish=date(2026, 12, 1),
                baseline_finish=date(2026, 10, 15),
            ),
        ],
    )
    report = run_float_date_resource_audit(project)
    check11_findings = [f for f in report.findings if f.check_number == 11]
    assert [f.target_id for f in check11_findings] == ["T2"]
    assert (report.check_results[11].offending_count, report.check_results[11].total_applicable) == (1, 2)
    assert (report.check_results[14].measured_value, report.check_results[14].status) == (0.5, "Fail")


def test_check11_no_due_activities_returns_not_applicable():
    project = Project(
        name="Future Baseline Programme",
        data_date=date(2026, 11, 1),
        activities=[
            Activity(
                id="T1",
                name="Future Task",
                status="Not Started",
                duration=10,
                start=date(2026, 11, 10),
                finish=date(2026, 11, 20),
                baseline_finish=date(2026, 12, 5),
                resource="Crew 1",
            )
        ],
    )
    graph = programme_to_graph(project)
    res11 = calculate_check_11_missed_activities(graph)
    assert (res11.measured_value, res11.status) == (None, NOT_APPLICABLE)
