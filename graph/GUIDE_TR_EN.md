# Schedule Quality Checker — Modül & Kural Kılavuzu (TR / EN)

---

## TÜRKÇE KILAVUZ

### 1. Projenin Amacı ve Genel İş Bölümü
Bu proje, inşaat projelerinde yüklenicilerin teslim ettiği iş programlarını (Excel şablonu üzerinden) **DCMA 14-Point Schedule Assessment** standartlarına göre otomatik denetleyen bir Python aracıdır. Excel verisi önce bir **RDF Bilgi Çizgesine (Knowledge Graph)** dönüştürülür, ardından **SHACL** kuralları ile hatalı satırlar yakalanır ve **SPARQL** sorguları ile her kontrolün oranı / geçti-kaldı durumu hesaplanır.

#### Ekip ve Modül Dağılımı (7 Üye)
| Alan / Modül | Klasör | Sorumlu | İkinci Üye | Görevi |
| :--- | :--- | :--- | :--- | :--- |
| **Template Reader** | `reader/` | Aysu Akdüzen | Esra Kaya | 3 sayfalı Excel şablonunu okuma, sütun kontrolü, regex ile temizleme |
| **RDF Vocabulary & Mapping** | `graph/` | Eylem Sarıbal | Burak Sami Şirin | Proje, aktivite ve ilişki sınıflarının RDF grafiğine aktarılması |
| **DCMA Checks 1–5** | `shapes/` | Burak Sami Şirin | Eylem Sarıbal | Logic, Leads, Lags, Relationship Types, Hard Constraints kuralları |
| **DCMA Checks 6–11 & BEI (14)** | `shapes/`, `graph/` | **Arda Çiftçi** | Burak Sami Şirin | High/Negative Float, High Duration, Invalid Dates, Resources, Missed Activities, BEI |
| **Excel Audit Report** | `report/` | Arda Özcan | Aysu Akdüzen | Summary, Findings ve Method sayfalı Excel raporunu üretme |
| **CLI & Folder Mode** | `cli/` | Esra Kaya | Arda Özcan | Tek dosya veya klasörü paralel (`ThreadPoolExecutor`) tarama |
| **Synthetic Programmes & Tests** | `tests/` | Mehmet Mert Seyhan | **Arda Çiftçi** | Hata tohumlanmış sentetik Excel üretimi ve `pytest` testleri |

---

### 2. Arda Çiftçi'nin Modül Yapısı ve Dosya Bölümü (`ardac` Branch'i)

Kodlar, `proposal.md` içindeki **Objective 4** kapsam kuralına uygun olarak yalnızca izin verilen `graph/`, `shapes/` ve `tests/` klasörleri altında düzenlenmiştir:

| Dosya | Görevi | İçindeki Ana Yapılar |
| :--- | :--- | :--- |
| `graph/vocabulary.py` | Ortak RDF terimler sözlüğü (`http://example.org/schedule#`) | `Project`, `Activity`, `Relationship`, `Check`, sütun ve metrik sabitleri |
| `graph/models.py` | Alan sınıfları (Domain dataclasses) ve RDF dönüştürücü | `Activity`, `Relationship`, `Project`, `Check`, `CheckResult`, `Finding`, `AuditReport`, `programme_to_graph()` |
| `shapes/float_date_resource_shapes.ttl` | Check 6–11 SHACL kuralları ve Check 6–11, 14 eşik tanımları | `sched:Check6`..`Check11`, `sched:Check14`, `IncompleteTaskTarget`, `PositiveDurationTaskTarget`, 6 adet `NodeShape` |
| `graph/metrics.py` | Check 6–11 oranları ve Check 14 (BEI) SPARQL hesaplamaları | Her kural için ayrı `def`: `calculate_check_6_high_float()` ... `calculate_check_14_bei()` + `evaluate_checks_6_to_11_and_bei()` |
| `graph/validator.py` | `pySHACL` doğrulayıcı ve dinamik eşik okuyucu (Story S5) | `load_shapes_graph()`, `load_check_definitions()`, `get_shape_threshold()`, `validate_programme_graph()`, `run_float_date_resource_audit()` |
| `tests/test_s4.py` | Story S4, sınır değeri (44/45 gün) ve boş baseline testleri | 4 adet `pytest` senaryosu |
| `tests/test_s5.py` | Story S5 (`.ttl` üzerinden eşik değiştirme) testleri | Gün sınırı (`44 -> 30`) ve yüzde sınırı (`5.0 -> 50.0`) testleri |
| `tests/test_integration_compat.py` | Burak'ın Check 1–5 modülüyle tam uyumluluk testleri | URI tabanlı bağlantılar, proje seviyesi `dataDate`, SHACL–SPARQL tutarlılığı |

---

### 3. Burak'ın Kurallarıyla (Check 1–5) Çakışmasız Paralel Uyum
İki modülün (`origin/burak` + `ardac`) ileride tek bir bütün olarak sorunsuz birleşmesi için şu ortak standartlar hizalanmıştır:

