"""DCMA kontrol 1–5 oranlarının ve geçti/kaldı kararının testleri.

Çalıştırma (proje klasöründe, .venv aktifken):
    pytest

Örnek programda (tests/data/ornek_program.ttl) sayılanlar:
    task'lar     : A2, A3, A4, A5, A6           -> 5   (A1 tamamlanmış)
    bağlantılar  : R2, R3, R4, R5, R6           -> 5   (R1'in ardılı A1 tamamlanmış,
                                                        R7'nin ardılı A8 milestone)
Her kontrolde 1 bulgu var -> 1/5 = %20 (kontrol 4'te FS payı 4/5 = %80).
"""

import pytest
from pyshacl import validate
from rdflib import RDF, Graph, Literal
from rdflib.namespace import SH

from metrics.ratios import (
    FAIL,
    NOT_APPLICABLE,
    PASS,
    compute_ratios,
    decide,
    load_checks,
)
from tests.test_dcma_1_5 import SCHED, SHAPES_FILE, XSD_STRING, load_programme, set_value


# --- Yardımcı fonksiyonlar -------------------------------------------------

def load_shapes() -> Graph:
    """Kural dosyasını her test için sıfırdan yükler."""
    return Graph().parse(SHAPES_FILE)


def results_by_number(data: Graph, shapes: Graph | None = None) -> dict:
    """{kontrol numarası: CheckResult} sözlüğü döndürür."""
    shapes = shapes if shapes is not None else load_shapes()
    return {r.check_number: r for r in compute_ratios(data, shapes)}


def set_threshold(shapes: Graph, check: str, value: float) -> None:
    """Kural dosyasındaki bir eşiği değiştirir (planlama mühendisinin yaptığı gibi)."""
    shapes.set((SCHED[check], SCHED.thresholdPercent, Literal(value)))


def fix_all_defects(g: Graph) -> None:
    """Örnek programdaki 5 hatayı düzeltir (test_dcma_1_5.py'deki nominal senaryo)."""
    r = SCHED["relationship_8"]
    g.add((r, SCHED.predecessor, SCHED.activity_A5))
    g.add((r, SCHED.successor, SCHED.activity_A8))
    g.add((r, SCHED.relationshipType, Literal("FS")))
    g.add((r, SCHED.lag, Literal(0.0)))
    set_value(g, "relationship_4", "relationshipType", "FS")
    set_value(g, "relationship_4", "lag", 0.0)
    set_value(g, "relationship_6", "lag", 0.0)
    g.remove((SCHED.activity_A4, SCHED.constraintType, None))


def add_isolated_task(g: Graph) -> None:
    """Hiç bağlantısı olmayan bir task ekler (öncülü de ardılı da yok)."""
    a = SCHED.activity_A9
    g.add((a, RDF.type, SCHED.Activity))
    g.add((a, SCHED.activityType, Literal("Task")))
    g.add((a, SCHED.status, Literal("Not Started")))


# --- Kural dosyası ---------------------------------------------------------

def test_kural_dosyasinda_bes_kontrol_ve_dcma_esikleri_var():
    checks = {c.number: (c.name, c.comparison, c.threshold) for c in load_checks(load_shapes())}
    assert checks == {
        1: ("Logic", "<=", 5.0),
        2: ("Leads", "<=", 0.0),
        3: ("Lags", "<=", 5.0),
        4: ("Relationship types", ">=", 90.0),
        5: ("Hard constraints", "<=", 5.0),
    }


def test_her_kontrolun_sayim_kurali_var():
    """Raporun Method sayfası boş kalmasın."""
    assert all(c.counting_rule for c in load_checks(load_shapes()))


def test_yanlis_yazilmis_karsilastirma_hata_verir():
    """'<' gibi tanımsız bir karşılaştırma sessizce yanlış sonuç vermemeli."""
    shapes = load_shapes()
    shapes.set((SCHED.Check3, SCHED.comparison, Literal("<")))
    with pytest.raises(ValueError, match="Check 3"):
        load_checks(shapes)


# --- Örnek programın oranları ----------------------------------------------

def test_ornek_program_oranlari():
    """(payda, bulgu, oran, sonuç) her kontrol için beklenen değerde olmalı."""
    got = {
        n: (r.total_applicable, r.offending_count, r.measured_value, r.status)
        for n, r in results_by_number(load_programme()).items()
    }
    assert got == {
        1: (5, 1, 20.0, FAIL),
        2: (5, 1, 20.0, FAIL),
        3: (5, 1, 20.0, FAIL),
        4: (5, 1, 80.0, FAIL),   # FS payı: 4/5
        5: (5, 1, 20.0, FAIL),
    }


def test_hatalar_duzeltilince_hepsi_gecer():
    g = load_programme()
    fix_all_defects(g)
    results = results_by_number(g)
    assert {n: r.status for n, r in results.items()} == {n: PASS for n in range(1, 6)}
    assert results[4].measured_value == 100.0
    assert all(results[n].measured_value == 0.0 for n in (1, 2, 3, 5))


# --- Eşik değişikliği (Story 5) --------------------------------------------

