# Land control integration

The four refreshed FRED extracts are validated and integrated through a new `land_controls.py`. `stocks.py` delegates its scaling factor to that module. `params.py` selects the structure source, scaling method, sector exclusions, reference year, and land bases. The old 1,654 and 2,572 controls are retained only as labelled historical comparison values; changing them cannot change current stock weights.

The default calculation uses total real estate and both structure series for Z.1 nonfinancial corporations. It measures an approximate nonfinancial all-corporation market/book multiple and applies it to C-corporation book land industry by industry. The same 2022 factor is used in both stock years.

## Reference-year arithmetic ($ billions)

- Total real estate: 16,281.440.
- Nonresidential structures: 13,051.255.
- Residential structures: 334.272.
- Total land residual: 2,895.913.
- SOI all-corporation book land excluding sector 52: 880.334826.
- Total valuation factor: approximately 3.289559.
- SOI C-corporation book land, all industries: 721.315422.
- Implied C-corporation land: 2,372.809352, versus the previous 2,572.

The nonresidential residual is 1,819.794; its factor is approximately 2.067161 and its implied C-corporation land is 1,491.075257, versus the previous 1,654.

These figures differ from the earlier provisional test because the refreshed real-estate downloads revise the 2022 observations. All four current source files were supplied together. Their release vintage is not embedded in the CSV; the source audit retains exact file hashes and the upload capture date.

## Baseline effects

| Metric | Previous EP3-corrected | Derived land |
|---|---:|---:|
| Mean wedge (%) | 5.6390 | 5.5572 |
| Between-industry SD (pp) | 5.2807 | 5.2195 |
| Within-industry SD (pp) | 10.0935 | 10.0535 |
| Excess burden / B (%) | 0.7442 | 0.7342 |
| Equivalent uniform wedge (%) | 15.7503 | 15.6443 |
| Annual excess burden ($ billions) | 23.6447 | 23.2456 |

## Coverage assumptions

Excluding SOI sector 52 is an approximate match to Z.1, not a complete reconciliation. Financial holding companies in sector 55 and consolidation differences remain unallocated. The measured valuation multiple is assumed to apply to all C-corporation industries, including finance, and across legal forms. Total real estate is the main basis because SOI book land includes residential land. The nonresidential basis is retained as a sensitivity.

Equity REITs are included in the Z.1 nonfinancial corporate sector in releases since December 2023; mortgage REITs remain financial. The module's description now reflects that distinction. BEA all-corporation and nonfinancial-structure comparisons are labelled diagnostics, with their coverage differences disclosed.

## Validation and use

All original stock checks pass. Thirteen land-control tests pass, covering exact date selection, missing and duplicate Q4 observations, source headers and units, residual arithmetic, invalid residuals/denominators, scaling identities, aliases, legacy-input independence, reference-year application to both stock years, and audit content. Five reporting tests pass against the regenerated outputs, including all six retained tables and welfare identities. All non-land cells in the 2022 main and both historical stock matrices are identical to the preceding version. Tax inputs and depreciation parameters are unchanged.

Extract the replication package and replace the Python files together; restart any notebook or IDE kernel. Use its `data/` folder or replace the four FRED CSVs in your existing data folder with the included versions. Run `python reproduce.py`. See `README.md` for the complete procedure and assumptions.

The package includes source code, tests, unchanged raw stock inputs, the four refreshed FRED files, all regenerated results and figures, and the exact source audit. `results/paper_report.md` is the readable results document. `results/land_update_comparison.csv` records the old/new baseline comparison.

The LaTeX manuscript last delivered still reflects the preceding land inputs. Its narrative, tables, and figures need a further numerical update from these regenerated outputs.
