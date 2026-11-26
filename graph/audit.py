"""12 DCMA kontrolünü tek çağrıyla çalıştıran giriş noktası (kontrol 1–11 ve BEI).

Kim kullanacak?
    - Esra'nın CLI'si (cli/): her Excel dosyası için audit_programme(project).
    - Arda Özcan'ın rapor yazıcısı (report/): dönen AuditReport'tan
      Summary (check_results) ve Findings (findings) sayfalarını yazar.

Ne yapar? (proposal'daki sıra: Mapper -> Validator -> Metrics)
    1. İki kural dosyasını BİRLİKTE yükler:
         shapes/dcma_1_5.ttl                 kontrol 1–5   (Burak)
         shapes/float_date_resource_shapes.ttl  kontrol 6–11, 14 (Arda Çiftçi)
    2. pySHACL'ı BİR KEZ çalıştırır -> bulgular (Findings), kontrol numarasıyla.
    3. Oranları hesaplar:
         kontrol 1–5   -> graph/ratios.py   (shapes/queries/*.rq sorguları)
         kontrol 6–14  -> graph/metrics.py  (Arda'nın fonksiyonları)
    4. Hepsini numara sırasıyla tek sözlükte birleştirir: {1: ..., 11: ..., 14: ...}

Neden iki ayrı oran modülü?
    1–5 ve 6–11 farklı zamanlarda, farklı kalıplarla yazıldı. Teslimden önce
    birini diğerine taşımak riskli; bu dosya ikisini olduğu gibi birleştirir.
    Dışarıya tek bir arayüz (bu dosya) ve tek bir sonuç sınıfı
    (graph.models.CheckResult) görünür. İçeride sonradan birleştirilebilir.

Eşikler nereden gelir? (Story 5)
    Hepsi kural dosyalarından: oran eşikleri sched:CheckN düğümlerinden,
    6 ve 8'in gün sınırı (44) shape'lerdeki sh:maxInclusive'den. Kodda eşik yok.

Kendin dene (proje klasöründe, .venv aktifken):
    python -m graph.audit tests/data/ornek_program.ttl
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

from rdflib import Graph

from graph.metrics import evaluate_checks_6_to_11_and_bei
from graph.models import AuditReport, CheckResult, Finding, Project, programme_to_graph
from graph.ratios import compute_ratios
from graph.validator import (
    SH,
    get_shape_threshold,
    load_ratio_thresholds,
    load_shapes_graph,
    validate_programme_graph,
)
from graph.vocabulary import SCHED

ROOT = Path(__file__).resolve().parent.parent

# Varsayılan kural dosyaları. Firma kendi eşikleriyle bir kopya kullanmak
# isterse shapes_files parametresiyle başka dosyalar verebilir.
SHAPES_FILES = (
    ROOT / "shapes" / "dcma_1_5.ttl",
    ROOT / "shapes" / "float_date_resource_shapes.ttl",
)

# BEI bir indeks (0.95), diğerleri yüzde (5.0 = %5). Sadece ekrana yazarken
# fark eder; CheckResult içinde ikisi de düz sayı.
INDEX_CHECKS = {14}


def run_all_checks(
    data: Graph,
    shapes_files: Iterable[str | Path] = SHAPES_FILES,
) -> tuple[dict[int, CheckResult], list[Finding]]:
    """Bir programın grafiğinde 12 kontrolü çalıştırır.

    Döndürür:
        sonuçlar  {kontrol numarası: CheckResult}, numara sırasıyla (1–11, 14)
        bulgular  [Finding, ...] — her ihlal bir satır, kontrol numarasıyla
    """
    shapes_files = [Path(p) for p in shapes_files]
    shapes = load_shapes_graph(shapes_files)

    # 1) SHACL: tek tek bulgular (iki dosya birlikte, advanced=True ile).
    findings = validate_programme_graph(data, shapes_files)

    # 2) Kontrol 1–5 oranları. compute_ratios sadece sched:ratioQuery'si
    #    olan kontrolleri çalıştırır; Arda'nın 6–14 düğümlerinde bu alan
    #    yok, o yüzden birleşik kural grafiğinde de sadece 1–5'i alır.
    results = {r.check_number: r for r in compute_ratios(data, shapes)}

    # 3) Kontrol 6–11 ve BEI. Eşikler kural dosyasından (Arda'nın
    #    run_float_date_resource_audit'teki adımların aynısı).
    max_float = get_shape_threshold(shapes, SCHED.Check6_HighFloatShape, SH.maxInclusive, 44.0)
    max_duration = get_shape_threshold(shapes, SCHED.Check8_HighDurationShape, SH.maxInclusive, 44.0)
    results.update(
        evaluate_checks_6_to_11_and_bei(
            data,
            max_float=max_float,
            max_duration=max_duration,
            thresholds=load_ratio_thresholds(shapes),
        )
    )

    return dict(sorted(results.items())), findings


def audit_programme(
    project: Project,
    shapes_files: Iterable[str | Path] = SHAPES_FILES,
) -> AuditReport:
    """Reader'dan gelen Project'i grafiğe çevirir ve 12 kontrolü çalıştırır.

    CLI ve rapor yazıcı bunu çağıracak.
    """
    results, findings = run_all_checks(programme_to_graph(project), shapes_files)
    return AuditReport(project=project, check_results=results, findings=findings)


# --- Komut satırından deneme -----------------------------------------------

def format_summary(results: dict[int, CheckResult]) -> str:
    """Summary sayfasının terminaldeki karşılığı."""
    lines = [f"{'Check':<36} {'Value':>7}  {'Threshold':<9}  {'Result':<14}  Findings"]
    for n, r in results.items():
        if n in INDEX_CHECKS:
            value = "-" if r.measured_value is None else f"{r.measured_value:.2f}"
            threshold = f"{r.comparison} {r.threshold:g}"
        else:
            value = "-" if r.measured_value is None else f"{r.measured_value:.1f}%"
            threshold = f"{r.comparison} {r.threshold:g}%"
        lines.append(
            f"{n:<3}{r.check_name:<33} {value:>7}  {threshold:<9}  "
            f"{r.status:<14}  {r.offending_count}/{r.total_applicable}"
        )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python -m graph.audit <programme.ttl>")
        return 2
    results, findings = run_all_checks(Graph().parse(argv[0]))
    print(format_summary(results))
    print(f"\n{len(findings)} findings")
    for f in findings:
        print(f"  Check {f.check_number:<3} {f.target_id:<16} {f.message}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
