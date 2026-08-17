# Capital Tax Distortions after OBBBA — replication package

Code and data for *Capital Tax Distortions after OBBBA: Evidence Across Assets and
Industries*.

Everything in the paper comes from one command:

```bash
pip install -r requirements.txt
python reproduce.py
```

which writes every table and figure to `results/`.

## What the code computes

The paper reports two specifications. They answer different questions and are kept
separate on purpose.

**Primary — user-cost wedges on capital-service weights.** Each asset's published
marginal effective tax rate is converted into the proportional tax-induced change
in the price relevant to capital demand,

```
z_a = (c_a^T - c_a^0)/c_a^0 = s/(s+δ_a) · m_a/(1-m_a),
```

and weighted by the benchmark annual value of capital services,
`B_ia = (s+δ_a)·K_ia`. From those come the industry wedge `Z_i`, the economy wedge
`z̄`, and the between- and within-industry variances `V_B` and `V_W` that enter the
excess-burden expression. `V_B` and `V_W` are multiplied by *different* elasticities
there, so no ratio between them is reported: their relative size carries no welfare
interpretation without a calibration the paper does not impose.

**Secondary — flow-weighted effective rates.** The published rates aggregated over
the composition of current investment, `M_i = 1 - (Σ_a w_ia/(1-m_a))^-1`. This is
descriptive: it summarises current acquisition activity, not the distortion facing
the installed stock. It prices distortions in required-return space rather than
user-cost space and weights by acquisition rather than capital service.

## Layout

| file                | role                                                         |
| ------------------- | ------------------------------------------------------------ |
| `params.py`         | **every published constant**: rate schedules, `δ_a`, saver returns, sectors, asset categories, source filenames, mappings. The only file to edit. |
| `soi.py`            | SOI Complete Report balance sheets. Shared: the primary pipeline reads levels, the flow pipeline differences them across years. |
| `wedges.py`         | `z_a` from a rate schedule; the section 41 variant           |
| `stocks.py`         | `K_ia` — BEA detail → Table 4.1 corporate carve → SOI C-corp → land and inventories |
| `distortion.py`     | `z̄`, `Z_i`, `φ_i`, `α_ia`, `V_B`, `V_W`; the law × stock-year decomposition |
| `flows.py`          | the investment flow matrix — Form 4562 + NSF + differenced balance sheets |
| `flow_metrs.py`     | `M_i` and the economy-wide `M`                               |
| `figures.py`        | the three figures                                            |
| `reproduce.py`      | the driver                                                   |
| `tests/test_all.py` | parameter reconciliation and algebraic identities            |

`python reproduce.py --z` or `--flow` runs one pipeline; `--year` sets the flow tax
year.

Modules share names defined in `params.py`, so they must be replaced as a set. Each
checks `params.SCHEMA` on import and fails with an explicit message if the folder
holds a mix of versions, rather than raising an `ImportError` on a renamed constant.

### Running from an IDE

Open `reproduce.py` and press Run (F5 in Spyder). That is equivalent to
`python reproduce.py` with no arguments. The working directory does not matter, and
arguments an IDE injects are ignored.

To explore the results rather than write them, run the file once and then:

```python
from reproduce import run_z, run_flow
out  = run_z()                    # baseline primary specification
out2 = run_z(exclude_s41=True)    # section 41 excluded
flow = run_flow(2022)             # flow-weighted specification
```

`run_z` returns a dict with `wedges` (the asset-level table), `dispersion` (the
land-valuation rows), `stats` (the primary cell, including `Z_i`, `phi`, `alpha`,
`V_B`, `V_W`), `K`, `cells` (the 2×2) and `decomposition`. `run_flow` returns one
entry per asset universe. Pass `verbose=False` to silence printing. Individual
modules also work alone — `import wedges; wedges.mixed_obbba_12()`, or
`import stocks; K13, K8 = stocks.build_K(2022)`.

Spyder caches imported modules, so restart the kernel (Ctrl+.) after editing
`params.py`.

