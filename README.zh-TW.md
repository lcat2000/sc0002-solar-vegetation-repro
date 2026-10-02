# SC0002 太陽光電開發 / 光譜植被變化

**可重現個案研究 · 台灣高雄 · Sentinel-2 + 政府地號資料 + matched controls**

**[專案說明頁](https://sc0002-solar-vegetation-repro.vercel.app)** · [English README](README.md) · [驗證指南](docs/VERIFY.md) · [研究方法](docs/METHOD.md) · [完整重跑](docs/REPRODUCE.md) · [限制](docs/LIMITATIONS.md)

這個 repository 整理 SC0002 個案的**完整公開稽核鏈**。第三方可以選擇：

1. **完全離線驗證已封存結果**，不需要 Google Earth Engine 帳號；或
2. **重新執行完整方法**，包括 Google Earth Engine 分析。

本研究刻意使用 **spectral vegetation loss / decline（光譜植被下降）**，不把 NDVI/NDMI 直接稱為「樹木損失」，也不把 matched-control 差距稱為 causal treatment effect。

---

## 研究問題

> SC0002 在 2022 年後是否出現大幅光譜植被下降，而且其時間與空間位置是否與清除整地及後續光電施工的獨立影像證據一致；同時，此變化是否明顯大於開發前條件相似的 matched controls？

## 主要封存結果

以 Sentinel-2 SR Harmonized、每年 3–7 月、P70 NDVI/NDMI、固定 UTM 10 m grid：

```text
2022 baseline spectral vegetation    58.239810 ha
2022→2026 standard spectral loss     16.795013 ha
loss fraction                         28.8377%
```

五個 controls 在查看 2023–2026 NDVI/NDMI outcome **以前**就已凍結：

```text
C162, C172, C176, C222, C129
```

| 年份 | SC0002 | Control mean | 當年最高 control | SC0002 − control mean |
|---|---:|---:|---:|---:|
| 2023 | 25.67% | 0.73% | 1.52% | +24.93 pp |
| 2024 | 18.96% | 0.52% | 1.45% | +18.44 pp |
| 2025 | 36.99% | 0.71% | 1.18% | +36.28 pp |
| 2026 | 28.84% | 1.30% | 2.25% | +27.54 pp |

Mean、median、trimmed mean、最高-loss control、leave-one-control-out 與有效資料覆蓋 sensitivity 均通過。

**解讀提醒。** 2022→2026 combined rule 與 NDVI-only 數值非常接近（`28.84%` vs `29.33%`），而 NDMI-only 變異較大，2020→2021 開發前 null 為 `43.02%`。因此 NDMI 在主分析中視為額外的保守條件，而不是獨立確認訊號。逐月比較在低 observation 月份也非常不穩定，因此本研究不宣稱精確的清除起始日期。詳見 [限制](docs/LIMITATIONS.md) 與 [預期結果](docs/EXPECTED_RESULTS.md)。

---

# 最快驗證方式 — 不需要 GEE

### Windows PowerShell

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -3.13 -m pip install -r requirements-verify.txt
py -3.13 src\verify\verify_all.py
```

或：

```powershell
.\verify.ps1
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-verify.txt
python3 src/verify/verify_all.py
```

或：

```bash
./verify.sh
```

預期最後顯示：

```text
ALL PASS — repository archive, AOI, raw GEE exports, full control-candidate chain, RGB review archive, derived analyses, rasters, results, hashes, and control-selection invariance verified.
```

驗證內容包括：

- SHA-256 檔案雜湊；
- AOI geometry / properties；
- Step 2 V4 光譜結果與 raster QA；
- Step 3A / 3A.1 raw GEE exports；
- Step 3B.1 **432 candidates → 60 hard-pass → exact Top20**；
- Step 3B.2 20 張 RGB review contact sheets + 年度 metadata；
- final control selection 與 screening-invariance；
- Step 3B.3 **30-row raw site-outcome CSV**、6-site geometry、6 個 loss TIFF；
- 由 raw 30-row CSV 離線重建 Step 3B.3 / 3B.4；
- Step 3B.4 LOO / conservative-control / coverage checks。

完整 audit matrix： [docs/VERIFY.md](docs/VERIFY.md)

---

# 核心方法

```text
Sentinel-2:      COPERNICUS/S2_SR_HARMONIZED
年度期間:         3月1日–7月31日
年度統計:         per-pixel P70
CRS:             EPSG:32651
固定 grid:        10 m
Transform:       [10, 0, 0, 0, -10, 0]
```

SCL 排除：

```text
0, 1, 3, 7, 8, 9, 10, 11
```

指標：

```text
NDVI = (B8 - B4) / (B8 + B4)
NDMI = (B8 - B11) / (B8 + B11)
```

2022 baseline spectral vegetation：

```text
NDVI_P70 >= 0.55
AND
NDMI_P70 >= 0.10
```

Standard loss：

```text
2022 baseline vegetation
AND (NDVI_2022 - NDVI_target) >= 0.20
AND (NDMI_2022 - NDMI_target) >= 0.10
```

正式面積用 `ee.Image.pixelArea()` 在 AOI 內積分；GeoTIFF pixel-count area 只作 QA。

---

# 證據鏈

## 1. 政府資料 / AOI

來源：經濟部能源署 **取得電業設置發電設備工作許可證太陽光電案場土地地號**，`set_id=344`。

封存研究範圍：民國 108–113 年（2019–2024）。

Validated SC0002 reconstruction：

```text
official input records       107
located                      106
unresolved                     1
connected clusters             3
chosen cluster points         93
EPSG:3826 planar area    63.304526 ha
Earth Engine geodesic    63.456375 ha
```

Exact V4 AOI：

```text
data/aoi/SC0002_Envelope_USED_BY_GEE_V4.geojson
```

Public GEE scripts 已直接嵌入這個 AOI，不需要私人 GCP project / Earth Engine asset。

## 2. Google Earth 歷史影像

判讀紀錄：

```text
data/evidence/google_earth/historical_image_review.csv
```

```text
2022-02-02  植被為主
2023-05-05  已可見大規模清除 / 整地
2024-02-17  光電施工
2025-03-08  大面積規則 PV arrays
2026-02-12  成熟光電場持續存在
```

第三方 Google Earth screenshots 不隨 repository 再散布。Reviewer 應自行以相同 AOI / 日期重新確認。2023-05-05 只能證明「截至該日清除已發生」，不是 exact onset date。

## 3. Step 3A robustness

Repository 已封存 Step 3A / Step 3A.1 raw GEE exports，包括：

- 2020 / 2021 / 2022 baseline-year sensitivity；
- NDVI-only / NDMI-only / combined ablation；
- pre-development null comparisons；
- event-window；
- monthly / same-season bimonth temporal-break analysis。

數值見 [docs/EXPECTED_RESULTS.md](docs/EXPECTED_RESULTS.md)。

## 4. Matched controls 完整 audit trail

Step 3B.1：

```text
432 all candidates
→ 60 hard-pass candidates
→ Top20 by ascending pre-treatment match_score
```

Pre-treatment `match_score` 嚴格使用 **9 個變數**：

- 2020、2021、2022 P70 NDVI/NDMI（6 項）；
- 2022 baseline vegetation fraction（1 項）；
- SRTM elevation / slope（2 項）。

2020–2022 valid observations 是 hard screen（每年 `>=10`），**不進 match_score**；geographic distance 只定義 deterministic **2–12 km candidate-search ring**，也**不進 match_score**。**Ranking 不使用 2023–2026 NDVI/NDMI outcome。**

Step 3B.2 已封存：

```text
20 張 Top20 RGB contact sheets
140 control-year metadata rows = 20 controls × 7 years
screening decisions
final-control status
```

Visual screen 使用 post-treatment true-color imagery，理論上可能帶來方向性 selection bias，因此 [LIMITATIONS.md](docs/LIMITATIONS.md) 有明確說明。不過 verifier 也會檢查：即使強制 C221、C171、兩者、甚至所有 Top20 全部 PASS，依照原本 spatial-selection rule，final five 仍然不變。

Final selection rule：

```text
screen_pass = YES
→ pre-treatment match_score 升冪
→ greedy center separation >= 2 km
→ max 5 controls
```

Final controls：

```text
C162, C172, C176, C222, C129
```

---

# Repository 結構

```text
.
├── README.md
├── README.zh-TW.md
├── LICENSE
├── CHANGELOG.md
├── SHA256SUMS.txt
├── verify.ps1
├── verify.sh
├── requirements.txt
├── requirements-verify.txt
├── site/
│   ├── index.html
│   └── vercel.json
├── .github/workflows/verify-reference.yml
├── docs/
│   ├── VERIFY.md
│   ├── AUDIT_TRAIL.md
│   ├── METHOD.md
│   ├── REPRODUCE.md
│   ├── EXPECTED_RESULTS.md
│   ├── REPRODUCIBILITY_STATUS.md
│   ├── RELEASE_CHECKLIST.md
│   ├── PUBLISH_TO_GITHUB.md
│   └── LIMITATIONS.md
├── src/
│   ├── aoi/
│   ├── gee/
│   ├── screening/
│   ├── analysis/
│   └── verify/
└── data/
    ├── aoi/
    ├── evidence/google_earth/
    └── reference/
        ├── step2/
        ├── step3a/
        ├── step3a1/
        ├── step3b1/
        ├── step3b2/
        ├── step3b3/
        └── step3b4/
```

---

# 完整重跑

完整重現政府資料、NLSC、AOI 與 GEE 分析：

**[docs/REPRODUCE.md](docs/REPRODUCE.md)**

---

# 解讀界線

本 repository 支持：

> SC0002 在 2022 年後出現大幅且持續的 site-specific spectral vegetation decline；其時間與空間位置與獨立判讀的清除整地及後續光電施工一致，而且變化幅度明顯大於五個以開發前條件匹配、且 outcome-blind ranking 的 controls，並通過封存 sensitivity checks。

本 repository 本身不支持：

- 直接稱為樹種 / 樹冠損失；
- 法律地籍層級的精確施工面積；
- 將所有 changed pixels 都歸因於 PV modules；
- causal treatment-effect estimate；
- 專案層級法律或因果責任。

詳見 [docs/LIMITATIONS.md](docs/LIMITATIONS.md)。

---

# 建議 GitHub 設定

Repository 名稱：

```text
sc0002-solar-vegetation-repro
```

Description：

```text
Reproducible Sentinel-2 case study of post-development spectral vegetation change at SC0002, Kaohsiung, with archived government-data AOI, matched controls, raw GEE exports, RGB review evidence, and offline verification.
```

Topics：

```text
remote-sensing sentinel-2 google-earth-engine ndvi ndmi solar-pv
reproducible-research environmental-monitoring taiwan geospatial
```

## License

程式碼採 MIT License。政府資料、NLSC、Sentinel data 與第三方歷史影像仍依各自授權與服務條款。
