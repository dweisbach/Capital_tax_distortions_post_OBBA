"""
params — every published constant, in one place, used by both pipelines.

The two pipelines answer different questions and share their inputs:

  z pipeline     prices distortions as proportional user-cost wedges
                 z_a = s/(s+delta_a) * m_a/(1-m_a) and weights them by capital
                 service (s+delta_a)*K_ia.  This is the paper's primary
                 specification and the object the excess-burden expression uses.

  flow pipeline  aggregates the published METRs m_a over the composition of
                 current investment, M_i = 1 - (sum_a w_ia/(1-m_a))^-1.  This is
                 descriptive: it summarises current acquisition activity.

Both read the same CRS rate schedules and the same SOI balance sheets, so those
live here rather than in either pipeline.  Nothing downstream hard-codes a
number that appears in this file.

SOURCES
  m_a       CRS R48631 (post-OBBBA) and R48153 (pre-TCJA, equity)
  delta_a   CRS R48277 Table A-2
  s         CRS R48277 Table A-1; see derive_s() below
"""
import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# Bumped whenever a name shared across modules changes. Every module checks it on
# import, so a folder holding a mix of versions fails immediately with a clear
# message instead of an ImportError on some renamed constant.
SCHEMA = 2


def check_schema(expected=SCHEMA, module=""):
    if expected != SCHEMA:
        raise ImportError(
            f"Version mismatch: {module or 'a module'} expects params SCHEMA "
            f"{expected} but params.py is SCHEMA {SCHEMA}. The files in this "
            f"folder are from different versions of the package -- replace all of "
            f"them together, then restart the kernel.")

# ==========================================================================
# 1. input file names
# ==========================================================================
# Declared before the data folder is resolved, because resolution works by
# counting how many of these a candidate folder actually holds.
BEA_DETAIL = "detailnonres_stk1.xlsx"   # nonres detailed net stocks, CURRENT cost
BEA_T41 = "BEA_Table_4_1.csv"           # nonres by industry group x legal form
BEA_T51 = "BEA_Table_5_1.csv"           # residential by owner/legal form
FRED_RE_TOTAL = "NCBREMV.csv"
FRED_RE_NONRES = "BOGZ1FL105035033A.csv"
FRED_STRUCT_NONRES = "RCSNNWMVBSNNCB.csv"
FRED_STRUCT_RES = "RCVSRNWMVBSNNCB.csv"
SOI_BALANCE = {                          # (all corporations, S corporations)
    2016: ("16co51ccr.xlsx", "16co61ccr.xlsx"),
    2018: ("18co51ccr.xlsx", "18co61ccr.xlsx"),
    2019: ("19co51ccr.xlsx", "19co61ccr.xlsx"),
    2021: ("21co51ccr.xlsx", "21co61ccr.xlsx"),
    2022: ("22co51ccr.xlsx", "22co61ccr.xlsx"),
}
SOI_TABLE13 = {2022: "22co13ccr.xlsx", 2019: "19co13ccr.xlsx"}
# NSF business R&D.  The 2022 source is the BERD detailed statistical tables
# (NSF 24-335) Table 10.  Do NOT substitute the NSB Indicators DISC-3 summary
# table: it reports only sectors 31-33, 51, 52 and 54 at two digits and so drops
# about 6.5% of national R&D.  Matching ignores separators and case.
NSF_FILE_STEMS = {2022: ["nsf24335-tab010", "nsf24335"],
                  2019: ["nsf22329-tab010", "nsf22329"],
                  2016: ["brdis16-dst-tab010", "brdis16"]}


def expected_files():
    """Every input filename the code may look for."""
    names = [BEA_DETAIL, BEA_T41, BEA_T51, FRED_RE_TOTAL, FRED_RE_NONRES,
             FRED_STRUCT_NONRES, FRED_STRUCT_RES]
    names += [f for pair in SOI_BALANCE.values() for f in pair]
    names += list(SOI_TABLE13.values())
    return names


