"""
figures — the two exhibits for the current-law distortion section.

fig_between            industry wedges Z_i against the economy average zbar, dot
                       area proportional to capital-service share phi_i, so the
                       picture matches the weighted statistic V_B.
fig_within_composition stacked asset-composition bars, segments ordered by the
                       asset's wedge z_a, rows sorted by within-industry SD, with
                       that SD in the right margin.
fig_flow_metrs         flow-weighted industry rates against the economy rate.

No titles, subtitles or explanatory notes are drawn: those belong in the LaTeX
caption, where they can be edited without regenerating the figure and are set in
the document's own type. Axis labels and legends stay, since they are needed to
read the plot.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from params import check_schema, SECTOR_NAMES  # noqa: F401  (kept for callers)

check_schema(2, __name__)

SHORT = {
    "Real Estate and Rental and Leasing": "Real Estate & Leasing",
    "Accommodation and Food Services": "Accommodation & Food",
    "Arts, Entertainment, and Recreation": "Arts & Recreation",
    "Educational Services": "Education",
    "Management of Companies and Enterprises": "Management of Companies",
    "Transportation and Warehousing": "Transportation",
    "Finance and Insurance": "Finance & Insurance",
    "Mining, Quarrying, and Oil and Gas Extraction": "Mining and Oil & Gas",
    "Administrative and Support and Waste Management": "Administrative & Waste",
    "Agriculture, Forestry, Fishing, Hunting": "Agriculture & Forestry",
    "Health Care and Social Assistance": "Health Care",
    "Professional, Scientific, and Technical Services": "Professional & Technical",
}
_short = lambda n: SHORT.get(n, n)
_CMAP = plt.cm.RdYlBu_r
_NORM = plt.Normalize(-0.10, 0.30)

# --------------------------------------------------------------------------
# Asset colours.
#
# Colour has to do one job, not two. If it encodes each specification's own z,
# then a variant that moves an asset's wedge (excluding the section 41 credit
# drives R&D from -0.08 to +0.00) recolours that asset into its neighbours and it
# becomes unfindable -- and assets with near-identical wedges collide even within
# one figure (five categories sit at +0.01).
#
# So colour encodes ASSET IDENTITY, fixed once and identical in every figure and
# every specification. The palette is drawn from the diverging map at evenly
# spaced ranks of the BASELINE post-OBBBA wedge, so hue still reads low-to-high
# left-to-right, and no two assets ever share a colour. Each specification's
# actual wedge is printed in the legend, and segments are still ordered by that
# specification's wedge, so a moved asset visibly changes position.
# --------------------------------------------------------------------------
# ranked by the baseline post-OBBBA mixed wedge: RD -0.078, Equipment +0.010,
# Mfg +0.012, Farm +0.013, Comms +0.013, OilGas +0.077, Power +0.095,
# Residential +0.172, OtherNonres +0.196, Commercial +0.197, Land +0.289,
# Inventories +0.332.
CANONICAL_ORDER_DETAILED = ["RD", "Software", "Equipment", "Manufacturing_Struct", "Farm_Struct",
                      "Communications_Struct", "OilGasMining_Struct", "Power_Struct",
                      "Residential_Struct", "Other_Nonres", "Commercial_HealthCare",
                      "Land", "Inventories"]
CANONICAL_ORDER_8 = ["RD", "Equipment", "Nonres_Struct", "OilGasMining_Struct",
                     "Power_Struct", "Residential_Struct", "Land", "Inventories"]


def asset_colors(cats):
    """Fixed colour per asset, evenly spaced along the diverging map by canonical rank."""
    order = [c for c in CANONICAL_ORDER_DETAILED if c in cats] or list(cats)
    order += [c for c in cats if c not in order]          # any unexpected category last
    if set(cats) <= set(CANONICAL_ORDER_8):
        order = [c for c in CANONICAL_ORDER_8 if c in cats]
    n = max(len(order) - 1, 1)
    return {c: _CMAP(i / n) for i, c in enumerate(order)}



def fig_between(stats, path):
    """`stats` from distortion.capital_service_stats.  Caption belongs in LaTeX."""
    Zi, phi = stats["Z_i"], stats["phi"]
    zbar = stats["zbar"]
    order = Zi.sort_values(ascending=False).index
    yy = np.arange(len(order))[::-1]
    SCALE = 4800   # marker area per unit of phi; area is exactly proportional
    fig, ax = plt.subplots(figsize=(9.4, 7.2))
    for k, nm in enumerate(order):
        col = "#2b6cb0" if Zi[nm] < zbar else "#8fbcdb"
        ax.plot([zbar, Zi[nm]], [yy[k], yy[k]], color="#d2d2d2", lw=1.2, zorder=1)
        # No floor on the area: a floor would break the proportionality the
        # legend asserts, and small industries should look small.
        ax.scatter([Zi[nm]], [yy[k]], s=phi[nm] * SCALE, color=col,
                   edgecolors="#28425e", linewidths=0.7, zorder=3)
    ax.axvline(zbar, color="k", ls="--", lw=1.2, zorder=2)
    ax.axvline(0, color="#bbb", lw=0.8, zorder=0)
    ax.set_yticks(yy); ax.set_yticklabels([_short(n) for n in order], fontsize=9.5)
    ax.set_xlabel(r"Industry user-cost wedge  Z$_i$", fontsize=10.5)
    h = [ax.scatter([], [], s=p * SCALE, color="#8fbcdb", edgecolors="#28425e",
                    linewidths=0.7, label=f"{int(p*100)}%") for p in (0.05, 0.15, 0.25)]
    ax.legend(handles=h, title=r"capital-service share $\phi_i$", loc="lower right",
              fontsize=8.6, title_fontsize=8.8, labelspacing=1.6, borderpad=1.1,
              handletextpad=1.3, framealpha=0.95)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="x", alpha=0.25); ax.set_ylim(-0.9, len(order) - 0.2)
    plt.tight_layout(); plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()


def fig_within_composition(K, z, stats, path, legend_labels=None):
    """Figure C. K: stock matrix; z: dict of wedges; stats: capital_service_stats output.

    Colour = asset identity (fixed across specifications, see asset_colors).
    Segment order and the legend numbers = this specification's wedges.
    """
    cats = list(K.columns)
    alpha = stats["alpha"]; within_sd = stats["within_sd"]
    zv = {c: z[c] for c in cats}
    seg_order = sorted(cats, key=lambda c: zv[c])           # blue -> red
    colors = asset_colors(cats)
    row_order = within_sd.sort_values(ascending=False).index
    yy = np.arange(len(row_order))[::-1]
    labels = legend_labels or {c: c for c in cats}
    fig, ax = plt.subplots(figsize=(12, 9))
    for r, nm in enumerate(row_order):
        y = yy[r]; left = 0.0
        for c in seg_order:
            w = alpha.loc[nm, c]
            if w <= 0:
                continue
            ax.barh(y, w, left=left, height=0.72, color=colors[c],
                    edgecolor="white", linewidth=0.6)
            left += w
        ax.text(1.015, y, f"{within_sd[nm]:.3f}", va="center", ha="left", fontsize=9)
    ax.text(1.015, len(row_order) - 0.1, "within-SD", va="bottom", ha="left", fontsize=9, style="italic")
    ax.set_yticks(yy); ax.set_yticklabels([_short(n) for n in row_order], fontsize=9.5)
    ax.set_xlim(0, 1); ax.set_ylim(-0.7, len(row_order) - 0.3)
    ax.set_xlabel("share of the industry's capital services", fontsize=10.5)
    handles = [Patch(facecolor=colors[c], edgecolor="white",
                     label=f"{labels.get(c, c)}  ({zv[c]:+.2f})") for c in seg_order]
    ax.legend(handles=handles, title="asset (user-cost wedge z)", ncol=3, fontsize=8.3,
              title_fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.09), frameon=False)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(left=False)
    plt.tight_layout(); plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()


def fig_flow_metrs(Mi, aggregate, path):
    """Flow-weighted industry rates, sorted, with the economy rate marked."""
    s = Mi.sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(9.4, 7.0))
    yy = np.arange(len(s))[::-1]
    # Colour encodes position relative to the economy rate, matching fig_between.
    # Nothing marks the maximum: "is the largest" is not a property worth a hue.
    colors = ["#2b6cb0" if v < aggregate else "#8fbcdb" for v in s.values]
    ax.barh(yy, s.values, color=colors, edgecolor="#28425e", linewidth=0.6, height=0.68)
    ax.axvline(aggregate, color="k", ls="--", lw=1.2,
               label=f"Economy-wide flow-weighted METR: {aggregate*100:+.1f}%")
    ax.axvline(0, color="#bbb", lw=0.8)
    ax.set_yticks(yy); ax.set_yticklabels([_short(n) for n in s.index], fontsize=9.5)
    ax.set_xlabel("Flow-weighted marginal effective tax rate", fontsize=10.5)
    # Outside the axes: the most negative bar reaches the bottom-right corner,
    # where an inset legend sits on top of it.
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), fontsize=9,
              frameon=False, ncol=1)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="x", alpha=0.25)
    plt.tight_layout(); plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
