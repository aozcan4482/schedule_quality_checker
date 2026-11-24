from datetime import date
from pathlib import Path
from graph.models import Activity, Project
from graph.validator import DEFAULT_SHAPES_PATH, run_float_date_resource_audit


def test_s5_change_threshold_in_rules_file(tmp_path: Path):
    original_shapes = DEFAULT_SHAPES_PATH.read_text(encoding="utf-8")
    modified_shapes = original_shapes.replace(
        "sh:path sched:totalFloat ;\n        sh:maxInclusive 44 ;",
        "sh:path sched:totalFloat ;\n        sh:maxInclusive 30 ;",
    )
    custom_shapes_file = tmp_path / "custom_shapes.ttl"
    custom_shapes_file.write_text(modified_shapes, encoding="utf-8")

    project = Project(
        name="Custom Threshold Programme",
        data_date=date(2026, 11, 1),
        activities=[
            Activity(
                id="A201",
                name="Medium Float Activity",
                status="Incomplete",
                duration=12,
                start=date(2026, 11, 5),
                finish=date(2026, 11, 20),
                total_float=35,
                resource="Steel Crew",
            ),
            Activity(
                id="A202",
                name="Low Float Activity",
                status="Incomplete",
                duration=10,
                start=date(2026, 11, 5),
                finish=date(2026, 11, 15),
                total_float=25,
                resource="Masonry Crew",
            ),
        ],
    )

    default_report = run_float_date_resource_audit(project)
    default_check6 = [f.target_id for f in default_report.findings if f.check_number == 6]
    assert "A201" not in default_check6

    custom_report = run_float_date_resource_audit(project, shapes_file_path=custom_shapes_file)
    custom_check6 = [f.target_id for f in custom_report.findings if f.check_number == 6]
    assert custom_check6 == ["A201"]
    assert custom_report.check_results[6].status == "Fail"


def test_s5_change_ratio_threshold_in_rules_file(tmp_path: Path):
    original_shapes = DEFAULT_SHAPES_PATH.read_text(encoding="utf-8")
    modified_shapes = original_shapes.replace(
        "sched:checkNumber 6 ;\n    sched:checkName \"High Float\" ;\n    sched:thresholdPercent 5.0 ;",
        "sched:checkNumber 6 ;\n    sched:checkName \"High Float\" ;\n    sched:thresholdPercent 50.0 ;",
    )
    custom_shapes_file = tmp_path / "custom_ratio_shapes.ttl"
    custom_shapes_file.write_text(modified_shapes, encoding="utf-8")

    project = Project(
        name="Ratio Threshold Programme",
        data_date=date(2026, 11, 1),
        activities=[
            Activity(
                id="A1",
                name="High Float Task",
                status="Incomplete",
                duration=10,
                start=date(2026, 11, 5),
                finish=date(2026, 11, 15),
                total_float=60,
                resource="Crew 1",
            ),
            Activity(
                id="A2",
                name="Normal Task",
                status="Incomplete",
                duration=10,
                start=date(2026, 11, 5),
                finish=date(2026, 11, 15),
                total_float=5,
                resource="Crew 2",
            ),
        ],
    )

    default_report = run_float_date_resource_audit(project)
    assert default_report.check_results[6].status == "Fail"

    relaxed_report = run_float_date_resource_audit(project, shapes_file_path=custom_shapes_file)
    assert relaxed_report.check_results[6].measured_value == 50.0
    assert relaxed_report.check_results[6].status == "Pass"