# ==========================================================================
# 2. where the data lives
# ==========================================================================
# Input files may sit in a subfolder (any name: data, Data, inputs, ...) or
# alongside the scripts.  Rather than insist on a layout, score every plausible
# folder by how many expected inputs it actually holds and take the best.  A
# folder holding one stray file must not win over the folder holding the data,
# which is why this counts rather than stopping at the first match.
#
#   1. the METR_DATA_DIR environment variable wins outright, if set
#   2. otherwise the highest-scoring candidate folder
#
# To override in a session:
#   import params; params.DATA_DIR = Path(r"C:\\path\\to\\data")
_SKIP_DIRS = ("results", "__pycache__", "tests", ".git", ".ipynb_checkpoints",
              "deprecated")


def _score(folder):
    """How many expected inputs this folder holds (NSF file counts as one)."""
    try:
        if not folder.is_dir():
            return 0
        present = {p.name.lower() for p in folder.iterdir() if p.is_file()}
    except OSError:
        return 0
    n = sum(1 for name in expected_files() if name.lower() in present)
    flat = {"".join(ch for ch in nm if ch.isalnum()) for nm in present}
    for stems in NSF_FILE_STEMS.values():
        key = "".join(ch for ch in stems[0] if ch.isalnum())
        if any(key in f for f in flat):
            n += 1
            break
    return n


def _candidates():
    """Every folder worth checking, in priority order."""
    out = []
    for base in (_HERE, _HERE.parent, Path.cwd()):
        try:
            if not base.is_dir():
                continue
        except OSError:
            continue
        out.append(base)
        try:
            out.extend(sorted(
                d for d in base.iterdir()
                if d.is_dir() and not d.name.startswith((".", "__"))
                and not d.name.lower().startswith(_SKIP_DIRS)))
        except OSError:
            pass
    seen, unique = set(), []
    for d in out:
        key = str(d).lower()
        if key not in seen:
            seen.add(key)
            unique.append(d)
    return unique


def resolve_data_dir():
    env = os.environ.get("METR_DATA_DIR")
    if env:
        return Path(env).expanduser()
    scored = [(_score(c), -i, c) for i, c in enumerate(_candidates())]
    best = max(scored, default=(0, 0, _HERE))
    return best[2] if best[0] > 0 else _HERE


DATA_DIR = resolve_data_dir()
OUTPUT_DIR = _HERE / "results"


def describe_paths():
    """Print where inputs are being read from and what is missing.  Call this
    first if a file is not found."""
    print(f"script folder : {_HERE}")
    print(f"data folder   : {DATA_DIR}"
          f"{'' if DATA_DIR.is_dir() else '   (does not exist)'}")
    print(f"results folder: {OUTPUT_DIR}")
    print(f"env METR_DATA_DIR: {os.environ.get('METR_DATA_DIR') or 'not set'}")
    print("\nfolders scanned, with the number of expected inputs found:")
    for c in _candidates():
        mark = " <-- chosen" if c.resolve() == DATA_DIR.resolve() else ""
        print(f"  {_score(c):3d}  {c}{mark}")
    present = ({p.name.lower() for p in DATA_DIR.iterdir() if p.is_file()}
               if DATA_DIR.is_dir() else set())
    missing = [w for w in expected_files() if w.lower() not in present]
    print(f"\nfound {len(expected_files()) - len(missing)} of "
          f"{len(expected_files())} expected files")
    if missing:
        print("missing (only the years you actually run are required):")
        for m in missing:
            print(f"   {m}")
    nsf = sorted(p.name for p in DATA_DIR.glob("*")
                 if "nsf" in p.name.lower() or "brdis" in p.name.lower()) \
        if DATA_DIR.is_dir() else []
    print(f"NSF R&D files present: {nsf or 'none'}")


# ==========================================================================
# 3. sectors and asset categories
# ==========================================================================
# Canonical sector key is the NAICS code as SOI reports it; the display name is
# the index used in every output file, so the two pipelines line up row-wise.
SECTOR_CODES = ["11", "21", "22", "23", "31-33", "42", "44-45", "48-49", "51",
                "52", "53", "54", "55", "56", "61", "62", "71", "72", "81"]
