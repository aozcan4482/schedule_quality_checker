"""DCMA kontrol 1–5 shape'lerinin testleri.

Çalıştırma (proje klasöründe, .venv aktifken):
    pytest

Her test aynı fikri kullanır:
    1. Örnek programı (tests/data/ornek_program.ttl) yükle.
    2. Gerekirse grafikte küçük bir değişiklik yap (hatayı düzelt / yeni hata ekle).
    3. pySHACL ile shapes/dcma_1_5.ttl'e göre doğrula.
    4. Hangi kontrolün hangi düğümü işaretlediğine bak ve beklenenle karşılaştır.
"""

from pathlib import Path

import pytest
from pyshacl import validate
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import SH

# --- Dosya yolları ---------------------------------------------------------
# Path(__file__) = bu test dosyası; .parent.parent = proje kök klasörü.
ROOT = Path(__file__).resolve().parent.parent
SHAPES_FILE = ROOT / "shapes" / "dcma_1_5.ttl"
DATA_FILE = ROOT / "tests" / "data" / "ornek_program.ttl"

SCHED = Namespace("http://example.org/schedule#")


# --- Yardımcı fonksiyonlar -------------------------------------------------

def load_programme() -> Graph:
    """Örnek programı her test için sıfırdan yükler (testler birbirini etkilemesin)."""
    return Graph().parse(DATA_FILE)


def findings(data: Graph) -> set[tuple[str, str]]:
    """Grafiği doğrular ve bulguları {(shape adı, düğüm adı), ...} kümesi olarak döndürür.

    Örnek: ("Check1_MissingSuccessor", "activity_A5")

    advanced=True ŞART: SPARQL hedefleri (sh:SPARQLTarget) sadece bu modda çalışır.
    """
    shapes = Graph().parse(SHAPES_FILE)
    _conforms, report, _text = validate(data, shacl_graph=shapes, advanced=True)

    result = set()
    # Rapordaki her ihlal bir sh:ValidationResult düğümüdür.
    for violation in report.subjects(predicate=SH.resultSeverity):
        source = report.value(violation, SH.sourceShape)   # hangi kural
        focus = report.value(violation, SH.focusNode)      # hangi aktivite/bağlantı
        result.add((local_name(source), local_name(focus)))
    return result


def local_name(uri: URIRef) -> str:
    """'http://example.org/schedule#activity_A5' -> 'activity_A5'"""
    return str(uri).split("#")[-1]


def only_check(found: set[tuple[str, str]], prefix: str) -> set[str]:
    """Bulgulardan sadece adı prefix ile başlayan kontrolün düğümlerini seçer."""
    return {node for shape, node in found if shape.startswith(prefix)}


def set_value(graph: Graph, subject: str, prop: str, value) -> None:
    """Bir düğümün özelliğini değiştirir (eski değeri silip yenisini ekler)."""
    graph.set((SCHED[subject], SCHED[prop], Literal(value)))


# --- Örnek programın tamamı ------------------------------------------------

def test_ornek_program_tam_olarak_bes_bulgu_verir():
    """Bilerek konulan 5 hata bulunmalı, fazlası ya da eksiği olmamalı."""
    assert findings(load_programme()) == {
        ("Check1_MissingSuccessor", "activity_A5"),
        ("Check2_NegativeLag", "relationship_6"),
        ("Check3_PositiveLag", "relationship_4"),
        ("Check4_NonFinishToStart", "relationship_4"),
        ("Check5_HardConstraint", "activity_A4"),
    }


def test_hatalar_duzeltilince_bulgu_kalmaz():
    """Nominal senaryo: hatasız programda hiçbir bulgu çıkmamalı."""
    g = load_programme()
    # A5'e bir ardıl ekle (A5 -> A8, FS, lag 0)
    r = SCHED["relationship_8"]
    g.add((r, SCHED.predecessor, SCHED.activity_A5))
    g.add((r, SCHED.successor, SCHED.activity_A8))
    g.add((r, SCHED.relationshipType, Literal("FS")))
    g.add((r, SCHED.lag, Literal(0.0)))
    # R4'ü düz FS yap, R6'nın lead'ini kaldır, A4'ün kısıtını sil
    set_value(g, "relationship_4", "relationshipType", "FS")
    set_value(g, "relationship_4", "lag", 0.0)
    set_value(g, "relationship_6", "lag", 0.0)
    g.remove((SCHED.activity_A4, SCHED.constraintType, None))

    assert findings(g) == set()


