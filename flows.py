"""
flows — the industry-by-asset investment flow matrix, in dollars.

Three sources, because no single one covers all assets:

  depreciable property   SOI Complete Report Table 13, the Form 4562 basis of
                         property placed in service during the year, by recovery
                         period.  GROSS: it reports acquisitions and cannot be
                         negative.
  research               NSF business R&D by industry.  Also gross.
  inventories, land      SOI balance sheets differenced across two years, since
                         those tables report year-end stocks rather than
                         acquisitions.  NET, and so can be negative.

That asymmetry is data-imposed, not chosen: there is no gross measure of land
acquisition, and full netting of depreciable property would need Form 4797
disposition data.  It is disclosed rather than papered over.

SOFTWARE.  Form 4562 does not identify software separately, so the flow matrix
carries no software column of its own; software acquisition is inside the
depreciable-property rows.  The stock matrix does separate it, so the two
specifications differ in that one respect.

LEGAL FORM.  The three sources do not share one legal-form universe, so the
assembled matrix is not literally a C-corporation matrix and should not be
labelled as one without qualification.  Land and inventories are C-corporation,
being Table 5.1 less Table 6.1.  Table 13 is headed "Returns of Active
Corporations"; IRS documentation elsewhere describes the post-2013 depreciation
series as excluding Forms 1120-S, REIT and RIC, so the workbook notes should be
checked for the vintage in use.  NSF business R&D is R&D performed by companies
and is not broken out by legal form at all.  The flow results are therefore best
described as corporate, with the R&D component on a company basis.

The output is a DOLLAR matrix, deliberately.  Everything downstream -- the row
shares w_ia, the industry weights phi_i, and the economy-wide asset shares --
is recoverable from it, because

    W_a = sum_i phi_i w_ia = sum_i (row total_i / total) * (D_ia / row total_i)
        = sum_i D_ia / total,

i.e. the economy-wide asset shares are just column sums over the grand total.
Shipping a row-normalised matrix instead would throw away the row totals and
force a second file to carry them.
"""
import re
import warnings

import openpyxl
import pandas as pd

from params import (check_schema, DATA_DIR, SECTOR_CODES, SECTOR_NAMES, NAMES, CATS_DETAILED,
                    TABLE13_ROWS, TABLE13_EXCLUDED, NONRES_STRUCT_ASSIGNMENT,
                    NEGLIGIBLE_INVENTORY_SECTORS, NSF_FILE_STEMS,
                    NSF_CODE_TO_SECTOR, SOI_TABLE13)

check_schema(2, __name__)
import soi


def _num(v):
    """Numeric value, or None if the cell is withheld for disclosure.

    Table 13 gives no All Industries column for the sector rows, so a withheld
    cell here cannot be estimated from a published residual the way the balance
    sheets can.  Withheld cells therefore contribute nothing, but they are
    counted and reported rather than silently zeroed.
    """
    return float(v) if isinstance(v, (int, float)) else None


# ---- depreciable property: Form 4562, SOI Table 13 -------------------------

def depreciable_flow(year):
    """Basis of property placed in service, by sector x category ($ thousands)."""
    path = DATA_DIR / SOI_TABLE13[year]
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)["Table 13"]
    rows = list(ws.iter_rows(min_row=1, max_row=60, max_col=25, values_only=True))
    out = pd.DataFrame(0.0, index=SECTOR_CODES, columns=CATS_DETAILED)
    seen, withheld = 0, 0
    withheld_by_row, row_totals = {}, {}
    for label, cat in TABLE13_ROWS:
        row = next((r for r in rows
                    if r[0] and str(r[0]).strip().startswith(label)), None)
        if row is None:
            warnings.warn(f"Table 13 row not found: {label!r}")
            continue
        seen += 1
        if cat is None:                      # dropped (heterogeneous ADS class life)
            continue
        # sector columns run left to right in SECTOR_CODES order, starting at col 2
        for k, sector in enumerate(SECTOR_CODES):
            target = NONRES_STRUCT_ASSIGNMENT[sector] if cat == "IND" else cat
            v = _num(row[2 + k])
            if v is None:
                withheld += 1
                withheld_by_row[label] = withheld_by_row.get(label, 0) + 1
            else:
                out.loc[sector, target] += v
                row_totals[label] = row_totals.get(label, 0.0) + v
    if seen < len(TABLE13_ROWS):
        warnings.warn(f"only {seen} of {len(TABLE13_ROWS)} Table 13 rows matched")
    # Amounts on rows deliberately treated as deductions rather than acquisition.
    excluded = {}
    for label in TABLE13_EXCLUDED:
        row = next((r for r in rows
                    if r[0] and str(r[0]).strip().startswith(label)), None)
        if row is not None:
            excluded[label] = sum(v for v in (_num(row[2 + k])
                                              for k in range(len(SECTOR_CODES)))
                                  if v is not None)
    out.attrs["withheld_cells"] = withheld
    out.attrs["withheld_by_row"] = dict(withheld_by_row)
    out.attrs["withheld_rows_published_share"] = (
        sum(row_totals[r] for r in withheld_by_row) / sum(row_totals.values())
        if row_totals else 0.0)
    out.attrs["excluded_deduction_rows"] = excluded
    if withheld:
        share = out.attrs["withheld_rows_published_share"]
        warnings.warn(
            f"Table 13: {withheld} sector cells withheld for disclosure contributed "
            f"nothing; unlike the balance sheets there is no published All Industries "
            f"residual to estimate them from. They fall on rows carrying {share:.1%} "
            f"of published basis, and none on the section 179, bonus, 3/5/7-year or "
            f"39-year nonresidential rows, so the omission is bounded well below that.")
    return out