SECTOR_NAMES = {
    "11": "Agriculture, Forestry, Fishing, Hunting",
    "21": "Mining, Quarrying, and Oil and Gas Extraction",
    "22": "Utilities", "23": "Construction", "31-33": "Manufacturing",
    "42": "Wholesale Trade", "44-45": "Retail Trade",
    "48-49": "Transportation and Warehousing", "51": "Information",
    "52": "Finance and Insurance", "53": "Real Estate and Rental and Leasing",
    "54": "Professional, Scientific, and Technical Services",
    "55": "Management of Companies and Enterprises",
    "56": "Administrative and Support and Waste Management",
    "61": "Educational Services", "62": "Health Care and Social Assistance",
    "71": "Arts, Entertainment, and Recreation",
    "72": "Accommodation and Food Services", "81": "Other Services",
}
NAMES = [SECTOR_NAMES[c] for c in SECTOR_CODES]
# BEA reports 2-digit NAICS; map onto the canonical keys.
BEA_NAICS_ALIAS = {"31": "31-33", "32": "31-33", "33": "31-33",
                   "44": "44-45", "45": "44-45", "48": "48-49", "49": "48-49"}

# Software is kept separate from equipment. Pooling the two misstates both inputs:
# software's economic depreciation is an order of magnitude faster (0.51 against
# 0.13), and it is expensed without a credit, so its rate is the expensed-no-credit
# rate rather than the published equipment aggregate (which blends in regulated
# transmission equipment that is denied expensing).
CATS_DETAILED = ["Equipment", "Software", "RD", "Inventories", "Land",
                 "Manufacturing_Struct", "Communications_Struct", "Farm_Struct",
                 "Commercial_HealthCare", "Other_Nonres", "OilGasMining_Struct",
                 "Power_Struct", "Residential_Struct"]
# Historical comparison. CRS's equity-financed tables report prepackaged and
# custom software separately but pool ordinary nonresidential structures. Keeping
# the two software categories separate avoids assigning software the equipment
# depreciation rate. The resulting historical specification has ten categories.
CATS_HIST = ["Equipment", "Prepackaged_Software", "Custom_Software", "RD",
             "Inventories", "Land", "Nonres_Struct", "OilGasMining_Struct",
             "Power_Struct", "Residential_Struct"]

# Legacy eight-category objects are retained only so older auxiliary scripts do
# not fail on import. They are not used by reproduce.py or the historical results.
CAT8 = ["Equipment", "RD", "Inventories", "Land", "Nonres_Struct",
        "OilGasMining_Struct", "Power_Struct", "Residential_Struct"]
DETAILED_TO_COMPARABLE = {
    "Equipment": "Equipment", "Software": "Equipment", "RD": "RD", "Inventories": "Inventories", "Land": "Land",
    "Manufacturing_Struct": "Nonres_Struct", "Communications_Struct": "Nonres_Struct",
    "Farm_Struct": "Nonres_Struct", "Commercial_HealthCare": "Nonres_Struct",
    "Other_Nonres": "Nonres_Struct", "OilGasMining_Struct": "OilGasMining_Struct",
    "Power_Struct": "Power_Struct", "Residential_Struct": "Residential_Struct",
}
LEGEND = {"RD": "R&D", "Software": "Software", "Manufacturing_Struct": "Manufacturing Struct",
          "Communications_Struct": "Communications Struct", "Farm_Struct": "Farm Struct",
          "Commercial_HealthCare": "Commercial/Health", "Other_Nonres": "Other Nonres",
          "OilGasMining_Struct": "OilGasMining Struct", "Power_Struct": "Power Struct",
          "Residential_Struct": "Residential Struct"}

