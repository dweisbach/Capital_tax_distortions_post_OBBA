"""
distortion — the capital-service-weighted distortion statistics.

This is the z-space, stock-weighted analog of the flow package's statistics_25.
Given a stock matrix K_ia, an asset wedge vector z_a, and the depreciation and
saver-return parameters, it forms the benchmark capital-service weights

    B_ia = (s + delta_a) K_ia,   phi_i = B_i / B,   alpha_ia = B_ia / B_i

and returns the four objects the framework's excess-burden expression uses:

    zbar = sum_i phi_i Z_i,           Z_i = sum_a alpha_ia z_a
    V_B  = sum_i phi_i (Z_i - zbar)^2
    V_W  = sum_i phi_i sum_a alpha_ia (z_a - Z_i)^2

None of these requires an elasticity; the elasticities enter only when V_B, V_W
and zbar^2 are combined into EB/B = 1/2 (eps zbar^2 + eta V_B + sigma V_W).
"""
import numpy as np
import pandas as pd

from params import check_schema
check_schema(2, __name__)


def capital_service_stats(K, z, delta, s):
    """K: DataFrame (industry x asset); z, delta: dicts keyed by asset; s: float.

    Returns a dict of scalars and Series, all on capital-service weights.
    """
    cats = list(K.columns)
    zv = np.array([z[c] for c in cats], dtype=float)
    dv = np.array([delta[c] for c in cats], dtype=float)
    B = K.to_numpy(dtype=float) * (s + dv)
    Bi = B.sum(1)
    if (Bi <= 0).any():
        bad = [K.index[i] for i in np.where(Bi <= 0)[0]]
        raise ValueError(f"non-positive capital service for: {bad}")
    phi = Bi / Bi.sum()
    alpha = B / Bi[:, None]
    Zi = alpha @ zv
    zbar = float(phi @ Zi)
    within_var = np.array([np.sum(alpha[i] * (zv - Zi[i]) ** 2) for i in range(len(phi))])
    V_B = float(phi @ (Zi - zbar) ** 2)
    V_W = float(phi @ within_var)
    idx = K.index
    return {
        # V_B and V_W are reported as levels, and as square roots for readability.
        # No ratio or share is returned: the two enter excess burden multiplied by
        # different elasticities, so their relative size carries no welfare
        # interpretation without a calibration this code does not impose.
        "zbar": zbar, "V_B": V_B, "V_W": V_W, "V": V_B + V_W,
        "sqrt_V_B": float(np.sqrt(V_B)), "sqrt_V_W": float(np.sqrt(V_W)),
        "Z_i": pd.Series(Zi, index=idx), "phi": pd.Series(phi, index=idx),
        "within_sd": pd.Series(np.sqrt(within_var), index=idx),
        "alpha": pd.DataFrame(alpha, index=idx, columns=cats),
        "asset_shares": pd.Series(B.sum(0) / B.sum(), index=cats),
    }


def two_by_two(cells, old_law, new_law):
    """cells: dict {(year, law): stats}.  Returns the z-bar decomposition (pp).

    The law names are passed explicitly rather than inferred from dictionary
    order, so an interactive call cannot silently reverse the sign of the law
    effect by building the dict the other way round.
    """
    missing = [k for k in cells if k[1] not in (old_law, new_law)]
    if missing:
        raise KeyError(f"cells contain laws other than {old_law!r}/{new_law!r}: "
                       f"{sorted({k[1] for k in missing})}")
    zb = lambda y, l: cells[(y, l)]["zbar"]
    years = sorted({y for (y, _) in cells})
    lo_y, hi_y = years[0], years[-1]
    return {
        "law_effect_at_%d_stocks" % lo_y: (zb(lo_y, new_law) - zb(lo_y, old_law)) * 100,
        "law_effect_at_%d_stocks" % hi_y: (zb(hi_y, new_law) - zb(hi_y, old_law)) * 100,
        "composition_effect_under_%s" % old_law: (zb(hi_y, old_law) - zb(lo_y, old_law)) * 100,
        "composition_effect_under_%s" % new_law: (zb(hi_y, new_law) - zb(lo_y, new_law)) * 100,
        "total_diagonal": (zb(hi_y, new_law) - zb(lo_y, old_law)) * 100,
    }
