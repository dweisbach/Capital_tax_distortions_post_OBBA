"""Derive land valuation multiples from archived Financial Accounts observations.

The default total-real-estate residual subtracts Z.1 nonfinancial corporate
nonresidential and residential structures from real estate at market value.
All four FRED level series are in millions of dollars; outputs are in billions.

Matched scaling divides the residual by SOI all-corporation book land outside
LAND_NONFIN_EXCLUDE, then applies that multiple to C-corporation book land.
This SOI/Z.1 crosswalk is approximate. The application assumes a common uplift
across legal forms and industries, including financial C corporations.
Equity REITs are in Z.1 nonfinancial corporations in releases since Dec. 2023;
mortgage REITs and financial holding companies are financial. Excluding all
of SOI sector 55 would also exclude nonfinancial management companies.

The 2022 multiple is applied to both 2016 and 2022 stock matrices. Nonresidential
real estate omits residential land and is retained only as a sensitivity basis.
BEA line 19/line 3 comparisons are explicitly mismatched diagnostics; line 39
matches nonfinancial nonresidential structures, but BEA line 3 is all corporate.
"""
from functools import lru_cache
import hashlib
import math
from pathlib import Path

import pandas as pd
import params as P
import soi

P.check_schema(2, __name__)
BASES = ("nonres", "total")


def _series_specs():
    return {
        P.FRED_RE_NONRES: ("BOGZ1FL105035033A", "annual"),
        P.FRED_RE_TOTAL: ("NCBREMV", "quarterly"),
        P.FRED_STRUCT_NONRES: ("RCSNNWMVBSNNCB", "quarterly"),
        P.FRED_STRUCT_RES: ("RCVSRNWMVBSNNCB", "quarterly"),
    }


def _basis(basis):
    aliases = {"SOI_book": "book", "book": "book", "nonres": "nonres",
               "total": "total", "residual_nonres_RE": "nonres",
               "residual_total_RE": "total"}
    if basis not in aliases:
        raise ValueError(f"Unknown land basis {basis!r}")
    return aliases[basis]


@lru_cache(maxsize=None)
def _fred(path, series_id):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path.name}; download CSV from "
                                f"https://fred.stlouisfed.org/series/{series_id}")
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    if list(df.columns) != ["observation_date", series_id]:
        raise ValueError(f"{path.name}: expected observation_date and {series_id}; "
                         f"found {list(df.columns)}")
    dates = pd.to_datetime(df["observation_date"], errors="raise")
    if dates.isna().any() or dates.duplicated().any():
        raise ValueError(f"{path.name}: missing or duplicate observation dates")
    raw = df[series_id].str.strip()
    values = pd.to_numeric(raw, errors="coerce")
    bad = values.isna() & raw.notna() & ~raw.isin(["", "."])
    if bad.any():
        raise ValueError(f"{path.name}: invalid nonnumeric observations")
    return pd.Series(values.to_numpy(dtype=float) / 1000, index=dates)


def year_end(fname, year):
    """Require the annual year-end level or precisely the quarterly Q4 level.

    Frequency comes from a declared series specification, not the number of
    nonmissing observations. Annual date labels are Jan. 1; Q4 labels are Oct. 1.
    """
    if fname not in _series_specs():
        raise ValueError(f"Frequency/units not declared for {fname!r}")
    series_id, frequency = _series_specs()[fname]
    date = pd.Timestamp(int(year), 1 if frequency == "annual" else 10, 1)
    s = _fred(P.DATA_DIR / fname, series_id)
    if date not in s.index or not math.isfinite(float(s.loc[date])):
        raise KeyError(f"{fname}: no valid {frequency} year-end observation for "
                       f"{year} (required date {date.date()})")
    value = float(s.loc[date])
    if value < 0:
        raise ValueError(f"{fname}: negative asset level for {year}")
    return value


def real_estate(year, basis):
    basis = _basis(basis)
    if basis == "book":
        raise ValueError("Book land has no real-estate residual")
    return year_end(P.FRED_RE_NONRES if basis == "nonres" else P.FRED_RE_TOTAL, year)