# ==========================================================================
# 4. rate schedules m_a
# ==========================================================================
MIXED_DETAILED = {  # R48631, corporate mixed finance, post-OBBBA. Primary level spec.
    "Equipment": 0.033, "Software": 0.018, "RD": -0.472, "Inventories": 0.249, "Land": 0.224,
    "Manufacturing_Struct": 0.018, "Communications_Struct": 0.018, "Farm_Struct": 0.018,
    "Commercial_HealthCare": 0.221, "Other_Nonres": 0.226, "OilGasMining_Struct": 0.122,
    "Power_Struct": 0.116, "Residential_Struct": 0.177,
}
EQUITY_DETAILED = {  # R48631, corporate equity financed, post-OBBBA
    "Equipment": 0.093, "Software": 0.078, "RD": -0.303, "Inventories": 0.290, "Land": 0.271,
    "Manufacturing_Struct": 0.078, "Communications_Struct": 0.078, "Farm_Struct": 0.078,
    "Commercial_HealthCare": 0.268, "Other_Nonres": 0.272, "OilGasMining_Struct": 0.171,
    "Power_Struct": 0.173, "Residential_Struct": 0.232,
}
EQUITY_HIST = {  # R48153 Table 4 / R48631 Table 3, corporate equity finance
    "eq_2017": {
        "Equipment": 0.198, "Prepackaged_Software": 0.320, "Custom_Software": 0.236,
        "RD": -0.358, "Inventories": 0.416, "Land": 0.392, "Nonres_Struct": 0.376,
        "OilGasMining_Struct": 0.240, "Power_Struct": 0.206, "Residential_Struct": 0.335,
    },
    "eq_2025_obbba": {
        "Equipment": 0.093, "Prepackaged_Software": 0.078, "Custom_Software": 0.078,
        "RD": -0.303, "Inventories": 0.290, "Land": 0.271, "Nonres_Struct": 0.221,
        "OilGasMining_Struct": 0.171, "Power_Struct": 0.173, "Residential_Struct": 0.232,
    },
}

# Legacy eight-category schedule retained for backward compatibility only.
EQUITY_8 = {
    "eq_2017": {"Equipment": 0.198, "RD": -0.358, "Inventories": 0.416, "Land": 0.392,
                "Nonres_Struct": 0.376, "OilGasMining_Struct": 0.240,
                "Power_Struct": 0.206, "Residential_Struct": 0.335},
    "eq_2025_obbba": {"Equipment": 0.093, "RD": -0.303, "Inventories": 0.290,
                      "Land": 0.271, "Nonres_Struct": 0.221,
                      "OilGasMining_Struct": 0.171, "Power_Struct": 0.173,
                      "Residential_Struct": 0.232},
}
CORP_RATE = {"mixed_obbba": 0.21, "equity_obbba": 0.21,
             "eq_2017": 0.34, "eq_2025_obbba": 0.21}

# Excluding the section 41 R&E credit (positive-externality variant).  With
# expensing retained and the credit removed, rho = r, so m = (r-s)/r: purely
# investor-level, independent of delta and of the statutory rate.  These are the
# published rates for assets expensed WITHOUT a credit (advertising, human
# capital, software, films, TV), which is the cross-check in tests.
RD_NO_CREDIT = {"mixed": 0.018, "equity": 0.078}

# ==========================================================================
# 5. depreciation and saver returns
# ==========================================================================
# CRS R48277 Table A-2, except two CONSTRUCTED AGGREGATES, described as such in
# the paper: Equipment (Table A-2 has ~20 types spanning 0.05-0.33; results are
# flat over 0.10-0.18 because equipment's z is near zero throughout) and
# Nonres_Struct in the 8-category set (the stock-weighted alternative is 0.0266
# in both 2016 and 2022, so the aggregation is immaterial).
DELTA_DETAILED = {
    "Equipment": 0.126, "Software": 0.510, "RD": 0.1745, "Inventories": 0.0, "Land": 0.0,
    "Manufacturing_Struct": 0.0314, "Communications_Struct": 0.0237,
    "Farm_Struct": 0.0239, "Commercial_HealthCare": 0.0247, "Other_Nonres": 0.0272,
    "OilGasMining_Struct": 0.0450, "Power_Struct": 0.0211, "Residential_Struct": 0.0140,
}
DELTA_HIST = {
    "Equipment": 0.126, "Prepackaged_Software": 0.7083, "Custom_Software": 0.3813,
    "RD": 0.1745, "Inventories": 0.0, "Land": 0.0, "Nonres_Struct": 0.027,
    "OilGasMining_Struct": 0.0450, "Power_Struct": 0.0211, "Residential_Struct": 0.0140,
}

# Legacy eight-category depreciation schedule retained for older auxiliaries.
DELTA8 = {"Equipment": 0.130, "RD": 0.1745, "Inventories": 0.0, "Land": 0.0,
          "Nonres_Struct": 0.027, "OilGasMining_Struct": 0.0450,
          "Power_Struct": 0.0211, "Residential_Struct": 0.0140}