1. **Ortak Namespace ve URI Biçimi:** Her iki taraf da `sched: <http://example.org/schedule#>`, `sched:activity_<id>` ve `sched:relationship_<no>` URI yapısını kullanır.
2. **İlişki Bağlantıları (Check 1 Uyumu):** `programme_to_graph()` artık `sched:predecessor` ve `sched:successor` alanlarını metin (`"A5"`) yerine doğrudan aktivite URI'si (`sched:activity_A5`) olarak üretir.
3. **Aktivite Türü ve Durum Filtresi:** `IncompleteTaskTarget` (Checks 6, 7, 8) ve `PositiveDurationTaskTarget` (Check 10), tıpkı Check 1–5 gibi `LCASE(STR(?type)) = "task"` ve `LCASE(STR(?status)) NOT IN ("complete", "completed")` filtresini kullanır. Milestone, LOE ve Summary aktiviteleri sayım dışı bırakılır.
4. **Proje Seviyesi `dataDate` Desteği:** Check 9, Check 11 ve Check 14 sorguları `dataDate` bilgisini hem aktivite üzerinde hem de `sched:Project` düğümünde (`COALESCE(?actDD, ?projDD)`) okuyabilir.
5. **`pySHACL` Gelişmiş Mod (`advanced=True`):** `validator.py` doğrulamayı `advanced=True` ile çalıştırır ve birden fazla `.ttl` dosyasını (`dcma_1_5.ttl` + `float_date_resource_shapes.ttl`) aynı grafikte birleştirip tek seferde çalıştırabilir.
6. **Ortak `Check` ve `CheckResult` Şeması:** `.ttl` dosyasındaki `sched:Check6`..`Check14` düğümleri `sched:checkNumber`, `sched:checkName`, `sched:thresholdPercent` / `sched:thresholdIndex`, `sched:comparison` ve `sched:countingRule` alanlarını kullanarak raporun `Summary` ve `Method` sayfalarına aynı formatta veri sağlar.

---

### 4. Kontrollerin Özeti (Check 6–11 ve Check 14 BEI)
| No | Kontrol Adı | Kural (Hata Koşulu) | Oran / Formül | Geçme Eşiği |
| :--- | :--- | :--- | :--- | :--- |
| **6** | **High Float** | Tamamlanmamış `Task` işinde `totalFloat > 44` iş günü | `hatalı task / tamamlanmamış task * 100` | `<= %5.0` |
| **7** | **Negative Float** | Tamamlanmamış `Task` işinde `totalFloat < 0` iş günü | `hatalı task / tamamlanmamış task * 100` | `<= %0.0` (0 hata) |
| **8** | **High Duration** | Tamamlanmamış `Task` işinde `duration > 44` iş günü | `hatalı task / tamamlanmamış task * 100` | `<= %5.0` |
| **9** | **Invalid Dates** | Tamamlanmamış işin tahmini `start/finish < dataDate` veya herhangi bir işin `actualStart/actualFinish > dataDate` | `hatalı aktivite / tüm aktiviteler * 100` | `<= %0.0` (0 hata) |
| **10** | **Resources** | Süresi `> 0` olan tamamlanmamış `Task` işinde `resource` boş | `kaynaksız task / süresi > 0 tamamlanmamış task * 100` | `<= %0.0` (0 hata) |
| **11** | **Missed Activities** | `baselineFinish <= dataDate` olup tamamlanmamış veya `baselineFinish` sonrası bitmiş iş | `geciken / baseline bitişi <= dataDate * 100` | `<= %5.0` *(Baseline yoksa Not Applicable)* |
| **14** | **BEI** | Baseline'a göre bitmesi gereken işlere kıyasla tamamlanan işlerin oranı | `tamamlanan iş / (baselineFinish <= dataDate)` | `>= 0.95` *(Baseline yoksa Not Applicable)* |

### 5. Yerel Test Komutu
```bash
python -m pytest -v
```

---

## ENGLISH GUIDE

### 1. Project Overview & Team Division
The **Schedule Quality Checker** audits construction programmes exported from Primavera P6 or MS Project into a three-sheet Excel template (`Project`, `Activities`, `Relationships`). It converts schedule rows into an **RDF Knowledge Graph**, detects individual rule violations using **SHACL** shapes (`pySHACL`), and calculates pass/fail ratios and the Baseline Execution Index (BEI) using **SPARQL** queries.

#### Team & Responsibility Matrix (7 Members)
| Module / Feature | Folder | Primary Owner | Second Member | Responsibility |
| :--- | :--- | :--- | :--- | :--- |
| **Template Reader** | `reader/` | Aysu Akdüzen | Esra Kaya | Load 3-sheet Excel template via `openpyxl`, validate headers, clean values via regex |
| **Vocabulary & RDF Mapping** | `graph/` | Eylem Sarıbal | Burak Sami Şirin | Schedule ontology and row-to-RDF mapping |
| **Logic & Constraint Shapes (Checks 1–5)** | `shapes/` | Burak Sami Şirin | Eylem Sarıbal | Logic, Leads, Lags, Relationship Types, Hard Constraints |
| **Float, Date & Resource Shapes (Checks 6–11, BEI)** | `shapes/`, `graph/` | **Arda Çiftçi** | Burak Sami Şirin | High/Negative Float, High Duration, Invalid Dates, Resources, Missed Activities, BEI |
| **Excel Audit Report** | `report/` | Arda Özcan | Aysu Akdüzen | Generate 3-sheet Excel report (`Summary`, `Findings`, `Method`) |
| **CLI & Folder Mode** | `cli/` | Esra Kaya | Arda Özcan | Check single file or folder in parallel via `pathlib` + `ThreadPoolExecutor` |
| **Synthetic Programmes & Tests** | `tests/` | Mehmet Mert Seyhan | **Arda Çiftçi** | Seeded-defect synthetic generator and `pytest` acceptance tests |

