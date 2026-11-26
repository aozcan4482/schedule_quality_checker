"""Kontrol 6–11 ve BEI (Arda Çiftçi) için review testleri — ikinci kişi: Burak.

Çalıştırma (proje klasöründe, .venv aktifken):
    pytest tests/test_review_6_11.py -v

İki tür test var:

1. Review'da doğru çalıştığı görülen davranışlar: sınır değerler (veri
   tarihine eşit tarih), SHACL ile SPARQL'ın aynı öğeleri sayması ve iki
   shapes dosyasının birlikte çalışması.

2. Review'da BULUNAN 4 HATANIN regresyon testleri. 24 Kasım'da bunlar
   @pytest.mark.xfail(strict=True) olarak yazıldı: test DCMA'ya göre doğru
   sonucu bekliyordu, kod yanlış verdiği için "beklenen hata" görünüyordu.
   Arda 26 Kasım'da düzeltti (ardac, dacc5c6); testler "XPASS" verince xfail
   satırları silindi. Artık normal test: hata geri gelirse paket kırılır.

Bütün programlar Arda'nın mapper'ıyla (programme_to_graph) kuruluyor; yani
testler gerçek veri yolunu kullanıyor.
"""

from datetime import date
from pathlib import Path

import pytest

from graph.metrics import (
    FAIL,
    NOT_APPLICABLE,
    calculate_check_9_invalid_dates,
    calculate_check_11_missed_activities,
    calculate_check_14_bei,
    evaluate_checks_6_to_11_and_bei,
)
from graph.models import Activity, Project, Relationship, programme_to_graph
from graph.validator import validate_programme_graph
from tests.test_dcma_1_5 import SHAPES_FILE as SHAPES_1_5

SHAPES_6_11 = Path(__file__).resolve().parent.parent / "shapes" / "float_date_resource_shapes.ttl"

# Bütün örneklerde veri tarihi (data date / status date) bu gün.
DATA_DATE = date(2026, 11, 1)


# --- Yardımcı fonksiyonlar -------------------------------------------------

def graph_of(*activities, relationships=()):
    """Aktivitelerden mapper ile RDF grafiği kurar."""
    project = Project("Review", DATA_DATE, list(activities), list(relationships))
    return programme_to_graph(project)


def task(id_, **fields):
    """Varsayılanları sorunsuz bir task: başlamamış, 10 gün, float 5, kaynaklı,
    tarihleri veri tarihinden sonra. Testte sadece incelenen alan değiştirilir."""
    values = dict(
        name=id_, activity_type="Task", status="Not Started", duration=10,
        start=date(2026, 11, 10), finish=date(2026, 11, 20),
        total_float=5, resource="Crew",
    )
    values.update(fields)
    return Activity(id=id_, **values)


# --- Kontrol 9: sınır değerler (doğru çalışıyor) ----------------------------

def test_kontrol9_veri_tarihine_esit_gercek_bitis_gecerli():
    """Gerçek bitiş = veri tarihi -> 'gelecekte gerçek tarih' sayılmamalı (> değil)."""
    g = graph_of(task("A1", status="Completed", actual_start=date(2026, 10, 20),
                      actual_finish=DATA_DATE, start=date(2026, 10, 20), finish=DATA_DATE))
    assert calculate_check_9_invalid_dates(g).offending_count == 0


def test_kontrol9_veri_tarihine_esit_tahmini_bitis_gecerli():
    """Tahmini bitiş = veri tarihi -> 'geçmişte tahmini tarih' sayılmamalı (< değil)."""
    g = graph_of(task("A1", start=DATA_DATE, finish=DATA_DATE, duration=1))
    assert calculate_check_9_invalid_dates(g).offending_count == 0


def test_kontrol9_baslamamis_isin_gecmisteki_tahmini_baslangici_hata():
    g = graph_of(task("A1", start=date(2026, 10, 25), finish=date(2026, 11, 5)))
    r = calculate_check_9_invalid_dates(g)
    assert (r.offending_count, r.status) == (1, FAIL)


def test_kontrol9_gelecekteki_gercek_baslangic_hata():
    g = graph_of(task("A1", status="In Progress", actual_start=date(2026, 11, 3)))
    assert calculate_check_9_invalid_dates(g).offending_count == 1