# Benchmark elasticities used for the paper's excess-burden calculations.
EPSILON_BENCHMARK = 0.6
ETA_BENCHMARK = 1.0
SIGMA_BENCHMARK = 1.0

# CRS Table A-2 range across detailed equipment types. Used only for the
# aggregation diagnostic in test_all.py and reproduce.py.
EQUIPMENT_DELTA_MIN = 0.0500
EQUIPMENT_DELTA_MAX = 0.3333

# CRS R48277 Table A-2 component rates, used ONLY for the appendix diagnostics.
# The headline Equipment depreciation input remains DELTA_DETAILED['Equipment'].
# Each tuple supplies the source asset class, rate, and corresponding BEA codes.
EQUIPMENT_DEPRECIATION_CROSSWALK = [
    ("Office/Computing Equipment", 0.2729,
     ("EP1A", "EP1B", "EP1C", "EP1D", "EP1E", "EP1F", "EP1G", "EP1H", "EP12", "EP31")),
    ("Communications Equipment", 0.1100, ("EP20",)),
    ("Instruments", 0.1350, ("EP34", "EP35", "EP36")),
    ("Fabricated Metal Products", 0.0917, ("EI12",)),
    ("Engines and Turbines", 0.0516, ("EI21", "EI22")),
    ("Metal Working Machinery", 0.1225, ("EI30",)),
    ("Special Industrial Equipment", 0.1031, ("EI40",)),
    ("General Industrial Equipment", 0.1072, ("EI50",)),
    ("Electric Transmission Equipment", 0.0500, ("EI60",)),
    ("Trucks, Buses, and Trailers", 0.1725, ("ET11", "ET12")),
    ("Autos", 0.3333, ("ET20",)),
    ("Aircraft", 0.0660, ("ET30",)),
    ("Ships and Boats", 0.0611, ("ET40",)),
    ("Railroad Equipment", 0.0589, ("ET50",)),
    ("Furniture and Fixtures", 0.1375, ("EO11", "EO12")),
    ("Agricultural Equipment", 0.1179, ("EO21", "EO30")),
    ("Construction Machinery", 0.1550, ("EO22", "EO40")),
    ("Mining and Oilfield Machinery", 0.1500, ("EO50",)),
    ("Service Industry Machinery", 0.1650, ("EO60",)),
    ("Other Electrical Equipment", 0.1834, ("EO71", "EO72")),
    ("Other Nonresidential Equipment", 0.1473, ("EI11", "EO80")),
]
EQUIPMENT_COMPONENT_DELTA = {code: rate
                             for _name, rate, codes in EQUIPMENT_DEPRECIATION_CROSSWALK
                             for code in codes}
# Table A-2 has no separate nuclear-fuel or household-appliance line. These
# explicit proxies affect diagnostic calculations, not the headline parameters.
EQUIPMENT_COMPONENT_PROXIES = {
    "EI11": "Nuclear fuel assigned to Other Nonresidential Equipment",
    "EO71": "Household appliances assigned to Other Electrical Equipment",
}

ELASTICITY_CASES = {
    "Benchmark": (EPSILON_BENCHMARK, ETA_BENCHMARK, SIGMA_BENCHMARK),
    "Low elasticities": (0.3, 0.5, 0.5),
    "High elasticities": (0.9, 2.0, 2.0),
    "High asset substitution": (0.6, 1.0, 3.0),
}

INFLATION = 0.020
NOMINAL_INTEREST = 0.0682
DIVIDEND_RETURN = 0.0361          # real, after corporate tax
CAPGAIN_RETURN = 0.0317           # real; also CRS's proxy for real GDP growth g
DEBT_SHARE_CORP = 0.3226
INTEREST_DEDUCTIBLE_CORP = 0.9808
E_C = DIVIDEND_RETURN + CAPGAIN_RETURN            # required real return on corp equity
S_DEBT = 0.04209269               # real after-tax return on the debt leg
S_EQUITY = 0.062508481792         # all-equity saver return; regime-invariant
INV_HOLDING_PERIOD = 0.385        # T_inv (CRS R48277 Appendix C)
INV_FIFO_SHARE = 0.50             # gamma