---

### 2. Architecture of Arda Çiftçi's Module (`ardac` Branch)
To comply strictly with **Objective 4** in `proposal.md` (zero commits outside `reader/`, `graph/`, `shapes/`, `report/`, `cli/`, `tests/`), all module artifacts live within `graph/`, `shapes/`, and `tests/`:

* **`graph/vocabulary.py`**: Shared RDF namespace (`http://example.org/schedule#`) and predicates for activities, relationships, and `sched:Check` metadata.
* **`graph/models.py`**: Core domain dataclasses (`Activity`, `Relationship`, `Project`, `Check`, `CheckResult`, `Finding`, `AuditReport`) and `programme_to_graph()`.
* **`shapes/float_date_resource_shapes.ttl`**: `sched:Check` metadata nodes (`Check6`–`Check11`, `Check14`), `sh:SPARQLTarget` selectors (`IncompleteTaskTarget`, `PositiveDurationTaskTarget`), and 6 SHACL node shapes.
* **`graph/metrics.py`**: Independent SPARQL calculation function (`def`) per check (`calculate_check_6_high_float` through `calculate_check_14_bei`) plus `evaluate_checks_6_to_11_and_bei()`. Returns `"Not Applicable"` when denominator is 0 or baseline dates are absent.
* **`graph/validator.py`**: Unified SHACL + SPARQL runner (`load_shapes_graph`, `load_check_definitions`, `get_shape_threshold`, `validate_programme_graph`, `run_float_date_resource_audit`) supporting single or multiple `.ttl` files and Story S5 dynamic threshold edits.
* **`tests/test_s4.py`, `tests/test_s5.py`, `tests/test_integration_compat.py`**: Automated verification for Stories S4 and S5, boundary values (44 vs 45 days), absent baselines, completed-only schedules, and cross-module compatibility.

---

### 3. Conflict-Free Alignment with Checks 1–5 (`origin/burak`)
1. **Unified Namespace & URIs**: Uses `sched: <http://example.org/schedule#>`, `sched:activity_<id>`, and `sched:relationship_<idx>`.
2. **URI-Linked Relationships**: `programme_to_graph()` emits `URIRef` links (`sched:activity_A1`) for `sched:predecessor` and `sched:successor`, directly satisfying Check 1's graph traversal.
3. **Case-Insensitive Task & Status Filters**: Both Checks 1–5 and Checks 6–11 filter incomplete tasks with `LCASE(STR(?type)) = "task"` and `LCASE(STR(?status)) NOT IN ("complete", "completed")`, excluding `Milestone`, `LOE`, and `Summary` activities from task-only metrics.
4. **Project-Level `dataDate` Resolution**: Date checks (`Check 9`, `Check 11`, `Check 14`) resolve `dataDate` from either the activity or `sched:Project` (`COALESCE(?actDD, ?projDD)`).
5. **Advanced SHACL Execution**: `validate_programme_graph()` runs `pyshacl.validate(..., advanced=True)` and accepts multiple `.ttl` files so Checks 1–5 and Checks 6–11 can be validated together in one pass.

---

### 4. DCMA Checks Covered (6–11 & 14 BEI)
| Check | Metric | Violation Condition | Threshold |
| :--- | :--- | :--- | :--- |
| **6** | **High Float** | Incomplete task with `totalFloat > 44` working days | `<= 5.0%` |
| **7** | **Negative Float** | Incomplete task with `totalFloat < 0` working days | `<= 0.0%` (0 tasks) |
| **8** | **High Duration** | Incomplete task with `duration > 44` working days | `<= 5.0%` |
| **9** | **Invalid Dates** | Incomplete activity with forecast `start/finish < dataDate`, or any activity with `actualStart/actualFinish > dataDate` | `<= 0.0%` (0 activities) |
| **10** | **Resources** | Incomplete task with `duration > 0` missing a `resource` | `<= 0.0%` (0 tasks) |
| **11** | **Missed Activities** | Activity with `baselineFinish <= dataDate` that is incomplete or finished after `baselineFinish` | `<= 5.0%` *(Not Applicable if no baseline)* |
| **14** | **BEI** | Ratio of completed activities to activities planned to finish on or before `dataDate` | `>= 0.95` *(Not Applicable if no baseline)* |

### 5. Running the Verification Suite
```bash
python -m pytest -v
```
