"""
flow_metrs — flow-weighted marginal effective tax rates.

The whole analytical content of the flow specification, which is small: the
industry rate is a harmonic aggregation of the asset rates under investment-share
weights,

    M_i = 1 - ( sum_a w_ia / (1 - m_a) )^-1,

and the economy-wide rate is the same expression evaluated at the economy's asset
shares.  Because the weights enter only through those shares, and the shares are
column sums of the dollar flow matrix over its grand total, the industry weights
never have to be formed explicitly.

This is a different object from the user-cost wedge of the z pipeline: it prices
distortions in required-return space rather than user-cost space, and weights by
current acquisition rather than by capital service.  The two are reported side by
side rather than reconciled.
"""
import numpy as np
import pandas as pd

from params import check_schema
check_schema(2, __name__)

DEPRECIABLE_EXCLUDES = ("Inventories", "Land")


def _grossup(schedule, cats):
    m = np.array([schedule[c] for c in cats], dtype=float)
    if (m >= 1.0).any():
        bad = [c for c, v in zip(cats, m) if v >= 1.0]
        raise ValueError(f"METR >= 1 gives a non-positive gross-up: {bad}")
    return 1.0 / (1.0 - m)


def industry_metrs(flow, schedule, universe="total"):
    """M_i by industry.  universe: 'total' or 'depreciable' (drops inv. and land).

    flow is the DOLLAR matrix from flows.build_flow_matrix.
    """
    cats = [c for c in flow.columns
            if universe == "total" or c not in DEPRECIABLE_EXCLUDES]
    D = flow[cats].to_numpy(dtype=float)
    totals = D.sum(axis=1)
    if (totals <= 0).any():
        bad = [flow.index[i] for i in np.where(totals <= 0)[0]]
        raise ValueError(f"no positive flow for: {bad}")
    shares = D / totals[:, None]
    return pd.Series(1.0 - 1.0 / (shares @ _grossup(schedule, cats)), index=flow.index)


def economy_metr(flow, schedule, universe="total"):
    """Economy-wide M: the same expression at economy asset shares."""
    cats = [c for c in flow.columns
            if universe == "total" or c not in DEPRECIABLE_EXCLUDES]
    D = flow[cats].to_numpy(dtype=float)
    shares = D.sum(axis=0) / D.sum()
    return float(1.0 - 1.0 / (shares @ _grossup(schedule, cats)))


def asset_shares(flow, universe="total"):
    """Economy-wide investment share of each asset."""
    cats = [c for c in flow.columns
            if universe == "total" or c not in DEPRECIABLE_EXCLUDES]
    D = flow[cats].to_numpy(dtype=float)
    return pd.Series(D.sum(axis=0) / D.sum(), index=cats)


def industry_weights(flow, universe="total"):
    """phi_i, the industry's share of measured flow."""
    cats = [c for c in flow.columns
            if universe == "total" or c not in DEPRECIABLE_EXCLUDES]
    totals = flow[cats].sum(axis=1)
    return totals / totals.sum()


def summary(flow, schedule, universe="total"):
    """Everything the paper reports from the flow side, in one call."""
    Mi = industry_metrs(flow, schedule, universe)
    phi = industry_weights(flow, universe)
    return {"M": economy_metr(flow, schedule, universe),
            "M_i": Mi, "phi": phi, "asset_shares": asset_shares(flow, universe),
            "M_i_min": float(Mi.min()), "M_i_max": float(Mi.max()),
            "M_i_range_pp": float(100 * (Mi.max() - Mi.min()))}