def derive_s(debt_share=DEBT_SHARE_CORP):
    """Saver return at a given debt share: s = f*S_DEBT + (1-f)*S_EQUITY.

    S_EQUITY is investor-side (both r = E_c and s = E_c(1-nu) are), so it does
    not move with the statutory regime -- verified in tests by recovering it from
    the published land rate, for which rho_land = r/(1-tau) in closed form.
    """
    return debt_share * S_DEBT + (1.0 - debt_share) * S_EQUITY


def derive_r(debt_share=DEBT_SHARE_CORP, corp_rate=0.21):
    """Firm real after-tax discount rate at a given debt share."""
    debt_leg = NOMINAL_INTEREST * (1 - INTEREST_DEDUCTIBLE_CORP * corp_rate) - INFLATION
    return debt_share * debt_leg + (1 - debt_share) * E_C


S_MIXED = derive_s()              # 0.055922
R_MIXED = derive_r()              # 0.056946
R_EQUITY = E_C                    # 0.0678

# ==========================================================================
# 6. flow pipeline: Form 4562 mapping
# ==========================================================================
# SOI Complete Report Table 13 reports Form 4562 items down the rows and NAICS
# sectors across the columns.  Each row of basis placed in service maps to an
# asset category; "IND" means the assignment depends on the industry (the
# 39-year and 40-year ADS lines are nonresidential real property, whose type
# differs by sector), and None means the row is dropped.
#
# What is included, and why.  Part III reports the basis of property placed in
# service during the year, which is the acquisition measure wanted -- but that
# basis is net of the section 179 deduction and the special depreciation
# allowance, so those two are added back to reconstruct acquisition cost.  Rows
# that report a DEDUCTION on property that may have been acquired in earlier
# years are excluded, because they are not acquisition and cannot be dated:
#   - "Property subject to section 168(f)(1) election" (Part II). Property under
#     that election is outside MACRS, so its basis never appears in Part III;
#     the reported figure is a deduction. About 0.3% of Part III basis.
#   - "Other depreciation (including ACRS)" (Part II). A deduction on old assets.
#   - "Listed property" (Part IV). Carried from Part V as a deduction, and
#     includes property placed in service in earlier years. About 6% of Part III
#     basis, so excluding it omits some genuine equipment acquisition; that is
#     preferred to adding a deduction to a basis measure. Reported in the notes.
#   - "Class life property basis" (Part III Section C). Basis, but the ADS class
#     lives it covers are too heterogeneous to map to one asset category.
TABLE13_ROWS = [
    ("Section 179 expense deduction", "Equipment"),
    ("Special depreciation allowance", "Equipment"),
    ("3-year property basis", "Equipment"),
    ("5-year property basis", "Equipment"),
    ("7-year property basis", "Equipment"),
    ("10-year property basis", "Equipment"),
    ("15-year property basis", "Equipment"),
    ("20-year property basis", "Equipment"),
    ("25-year property basis", "Power_Struct"),
    ("Residential rental property basis", "Residential_Struct"),
    ("Nonresidential real property basis", "IND"),
    ("50-year property basis", "Other_Nonres"),
    ("Class life property basis", None),          # heterogeneous ADS; dropped
    ("12-year property basis", "Equipment"),
    ("30-year property basis", "Residential_Struct"),
    ("40-year property basis", "IND"),
]
# Rows deliberately not treated as acquisition; reported by the loader so the
# omission is visible rather than silent.
TABLE13_EXCLUDED = ["Property subject to section 168(f)(1)",
                    "Other depreciation (including ACRS)", "Listed property"]