### Runtime

A full run takes roughly ten to fifteen seconds, nearly all of it parsing the BEA
detailed-stocks workbook, which holds every industry-by-asset series for every
vintage. That sheet is parsed once per session and cached, as are the SOI workbooks,
so repeated calls in one session are fast. After editing an input file mid-session,
call `stocks.clear_cache()` or restart the kernel.

## Input data

Put the files below either in a subfolder (any name) or alongside the scripts; the
code scores candidate folders by how many expected inputs they hold and picks the
best. To see what it resolved:

```python
import params; params.describe_paths()
```

which prints the chosen folder, every folder scanned with its score, and any missing
files. Override with the `METR_DATA_DIR` environment variable or by setting
`params.DATA_DIR` in a session.

| file                                   | source                                                       |
| -------------------------------------- | ------------------------------------------------------------ |
| `detailnonres_stk1.xlsx`               | BEA, Detailed Data for Fixed Assets, nonresidential net stocks, **current cost** |
| BEA Fixed Assets Table 4.1             | nonresidential stocks by industry group and legal form       |
| BEA Fixed Assets Table 5.1             | residential stocks by owner and legal form                   |
| `NCBREMV.csv`, `BOGZ1FL105035033A.csv` | FRED, corporate real-estate market value (land controls)     |
| `{yy}co51ccr.xlsx`, `{yy}co61ccr.xlsx` | SOI Corporation Complete Report Tables 5.1 (all corporations) and 6.1 (S corporations), for each year in `SOI_BALANCE` |
| `{yy}co13ccr.xlsx`                     | SOI Complete Report Table 13 (Form 4562 property placed in service) |
| `nsf24335-tab010.xlsx`                 | NSF BERD 2022 detailed statistical tables, Table 10          |

Two notes on inputs that have caused errors:

- BEA exports every interactive table as `Table.csv`, so a second download lands as
  `Table (1).csv`. The code prefers the filenames in `params.py` but falls back to
  identifying Tables 4.1 and 5.1 by their **title row**, so raw export names work.
- For R&D, use the **BERD detailed tables** (Table 10). Do not substitute the NSB
  Indicators DISC-3 summary table: it reports only sectors 31–33, 51, 52 and 54 at
  two digits and drops about 6.5% of national R&D. The loader reports coverage and
  warns below 97%.

## Choices a reader should know about

- **The saver return is tied to the financing basis of the schedule.** Mixed-finance
  rates pair with the mixed-finance `s`, equity rates with the all-equity `s`. The
  primary specification uses mixed finance; the historical comparison uses equity,
  because the pre-TCJA rates exist only on that basis. `S_EQUITY` is investor-side
  and so invariant to the statutory regime — the tests verify this by recovering it
  from the published land rate, for which `ρ_land = r/(1-τ)` in closed form.
- **Software is its own category**, following the source, with `δ` = 0.510 (the
  stock-weighted blend of pre-packaged and custom software) and the
  expensed-without-credit rate. Grouping it with equipment would misstate both.
- **Land and inventories have `δ = 0`, so `z = τ`.** For inventories this is the only
  treatment consistent with the model: inventory is working capital whose annual
  opportunity cost is `s` untaxed and `ρ_inv` taxed. The published inventory user
  cost `e^{ρT}` is the *gross* amount for which inventory must sell, including
  recovery of principal — not a rental price — and `ρ_inv` is already annualised, so
  scaling by the holding period again would double-count. The check is the
  dollar-wedge identity `B_inv·z_inv = (ρ_inv − s)·K_inv`.
- **Withheld SOI cells are estimated, not read as zero.** Because the C-corporation
  figure is Table 5.1 less Table 6.1, a withheld S-corporation cell read as zero
  overstates the C-corporation amount one for one. The published All Industries
  column gives the withheld total, which is allocated across the affected sectors in
  proportion to each sector's S-corporation share of total assets applied to the
  all-corporation amount. Estimates are *added* to any published part of a sector,
  since SOI splits some sectors across more than one column.
