"""
Reproduce the stock-based tables, figures, and narrative values in the paper.

    python reproduce.py       baseline, Section 41 sensitivity, all paper outputs
    python reproduce.py --z   compatibility alias for the same stock-only run

Running this file from an IDE does the same. Unknown IDE arguments are ignored.
The retired flow-METR pipeline is not imported or run. Outputs go to results/.

Interactive use:
    from reproduce import run_z, run_paper
    out = run_z()             # one specification
    complete = run_paper()    # both specifications and full paper reporting
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


def _eb_over_B(st):
    """Benchmark EB/B = 1/2 [eps*zbar^2 + eta*V_B + sigma*V_W]."""
    return 0.5 * (P.EPSILON_BENCHMARK * st["zbar"] ** 2
                  + P.ETA_BENCHMARK * st["V_B"]
                  + P.SIGMA_BENCHMARK * st["V_W"])



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

    # -- Table B.3: bridge from the main current-law specification to the
    # historical specification. All three rows use 2022 stocks and post-OBBBA law.
    # This shows separately the financing effect and the effect of pooling ordinary
    # nonresidential structures while preserving the two software categories.
    K_hist_2022 = stocks.build_K_historical(2022)
    equity13_z = wedges.equity_obbba_12(exclude_s41=exclude_s41)["z"].to_dict()
    hist_post_z = wedges.equity_historical("eq_2025_obbba", exclude_s41=exclude_s41)["z"].to_dict()
    bridge_stats = [
        ("13 categories, mixed finance", primary),
        ("13 categories, equity finance",
         D.capital_service_stats(K_primary, equity13_z, P.DELTA_DETAILED, P.S_EQUITY)),
        ("10 categories, equity finance",
         D.capital_service_stats(K_hist_2022, hist_post_z, P.DELTA_HIST, P.S_EQUITY)),
    ]
    pd.DataFrame([{"specification": name, "zbar": st["zbar"],
                   "sqrt_VB": st["sqrt_V_B"], "sqrt_VW": st["sqrt_V_W"],
                   "EB_over_B": _eb_over_B(st)}
                  for name, st in bridge_stats]).to_csv(
        P.OUTPUT_DIR / f"table_B3_specification_bridge{tag}.csv", index=False)

    # Equipment aggregation diagnostic: the published equipment METR is held
    # fixed and only the CRS Table A-2 depreciation rate varies.
    m_eq = P.MIXED_DETAILED["Equipment"]
    tau_eq = m_eq / (1 - m_eq)
    z_fast = (P.S_MIXED / (P.S_MIXED + P.EQUIPMENT_DELTA_MAX)) * tau_eq
    z_slow = (P.S_MIXED / (P.S_MIXED + P.EQUIPMENT_DELTA_MIN)) * tau_eq
    pd.DataFrame([{
        "equipment_delta_min": P.EQUIPMENT_DELTA_MIN,
        "equipment_delta_max": P.EQUIPMENT_DELTA_MAX,
        "equipment_z_min": z_fast,
        "equipment_z_max": z_slow,
        "equipment_z_at_aggregate_delta": tab.loc["Equipment", "z"],
    }]).to_csv(P.OUTPUT_DIR / f"aggregation_diagnostics{tag}.csv", index=False)

    # -- Table 3: law x stock-year, equity basis, ten historical categories
    cells = {}
    for year in (2016, 2022):
        K_hist = stocks.build_K_historical(year)
        for law in ("eq_2017", "eq_2025_obbba"):
            zv = wedges.equity_historical(law, exclude_s41=exclude_s41)["z"].to_dict()
            st = D.capital_service_stats(K_hist, zv, P.DELTA_HIST, P.S_EQUITY)
            st["EB_over_B"] = _eb_over_B(st)
            cells[(year, law)] = st
    pd.DataFrame([{"stock_year": y, "law": l, "zbar": st["zbar"],
                   "sqrt_VB": st["sqrt_V_B"], "sqrt_VW": st["sqrt_V_W"],
                   "EB_over_B": st["EB_over_B"]}
                  for (y, l), st in cells.items()]).to_csv(
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
                  f"sqrtV_B={_pct(s['sqrt_V_B'])} sqrtV_W={_pct(s['sqrt_V_W'])} "
                  f"EB/B={_pct(s['EB_over_B'])}")
        print("  2x2 (pp):", {k: round(v, 2) for k, v in dec.items()})
    return {"wedges": tab, "dispersion": pd.DataFrame(rows), "stats": primary,
            "K": K12, "cells": cells, "decomposition": dec}


def run_paper(verbose=True):
    """Generate all retained paper outputs without any flow-data requirements."""
    import paper_reporting
    baseline = run_z(exclude_s41=False, verbose=verbose)
    no_credit = run_z(exclude_s41=True, verbose=verbose)
    reports = paper_reporting.write_paper_outputs(baseline, no_credit, verbose=verbose)
    return {"baseline": baseline, "no_credit": no_credit, "reports": reports}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--z", action="store_true", help="compatibility alias for the stock-only run")
    ap.add_argument("--flow", action="store_true", help=argparse.SUPPRESS)
    ns, _ignored = ap.parse_known_args()
    if ns.flow:
        ap.error("The flow-METR exercise has been removed from this paper driver. Run without --flow.")
    run_paper()
    print("\nwritten to", P.OUTPUT_DIR)