# Which structure type the 39-year / 40-year lines represent, by sector.
NONRES_STRUCT_ASSIGNMENT = {
    "11": "Farm_Struct", "21": "OilGasMining_Struct", "22": "Power_Struct",
    "23": "Other_Nonres", "31-33": "Manufacturing_Struct",
    "48-49": "Other_Nonres",
    **{c: "Commercial_HealthCare" for c in
       ("42", "44-45", "51", "52", "53", "54", "55", "56", "61", "62", "71", "72", "81")},
}
# Sectors where SOI inventories are negligible and are set to zero.
NEGLIGIBLE_INVENTORY_SECTORS = {"51", "52", "53", "54", "55", "56", "61", "62", "71", "81"}
# NAICS code as it appears in the NSF table -> canonical sector key.
NSF_CODE_TO_SECTOR = {"31-33": "31-33", "21": "21", "22": "22", "42": "42",
                      "48-49": "48-49", "51": "51", "52": "52", "53": "53",
                      "54": "54", "621-23": "62"}

# ==========================================================================
# 7. land valuation
# ==========================================================================
# SOI supplies industry book-land holdings. land_controls.py derives the residual
# from four Financial Accounts series and scales those holdings by an explicitly
# approximate nonfinancial-corporate market/book multiple. No external numerical
# control is used by the current calculations. One 2022 multiple is applied to
# both stock years, preserving the historical comparison's fixed valuation rule.
LAND_BASES = {"SOI_book": None, "residual_nonres_RE": "nonres", "residual_total_RE": "total"}
LAND_STRUCTURES = "z1"
LAND_SCALING = "matched"
LAND_NONFIN_EXCLUDE = ("52",)
LAND_SOURCE_CAPTURE_DATE = "2026-10-12"  # four refreshed CSVs uploaded together
# SOI excluding sector 52 is an approximate crosswalk, not an exact Z.1 sector.
# The nonfinancial-corporate multiple is applied to all C-corporation industries,
# including finance: a common market/book uplift across legal forms and sectors.
LAND_COVERAGE_NOTE = (
    "Approximate nonfinancial SOI population excludes sector 52; financial holding "
    "companies and consolidation differences are not separately reconciled. The "
    "same valuation multiple is assumed for all C-corporation industries.")
# Historical inputs for comparison only; never used to construct stock weights.
LAND_LEGACY_CONTROLS = {"residual_nonres_RE": 1654.0, "residual_total_RE": 2572.0}
LAND_PRIMARY = "residual_total_RE"
LAND_REFERENCE_YEAR = 2022      # the factor is estimated here and applied to all years


def bea_asset_to_hist_cat(code):
    """BEA detailed asset code -> ten-category historical specification.

    Purchased software remains split into prepackaged and custom categories, as
    in the CRS equity-finance tables. Ordinary nonresidential structures are
    pooled because CRS publishes only their aggregate rate historically.
    """
    c = code.upper()
    if c == "ENS1":
        return "Prepackaged_Software"
    if c == "ENS2":
        return "Custom_Software"
    if c == "EQ00":
        return "Equipment"
    # EQ00 already includes every detailed equipment component, including
    # EP31/EP34/EP35/EP36. Do not add those components again as research.
    if c[:2] in ("EN", "RD"):
        return "RD"
    if c in ("SM01", "SM02"):
        return "OilGasMining_Struct"
    if c in ("SU30", "SU40", "SU50", "SU60"):
        return "Power_Struct"
    if c.startswith("S"):
        return "Nonres_Struct"
    return None


def bea_asset_to_cat(code):
    """BEA detailed asset code -> model category.

    Pre-packaged and custom software form their own category; own-account software
    stays with R&D, following the source's own treatment.
    """
    c = code.upper()
    if c in ("ENS1", "ENS2"):        # pre-packaged and custom software
        return "Software"
    if c == "EQ00":
        return "Equipment"
    # EQ00 already includes every detailed equipment component, including
    # EP31/EP34/EP35/EP36. Do not add those components again as research.
    if c[:2] in ("EN", "RD"):
        return "RD"                  # includes own-account software, per the source
    if c == "SI00":
        return "Manufacturing_Struct"
    if c == "SU20":
        return "Communications_Struct"
    if c == "SN00":
        return "Farm_Struct"
    if c in ("SM01", "SM02"):
        return "OilGasMining_Struct"
    if c in ("SU30", "SU40", "SU50", "SU60"):
        return "Power_Struct"
    if c in ("SB31", "SB32", "SC01", "SC02", "SC03", "SC04", "SOO1", "SOO2"):
        return "Commercial_HealthCare"
    if c.startswith("S"):
        return "Other_Nonres"
    return None
