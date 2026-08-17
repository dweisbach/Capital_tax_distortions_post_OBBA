"""
reproduce — one entry point for every number and figure in the paper.

    python reproduce.py            both pipelines, all specifications
    python reproduce.py --z        primary (user-cost wedge) specification only
    python reproduce.py --flow     flow-weighted specification only

FROM AN IDE (Spyder, PyCharm, VS Code, Jupyter)
Press Run / F5 on this file and it does the same as `python reproduce.py` with no
arguments: both pipelines, everything written to results/. Unrecognised arguments
that an IDE may inject are ignored, and the working directory does not matter.

To work with the results interactively instead, run the file once (which puts the
package on the path) and then:

    from reproduce import run_z, run_flow
    out  = run_z()                      # baseline primary specification
    out2 = run_z(exclude_s41=True)      # section 41 excluded
    flow = run_flow(2022)               # flow-weighted specification

Each returns a dict. run_z gives 'wedges' (the asset table), 'dispersion' (the
land-valuation rows), 'stats' (the primary cell: Z_i, phi, alpha, V_B, V_W),
'cells' (the 2x2) and 'decomposition'. run_flow gives one entry per asset
universe, each with M, M_i and phi. Pass verbose=False to silence the printing.

Outputs go to results/.  Section numbers refer to the paper.

    Table 1, A.1   asset-level m, delta, z                      (z pipeline)
    Figure 1       industry user-cost wedges Z_i                 (z pipeline)
    Figure 2       asset composition and within-industry wedges  (z pipeline)
    Table 2        z-bar, V_B, V_W across land valuations        (z pipeline)
    Table 3        law x stock-year 2x2                          (z pipeline)
    Figure 3       flow-weighted industry METRs                  (flow pipeline)

Every table is also written as a CSV so that a reader can check a number without
recompiling the paper.
"""
import argparse
import sys
from pathlib import Path

# Put this file's folder on the import path, so the package can be run from an
# IDE whose working directory is somewhere else.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import pandas as pd

import params as P
import wedges
import distortion as D
import figures as F

P.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
_pct = lambda x: f"{x * 100:6.2f}%"


# ==========================================================================
# primary specification: user-cost wedges on capital-service weights
# ==========================================================================

def run_z(exclude_s41=False, verbose=True):
    import stocks
    tag = "_ex_s41" if exclude_s41 else ""
    label = "excluding the section 41 credit" if exclude_s41 else "baseline"

    # -- Table 1 / A.1: asset-level wedges
    tab = wedges.mixed_obbba_12(exclude_s41=exclude_s41)
    tab.to_csv(P.OUTPUT_DIR / f"table_A1_asset_wedges{tag}.csv")

    # -- Table 2: dispersion across land valuations
    K12, _ = stocks.build_K(2022)
    z = tab["z"].to_dict()
    rows, primary, K_primary = [], None, None
    for basis in P.LAND_BASES:
        K, _ = stocks.build_K(2022, land_basis=basis)
        st = D.capital_service_stats(K, z, P.DELTA_DETAILED, P.S_MIXED)
        rows.append({"land_basis": basis, "zbar": st["zbar"],
                     "sqrt_VB": st["sqrt_V_B"], "sqrt_VW": st["sqrt_V_W"],
                     "V_B": st["V_B"], "V_W": st["V_W"],
                     "land_share": st["asset_shares"]["Land"]})
        if basis == P.LAND_PRIMARY:
            primary, K_primary = st, K
    pd.DataFrame(rows).to_csv(P.OUTPUT_DIR / f"table_2_dispersion{tag}.csv", index=False)

    # -- Figures 1 and 2, and the industry detail behind them
    pd.DataFrame({"Z_i": primary["Z_i"], "phi": primary["phi"],
                  "within_sd": primary["within_sd"]}).sort_values(
        "Z_i", ascending=False).to_csv(P.OUTPUT_DIR / f"industry_wedges{tag}.csv")
    K12.round(1).to_csv(P.OUTPUT_DIR / "K_ia_2022_ccorp.csv")
    F.fig_between(primary, P.OUTPUT_DIR / f"figure_1_between_industry{tag}.png")
    F.fig_within_composition(K_primary, z, primary,
                             P.OUTPUT_DIR / f"figure_2_within_composition{tag}.png",
                             legend_labels=P.LEGEND)

    # -- Table 3: law x stock-year, equity basis, eight categories
    cells = {}
    for year in (2016, 2022):
        _, K8 = stocks.build_K(year)
        for law in ("eq_2017", "eq_2025_obbba"):
            zv = wedges.equity_8(law, exclude_s41=exclude_s41)["z"].to_dict()
            cells[(year, law)] = D.capital_service_stats(K8, zv, P.DELTA8, P.S_EQUITY)
    pd.DataFrame([{"stock_year": y, "law": l, "zbar": s["zbar"],
                   "sqrt_VB": s["sqrt_V_B"], "sqrt_VW": s["sqrt_V_W"]}
                  for (y, l), s in cells.items()]).to_csv(
        P.OUTPUT_DIR / f"table_3_law_x_stockyear{tag}.csv", index=False)
    dec = D.two_by_two(cells, "eq_2017", "eq_2025_obbba")
    pd.DataFrame([dec]).T.rename(columns={0: "pp"}).to_csv(
        P.OUTPUT_DIR / f"table_3_decomposition{tag}.csv")

    if verbose:
        print(f"\n--- primary specification, {label} ---")
        print(f"  R&D wedge  m={tab.loc['RD','m']:+.4f}  z={tab.loc['RD','z']:+.4f}")
        for r in rows:
            print(f"  land={r['land_basis']:18s} zbar={_pct(r['zbar'])} "
                  f"sqrtV_B={_pct(r['sqrt_VB'])} sqrtV_W={_pct(r['sqrt_VW'])} "
                  f"land share={r['land_share']:.3f}")
        for (y, l), s in cells.items():
            print(f"  {y} {l:14s} zbar={_pct(s['zbar'])} "
                  f"sqrtV_B={_pct(s['sqrt_V_B'])} sqrtV_W={_pct(s['sqrt_V_W'])}")
        print("  2x2 (pp):", {k: round(v, 2) for k, v in dec.items()})
    return {"wedges": tab, "dispersion": pd.DataFrame(rows), "stats": primary,
            "K": K12, "cells": cells, "decomposition": dec}


