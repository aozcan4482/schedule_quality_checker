"""12 kontrolün tek giriş noktası (graph/audit.py) için testler.

Çalıştırma (proje klasöründe, .venv aktifken):
    pytest tests/test_audit.py -v

Bu testler kontrollerin KENDİSİNİ değil, giriş noktasının SÖZLEŞMESİNİ test eder:
    - 12 kontrolün hepsi tek çağrıda, numara sırasıyla geliyor mu?
    - Hepsi aynı sınıfta (graph.models.CheckResult) ve aynı sonuç metinleriyle mi?
    - Bulgular iki modülden de geliyor ve Summary'deki sayılarla tutuyor mu?
    - Eşikler iki kural dosyasından da okunuyor mu (Story 5)?
Kontrollerin tek tek doğruluğu test_dcma_1_5.py, test_ratios.py, test_s4.py ve
test_review_6_11.py'de.
"""

from datetime import date

import pytest
from rdflib import Graph, Literal
from rdflib.namespace import SH

from graph.audit import SHAPES_FILES, audit_programme, run_all_checks
from graph.metrics import FAIL, NOT_APPLICABLE, PASS
from graph.models import Activity, AuditReport, CheckResult, Project, Relationship, programme_to_graph
from graph.ratios import compute_ratios
from tests.test_dcma_1_5 import SCHED, SHAPES_FILE, load_programme

ALL_CHECKS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14]
DATA_DATE = date(2026, 11, 1)


# --- Yardımcı fonksiyonlar -------------------------------------------------

def task(id_, **fields):
    """Sorunsuz bir task; testte sadece incelenen alan değiştirilir."""
    values = dict(
        name=id_, activity_type="Task", status="Not Started", duration=10,
        start=date(2026, 11, 10), finish=date(2026, 11, 20),
        total_float=5, resource="Crew", baseline_finish=date(2026, 11, 20),
    )
    values.update(fields)
    return Activity(id=id_, **values)


def small_project(**t2_fields) -> Project:
    """Başlangıç -> T1 -> T2 -> T3 -> Bitiş zinciri. T2'ye istenen hata konur."""
    acts = [
        Activity("M0", "Başlangıç", activity_type="Milestone", duration=0),
        task("T1"), task("T2", **t2_fields), task("T3"),
        Activity("M9", "Bitiş", activity_type="Milestone", duration=0),
    ]
    rels = [Relationship("M0", "T1"), Relationship("T1", "T2"),
            Relationship("T2", "T3"), Relationship("T3", "M9")]
    return Project("Küçük program", DATA_DATE, acts, rels)


def load_shapes() -> tuple[Graph, Graph]:
    """İki kural dosyasını belleğe yükler (testte değiştirip geçici dosyaya yazmak için)."""
    return Graph().parse(SHAPES_FILES[0]), Graph().parse(SHAPES_FILES[1])


def save(tmp_path, shapes_1_5: Graph, shapes_6_11: Graph) -> list:
    """Değiştirilmiş kural dosyalarını geçici klasöre yazar, yollarını döndürür."""
    paths = [tmp_path / "dcma_1_5.ttl", tmp_path / "float_date_resource_shapes.ttl"]
    shapes_1_5.serialize(paths[0], format="turtle")
    shapes_6_11.serialize(paths[1], format="turtle")
    return paths


# --- Sözleşme: 12 sonuç, tek sınıf ------------------------------------------

def test_on_iki_kontrol_tek_cagrida_numara_sirasiyla_gelir():
    results, _findings = run_all_checks(load_programme())
    assert list(results) == ALL_CHECKS
    assert [r.check_number for r in results.values()] == ALL_CHECKS


def test_butun_sonuclar_ayni_sinif_ve_ayni_sonuc_metinleri():
    """Rapor yazıcı 12 satırı tek tip okuyabilmeli."""
    results, _ = run_all_checks(load_programme())
    assert all(type(r) is CheckResult for r in results.values())
    assert {r.status for r in results.values()} <= {PASS, FAIL, NOT_APPLICABLE}
    assert all(r.comparison in ("<=", ">=") for r in results.values())