def _bea_line(table, line, label, year):
    import stocks  # lazy: stocks delegates its land_factor to this module
    configured = {"4.1": P.BEA_T41, "5.1": P.BEA_T51}[table]
    path = stocks._bea_table(f"Table {table}", configured)
    frame = pd.read_csv(path, header=3, dtype=str)
    frame.columns = [str(c).strip() for c in frame.columns]
    row = frame[frame["Line"].str.strip() == str(line)]
    if len(row) != 1 or str(year) not in frame.columns:
        raise KeyError(f"BEA Table {table}: missing/ambiguous line {line}, year {year}")
    found = str(row.iloc[0, 1]).strip()
    if found != label:
        raise ValueError(f"BEA Table {table} line {line}: {found!r}, expected {label!r}")
    value = float(row[str(year)].iloc[0])
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"BEA Table {table}: invalid structure value")
    return value


def structure_components(year, basis, source=None):
    basis = _basis(basis)
    if basis == "book":
        raise ValueError("Book land has no structure subtraction")
    source = P.LAND_STRUCTURES if source is None else source
    if source == "z1":
        nonres = year_end(P.FRED_STRUCT_NONRES, year)
        res = year_end(P.FRED_STRUCT_RES, year) if basis == "total" else 0.0
    elif source in ("bea", "bea_nonfin"):
        nonres = _bea_line("4.1", 19 if source == "bea" else 39, "Structures", year)
        res = _bea_line("5.1", 3, "Corporate", year) if basis == "total" else 0.0
    else:
        raise ValueError(f"Unknown structure source {source!r}")
    return nonres, res


def structures(year, basis, source=None):
    return sum(structure_components(year, basis, source))


def land_market_value(year, basis, source=None):
    land = real_estate(year, basis) - structures(year, basis, source)
    if not math.isfinite(land) or land < 0:
        raise ValueError(f"Negative or nonfinite land residual for {year}/{basis}")
    return land


def book_land(year, population):
    if population == "ccorp":
        total = float(soi.levels(year, items=("land",))["land"].sum())
    elif population == "nonfin_allcorp":
        excluded = set(P.LAND_NONFIN_EXCLUDE)
        unknown = excluded - set(P.SECTOR_CODES)
        if unknown:
            raise ValueError(f"Unknown SOI sector exclusions: {sorted(unknown)}")
        f51, _ = P.SOI_BALANCE[year]
        allc, sup, _ = soi._read_one(P.DATA_DIR / f51, ("land", "total assets"))
        withheld = set(sup["land"]) - excluded
        if withheld:
            raise ValueError(f"Included SOI all-corporation land is withheld: {sorted(withheld)}")
        total = sum(v for s, v in allc["land"].items() if s not in excluded) / 1e6
    else:
        raise ValueError(f"Unknown SOI population {population!r}")
    if not math.isfinite(total) or total <= 0:
        raise ValueError(f"Nonpositive or nonfinite book-land denominator: {population}")
    return total


def land_factor(basis=P.LAND_PRIMARY, scaling=None, source=None, year=None):
    basis = _basis(basis)
    if basis == "book":
        return 1.0
    scaling = P.LAND_SCALING if scaling is None else scaling
    if scaling not in ("ccorp", "matched"):
        raise ValueError(f"Unknown land scaling {scaling!r}")
    year = P.LAND_REFERENCE_YEAR if year is None else year
    population = "ccorp" if scaling == "ccorp" else "nonfin_allcorp"
    return land_market_value(year, basis, source) / book_land(year, population)


