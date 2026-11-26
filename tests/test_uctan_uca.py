"""Uçtan uca test: hata koyulmuş bir program -> mapper -> SHACL -> 12 oran.

Çalıştırma (proje klasöründe, .venv aktifken):
    pytest tests/test_uctan_uca.py -v

27 Kasım teslimatının ("12 kontrol için SHACL + SPARQL") kabul testi.
Reader henüz yok; program, Reader'ın üreteceği Project nesnesi olarak elle
kuruluyor. Sonra CLI'nin çağıracağı fonksiyon (graph.audit.audit_programme)
çalıştırılıyor. Yani mapper'dan rapora kadar olan bütün yol test ediliyor.

Program (veri tarihi 1 Kasım 2026): M0 -> T1 -> T2 -> ... -> T9 -> M99 zinciri,
T2 -> T10 yan dalı ve bir LOE. Her kontrol için TAM BİR hata var:

    Kontrol  Hata                              Nerede
    1        ardılı yok                        T10
    2        lead (lag -2)                     relationship_4  (T3 -> T4)
    3        lag +3                            relationship_5  (T4 -> T5)
    4        SS bağlantı                       relationship_6  (T5 -> T6)
    5        Must Finish On                    T3
    6        float 61 gün                      T4
    7        float -3 gün                      T5
    8        süre 50 gün                       T6
    9        başlamamış, başlangıç geçmişte    T7
    10       kaynak yok                        T8
    11       baseline bitişi geçti, bitmedi    T9
    14 BEI   vadesi gelen 3 işten 2'si bitti   (M0, T1 bitti; T9 bitmedi)

Sayılmaması gerekenler: M0, M99 (Milestone), T1 (tamamlanmış), L1 (LOE).
L1'in kaynağı ve ardılı yok; yine de hiçbir kontrolde çıkmamalı.
"""

from datetime import date

import pytest

from graph.audit import audit_programme
from graph.metrics import FAIL, PASS
from graph.models import Activity, Project, Relationship

DATA_DATE = date(2026, 11, 1)


# --- Program ----------------------------------------------------------------

def task(id_, **fields):
    """Sorunsuz, başlamamış bir task. Hata, sadece değişen alanla konur."""
    values = dict(
        name=id_, activity_type="Task", status="Not Started", duration=10,
        start=date(2026, 11, 10), finish=date(2026, 11, 20),
        total_float=5, resource="Crew", baseline_finish=date(2026, 11, 25),
    )
    values.update(fields)
    return Activity(id=id_, **values)


def programme(defects: bool = True) -> Project:
    """defects=True: tablodaki 11 hata + BEI. defects=False: aynı program, hatasız."""
    bad = defects  # kısa ad: aşağıda "X if bad else Y" = hatalıysa X, değilse Y

    activities = [
        Activity("M0", "Başlangıç", activity_type="Milestone", status="Completed", duration=0,
                 start=date(2026, 10, 1), finish=date(2026, 10, 1),
                 actual_start=date(2026, 10, 1), actual_finish=date(2026, 10, 1),
                 baseline_finish=date(2026, 10, 1)),
        task("T1", status="Completed",
             start=date(2026, 10, 1), finish=date(2026, 10, 10),
             actual_start=date(2026, 10, 1), actual_finish=date(2026, 10, 10),
             baseline_finish=date(2026, 10, 10)),
        task("T2", status="In Progress", duration=30,              # normal devam eden iş
             start=date(2026, 10, 15), actual_start=date(2026, 10, 15),
             finish=date(2026, 11, 15), baseline_finish=date(2026, 11, 20)),
        task("T3", constraint_type="Must Finish On" if bad else None),        # 5
        task("T4", total_float=61 if bad else 5),                              # 6
        task("T5", total_float=-3 if bad else 5),                              # 7
        task("T6", duration=50 if bad else 10,                                 # 8
             finish=date(2027, 1, 20) if bad else date(2026, 11, 20)),
        task("T7", start=date(2026, 10, 28) if bad else date(2026, 11, 10)),   # 9
        task("T8", resource=None if bad else "Crew"),                          # 10
        task("T9", baseline_finish=date(2026, 10, 25) if bad else date(2026, 11, 25)),  # 11
        task("T10"),                                                           # 1 (aşağıda)
        Activity("L1", "Proje yönetimi", activity_type="LOE", status="In Progress",
                 duration=90, start=date(2026, 10, 1), actual_start=date(2026, 10, 1),
                 finish=date(2026, 12, 31), baseline_finish=date(2026, 10, 15)),
        Activity("M99", "Bitiş", activity_type="Milestone", duration=0,
                 start=date(2027, 2, 1), finish=date(2027, 2, 1),
                 baseline_finish=date(2027, 2, 1)),
    ]

    relationships = [
        Relationship("M0", "T1"),                                    # 1
        Relationship("T1", "T2"),                                    # 2
        Relationship("T2", "T3"),                                    # 3
        Relationship("T3", "T4", lag=-2 if bad else 0),              # 4  -> kontrol 2
        Relationship("T4", "T5", lag=3 if bad else 0),               # 5  -> kontrol 3
        Relationship("T5", "T6", "SS" if bad else "FS"),             # 6  -> kontrol 4
        Relationship("T6", "T7"),                                    # 7
        Relationship("T7", "T8"),                                    # 8
        Relationship("T8", "T9"),                                    # 9
        Relationship("T9", "M99"),                                   # 10
        Relationship("T2", "T10"),                                   # 11
    ]
    if not bad:
        relationships.append(Relationship("T10", "M99"))             # T10'a ardıl -> kontrol 1 düzelir

    return Project("Uçtan uca test programı", DATA_DATE, activities, relationships)