def test_kontrol9_iki_tarihi_bozuk_aktivite_bir_kez_sayilir():
    """Başlangıç ve bitiş ikisi de geçmişte: SHACL 2 ihlal, oran 1 aktivite sayar."""
    g = graph_of(task("A1", start=date(2026, 10, 1), finish=date(2026, 10, 20)))
    assert calculate_check_9_invalid_dates(g).offending_count == 1


# --- Review'da bulunan hatalar (regresyon testleri) ------------------------

# Review hatası 1 (24 Kas) — Arda düzeltti (26 Kas, dacc5c6):
#   Devam eden işin başlangıcı gerçek başlangıçtır ve geçmişte olması
#   normaldir. DCMA 9a sadece başlamamış işin tahmini başlangıcına bakar.
#   Düzeltme: 'start < dataDate' dalı sadece actualStart'ı OLMAYAN işlere
#   uygulanmalı (hem shapes'teki Check9 hem metrics.py).
def test_kontrol9_devam_eden_isin_gecmisteki_baslangici_hata_degil():
    g = graph_of(task("A1", status="In Progress", start=date(2026, 10, 20),
                      actual_start=date(2026, 10, 20), finish=date(2026, 11, 20), duration=30))
    shacl_9 = [f for f in validate_programme_graph(g, SHAPES_6_11) if f.check_number == 9]
    assert calculate_check_9_invalid_dates(g).offending_count == 0
    assert shacl_9 == []


# Review hatası 2 (24 Kas) — Arda düzeltti (26 Kas, dacc5c6):
#   BEI'nin payı (tamamlanan) bütün aktivite türlerini sayıyor, paydası ise
#   sadece baseline'ı olanları. Tamamlanmış bir Summary BEI'yi 0.5'ten 1.0'a
#   çıkarıp kontrolü yanlışlıkla geçiriyor. Pay ve payda aynı aktivite
#   kümesinden sayılmalı.
def test_bei_payi_ve_paydasi_ayni_aktivite_kumesini_sayar():
    g = graph_of(
        task("T1", status="Completed", baseline_finish=date(2026, 10, 10),
             actual_finish=date(2026, 10, 10), finish=date(2026, 10, 10)),
        task("T2", baseline_finish=date(2026, 10, 20)),          # vadesi geçti, bitmedi
        Activity("S1", "Özet", activity_type="Summary", status="Completed", duration=5),
    )
    r = calculate_check_14_bei(g)
    assert (r.measured_value, r.status) == (0.5, FAIL)


# Review hatası 3 (24 Kas) — Arda düzeltti (26 Kas, dacc5c6):
#   Kontrol 11 ve BEI'de tür filtresi yok; LOE de sayılıyor. DCMA LOE ve
#   Summary'yi bütün kontrollerden çıkarır (6, 7, 8, 10'da Arda da
#   çıkarıyor). Karar (Arda, 26 Kas): LOE ve Summary sayılmaz, Milestone
#   sayılır. Bu test sadece LOE'ye bakıyor.
def test_kontrol11_ve_bei_loe_saymaz():
    g = graph_of(
        task("T1", status="Completed", baseline_finish=date(2026, 10, 10),
             actual_finish=date(2026, 10, 10), finish=date(2026, 10, 10)),
        Activity("L1", "Proje yönetimi", activity_type="LOE", status="In Progress",
                 duration=60, baseline_finish=date(2026, 10, 15)),
    )
    check11 = calculate_check_11_missed_activities(g)
    bei = calculate_check_14_bei(g)
    assert (check11.offending_count, check11.total_applicable) == (0, 1)
    assert bei.measured_value == 1.0


# Review hatası 4 (24 Kas) — Arda düzeltti (26 Kas, dacc5c6):
#   Veri tarihine kadar bitmesi gereken iş yoksa kontrol 11 'Pass' (%0)
#   veriyor, aynı durumda BEI 'Not Applicable'. Payda 0 iken oran tanımsız;
#   diğer bütün kontroller (1–10) gibi 'Not Applicable' olmalı.
def test_kontrol11_vadesi_gelen_is_yoksa_not_applicable():
    g = graph_of(task("T1", baseline_finish=date(2026, 12, 5)))
    r = calculate_check_11_missed_activities(g)
    assert (r.measured_value, r.status) == (None, NOT_APPLICABLE)