def test_esik_kural_dosyasinda_degisince_sonuc_degisir():
    """Story 5: firma kendi eşiğini kullanmak isterse kodu değil, kural dosyasını değiştirir."""
    shapes = load_shapes()
    set_threshold(shapes, "Check3", 25.0)
    assert results_by_number(load_programme(), shapes)[3].status == PASS


def test_esige_esit_oran_gecer():
    """Sınır değer: %20 oran, eşik %20 iken geçer (<=). Kontrol 4'te %80, eşik %80 iken geçer (>=)."""
    shapes = load_shapes()
    set_threshold(shapes, "Check3", 20.0)
    set_threshold(shapes, "Check4", 80.0)
    results = results_by_number(load_programme(), shapes)
    assert results[3].status == PASS
    assert results[4].status == PASS


@pytest.mark.parametrize(
    "value, threshold, comparison, expected",
    [
        (5.0, 5.0, "<=", PASS),
        (5.01, 5.0, "<=", FAIL),
        (0.0, 0.0, "<=", PASS),       # kontrol 2: hiç lead yok
        (90.0, 90.0, ">=", PASS),
        (89.99, 90.0, ">=", FAIL),
        (None, 5.0, "<=", NOT_APPLICABLE),
    ],
)
def test_karar_fonksiyonu(value, threshold, comparison, expected):
    assert decide(value, threshold, comparison) == expected


# --- Payda ve sayım kuralları ----------------------------------------------

def test_sayilacak_task_yoksa_not_applicable():
    """Bütün task'lar tamamlanmışsa oran tanımsız -> N/A (0'a bölme hatası değil)."""
    g = load_programme()
    for act in ("A2", "A3", "A4", "A5", "A6"):
        set_value(g, f"activity_{act}", "status", "Completed")
    results = results_by_number(g)
    assert {n: r.status for n, r in results.items()} == {n: NOT_APPLICABLE for n in range(1, 6)}
    assert all(r.measured_value is None and r.total_applicable == 0 for r in results.values())


def test_kontrol1_iki_eksigi_olan_task_bir_kez_sayilir():
    """A9'un ne öncülü ne ardılı var: SHACL 2 ihlal verir, oran 1 task sayar."""
    g = load_programme()
    add_isolated_task(g)
    r = results_by_number(g)[1]
    assert (r.offending_count, r.total_applicable) == (2, 6)   # A5 ve A9


def test_kontrol4_payi_fs_sayisidir():
    """Bir bağlantıyı daha FF yapınca FS payı 3/5 = %60'a düşer, bulgu 2 olur."""
    g = load_programme()
    set_value(g, "relationship_3", "relationshipType", "FF")
    r = results_by_number(g)[4]
    assert (r.measured_value, r.offending_count) == (60.0, 2)


# --- SHACL ve SPARQL aynı şeyi mi sayıyor? ---------------------------------
#
# Kurallar iki yerde yazılı: shapes/dcma_1_5.ttl (bulgular) ve queries/*.rq
# (oranlar). Biri değişip diğeri unutulursa rapordaki bulgu sayısı ile
# Summary'deki sayı farklı çıkar. Bu test farklı senaryolarda ikisini karşılaştırır.

def shacl_focus_nodes_per_check(data: Graph) -> dict[int, set]:
    """SHACL raporundaki bulguları kontrol numarasına göre gruplar (düğüm başına 1)."""
    _conforms, report, _text = validate(data, shacl_graph=load_shapes(), advanced=True)
    per_check: dict[int, set] = {n: set() for n in range(1, 6)}
    for v in report.subjects(predicate=SH.resultSeverity):
        shape_name = str(report.value(v, SH.sourceShape)).split("#")[-1]   # "Check4_..."
        number = int(shape_name[len("Check")])
        per_check[number].add(report.value(v, SH.focusNode))
    return per_check


def scenario_original(g): pass
def scenario_fixed(g): fix_all_defects(g)
def scenario_isolated_task(g): add_isolated_task(g)


def scenario_mapper_literals(g):
    """Arda'nın mapper'ı gibi metinleri xsd:string tipiyle yaz."""
    for rel in range(1, 8):
        subj = SCHED[f"relationship_{rel}"]
        value = str(g.value(subj, SCHED.relationshipType))
        g.set((subj, SCHED.relationshipType, Literal(value, datatype=XSD_STRING)))
    g.set((SCHED.activity_A4, SCHED.constraintType, Literal("Must Finish On", datatype=XSD_STRING)))


def scenario_many_defects(g):
    set_value(g, "relationship_3", "relationshipType", "SF")
    set_value(g, "relationship_5", "lag", 3.0)
    set_value(g, "relationship_2", "lag", -2.0)
    set_value(g, "activity_A6", "constraintType", "Mandatory Start")
    set_value(g, "activity_A2", "constraintType", "Start No Earlier Than")   # yumuşak


@pytest.mark.parametrize(
    "scenario",
    [scenario_original, scenario_fixed, scenario_isolated_task,
     scenario_mapper_literals, scenario_many_defects],
)
def test_shacl_ve_sparql_ayni_sayida_oge_bulur(scenario):
    g = load_programme()
    scenario(g)
    shacl = shacl_focus_nodes_per_check(g)
    sparql = results_by_number(g)
    assert {n: len(nodes) for n, nodes in shacl.items()} == \
           {n: r.offending_count for n, r in sparql.items()}
