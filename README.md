# Stock replication with derived land controls

This version integrates `land_controls.py` into `stocks.py`, retains the EP3 equipment/R&D correction, and generates the six retained paper tables, figures, and narrative values. It uses the four Financial Accounts CSVs uploaded together on October 12, 2026. Their embedded observations, not previously typed controls, determine the land valuation multiples.

Replace all Python source files together and restart an IDE/notebook kernel. Use the included `data/` folder, or copy its four Financial Accounts CSVs into your existing stock-data folder. The package normalizes the downloaded filenames by removing browser suffixes such as `(2)`; file contents are unchanged.

```bash
python land_controls.py
python tests/test_land_controls.py
python tests/test_all.py
python reproduce.py
python tests/test_paper_reporting.py --check-outputs
```

The default driver runs the stock analysis and Section 41 sensitivity. It does not run the retired investment-flow METR exercise. Results go to `results/`.

## Land construction

The default is total real estate, Z.1 structure subtractions, and `matched` scaling. All inputs below are 2022 year-end levels in billions of dollars:

| Input | Series | Frequency / required date | Value |
|---|---|---|---:|
| Total real estate at market value | NCBREMV | Quarterly / 2022-10-01 | 16,281.440 |
| Nonresidential real estate at market value | BOGZ1FL105035033A | Annual / 2022-01-01 | 14,871.049 |
| Nonresidential structures at current cost | RCSNNWMVBSNNCB | Quarterly / 2022-10-01 | 13,051.255 |
| Residential structures at current cost | RCVSRNWMVBSNNCB | Quarterly / 2022-10-01 | 334.272 |

FRED CSV values are millions of dollars; the reader divides by 1,000. Quarterly Oct. 1 labels describe the Q4 end-of-period level; the annual Jan. 1 label describes that year's year-end level. The reader requires the exact expected date and rejects duplicate dates, incorrect series headers, missing year-end values, and negative residuals.

Total residual land is 16,281.440 - 13,051.255 - 334.272 = 2,895.913. Nonresidential residual land is 14,871.049 - 13,051.255 = 1,819.794. The numerator components all cover Z.1 nonfinancial corporate business, including C and S corporations.

The SOI all-corporation book-land denominator excluding sector 52 is 880.334826. C-corporation book land across all sectors is 721.315422. Therefore:

- Total valuation multiple = 2,895.913 / 880.334826 = approximately 3.289559.
- Total C-corporation land = multiple times 721.315422 = approximately 2,372.809352.
- Nonresidential multiple = 1,819.794 / 880.334826 = approximately 2.067161.
- Nonresidential C-corporation land = approximately 1,491.075257.

`stocks.land_factor()` delegates to this module. Existing names `SOI_book`, `residual_nonres_RE`, and `residual_total_RE` remain supported; the standalone module also accepts `nonres` and `total`. SOI book value retains factor 1. The same 2022 multiple is applied to both 2016 and 2022 stocks. The main historical comparison does not estimate a separate 2016 multiple.

## Explicit coverage and valuation assumptions

`LAND_NONFIN_EXCLUDE = ("52",)` is an approximate SOI/Z.1 sector crosswalk. Financial holding companies within sector 55 and SOI consolidation differences are not separately reconciled. Excluding all of sector 55 would also remove nonfinancial management companies and is not an automatic correction. Equity REITs are included in Z.1 nonfinancial corporations in releases since December 2023; mortgage REITs remain financial.

The default applies one market/book uplift to C-corporation land in every industry, including finance. It assumes the measured multiple is applicable across legal forms and industries. The resulting C-corporation total is an allocated estimate, not a separately observed market-value C-corporation total. This qualification is carried into the audit and reporting outputs.

The nonresidential basis omits residential land but uses a book-land denominator that includes it. It is a valuation sensitivity, not a fully matched alternative total. The total basis is the main specification.

`LAND_SCALING = "ccorp"` retains the earlier, population-mismatched scaling method as an explicit comparison option: it assigns the entire source-sector residual to C corporations. `LAND_STRUCTURES = "bea"` uses all-corporation BEA structures and is also a deliberately mismatched comparison. The audit additionally shows BEA line 39 nonfinancial nonresidential structures; BEA residential line 3 still covers all corporations. There is no automatic fallback from missing Z.1 files to these comparisons.

The old 1,654 and 2,572 values remain in `LAND_LEGACY_CONTROLS` solely for comparison. They are never used in stock construction. Their historical derivation is not recovered by this change.

## Reproducibility and outputs

`land_control_inputs.csv` distinguishes the source-sector residual from the implied C-corporation control. It records book totals, reference year, exclusions, scaling, factors, old comparison controls, and coverage notes. `land_control_source_audit.csv` records each selected observation, date, frequency, units, source filename, SHA-256 hash, upload capture date, and residual arithmetic. The CSVs do not embed a release vintage; the capture date and file hashes identify the supplied extracts. BEA comparisons also record extract revisions and line numbers.

`paper_report.md`, `paper_tables.tex`, and separate table fragments contain all six retained tables. `paper_values.csv` and `paper_values.tex` contain replacement narrative scalars. `welfare_summary.csv` contains annual capital-service cost, excess burden, its three components, and uniform-wedge comparisons. Unrounded stock/service matrices, industry detail, historical comparisons, land sensitivities, elasticity sensitivities, no-credit results, and updated figures are included.

Depreciation inputs, tax schedules, saver returns, elasticity calibration, and all produced-asset stocks are unchanged from the preceding EP3-corrected version. The equipment aggregation diagnostics retain their disclosed component proxies. The numerical changes in this version come from the revised land construction and refreshed real-estate observations.

The manuscript delivered before this land revision still uses the preceding land inputs. Use the new generated tables, scalar outputs, and figures for its next numerical update; this package does not edit the manuscript.

## Sources

- Total real estate: https://fred.stlouisfed.org/series/NCBREMV
- Nonresidential real estate: https://fred.stlouisfed.org/series/BOGZ1FL105035033A
- Nonresidential structures: https://fred.stlouisfed.org/series/RCSNNWMVBSNNCB
- Residential structures: https://fred.stlouisfed.org/series/RCVSRNWMVBSNNCB
- Financial Accounts sector descriptions: https://www.federalreserve.gov/releases/z1/20260911/z1_tables_description.pdf
