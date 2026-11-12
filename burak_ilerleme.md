# Burak — İlerleme Notları

Bu dosya sadece `burak` branch'inde tutulur, main'e gitmez.
Her tamamlanan iş tarihiyle birlikte madde madde eklenir.

## Dosya rehberi (hangi dosya ne işe yarar)

| Dosya | Ne işe yarar | Kim yazdı |
|---|---|---|
| `shapes/dcma_1_5.ttl` | **Benim modülüm.** DCMA kontrol 1–5 için SHACL kuralları. Her kural hatalı aktiviteyi/bağlantıyı işaretler. İçinde her kontrol için yorumlu açıklama var. | Claude (kontrol 2'nin ilk sürümü ben) |
| `tests/data/ornek_program.ttl` | Elle yazılmış 9 aktivitelik örnek program. İçinde her kontrol için bilerek konmuş bir hata var. | Claude |
| `tests/test_dcma_1_5.py` | 16 pytest testi. Her kontrolün doğru öğeyi bulduğunu ve yanlış öğeyi bulmadığını kontrol eder. | Claude |
| `.gitignore` | `.DS_Store`, `__pycache__`, `.pytest_cache`, `.venv` git'e girmesin. | Claude |
| `burak_ilerleme.md` | Bu dosya. Sadece `burak` branch'inde kalacak. | Claude + ben |
| `proposal/` | Takımın proposal'ı. Dokunmuyoruz. | Arda Özcan |

**Her şeyi tek komutla dene** (proje klasöründe, `.venv` aktifken):

```bash
pytest
```

`16 passed` görmelisin. Bulguları tek tek görmek istersen:

```bash
pyshacl -a -s shapes/dcma_1_5.ttl tests/data/ornek_program.ttl
```

**Okuma sırası önerisi:** önce `tests/data/ornek_program.ttl` (veri), sonra `shapes/dcma_1_5.ttl` (kurallar), en son `tests/test_dcma_1_5.py` (testler).

## 2026-11-10

- Repo bilgisayara klonlandı (`~/code/schedule_quality_checker`).
- Proposal okundu (`proposal.md`, `proposal.json`, `proposal_lineage.ttl`); proje ve görevlerim çıkarıldı:
  - Ana sorumlu: Logic and constraint shapes (DCMA 1–5)
  - İkinci kişi: Programme vocabulary (Eylem), Float/date/resource shapes 6–11 + BEI (Arda Çiftçi)
  - 27 Kasım teslimatının lideri: 12 kontrolün tamamı için SHACL + SPARQL
  - Roller: Process facilitator, System analysis lideri
- DCMA 1–5 kaynakları okundu (Mosaic WP1088, Deltek Acumen) ve sayım kuralları çıkarıldı:
  - Payda: tamamlanmamış task'lar (tamamlanmış, LOE, summary ve milestone hariç)
  - Bağlantı kontrollerinde (2, 3, 4): ardılı tamamlanmamış task olan bağlantılar
  - 1 Logic ≤ %5 · 2 Leads = 0 · 3 Lags ≤ %5 · 4 FS ≥ %90 · 5 Hard constraints ≤ %5
  - Sert kısıtlar (öneri): MSO, MFO, SNLT, FNLT, Mandatory Start, Mandatory Finish
- Takıma sorulacak açık sorular belirlendi:
  - Eylem: sınıf ve property adları
  - Aysu: durum/tür/kısıt değerleri, lag birimi
  - Arda Çiftçi: payda kuralı 6–11 için de aynı mı, oran/bulgu formatı
  - Mehmet + Arda Özcan: Story 3'te kontrol 1 "fail" değil, sadece bulgu listeler (eşik %5)
- `burak` branch'i açıldı.

## 2026-11-11

- Claude ile çalışma şekli belirlendi:
  - Kurulum ve test grafiği: Claude yazar, satır satır açıklar, onayımla ilerler.
  - Kontrol 1–2 shape'leri ve SPARQL oranları: ben yazarım, Claude yönlendirir. Öncesinde kısa bir SHACL girişi.
  - Kontrol 3–5: ben tek başıma yazarım, Claude review eder.
  - Her adım: önce anlatım → tek küçük değişiklik → komutu ben çalıştırırım → kendi cümlelerimle özetlerim.
  - Küçük, Türkçe mesajlı commit'ler; diff'i birlikte okuyup ben onaylayınca commit.
  - **Neden:** Modülün sahibi benim; demoda ve notlandırmada kodu anlatabilmem gerekiyor. Süre kısa olduğu için her şeyi elle değil, sadece projenin özünü kendim yazıyorum.
- Python sanal ortamı (`.venv`) kuruldu: Python 3.13.9, rdflib 7.6.0, pyshacl 0.40.2, openpyxl 3.1.5, pytest 9.2.0.
  - **Neden:** Paketler Anaconda'daki genel Python ile karışmasın; bozulursa `.venv` silinip yeniden kurulabilir.
  - **Ne öğrendim:** Her yeni terminalde `source .venv/bin/activate` gerekiyor. Python 3.13 `.venv` içine kendi `.gitignore` dosyasını koyduğu için klasör git'te görünmüyor.
- Elle yazılmış test grafiği eklendi: `tests/data/ornek_program.ttl` (9 aktivite, 7 bağlantı, 84 triple).
  - Bilerek konulan hatalar: A5 ardılı yok (1), R6 lead (2), R4 lag (3) ve SS (4), A4 Must Finish On (5).
  - **Neden:** Reader ve generator'ı beklemeden her shape'in doğru öğeyi bulduğunu görebilmek için.
  - **Kararlar:** Bağlantılar ayrı düğüm (tür ve lag bağlantının özelliği). İsimler (`sqc:`) geçici, Eylem'in sözlüğüne göre değişecek. Dosya `tests/` altında, çünkü kapsam dışı commit hedefi 0.
  - **Ne öğrendim:** Turtle'da `;` aynı konu için yeni özellik, `.` konunun sonu. Küçük programda tek hata bile yüksek oran (%20) verir.
- Kısa SHACL girişi: hedef (`sh:targetClass`), yol (`sh:path`), kısıt (`sh:minInclusive`, `sh:minCount`, `sh:in`), ihlal raporu (focus node, value, path, message).
- İlk shape yazıldı ve çalıştı: `shapes/dcma_1_5.ttl` → `sqcs:Kontrol2_Leads`. pySHACL sadece `ex:R6`'yı (lag = −1) yakaladı.
  - **Neden böyle:** Lag bağlantının özelliği, bu yüzden hedef `sqc:Relationship`. "Negatif olmasın" = `sh:minInclusive 0`.
  - **Ne öğrendim:** VS Code'da kaydetmeyi unutunca dosya boş kalıyor; boş shape dosyası `Conforms: True` verir. Yani "hata yok" her zaman "doğru çalıştı" demek değil. Klasör adı proposal'la aynı olmalı (`shapes/`).
  - **Sonra eklenecek:** Sadece ardılı tamamlanmamış task olan bağlantılar sayılmalı (şimdilik tüm bağlantılar kontrol ediliyor).

## 2026-11-12

- Çalışma şekli değişti: adım adım yazışmak yavaş ve pahalıydı. Artık Claude bir paketi tek seferde yazıyor, kodlara Türkçe yorum koyuyor, açıklamaları bu dosyaya yazıyor; ben VS Code'da okuyup inceliyorum, takıldığım yeri toplu soruyorum.

- `ardac` branch'i okundu (sadece okuma, hiçbir şey değişmedi). Arda Çiftçi şunları yazmış:
  - `graph/vocabulary.py` — sözlük: namespace `sched:` = `http://example.org/schedule#`
  - `graph/models.py` — dataclass'lar ve Excel → RDF mapper (`programme_to_graph`)
  - `shapes/float_date_resource_shapes.ttl` — kontrol 6, 7, 8, 10

- Geçici `sqc:` isimleri Arda'nın sözlüğüne uyarlandı:

  | Eski (geçici) | Yeni (Arda'nın sözlüğü) |
  |---|---|
  | `sqc:name` | `sched:activityName` / `sched:projectName` |
  | `sqc:lagDays` | `sched:lag` (ondalık) |
  | `sqc:relType` | `sched:relationshipType` |
  | `ex:A5`, `ex:R6` | `sched:activity_A5`, `sched:relationship_6` |
  | `"task"`, `"NotStarted"` | `"Task"`, `"Not Started"` |

- **DCMA 1–5 shape'lerinin hepsi yazıldı** (`shapes/dcma_1_5.ttl`) ve örnek programda tam beklenen 5 bulguyu veriyor:

  | Kontrol | Shape adı | Bulduğu | Nasıl |
  |---|---|---|---|
  | 1 Logic | `Check1_MissingPredecessor` / `Check1_MissingSuccessor` | A5 (ardılı yok) | Ters yol + `sh:minCount 1` |
  | 2 Leads | `Check2_NegativeLag` | R6 (lag −1) | `sh:minInclusive 0` |
  | 3 Lags | `Check3_PositiveLag` | R4 (lag +2) | `sh:maxInclusive 0` |
  | 4 Rel. types | `Check4_NonFinishToStart` | R4 (SS) | `sh:in ("FS")` |
  | 5 Hard constr. | `Check5_HardConstraint` | A4 (Must Finish On) | `sh:not [ sh:in (...) ]` |

  - **Neden SPARQL hedefi:** `sh:targetClass` filtre koyamıyor. "Tür = Task ve durum ≠ Completed" filtresi için küçük bir SPARQL sorgusu kullanıyoruz. Bağlantı kontrolleri (2, 3, 4) aynı hedefi paylaşıyor: `sched:CountedRelationshipTarget`.
  - **Neden property shape'lere isim verdik:** Raporda `sh:sourceShape` olarak bu isim çıkıyor; bulgunun hangi kontrolden geldiği buradan anlaşılıyor. Rapor yazıcı (Arda Özcan) bunu kullanacak.
  - **Neden mesajlar İngilizce:** Arda'nın 6–11 shape'leri İngilizce, rapor tutarlı olsun diye. Kontrol 2'deki Türkçe mesajın değişti; Türkçe istersen geri çevirebiliriz.

- **16 pytest testi** eklendi (`tests/test_dcma_1_5.py`), hepsi geçiyor. Neyi test ediyorlar:
  - Örnek programda tam 5 bulgu var; hatalar düzeltilince 0 bulgu kalıyor (nominal senaryo).
  - Milestone, LOE ve tamamlanmış aktiviteler sayılmıyor.
  - Sınır değer: lag = 0 kontrol 3'te sorun değil.
  - SS, FF, SF'nin üçü de kontrol 4'te yakalanıyor; yumuşak kısıt (Start No Earlier Than) kontrol 5'te yakalanmıyor.
  - Tuzak testi: `advanced=False` ile hiçbir şey bulunmuyor.

- **Ne öğrendim / bilmem gerekenler (demoda sorulabilir):**
  - SHACL kuralı = hedef (kimi kontrol et) + yol (neye bak) + kısıt (neye uymalı).
  - Ters yol (`sh:inversePath`): aktivite kendi öncülünü bilmez, bağlantılara "beni gösteren var mı?" diye sorarız.
  - Shape'ler sadece tek tek hatalı öğeleri işaretler. "%5'ten az mı?" sorusu ayrı: SPARQL ile oran hesabı (sıradaki iş).
  - pySHACL `-a` (advanced) olmadan SPARQL hedefleri sessizce boş kalır. "Hata yok" her zaman "doğru çalıştı" demek değil.

- **Arda'ya iletilecekler (önemli):**
  1. Mapper `predecessor` / `successor` değerini **metin** olarak yazıyor (`"A5"`). Aktivitenin kendisine (URI, `sched:activity_A5`) işaret etmeli; yoksa kontrol 1'in ters yolu çalışmaz ve bulgular aktiviteye bağlanamaz. Önerilen düzeltme `graph/models.py` içinde: `Literal(rel.predecessor, ...)` yerine `URIRef(f"{SCHED}activity_{rel.predecessor}")` (successor için de aynısı).
  2. Mapper tamamlanmışlığı `status != "complete"` ile kontrol ediyor. Şablondan `"Completed"` gelirse aktivite yanlışlıkla tamamlanmamış sayılır. `"complete"` ve `"completed"` ikisi de kabul edilmeli.
  3. `sched:IncompleteActivity` sınıfı milestone, LOE ve summary'leri de içeriyor. DCMA 1–5 için sadece task lazım, o yüzden ben kendi SPARQL hedefimi kullanıyorum. 6–11 için de aynı kural mı geçerli, birlikte karar verelim.

- **Aysu'ya iletilecek:** Kısıt adları şablondan tam bu yazımla gelmeli: `Must Start On`, `Must Finish On`, `Start No Later Than`, `Finish No Later Than`, `Mandatory Start`, `Mandatory Finish`. Tür değerleri `Task / Milestone / LOE / Summary`.

- **Sıradaki iş:** SPARQL ile oranlar ve geçti/kaldı kararı (kontrol 1–5), eşiklerin kural dosyasında parametre olarak durması (Story 5).

- Commit yapılmadı.
