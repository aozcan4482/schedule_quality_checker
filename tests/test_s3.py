"""Story S3 kabul testi — mantık kontrolleri (sahibi: Burak).

Proposal'daki story:
    As a   Planning engineer
    I want the logic checks (missing links, leads, lags, relationship types)
           applied to every activity
    So that I see where the network is broken

    Given  a programme with one activity missing its successor and one link
           with a negative lag
    When   I run the checker
    Then   checks 1 and 2 fail and list exactly those two items

Proposal'ın "Definition of done" kuralı: her story'nin kabul kriteri için story
id'siyle adlandırılmış bir pytest testi (Arda'nın test_s4.py ve test_s5.py'si gibi).

Çalıştırma (proje klasöründe, .venv aktifken):
    pytest tests/test_s3.py -v

"When I run the checker" = CLI'nin çağıracağı graph.audit.audit_programme.
Program Reader'ın üreteceği Project nesnesi olarak kuruluyor, mapper'dan geçiyor.
"""

from datetime import date

from graph.audit import audit_programme
from graph.metrics import FAIL, PASS
from graph.models import Activity, Project, Relationship

DATA_DATE = date(2026, 11, 1)


def task(id_):
    """Diğer kontrollere takılmayan sorunsuz bir task (süre, float, kaynak, tarih)."""
    return Activity(
        id=id_, name=id_, activity_type="Task", status="Not Started", duration=10,
        start=date(2026, 11, 10), finish=date(2026, 11, 20), total_float=5,
        resource="Crew", baseline_finish=date(2026, 11, 25),
    )


def s3_programme(missing_successor: bool = True, negative_lag: bool = True) -> Project:
    """Başlangıç -> A1 -> A2 -> A3 -> Bitiş zinciri ve A1 -> A4 yan dalı.

    missing_successor : A4'ün ardılı yok   (kontrol 1)
    negative_lag      : A2 -> A3 lag -2    (kontrol 2, bağlantı no 3)
    """
    activities = [
        Activity("M0", "Başlangıç", activity_type="Milestone", duration=0,
                 start=date(2026, 11, 10), finish=date(2026, 11, 10)),
        task("A1"), task("A2"), task("A3"), task("A4"),
        Activity("M9", "Bitiş", activity_type="Milestone", duration=0,
                 start=date(2026, 12, 31), finish=date(2026, 12, 31)),
    ]
    relationships = [
        Relationship("M0", "A1"),                                  # 1
        Relationship("A1", "A2"),                                  # 2
        Relationship("A2", "A3", lag=-2 if negative_lag else 0),   # 3
        Relationship("A3", "M9"),                                  # 4
        Relationship("A1", "A4"),                                  # 5
    ]
    if not missing_successor:
        relationships.append(Relationship("A4", "M9"))             # 6
    return Project("Story S3", DATA_DATE, activities, relationships)


def logic_findings(report) -> set[tuple[int, str]]:
    """Kontrol 1 ve 2'nin bulguları: {(kontrol, öğe), ...}"""
    return {(f.check_number, f.target_id) for f in report.findings if f.check_number in (1, 2)}


# --- Kabul kriteri ------------------------------------------------------------

def test_s3_missing_successor_and_negative_lag_fail_checks_1_and_2():
    """Given/When/Then: kontrol 1 ve 2 fail eder ve TAM OLARAK bu iki öğeyi listeler."""
    report = audit_programme(s3_programme())

    assert report.check_results[1].status == FAIL
    assert report.check_results[2].status == FAIL
    assert logic_findings(report) == {(1, "A4"), (2, "relationship_3")}


def test_s3_no_other_check_reports_anything():
    """'Exactly those two items': program başka hiçbir kontrolde bulgu vermemeli."""
    report = audit_programme(s3_programme())
    assert {(f.check_number, f.target_id) for f in report.findings} == \
           {(1, "A4"), (2, "relationship_3")}


# --- Nominal ve tek hata senaryoları ------------------------------------------

def test_s3_fixed_programme_passes_checks_1_to_4():
    """İki hata düzeltilince mantık kontrolleri (1–4) geçer, bulgu kalmaz."""
    report = audit_programme(s3_programme(missing_successor=False, negative_lag=False))

    assert {n: report.check_results[n].status for n in (1, 2, 3, 4)} == {n: PASS for n in (1, 2, 3, 4)}
    assert report.findings == []


def test_s3_each_defect_alone_fails_only_its_own_check():
    """Hatalardan biri tek başına: sadece kendi kontrolü fail eder."""
    only_link = audit_programme(s3_programme(negative_lag=False))
    only_lead = audit_programme(s3_programme(missing_successor=False))

    assert logic_findings(only_link) == {(1, "A4")}
    assert (only_link.check_results[1].status, only_link.check_results[2].status) == (FAIL, PASS)

    assert logic_findings(only_lead) == {(2, "relationship_3")}
    assert (only_lead.check_results[1].status, only_lead.check_results[2].status) == (PASS, FAIL)