# ---- research: NSF business R&D --------------------------------------------

def _find_nsf(year):
    stems = NSF_FILE_STEMS.get(year, [])
    for stem in stems:
        key = re.sub(r"[^a-z0-9]", "", stem.lower())
        for p in sorted(DATA_DIR.glob("*")):
            if p.suffix.lower() in (".xlsx", ".xls", ".csv") and \
                    key in re.sub(r"[^a-z0-9]", "", p.stem.lower()):
                return p
    raise FileNotFoundError(
        f"No NSF R&D file for {year} in {DATA_DIR}. Expected a file whose name "
        f"contains one of {stems} (BERD detailed tables, Table 10). Do not "
        f"substitute the NSB Indicators DISC-3 summary table: it reports only "
        f"sectors 31-33, 51, 52 and 54 at two digits and drops ~6.5% of "
        f"national R&D.")


def research_flow(year):
    """NSF domestic business R&D by sector ($ thousands), plus a coverage note.

    Sectors NSF does not break out at two digits are zero.  The shortfall is
    returned rather than hidden, because R&D carries the largest negative rate of
    any category, so a vintage with worse coverage biases the industry rate up.
    """
    path = _find_nsf(year)
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path, header=None)
    else:
        df = pd.read_excel(path, sheet_name=0, header=None)
    rd = dict.fromkeys(SECTOR_CODES, 0.0)
    national = None
    for _, row in df.iterrows():
        label = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        code = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
        if code.endswith(".0"):
            code = code[:-2]
        code = code.replace("\u2013", "-").replace("\u2014", "-")
        value = row.iloc[2] if len(row) > 2 else None
        if not isinstance(value, (int, float)) or pd.isna(value):
            continue
        if national is None and "all industries" in label.lower():
            national = float(value)
        sector = NSF_CODE_TO_SECTOR.get(code)
        if sector is not None:
            rd[sector] = float(value) * 1000.0        # $millions -> $thousands
    series = pd.Series(rd)
    if national:
        coverage = (series.sum() / 1000.0) / national
        series.attrs["coverage"] = coverage
        series.attrs["national_millions"] = national
        if coverage < 0.97:
            warnings.warn(
                f"NSF R&D {year}: the sectors reported at two digits cover "
                f"{coverage:.1%} of the published national total. The remainder is "
                f"in industries NSF publishes only inside aggregates. Coverage "
                f"differs across vintages, so compare years with this in mind.")
    if (series > 0).sum() < 3:
        warnings.warn(f"NSF R&D {year}: only {(series > 0).sum()} sectors are "
                      f"nonzero; check that Table 10 was supplied.")
    return series


# ---- inventories and land: differenced balance sheets ----------------------

def inventory_land_flow(year, prior_year):
    """Net change in C-corporation inventories and land ($ thousands)."""
    cur = soi.levels(year, items=("inventories", "land"), billions=False)
    pri = soi.levels(prior_year, items=("inventories", "land"), billions=False)
    delta = cur - pri
    for code in NEGLIGIBLE_INVENTORY_SECTORS:
        delta.loc[SECTOR_NAMES[code], "inventories"] = 0.0
    return delta


# ---- assembly --------------------------------------------------------------

def build_flow_matrix(year=2022, prior_year=None):
    """Industry-by-asset investment flow ($ thousands), C-corporation basis.

    Negative cells -- which can only arise in the two balance-sheet-derived
    categories -- are set to zero.  The framework is defined on acquisition: the
    quantities entering the cost index are assets bought, and a negative entry is
    not a smaller acquisition but a different transaction (disposition triggers
    recapture and gain against adjusted basis, for which no published METR
    exists).  The reported figure is therefore the rate on positive acquisition
    flow, weighted by positive acquisition flow, and should be labelled as such.

    Returns (flow, report).  report holds per-industry counts of suppressed
    negative cells, and in report.attrs the diagnostics that belong to the run as
    a whole: withheld Table 13 cells, the amounts on the excluded deduction rows,
    and NSF R&D coverage.
    """
    prior_year = prior_year or year - 1
    dep = depreciable_flow(year)
    rd = research_flow(year)
    # Capture the diagnostics now: pandas does not carry .attrs through
    # assignment into a DataFrame column, or through .where().
    diagnostics = dict(dep.attrs)
    diagnostics["rd_coverage"] = rd.attrs.get("coverage")
    diagnostics["rd_national_millions"] = rd.attrs.get("national_millions")
    diagnostics["rd_sectors_nonzero"] = int((rd > 0).sum())

    flow = dep
    flow["RD"] = rd
    il = inventory_land_flow(year, prior_year)
    for code in SECTOR_CODES:
        flow.loc[code, "Inventories"] = il.loc[SECTOR_NAMES[code], "inventories"]
        flow.loc[code, "Land"] = il.loc[SECTOR_NAMES[code], "land"]

    negative = flow < 0
    dropped = (-flow.where(negative, 0.0)).sum(axis=1)
    flow = flow.where(~negative, 0.0)
    flow.index = NAMES
    dropped.index = NAMES
    report = pd.DataFrame({
        "n_negative_cells": negative.sum(axis=1).set_axis(NAMES),
        "dropped_dollars": dropped,
        "dropped_share_of_positive": (dropped / flow.sum(axis=1)).fillna(0.0),
    })
    report.attrs.update(diagnostics)
    return flow[CATS_DETAILED], report