# --- Hatalı program -----------------------------------------------------------

EXPECTED_FINDINGS = {
    (1, "T10"),
    (2, "relationship_4"),
    (3, "relationship_5"),
    (4, "relationship_6"),
    (5, "T3"),
    (6, "T4"),
    (7, "T5"),
    (8, "T6"),
    (9, "T7"),
    (10, "T8"),
    (11, "T9"),
}


def test_her_kontrol_tam_olarak_konulan_hatayi_bulur():
    """11 kontrolün her biri kendi hatasını bulmalı; fazlası ya da eksiği olmamalı."""
    report = audit_programme(programme())
    assert {(f.check_number, f.target_id) for f in report.findings} == EXPECTED_FINDINGS


def test_sayilmamasi_gerekenler_hicbir_bulguda_yok():
    """Milestone, tamamlanmış task ve LOE (kaynağı ve ardılı olmasa bile) bulgu vermemeli."""
    report = audit_programme(programme())
    assert {f.target_id for f in report.findings}.isdisjoint({"M0", "M99", "T1", "L1"})


def test_hatali_programin_ozet_sayfasi():
    """(bulgu, payda) ve sonuç her kontrol için beklenen değerde olmalı.

    Paydalar:
      1, 5–8  sayılan task'lar: T2–T10 = 9
      2–4     ardılı sayılan task olan bağlantılar: 2–9 ve 11 = 9
      9       Arda'nın kuralı: bütün aktiviteler (13)
      10      süresi > 0 tamamlanmamış task'lar = 9
      11, 14  baseline bitişi <= veri tarihi (LOE hariç): M0, T1, T9 = 3
    """
    results = audit_programme(programme()).check_results
    got = {n: (r.offending_count, r.total_applicable, r.status) for n, r in results.items()}
    assert got == {
        1: (1, 9, FAIL),
        2: (1, 9, FAIL),
        3: (1, 9, FAIL),
        4: (1, 9, FAIL),      # FS payı 8/9 = %88.9 < %90
        5: (1, 9, FAIL),
        6: (1, 9, FAIL),
        7: (1, 9, FAIL),
        8: (1, 9, FAIL),
        9: (1, 13, FAIL),
        10: (1, 9, FAIL),
        11: (1, 3, FAIL),
        14: (1, 3, FAIL),     # BEI 2/3 = 0.67 < 0.95 (bulgu = bitmemiş 1 iş)
    }
    assert results[4].measured_value == pytest.approx(800 / 9)
    assert results[14].measured_value == pytest.approx(2 / 3)


# --- Hatasız program ----------------------------------------------------------

def test_hatalar_duzeltilince_on_iki_kontrolun_hepsi_gecer():
    """Nominal senaryo: aynı program hatasız -> bulgu yok, 12 kontrolün hepsi Pass."""
    report = audit_programme(programme(defects=False))
    assert report.findings == []
    assert {n: r.status for n, r in report.check_results.items()} == \
           {n: PASS for n in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14]}
    assert report.check_results[14].measured_value == 1.0


@pytest.mark.parametrize("check, finding", sorted(EXPECTED_FINDINGS))
def test_tek_hata_sadece_kendi_kontrolunu_bozar(check, finding):
    """Hatalardan sadece biri bırakılınca sadece o kontrol bulgu vermeli.
    (Kontroller birbirine karışmıyor: örneğin lead, lag kontrolünde çıkmıyor.)"""
    clean = programme(defects=False)
    faulty = programme(defects=True)
    project = _only_one_defect(clean, faulty, check)
    report = audit_programme(project)
    assert {(f.check_number, f.target_id) for f in report.findings} == {(check, finding)}


def _only_one_defect(clean: Project, faulty: Project, check: int) -> Project:
    """Hatasız programa, hatalı programdan SADECE bir kontrolün hatasını taşır."""
    defect_activity = {5: "T3", 6: "T4", 7: "T5", 8: "T6", 9: "T7", 10: "T8", 11: "T9"}
    defect_relationship = {2: 3, 3: 4, 4: 5}           # listedeki sıra (0'dan)
    if check in defect_activity:
        target = defect_activity[check]
        clean.activities = [
            next(a for a in faulty.activities if a.id == target) if a.id == target else a
            for a in clean.activities
        ]
    elif check in defect_relationship:
        i = defect_relationship[check]
        clean.relationships[i] = faulty.relationships[i]
    else:  # kontrol 1: T10'un ardılını kaldır
        clean.relationships = [r for r in clean.relationships if r.predecessor != "T10"]
    return clean