# ==========================================================================
# secondary specification: flow-weighted effective rates
# ==========================================================================

def run_flow(year=2022, verbose=True):
    import flows
    import flow_metrs as FM

    flow, report = flows.build_flow_matrix(year)
    flow.round(0).to_csv(P.OUTPUT_DIR / f"flow_matrix_{year}_dollars.csv")
    report.round(4).to_csv(P.OUTPUT_DIR / f"flow_negative_cells_{year}.csv")
    diag = dict(report.attrs)
    excluded = diag.pop("excluded_deduction_rows", {})
    pd.DataFrame(
        [{"item": k, "value": v} for k, v in diag.items()]
        + [{"item": f"excluded row: {k}", "value": v} for k, v in excluded.items()]
    ).to_csv(P.OUTPUT_DIR / f"flow_diagnostics_{year}.csv", index=False)

    out = {}
    for universe in ("total", "depreciable"):
        s = FM.summary(flow, P.MIXED_DETAILED, universe)
        out[universe] = s
        pd.DataFrame({"M_i": s["M_i"], "phi": s["phi"]}).sort_values(
            "M_i", ascending=False).to_csv(
            P.OUTPUT_DIR / f"figure_3_flow_metrs_{universe}.csv")
    F.fig_flow_metrs(out["total"]["M_i"], out["total"]["M"],
                     P.OUTPUT_DIR / "figure_3_flow_metrs.png")
    if verbose:
        print(f"\n--- flow-weighted specification, TY{year} ---")
        for universe, s in out.items():
            print(f"  {universe:12s} economy M={_pct(s['M'])}  "
                  f"industry range {_pct(s['M_i_min'])} to {_pct(s['M_i_max'])}")
        n = int(report["n_negative_cells"].sum())
        print(f"  negative cells set to zero: {n}")
        cov = report.attrs.get("rd_coverage")
        if cov is not None:
            print(f"  NSF R&D coverage: {cov:.1%} of the published national total")
        print(f"  Table 13 cells withheld for disclosure: "
              f"{report.attrs.get('withheld_cells')}")
        for k, v in report.attrs.get("excluded_deduction_rows", {}).items():
            print(f"  excluded as a deduction, not acquisition: {k} "
                  f"= ${v/1e6:,.1f}B")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--z", action="store_true", help="primary specification only")
    ap.add_argument("--flow", action="store_true", help="flow specification only")
    ap.add_argument("--year", type=int, default=2022, help="flow tax year")
    # parse_known_args, not parse_args: IDEs and notebook kernels pass their own
    # arguments through sys.argv, and parse_args would exit with an error.
    ns, _ignored = ap.parse_known_args()
    do_z = ns.z or not ns.flow
    do_flow = ns.flow or not ns.z
    if do_z:
        run_z(exclude_s41=False)
        run_z(exclude_s41=True)
    if do_flow:
        run_flow(ns.year)
    print("\nwritten to", P.OUTPUT_DIR)