- **Land valuation.** SOI reports land near historical cost, so the SOI data supply
  the industry *distribution* while the *total* is rescaled to a current-value
  control. `stocks.land_factor()` derives the scale from the constructed book total
  in the reference year rather than a hard-coded denominator, so it stays consistent
  when the construction changes. One factor applies to every year, because the
  control is a residual that is unstable year to year. Three valuations are reported.
- **Three constructed aggregate depreciation rates**, computed rather than assumed:
  equipment 0.126, software 0.510, and nonresidential structures 0.027 in the
  eight-category set. Aggregating `δ` is exact under capital-service weighting
  provided the category rate is the stock-weighted mean — see the paper's aggregation
  appendix.
- **Flow matrix inclusions.** Part III of Form 4562 reports the basis of property
  placed in service, net of the section 179 deduction and the special depreciation
  allowance, so both are added back to reconstruct acquisition cost. Rows reporting a
  *deduction* on property that may have been acquired earlier are excluded and their
  amounts reported: section 168(f)(1) property, other depreciation including ACRS,
  and listed property. Table 13 cells withheld for disclosure cannot be estimated —
  there is no All Industries residual on those rows — so they contribute nothing and
  are counted in the diagnostics.
- **Negative flow cells.** Depreciable property and R&D are gross and cannot be
  negative; inventories and land are net changes in stock and can be. Negative cells
  are set to zero, because the framework is defined on acquisition and a disposition
  is a different transaction for which no published rate exists. What was dropped is
  recorded in `results/flow_negative_cells_*.csv`.
- **Legal form differs across the flow sources.** Land and inventories are
  C-corporation; Table 13 is headed "Returns of Active Corporations"; NSF business
  R&D is not broken out by legal form. The flow results are therefore a separate
  descriptive exercise, not a flow implementation of the stock-based analysis.
- **Section 41.** Reported both ways. Excluding the credit leaves R&D expensed with
  no credit, so `ρ = r` and `m = (r−s)/r`, which reproduces the published rate for
  the other expensed-no-credit assets. Read the pair as bracketing the treatment of
  R&D, not as identifying the optimal subsidy.
- **Figure colours encode asset identity**, fixed across all figures and
  specifications. Colour cannot also encode `z`, because variants move `z` and
  several categories share a wedge. Titles and notes are not drawn: they belong in
  the LaTeX caption.

## Tests

```bash
python tests/test_all.py
```

Most groups need no data. They reconcile the published parameters against each other
(each schedule's `s` recovered from its land and inventory rates; the section 41
exclusion against the published expensed-no-credit rate) and check algebraic
identities (`V = V_B + V_W`; `z̄` computed two ways; uniform wedges zeroing both
variances; flow rates invariant to rescaling). Where the input files are present the
suite also checks that the imputed S-corporation sector totals reconcile to the
published All Industries total, that every C-corporation amount lies between zero and
the corresponding all-corporation amount, and that each land basis reproduces its
external control exactly in the reference year.

## Headline results as produced

Primary specification, mixed finance, 2022 C-corporation stocks:

| land valuation            |  `z̄` | `√V_B` | `√V_W` | land share |
| ------------------------- | ---: | -----: | -----: | ---------: |
| SOI book value            | 4.3% |   4.5% |   9.7% |       1.2% |
| nonresidential RE control | 4.7% |   4.8% |  10.0% |       2.8% |
| total RE control          | 5.1% |   5.1% |  10.2% |       4.3% |

Excluding the section 41 credit, at the total-RE control: `z̄` 6.7%, `√V_B` 4.1%,
`√V_W` 9.0%.

Law × stock-year (equity, eight categories): the law effect is **−9.8 pp** at 2016
stocks and **−10.1 pp** at 2022 stocks; the stock-composition effect is
**+0.01 to +0.29 pp**. The two dimensions separate cleanly.