def control_inputs(year=None):
    year = P.LAND_REFERENCE_YEAR if year is None else year
    book_c = book_land(year, "ccorp")
    book_n = book_land(year, "nonfin_allcorp")
    rows = []
    for basis in P.LAND_BASES:
        is_book = _basis(basis) == "book"
        factor = land_factor(basis, year=year)
        rows.append({"land_basis": basis, "reference_year": year,
                     "structures_source": None if is_book else P.LAND_STRUCTURES,
                     "scaling": "book" if is_book else P.LAND_SCALING,
                     "source_residual_billions": None if is_book else land_market_value(year, basis),
                     "control_billions": book_c * factor,
                     "legacy_control_billions": P.LAND_LEGACY_CONTROLS.get(basis),
                     "reference_SOI_book_billions": book_c,
                     "reference_nonfin_allcorp_book_billions": book_n,
                     "excluded_SOI_sectors": ",".join(P.LAND_NONFIN_EXCLUDE),
                     "factor": factor,
                     "provenance_status": "SOI book value" if is_book else
                         "Derived from archived observations; approximate coverage/valuation allocation",
                     "coverage_note": "Unscaled" if is_book else P.LAND_COVERAGE_NOTE})
    return pd.DataFrame(rows)


def _source_metadata(fname, year):
    series_id, frequency = _series_specs()[fname]
    path = P.DATA_DIR / fname
    return {"file": fname, "series_id": series_id,
            "observation_date": f"{year}-{'01' if frequency == 'annual' else '10'}-01",
            "frequency": frequency + ", end of period", "units": "Millions of US dollars",
            "value_billions": year_end(fname, year),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "capture_date": P.LAND_SOURCE_CAPTURE_DATE,
            "release_vintage": "Not embedded in CSV; capture date and exact file hash retained"}


def source_audit(year=None):
    year = P.LAND_REFERENCE_YEAR if year is None else year
    rows = []
    for source in ("z1", "bea", "bea_nonfin"):
        for basis in BASES:
            nonres, res = structure_components(year, basis, source)
            land = land_market_value(year, basis, source)
            row = {"source": source, "basis": basis, "reference_year": year,
                   "real_estate_billions": real_estate(year, basis),
                   "nonresidential_structure_billions": nonres,
                   "residential_structure_billions": res,
                   "source_residual_billions": land,
                   "factor_ccorp": land_factor(basis, "ccorp", source, year),
                   "factor_matched": land_factor(basis, "matched", source, year),
                   "Ccorp_land_ccorp_billions": land,
                   "Ccorp_land_matched_billions": land_factor(basis, "matched", source, year) * book_land(year, "ccorp"),
                   "status": "Same Z.1 sector for numerator components; SOI crosswalk approximate" if source == "z1" else
                       "Comparison only: all-corporate structures" if source == "bea" else
                       "Comparison only: nonfinancial nonresidential structures; all-corporate residential structures"}
            files = {"real_estate": P.FRED_RE_NONRES if basis == "nonres" else P.FRED_RE_TOTAL}
            if source == "z1":
                files["nonres_structure"] = P.FRED_STRUCT_NONRES
                if basis == "total": files["res_structure"] = P.FRED_STRUCT_RES
            else:
                import stocks
                for table, configured in [("4.1", P.BEA_T41)] + ([("5.1", P.BEA_T51)] if basis == "total" else []):
                    path = stocks._bea_table(f"Table {table}", configured)
                    row[f"BEA_{table}_file"] = path.name
                    row[f"BEA_{table}_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
                    row[f"BEA_{table}_vintage"] = next((line.strip() for line in path.read_text().splitlines()[:3] if "Revised" in line), "Not recorded")
                row["BEA_T41_line"] = 19 if source == "bea" else 39
                row["BEA_T51_line"] = 3 if basis == "total" else None
            for prefix, fname in files.items():
                row.update({f"{prefix}_{key}": value for key, value in _source_metadata(fname, year).items()})
            rows.append(row)
    return pd.DataFrame(rows)


def report(year=None):
    inputs, audit = control_inputs(year), source_audit(year)
    print("\nLand inputs ($ billions), reference year", inputs.reference_year.iloc[0])
    print(inputs[["land_basis", "source_residual_billions", "control_billions", "factor", "legacy_control_billions"]].round(6).to_string(index=False))
    print(P.LAND_COVERAGE_NOTE)
    print("\nSource/scaling diagnostics ($ billions)")
    print(audit[["source", "basis", "source_residual_billions", "factor_matched", "Ccorp_land_matched_billions"]].round(6).to_string(index=False))
    return audit


def clear_cache():
    _fred.cache_clear()


if __name__ == "__main__":
    report()
