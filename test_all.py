"""
Tests.  Run from the repository root:

    python tests/test_all.py

Three groups.  The first reconciles the published parameters against each other
and needs no data files.  The second checks algebraic identities of the two
computation layers, using a toy economy, and also needs no data.  The third runs
only if the input files are present.

A clean parse proves nothing, so these assert properties derivable in closed
form: a failure indicates the code or the constants, not the calibration.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import params as P
import wedges
import distortion as D
import flow_metrs as FM

TOL = 1e-12
_fails = []


def check(ok, msg):
    print(("  ok    " if ok else "  FAIL  ") + msg)
    if not ok:
        _fails.append(msg)


# ==========================================================================
# 1. the published parameters are mutually consistent
# ==========================================================================

def test_parameters():
    print("\n1. parameter reconciliation")
    check(abs(P.derive_s() - P.S_MIXED) < 1e-9,
          f"S_MIXED = f*S_DEBT + (1-f)*S_EQUITY  ({P.derive_s():.6f})")

    # Land ties each schedule to its saver return: rho_land = r/(1-tau) exactly,
    # so s = rho_land * (1 - m_land) recovers s from the published rate.
    specs = [("MIXED_DETAILED", P.MIXED_DETAILED, P.S_MIXED, P.R_MIXED, 0.21),
             ("EQUITY_DETAILED", P.EQUITY_DETAILED, P.S_EQUITY, P.R_EQUITY, 0.21),
             ("eq_2017", P.EQUITY_8["eq_2017"], P.S_EQUITY, P.R_EQUITY, 0.34),
             ("eq_2025_obbba", P.EQUITY_8["eq_2025_obbba"], P.S_EQUITY, P.R_EQUITY, 0.21)]
    for label, sched, s, r, tau in specs:
        implied = (r / (1 - tau)) * (1 - sched["Land"])
        check(abs(implied - s) < 1.5e-3,
              f"{label:14s} land implies s={implied:.5f} (target {s:.5f})")

    # Inventories tie the same way, through the holding-period model.
    for label, sched, s, r, tau in specs:
        rho = wedges.inventory_rho(r, tau)
        implied_m = (rho - s) / rho
        check(abs(implied_m - sched["Inventories"]) < 2.5e-3,
              f"{label:14s} model implies m_inv={implied_m:.4f} "
              f"(published {sched['Inventories']:.4f})")

    # Removing the section 41 credit leaves R&D expensed with no credit, so
    # rho = r and m = (r-s)/r. That must equal the published rate for the other
    # expensed-no-credit assets.
    for label, s, r, target in [("mixed", P.S_MIXED, P.R_MIXED, P.RD_NO_CREDIT["mixed"]),
                                ("equity", P.S_EQUITY, P.R_EQUITY, P.RD_NO_CREDIT["equity"])]:
        check(abs(wedges.rd_metr_no_credit(s, r) - target) < 1e-3,
              f"{label:14s} no-credit R&D m={wedges.rd_metr_no_credit(s, r):.4f} "
              f"(published {target:.3f})")

    check(set(P.DETAILED_TO_COMPARABLE) == set(P.CATS_DETAILED), "12->8 map domain is CATS_DETAILED")
    check(set(P.DETAILED_TO_COMPARABLE.values()) == set(P.CAT8), "12->8 map range is CAT8")
    check(len(P.SECTOR_CODES) == 19 and len(P.NAMES) == 19, "19 sectors")
    check(all(0 <= v < 1 for v in P.DELTA_DETAILED.values()), "DELTA_DETAILED in [0,1)")
    check(set(P.NONRES_STRUCT_ASSIGNMENT) == set(P.SECTOR_CODES),
          "every sector has a 39-year structure assignment")


# ==========================================================================
# 2. algebraic identities of the two computation layers
# ==========================================================================

def _toy():
    cats = ["A", "B", "C", "D"]
    z = {"A": -0.05, "B": 0.01, "C": 0.10, "D": 0.30}
    delta = {"A": 0.15, "B": 0.13, "C": 0.03, "D": 0.0}
    K = pd.DataFrame([[100, 50, 20, 5], [10, 5, 80, 40], [0, 200, 0, 10]],
                     index=["i1", "i2", "i3"], columns=cats, dtype=float)
    return K, z, delta


def test_wedges():
    print("\n2a. user-cost wedges")
    tab = wedges.equity_obbba_12()
    s = P.S_EQUITY
    ok = all(abs(tab.loc[a, "z"] - (s / (s + P.DELTA_DETAILED[a])) *
                 (P.EQUITY_DETAILED[a] / (1 - P.EQUITY_DETAILED[a]))) < TOL
             for a in ("Equipment", "Commercial_HealthCare", "Power_Struct"))
    check(ok, "z = s/(s+delta) * m/(1-m) for ordinary assets")
    # delta = 0 assets pass the wedge through whole
    for a in ("Land", "Inventories"):
        check(abs(tab.loc[a, "z"] - tab.loc[a, "tau"]) < TOL, f"{a}: z = tau (delta = 0)")


def test_distortion():
    print("\n2b. capital-service statistics")
    K, z, delta = _toy()
    s = 0.06
    st = D.capital_service_stats(K, z, delta, s)
    check(abs(st["phi"].sum() - 1) < TOL, "phi sums to one")
    check(np.allclose(st["alpha"].sum(axis=1).to_numpy(), 1.0, atol=TOL),
          "alpha rows sum to one")
    check(abs(st["V"] - (st["V_B"] + st["V_W"])) < TOL, "V = V_B + V_W")

    cats = list(K.columns)
    zv = np.array([z[c] for c in cats])
    dv = np.array([delta[c] for c in cats])
    check(np.allclose(st["Z_i"].to_numpy(), st["alpha"].to_numpy() @ zv, atol=TOL),
          "Z_i = alpha z")
    B = K.to_numpy() * (s + dv)
    check(abs(st["zbar"] - float((B * zv).sum() / B.sum())) < TOL,
          "zbar = phi Z_i equals the direct capital-service-weighted mean")

    flat = D.capital_service_stats(K, {c: 0.07 for c in cats}, delta, s)
    check(flat["V_B"] < TOL and flat["V_W"] < TOL and abs(flat["zbar"] - 0.07) < TOL,
          "uniform wedges: V_B = V_W = 0 and zbar is the common wedge")


def test_flow_metrs():
    print("\n2c. flow-weighted rates")
    D_ = pd.DataFrame([[100.0, 50.0], [10.0, 90.0]],
                      index=["i1", "i2"], columns=["Equipment", "Land"])
    sched = {"Equipment": 0.20, "Land": 0.20}
    Mi = FM.industry_metrs(D_, sched)
    check(np.allclose(Mi.to_numpy(), 0.20, atol=TOL),
          "uniform rates: every M_i equals the common rate")
    check(abs(FM.economy_metr(D_, sched) - 0.20) < TOL, "and so does the economy rate")

    sched2 = {"Equipment": 0.05, "Land": 0.30}
    a = FM.economy_metr(D_, sched2)
    b = FM.economy_metr(D_ * 1000.0, sched2)
    check(abs(a - b) < TOL, "economy rate is invariant to rescaling the matrix")
    # economy shares are column sums over the grand total, so the economy rate is
    # the industry rate of the pooled matrix
    pooled = pd.DataFrame([D_.sum().to_numpy()], index=["all"], columns=D_.columns)
    check(abs(a - FM.industry_metrs(pooled, sched2).iloc[0]) < TOL,
          "economy rate equals the rate on the pooled matrix")
    check(abs(FM.asset_shares(D_).sum() - 1) < TOL, "asset shares sum to one")
    check(abs(FM.industry_weights(D_).sum() - 1) < TOL, "phi sums to one")


# ==========================================================================
# 3. data-dependent, skipped when inputs are absent
# ==========================================================================

def test_soi_suppression():
    """The suppressed-cell estimator must reconcile and stay in bounds."""
    print("\n2d. SOI suppressed-cell estimator")
    if not (P.DATA_DIR / P.SOI_BALANCE[2022][0]).exists():
        print("  skip  SOI workbooks absent")
        return
    import soi
    from soi import _read_one
    need = ("land", "inventories", "depreciable assets", "total assets")
    for year in sorted(P.SOI_BALANCE):
        f51, f61 = P.SOI_BALANCE[year]
        if not (P.DATA_DIR / f61).exists():
            continue
        allc, _, _ = _read_one(P.DATA_DIR / f51, need)
        raw, sup, allind = _read_one(P.DATA_DIR / f61, need)
        filled = soi._fill_suppressed({k: dict(v) for k, v in raw.items()},
                                      sup, allind, allc)
        for item in ("land", "inventories"):
            if allind.get(item) is None:
                continue
            tot = sum(filled[item].values())
            check(abs(tot - allind[item]) < max(1.0, 1e-6 * abs(allind[item])),
                  f"{year} {item}: imputed S-corp sectors sum to All Industries")
        lv = soi.levels(year, items=("land", "inventories"), billions=False)
        for item in ("land", "inventories"):
            ok = all(0 <= lv.loc[P.SECTOR_NAMES[c], item] <= allc[item][c] + 1.0
                     for c in P.SECTOR_CODES)
            check(ok, f"{year} {item}: every C-corp amount in [0, all-corp]")


def test_land_control():
    """Each land basis must hit its external control exactly in the reference year."""
    print("\n2e. land scaling")
    if not (P.DATA_DIR / P.BEA_DETAIL).exists():
        print("  skip  BEA detail absent")
        return
    import stocks
    for basis, target in P.LAND_BASES.items():
        K12, _ = stocks.build_K(P.LAND_REFERENCE_YEAR, land_basis=basis)
        got = K12["Land"].sum()
        if target is None:
            check(abs(stocks.land_factor(basis) - 1.0) < TOL,
                  f"{basis}: unscaled (factor 1)")
        else:
            check(abs(got - target) < 0.5,
                  f"{basis}: 2022 land stock {got:.1f} hits control {target:.1f}")


def test_with_data():
    print("\n3. data-dependent")
    if not (P.DATA_DIR / P.BEA_DETAIL).exists():
        print("  skip  BEA detail file absent")
        return
    import stocks
    K12, K8 = stocks.build_K(2022)
    check(np.allclose(K12.sum(axis=1).to_numpy(), K8.sum(axis=1).to_numpy(), rtol=1e-9),
          "the 12- and 8-category matrices have identical row totals")
    check((K12.to_numpy() >= 0).all(), "no negative capital stocks")
    st = D.capital_service_stats(K12, wedges.mixed_obbba_12()["z"].to_dict(),
                                 P.DELTA_DETAILED, P.S_MIXED)
    check(0 < st["zbar"] < 0.2, f"zbar is plausible ({st['zbar']:.4f})")
    check(st["V_W"] > st["V_B"], "within-industry variance exceeds between")

    try:
        import flows
        flow, report = flows.build_flow_matrix(2022)
    except FileNotFoundError as e:
        print(f"  skip  flow inputs absent ({str(e).split('.')[0]})")
        return
    check((flow.to_numpy() >= 0).all(), "no negative flow cells after suppression")
    check(flow.shape == (19, 12), f"flow matrix is 19 x 12 (got {flow.shape})")


if __name__ == "__main__":
    test_parameters()
    test_wedges()
    test_distortion()
    test_flow_metrs()
    test_soi_suppression()
    test_land_control()
    test_with_data()
    print("\n" + ("ALL CHECKS PASSED" if not _fails else f"{len(_fails)} FAILED"))
    # Exit non-zero on the command line (so CI notices) but not under an IDE or
    # notebook kernel, where SystemExit would kill the session.
    if _fails and not hasattr(sys, "ps1") and "ipykernel" not in sys.modules:
        raise SystemExit(1)