# --- Kontrol 1: Logic ------------------------------------------------------

def test_kontrol1_ardili_olmayan_taski_bulur():
    assert only_check(findings(load_programme()), "Check1") == {"activity_A5"}


def test_kontrol1_milestone_ve_tamamlanmis_aktiviteleri_saymaz():
    """A0'ın öncülü, A8'in ardılı yok ama ikisi de Milestone -> bulgu olmamalı."""
    found = only_check(findings(load_programme()), "Check1")
    assert "activity_A0" not in found
    assert "activity_A8" not in found


def test_kontrol1_tamamlanan_task_sayilmaz():
    """A5 tamamlanmış olursa ardılı olmaması artık sorun değil."""
    g = load_programme()
    set_value(g, "activity_A5", "status", "Completed")
    assert only_check(findings(g), "Check1") == set()


def test_kontrol1_oncul_eksigini_de_bulur():
    """A2'nin tek öncül bağlantısını (R2) silince 'öncülü yok' bulgusu çıkmalı."""
    g = load_programme()
    g.remove((SCHED.relationship_2, None, None))
    assert ("Check1_MissingPredecessor", "activity_A2") in findings(g)


# --- Kontrol 2: Leads ------------------------------------------------------

def test_kontrol2_negatif_lagi_bulur():
    assert only_check(findings(load_programme()), "Check2") == {"relationship_6"}


def test_kontrol2_ardili_milestone_olan_baglanti_sayilmaz():
    """R7'nin ardılı A8 (Milestone). Lead olsa bile kontrol 2 onu saymamalı."""
    g = load_programme()
    set_value(g, "relationship_7", "lag", -3.0)
    assert "relationship_7" not in only_check(findings(g), "Check2")


# --- Kontrol 3: Lags -------------------------------------------------------

def test_kontrol3_pozitif_lagi_bulur():
    assert only_check(findings(load_programme()), "Check3") == {"relationship_4"}


def test_kontrol3_sifir_lag_sorun_degil():
    """Sınır değer: lag = 0 bulgu vermemeli."""
    g = load_programme()
    set_value(g, "relationship_4", "lag", 0.0)
    assert only_check(findings(g), "Check3") == set()


# --- Kontrol 4: Relationship types -----------------------------------------

@pytest.mark.parametrize("rel_type", ["SS", "FF", "SF"])
def test_kontrol4_fs_olmayan_her_turu_bulur(rel_type):
    g = load_programme()
    set_value(g, "relationship_3", "relationshipType", rel_type)
    assert "relationship_3" in only_check(findings(g), "Check4")


# --- Kontrol 5: Hard constraints -------------------------------------------

def test_kontrol5_sert_kisiti_bulur():
    assert only_check(findings(load_programme()), "Check5") == {"activity_A4"}


def test_kontrol5_yumusak_kisit_sorun_degil():
    """Start No Earlier Than yumuşak bir kısıt -> bulgu olmamalı."""
    g = load_programme()
    set_value(g, "activity_A4", "constraintType", "Start No Earlier Than")
    assert only_check(findings(g), "Check5") == set()


# --- Tuzak: advanced mod ---------------------------------------------------

def test_advanced_mod_olmadan_hicbir_sey_bulunmaz():
    """Bu test bir UYARI: advanced=False ile SPARQL hedefleri çalışmaz ve
    hatalı program bile 'conforms' çıkar. Kodda validate() çağrılırken
    advanced=True unutulmamalı."""
    shapes = Graph().parse(SHAPES_FILE)
    conforms, _report, _text = validate(load_programme(), shacl_graph=shapes, advanced=False)
    assert conforms is True