def test_kontrol_1_5_sonuclari_tek_basina_calistirmayla_ayni():
    """Giriş noktası 1–5 sonuçlarını değiştirmeden almalı."""
    data = load_programme()
    alone = {r.check_number: r for r in compute_ratios(data, Graph().parse(SHAPES_FILE))}
    together, _ = run_all_checks(data)
    assert {n: together[n] for n in range(1, 6)} == alone


# --- Bulgular ----------------------------------------------------------------

def test_bulgular_iki_modulden_de_gelir():
    """T2'de iki hata: ardılı yok (kontrol 1) ve float 61 (kontrol 6)."""
    project = small_project(total_float=61)
    project.relationships = [r for r in project.relationships if r.predecessor != "T2"]
    report = audit_programme(project)
    found = {(f.check_number, f.target_id) for f in report.findings}
    assert (1, "T2") in found
    assert (6, "T2") in found


@pytest.mark.parametrize(
    "t2_fields",
    [{}, {"total_float": 61, "resource": None}, {"total_float": -3, "duration": 50},
     {"constraint_type": "Must Start On", "baseline_finish": date(2026, 10, 20)}],
    ids=["temiz", "float_ve_kaynak", "negatif_float_ve_sure", "kisit_ve_gecikme"],
)
def test_bulgu_sayisi_ozetteki_sayiyla_tutar(t2_fields):
    """Findings sayfasındaki öğe sayısı = Summary'deki bulgu sayısı (kontrol 1–11)."""
    report = audit_programme(small_project(**t2_fields))
    per_check = {n: set() for n in range(1, 12)}
    for f in report.findings:
        per_check[f.check_number].add(f.target_id)
    assert {n: len(ids) for n, ids in per_check.items()} == \
           {n: report.check_results[n].offending_count for n in range(1, 12)}


# --- audit_programme (CLI'nin çağıracağı fonksiyon) -------------------------

def test_audit_programme_reader_ciktisini_alip_audit_report_dondurur():
    project = small_project()
    report = audit_programme(project)
    assert isinstance(report, AuditReport)
    assert report.project is project
    assert list(report.check_results) == ALL_CHECKS
    assert report.findings == []          # small_project() hatasız


# --- Eşikler iki kural dosyasından da okunur (Story 5) ----------------------

def test_esikler_iki_kural_dosyasindan_da_okunur(tmp_path):
    """Planlama mühendisi iki dosyada da eşik değiştirebilmeli; kod değişmeden:
      - kontrol 3'ün oran eşiği %5 -> %25 (dcma_1_5.ttl)
      - kontrol 6'nın gün sınırı 44 -> 30 (float_date_resource_shapes.ttl)
    """
    shapes_1_5, shapes_6_11 = load_shapes()
    shapes_1_5.set((SCHED.Check3, SCHED.thresholdPercent, Literal(25.0)))
    float_rule = shapes_6_11.value(SCHED.Check6_HighFloatShape, SH.property)
    shapes_6_11.set((float_rule, SH.maxInclusive, Literal(30)))
    paths = save(tmp_path, shapes_1_5, shapes_6_11)

    # Kontrol 3: örnek programda %20 lag -> varsayılan eşikte Fail, %25'te Pass.
    default, _ = run_all_checks(load_programme())
    changed, _ = run_all_checks(load_programme(), paths)
    assert (default[3].status, changed[3].status) == (FAIL, PASS)

    # Kontrol 6: 35 gün float -> 44'te sorun değil, 30'da bulgu (hem SHACL hem oran).
    data = programme_to_graph(small_project(total_float=35))
    default, default_findings = run_all_checks(data)
    changed, changed_findings = run_all_checks(data, paths)
    assert (default[6].offending_count, changed[6].offending_count) == (0, 1)
    assert (6, "T2") not in {(f.check_number, f.target_id) for f in default_findings}
    assert (6, "T2") in {(f.check_number, f.target_id) for f in changed_findings}
