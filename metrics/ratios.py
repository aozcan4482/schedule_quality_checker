"""DCMA oranları ve geçti/kaldı kararı (kontrol 1–5).

Ne yapar?
    1. Kural dosyasından (shapes/dcma_1_5.ttl) her kontrolün eşiğini okur
       -> sched:Check1 ... sched:Check5 düğümleri.
    2. Her kontrol için queries/ klasöründeki SPARQL sorgusunu programın
       grafiğinde çalıştırır -> payda, pay ve bulgu sayısı.
    3. Oranı yüzde olarak hesaplar ve eşikle karşılaştırır -> Pass / Fail / N/A.

SHACL ile farkı:
    SHACL (pySHACL) hatalı öğeleri TEK TEK bulur  -> raporun Findings sayfası.
    Bu modül kaç tane olduklarını SAYAR ve oranı eşikle karşılaştırır
    -> raporun Summary sayfası.

Kendin dene (proje klasöründe, .venv aktifken):
    python -m metrics.ratios tests/data/ornek_program.ttl

Yeni kontrol eklemek (örn. 6–11) için Python'a dokunmak gerekmez:
kural dosyasına bir sched:Check düğümü, queries/ klasörüne bir .rq dosyası
eklemek yeter.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from rdflib import Graph

# --- Dosya yolları ---------------------------------------------------------
# Path(__file__) = bu dosya; .parent.parent = proje kök klasörü.
ROOT = Path(__file__).resolve().parent.parent
QUERIES_DIR = ROOT / "queries"
DEFAULT_SHAPES_FILE = ROOT / "shapes" / "dcma_1_5.ttl"

# --- Sonuç değerleri -------------------------------------------------------
# Proposal: "pass, fail or not applicable". Rapor yazıcı (Arda Özcan) bu
# metinleri Summary sayfasına yazacak; değiştirmek gerekirse sadece burası.
PASS = "Pass"
FAIL = "Fail"
NOT_APPLICABLE = "N/A"

# Kural dosyasında izin verilen karşılaştırmalar.
COMPARISONS = ("<=", ">=")


@dataclass(frozen=True)
class CheckDefinition:
    """Kural dosyasındaki bir sched:Check düğümü (bir DCMA kontrolü)."""

    number: int
    name: str
    threshold: float          # yüzde: 5.0 = %5
    comparison: str           # "<=" ya da ">="
    query_file: str           # queries/ içindeki dosya adı
    counting_rule: str = ""   # raporun Method sayfası için


@dataclass
class CheckResult:
    """Bir kontrolün sonucu (raporun Summary sayfasında bir satır).

    Alan adları Arda'nın graph/models.py'deki CheckResult'ıyla AYNI;
    sadece sonuna `comparison` eklendi (raporda "<= 5%" / ">= 90%" yazmak için).
    Branch'ler birleşince bunun yerine onunki kullanılabilir.
    """

    check_number: int
    check_name: str
    measured_value: float | None   # yüzde; payda 0 ise None
    threshold: float               # yüzde
    status: str                    # PASS, FAIL ya da NOT_APPLICABLE
    offending_count: int = 0       # bulgu sayısı
    total_applicable: int = 0      # payda
    comparison: str = "<="


# --- 1. Eşikleri kural dosyasından oku -------------------------------------

# Kural dosyasındaki sched:Check düğümlerini seçen sorgu. Eşikleri de
# SPARQL ile okuyoruz: kural dosyası da bir RDF grafiği.
CHECKS_QUERY = """
PREFIX sched: <http://example.org/schedule#>
SELECT ?number ?name ?threshold ?comparison ?query ?rule WHERE {
    ?check a sched:Check ;
           sched:checkNumber ?number ;
           sched:checkName ?name ;
           sched:thresholdPercent ?threshold ;
           sched:comparison ?comparison ;
           sched:ratioQuery ?query .
    OPTIONAL { ?check sched:countingRule ?rule }
}
ORDER BY ?number
"""


def load_checks(shapes: Graph) -> list[CheckDefinition]:
    """Kural dosyasındaki kontrolleri numara sırasıyla döndürür."""
    checks = []
    for row in shapes.query(CHECKS_QUERY):
        comparison = str(row.comparison).strip()
        if comparison not in COMPARISONS:
            # Planlama mühendisi elle yazarken hata yapabilir ("=<", "<" ...).
            # Sessizce yanlış sonuç vermek yerine açıkça dur.
            raise ValueError(
                f"Check {row.number}: sched:comparison must be one of "
                f"{COMPARISONS}, got {comparison!r}"
            )
        checks.append(
            CheckDefinition(
                number=int(row.number),
                name=str(row.name),
                threshold=float(row.threshold),
                comparison=comparison,
                query_file=str(row.query),
                counting_rule=str(row.rule) if row.rule is not None else "",
            )
        )
    return checks


# --- 2. Oran sorgusunu çalıştır ---------------------------------------------

def run_ratio_query(data: Graph, query_file: str) -> tuple[int, int, int]:
    """Bir oran sorgusunu çalıştırır, (payda, pay, bulgu) döndürür.

    Her sorgu tek satır döndürür: ?applicable ?numerator ?offending
    (ayrıntı: queries/check1_logic.rq başındaki açıklama).
    """
    query = (QUERIES_DIR / query_file).read_text(encoding="utf-8")
    rows = list(data.query(query))
    # COUNT/SUM'lu ve GROUP BY'sız bir sorgu her zaman tam 1 satır döner
    # (hiç öğe yoksa bile, 0'larla). Başka bir şey gelirse sorgu bozuktur.
    if len(rows) != 1:
        raise ValueError(f"{query_file}: expected 1 row, got {len(rows)}")
    row = rows[0]
    return int(row.applicable), int(row.numerator), int(row.offending)


# --- 3. Eşikle karşılaştır --------------------------------------------------

def decide(value: float | None, threshold: float, comparison: str) -> str:
    """Oranı eşikle karşılaştırır. Eşitlik GEÇER (DCMA: "en fazla %5")."""
    if value is None:
        return NOT_APPLICABLE
    if comparison == "<=":
        return PASS if value <= threshold else FAIL
    if comparison == ">=":
        return PASS if value >= threshold else FAIL
    raise ValueError(f"unknown comparison {comparison!r}")


def evaluate(data: Graph, check: CheckDefinition) -> CheckResult:
    """Tek bir kontrolün sonucunu hesaplar."""
    applicable, numerator, offending = run_ratio_query(data, check.query_file)

    if applicable == 0:
        # Sayılacak öğe yok (örn. bütün task'lar tamamlanmış): oran tanımsız.
        value = None
    else:
        # Önce 100 ile çarp, sonra böl: 1 * 100 / 20 = 5.0 tam çıkar.
        # (1 / 20 * 100 gibi yazınca kayan nokta hatası sınırda yanlış
        #  karar verdirebilir.)
        value = numerator * 100 / applicable

    return CheckResult(
        check_number=check.number,
        check_name=check.name,
        measured_value=value,
        threshold=check.threshold,
        status=decide(value, check.threshold, check.comparison),
        offending_count=offending,
        total_applicable=applicable,
        comparison=check.comparison,
    )


def compute_ratios(data: Graph, shapes: Graph) -> list[CheckResult]:
    """Kural dosyasındaki BÜTÜN kontrollerin sonuçlarını hesaplar.

    data   : programın RDF grafiği (mapper'ın çıktısı)
    shapes : kural dosyası (shapes/dcma_1_5.ttl) — eşikler buradan okunur
    """
    return [evaluate(data, check) for check in load_checks(shapes)]


# --- Komut satırından deneme -----------------------------------------------

def format_table(results: list[CheckResult]) -> str:
    """Sonuçları terminalde okunur bir tablo olarak hazırlar."""
    lines = [f"{'Check':<24} {'Value':>7}  {'Threshold':<9}  {'Result':<6}  Findings"]
    for r in results:
        value = "-" if r.measured_value is None else f"{r.measured_value:.1f}%"
        threshold = f"{r.comparison} {r.threshold:g}%"
        lines.append(
            f"{r.check_number} {r.check_name:<22} {value:>7}  {threshold:<9}  "
            f"{r.status:<6}  {r.offending_count}/{r.total_applicable}"
        )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if not 1 <= len(argv) <= 2:
        print("usage: python -m metrics.ratios <programme.ttl> [shapes.ttl]")
        return 2
    data = Graph().parse(argv[0])
    shapes = Graph().parse(argv[1] if len(argv) == 2 else DEFAULT_SHAPES_FILE)
    print(format_table(compute_ratios(data, shapes)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
