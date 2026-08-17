"""
wedges — asset-level user-cost wedges z_a from a METR schedule.

The user-cost wedge is the proportional tax-induced change in the price
relevant to capital demand (negative where the asset is favoured):

    z_a = (c_a^T - c_a^0) / c_a^0 = s/(s+delta_a) * m_a/(1-m_a)

The compression relative to the METR wedge tau = m/(1-m) is entirely the factor
s/(s+delta): high-depreciation assets (equipment, R&D) are pulled toward zero,
low-depreciation assets pass through nearly whole.

LAND AND INVENTORIES both have delta = 0 (R48277 Table A-2), so both reduce to
z = tau. For inventories this is the ONLY treatment consistent with the rest of
the model, for two reasons.

  1. K_inv is a stock of working capital. The annual opportunity cost of one
     dollar of it is s in the benchmark and rho_inv under tax, so c^0 = s and
     c^T = rho_inv, giving z = (rho_inv - s)/s = tau_inv.
  2. CRS's ucc = exp(rho T) is the GROSS amount inventory must sell for,
     including recovery of the acquisition principal. That is not a rental
     price, so proportional changes in it are not the z of this framework.
     Also, rho_inv is already ANNUALIZED (it reproduces the published annual
     METR), so scaling by T again double-counts the holding period.

The dollar-wedge identity is the check: with B_inv = s K_inv and z = tau,
B_inv z_inv = (rho_inv - s) K_inv, the Harberger wedge times the stock. The
holding period T enters only inside rho_inv (via FIFO/LIFO tax timing), which is
what inventory_rho below computes and what check_zconfig uses to reconcile the
published inventory METR.
"""
import numpy as np
import pandas as pd

from params import (check_schema, S_EQUITY, S_MIXED, R_EQUITY, R_MIXED, INFLATION, INV_HOLDING_PERIOD,
                    INV_FIFO_SHARE, DELTA_DETAILED, DELTA8, MIXED_DETAILED, EQUITY_DETAILED, EQUITY_8,
                    CORP_RATE, CATS_DETAILED, CAT8)

check_schema(2, __name__)


def inventory_rho(r, corp_rate):
    """Required real pretax return on inventories (CRS FIFO/LIFO holding-period model)."""
    T, g, pi = INV_HOLDING_PERIOD, INV_FIFO_SHARE, INFLATION
    fifo = (1 / T) * np.log((np.exp((r + pi) * T) - corp_rate) / (1 - corp_rate)) - pi
    lifo = (1 / T) * np.log((np.exp(r * T) - corp_rate) / (1 - corp_rate))
    return float(g * fifo + (1 - g) * lifo)


def wedge_table(schedule, delta, s, cats=None):
    """Return a DataFrame with m, tau, delta, z for each asset in `cats`.

    schedule, delta : dicts keyed by asset category
    s               : saver return that generated `schedule` (equity or mixed)

    Every asset, including land and inventories, follows the one formula; the
    delta = 0 cases reduce to z = tau. inventory_rho is separate: it is used only
    to reconcile the published inventory rate in the parameter checks.
    """
    cats = cats or list(schedule)
    rows = []
    for a in cats:
        m = schedule[a]
        tau = m / (1 - m)
        z = (s / (s + delta[a])) * tau     # land and inventories: delta 0 -> z = tau
        rows.append((a, m, tau, delta[a], z))
    return pd.DataFrame(rows, columns=["asset", "m", "tau", "delta", "z"]).set_index("asset")


def rd_metr_no_credit(s, r):
    """R&D METR with the section 41 credit removed.

    Expensing with no credit gives rho = r, so m = (r - s)/r: purely
    investor-level, independent of delta and of the statutory rate.  See the note
    in params (RD_NO_CREDIT) for the cross-check against published rates.
    """
    return (r - s) / r


def exclude_section41(schedule, s, r):
    """Return a copy of `schedule` with R&D re-rated as expensed-without-credit.

    A sensitivity exercise for the treatment of research, not a claim that the
    credit is the right corrective subsidy. Every other asset is unchanged.
    """
    out = dict(schedule)
    out["RD"] = rd_metr_no_credit(s, r)
    return out


# convenience builders for the schedules the paper uses -----------------------

def mixed_obbba_12(exclude_s41=False):
    """Part 1 baseline: post-OBBBA mixed finance, 12 detailed categories."""
    sch = MIXED_DETAILED
    if exclude_s41:
        sch = exclude_section41(sch, S_MIXED, R_MIXED)
    return wedge_table(sch, DELTA_DETAILED, S_MIXED, cats=CATS_DETAILED)


def equity_obbba_12(exclude_s41=False):
    """Post-OBBBA equity, 12 detailed categories."""
    sch = EQUITY_DETAILED
    if exclude_s41:
        sch = exclude_section41(sch, S_EQUITY, R_EQUITY)
    return wedge_table(sch, DELTA_DETAILED, S_EQUITY, cats=CATS_DETAILED)


def equity_8(law, exclude_s41=False):
    """8-category comparable equity schedule for a law ('eq_2017' | 'eq_2025_obbba')."""
    sch = EQUITY_8[law]
    if exclude_s41:
        sch = exclude_section41(sch, S_EQUITY, R_EQUITY)
    return wedge_table(sch, DELTA8, S_EQUITY, cats=CAT8)


if __name__ == "__main__":
    pd.set_option("display.float_format", lambda x: f"{x:8.4f}")
    print("Post-OBBBA mixed, 12 categories (Section 1 table):")
    print(mixed_obbba_12().sort_values("z"))