# --- SHACL ve SPARQL aynı öğeleri mi sayıyor? (kontrol 6–11) -----------------
#
# test_ratios.py'deki 1–5 testinin aynısı: Findings sayfasındaki bulgu sayısı
# ile Summary'deki sayı tutmalı. Düzeltmeler (yukarıdaki 4 hata) iki tarafta da
# yapıldığı için test geçiyor; bir düzeltme tek tarafta yapılırsa kırılır.

def mixed_programme():
    """6, 7, 8, 9, 10, 11 için birer hata içeren program."""
    return [
        task("T1", status="Completed", actual_start=date(2026, 10, 1), actual_finish=date(2026, 10, 10),
             start=date(2026, 10, 1), finish=date(2026, 10, 10), baseline_finish=date(2026, 10, 12)),
        task("T2", total_float=61, resource=None),                       # 6 ve 10
        task("T3", total_float=-4, duration=50),                         # 7 ve 8
        task("T4", start=date(2026, 10, 25), finish=date(2026, 11, 5)),  # 9
        task("T5", baseline_finish=date(2026, 10, 20)),                  # 11
        Activity("M1", "Bitiş", activity_type="Milestone", duration=0,
                 start=date(2026, 12, 1), finish=date(2026, 12, 1)),
    ]


def clean_programme():
    return [task("T1"), task("T2", total_float=0), task("T3", duration=44, total_float=44)]


@pytest.mark.parametrize("activities", [mixed_programme(), clean_programme()],
                         ids=["hatali_program", "temiz_program"])
def test_kontrol6_11_shacl_ve_sparql_ayni_sayida_oge_bulur(activities):
    g = graph_of(*activities)
    shacl = {n: set() for n in range(6, 12)}
    for f in validate_programme_graph(g, SHAPES_6_11):
        shacl[f.check_number].add(f.target_id)
    sparql = evaluate_checks_6_to_11_and_bei(g)
    assert {n: len(ids) for n, ids in shacl.items()} == \
           {n: sparql[n].offending_count for n in range(6, 12)}


def test_hatali_programda_her_kontrol_tam_bir_bulgu_verir():
    """Karma programdaki her hata kendi kontrolünde ve sadece bir kez yakalanmalı."""
    results = evaluate_checks_6_to_11_and_bei(graph_of(*mixed_programme()))
    assert {n: results[n].offending_count for n in range(6, 12)} == {n: 1 for n in range(6, 12)}


# --- İki shapes dosyası birlikte (kontrol 1–11) -----------------------------

def test_iki_shapes_dosyasi_birlikte_kontrol_numaralarini_dogru_bulur():
    """Arda'nın validator'ı iki .ttl dosyasını birlikte çalıştırınca, benim
    kontrol 1–5 bulgularım da doğru kontrol numarasına bağlanmalı (rapordaki
    Findings sayfası buna göre gruplanacak). Program, tests/data/ornek_program.ttl
    ile aynı hataları taşıyor ama mapper'dan geçiyor."""
    acts = [
        Activity("A0", "Başlangıç", activity_type="Milestone", duration=0),
        task("A1", status="Completed"), task("A2", status="In Progress", start=DATA_DATE,
                                             actual_start=DATA_DATE),
        task("A3"), task("A4", constraint_type="Must Finish On"), task("A5"), task("A6"),
        Activity("A8", "Bitiş", activity_type="Milestone", duration=0),
    ]
    rels = [Relationship("A0", "A1"), Relationship("A1", "A2"), Relationship("A2", "A3"),
            Relationship("A3", "A4", "SS", 2), Relationship("A3", "A5"),
            Relationship("A4", "A6", lag=-1), Relationship("A6", "A8")]
    findings = validate_programme_graph(graph_of(*acts, relationships=rels), [SHAPES_1_5, SHAPES_6_11])
    found = {(f.check_number, f.target_id) for f in findings if f.check_number <= 5}
    assert found == {
        (1, "A5"),
        (2, "relationship_6"),
        (3, "relationship_4"),
        (4, "relationship_4"),
        (5, "A4"),
    }
