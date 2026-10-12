"""Generate the paper's empirical tables, narrative values, and source audits.

Rates and headline stock conventions remain those in params.py. Appendix
diagnostics are separately identified and do not change the headline estimates.
"""
from pathlib import Path
import numpy as np
import pandas as pd

import params as P
import distortion as D
import stocks
import wedges


def welfare(st, epsilon=0.6, eta=1.0, sigma=1.0):
    if min(epsilon, eta, sigma) < 0 or epsilon == 0:
        raise ValueError("epsilon must be positive and other elasticities nonnegative")
    pieces = np.array([epsilon * st["zbar"] ** 2, eta * st["V_B"], sigma * st["V_W"]]) / 2
    total = float(pieces.sum())
    shares = pieces / total if total else np.zeros(3)
    return {
        "EB_over_B": total, "EB_billions": total * st["B_total"],
        "quantity_EB_over_B": pieces[0], "between_EB_over_B": pieces[1],
        "within_EB_over_B": pieces[2], "quantity_EB_share": shares[0],
        "between_EB_share": shares[1], "within_EB_share": shares[2],
        "nonuniform_EB_share": shares[1] + shares[2],
        "uniform_at_mean_EB_over_B": pieces[0],
        "uniform_at_mean_EB_billions": pieces[0] * st["B_total"],
        "equivalent_uniform_wedge": float(np.sqrt(2 * total / epsilon)),
    }


def calibration_table(st):
    rows = []
    for name, (epsilon, eta, sigma) in P.ELASTICITY_CASES.items():
        row = {"specification": name, "epsilon": epsilon, "eta": eta, "sigma": sigma}
        row.update(welfare(st, epsilon, eta, sigma))
        rows.append(row)
    return pd.DataFrame(rows)


def historical_contrasts(cells):
    metrics = ("zbar", "sqrt_V_B", "sqrt_V_W", "EB_over_B")
    rows = []
    pairs = []
    for y in (2016, 2022):
        pairs.append((f"Law effect at {y} stocks", (y, "eq_2017"), (y, "eq_2025_obbba")))
    for law in ("eq_2017", "eq_2025_obbba"):
        pairs.append((f"Composition effect under {law}", (2016, law), (2022, law)))
    pairs.append(("Total diagonal", (2016, "eq_2017"), (2022, "eq_2025_obbba")))
    for label, before, after in pairs:
        for metric in metrics:
            rows.append({"contrast": label, "metric": metric,
                         "change_pp": 100 * (cells[after][metric] - cells[before][metric])})
        old, new = cells[before]["EB_over_B"], cells[after]["EB_over_B"]
        rows.append({"contrast": label, "metric": "relative_EB_reduction",
                     "change_pp": 100 * (old - new) / old})
    return pd.DataFrame(rows)


def _md(frame):
    """Markdown without a dependency on tabulate."""
    headers = [str(c) for c in frame.columns]
    result = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in frame.itertuples(index=False, name=None):
        result.append("| " + " | ".join(str(v).replace("|", "/") for v in row) + " |")
    return "\n".join(result)


def _tex_escape(value):
    return str(value).replace("\\", "\\textbackslash{} ").replace("&", "\\&").replace("_", "\\_").replace("%", "\\%").replace("#", "\\#")


def _latex_table(frame, caption, label):
    lines = ["\\begin{table}[htbp]", "\\centering", f"\\caption{{{caption}}}",
             f"\\label{{{label}}}", "\\small", "\\begin{tabular}{l" + "r" * (len(frame.columns) - 1) + "}", "\\hline"]
    lines.append(" & ".join(_tex_escape(c) for c in frame.columns) + r" \\")
    lines.append("\\hline")
    for row in frame.itertuples(index=False, name=None):
        lines.append(" & ".join(_tex_escape(v) for v in row) + r" \\")
    lines += ["\\hline", "\\end{tabular}", "\\end{table}", ""]
    return "\n".join(lines)


def aggregation_diagnostics(main, destination):
    """Recompute appendix checks from documented component rates and stocks."""
    rows, industry_rows, component_rows = [], [], []
    structure_cats = ["Manufacturing_Struct", "Communications_Struct", "Farm_Struct",
                      "Commercial_HealthCare", "Other_Nonres"]
    baseline = main["stats"]
    diagnostic_stats = {}
    for year in (2016, 2022):
        K, _ = stocks.build_K(year)
        H = stocks.build_K_historical(year)
        raw = stocks.equipment_components(year)
        missing = [c for c in raw if c not in P.EQUIPMENT_COMPONENT_DELTA and raw[c].sum() > 0]
        if missing:
            raise ValueError(f"Equipment depreciation crosswalk is incomplete: {missing}")
        shares = stocks._corporate_shares(max(2017, year))
        cc_share = __import__("soi").ccorp_share_of_depreciable(year)
        factors = pd.Series({P.SECTOR_NAMES[c]: shares[stocks._group(c)]["Equipment"] * cc_share[P.SECTOR_NAMES[c]]
                             for c in P.SECTOR_CODES})
        comp = raw.mul(factors, axis=0)
        rates = pd.Series({c: P.EQUIPMENT_COMPONENT_DELTA[c] for c in comp})
        total = comp.sum(axis=1)
        delta_i = comp.mul(rates, axis=1).sum(axis=1).div(total).fillna(P.DELTA_DETAILED["Equipment"])
        global_delta = float(comp.mul(rates, axis=1).to_numpy().sum() / comp.to_numpy().sum())
        software_delta = float((H["Prepackaged_Software"].sum() * P.DELTA_HIST["Prepackaged_Software"]
                               + H["Custom_Software"].sum() * P.DELTA_HIST["Custom_Software"])
                              / (H["Prepackaged_Software"].sum() + H["Custom_Software"].sum()))
        structure_delta = float(K[structure_cats].mul(pd.Series(P.DELTA_DETAILED), axis=1)[structure_cats].to_numpy().sum()
                                / K[structure_cats].to_numpy().sum())
        for cat, used, derived in [("Equipment", P.DELTA_DETAILED["Equipment"], global_delta),
                                   ("Software", P.DELTA_DETAILED["Software"], software_delta),
                                   ("Ordinary nonresidential structures", P.DELTA_HIST["Nonres_Struct"], structure_delta)]:
            rows.append({"stock_year": year, "category": cat, "implemented_delta": used,
                         "diagnostic_stock_weighted_delta": derived,
                         "basis": "C-corporation stocks; equipment crosswalk proxies explicitly listed"})
        for name in K.index:
            industry_rows.append({"stock_year": year, "industry": name, "equipment_delta": delta_i[name],
                                  "EQ00_ccorp_billions": K.loc[name, "Equipment"],
                                  "component_sum_ccorp_billions": total[name],
                                  "component_minus_EQ00_billions": total[name] - K.loc[name, "Equipment"]})
        for code in comp:
            source_class = next(name for name, _, codes in P.EQUIPMENT_DEPRECIATION_CROSSWALK if code in codes)
            component_rows.append({"stock_year": year, "BEA_code": code, "CRS_class": source_class,
                                   "delta": rates[code], "ccorp_stock_billions": comp[code].sum(),
                                   "proxy_note": P.EQUIPMENT_COMPONENT_PROXIES.get(code, "")})
        if year == 2022:
            z = main["wedges"]["z"].to_dict()
            deltas = pd.DataFrame({c: P.DELTA_DETAILED[c] for c in K}, index=K.index)
            zs = pd.DataFrame({c: z[c] for c in K}, index=K.index)
            deltas["Equipment"] = delta_i
            zs["Equipment"] = P.S_MIXED / (P.S_MIXED + delta_i) * P.MIXED_DETAILED["Equipment"] / (1 - P.MIXED_DETAILED["Equipment"])
            diagnostic_stats["industry-specific equipment depreciation"] = D.capital_service_stats(K, zs, deltas, P.S_MIXED)
            for chosen_delta in (0.10, 0.18):
                dd = dict(P.DELTA_DETAILED); dd["Equipment"] = chosen_delta
                zz = wedges.wedge_table(P.MIXED_DETAILED, dd, P.S_MIXED)["z"].to_dict()
                diagnostic_stats[f"equipment depreciation {chosen_delta:.2f}"] = D.capital_service_stats(K, zz, dd, P.S_MIXED)
            block_B = K[structure_cats].mul(pd.Series({c: P.S_EQUITY + P.DELTA_DETAILED[c] for c in structure_cats}), axis=1)
            detailed_z = wedges.equity_obbba_12()["z"]
            detailed_mean = float(block_B.mul(detailed_z, axis=1)[structure_cats].to_numpy().sum() / block_B.to_numpy().sum())
            pooled_z = float(wedges.equity_historical("eq_2025_obbba").loc["Nonres_Struct", "z"])
            pd.DataFrame([{"detailed_block_mean": detailed_mean, "pooled_block_wedge": pooled_z,
                           "block_difference_pp": 100 * (pooled_z - detailed_mean),
                           "detailed_block_service_share": block_B.to_numpy().sum() / D.capital_service_stats(K, detailed_z.to_dict(), P.DELTA_DETAILED, P.S_EQUITY)["B_total"]}]).to_csv(destination / "structure_aggregation_diagnostic.csv", index=False)
    pd.DataFrame(rows).to_csv(destination / "aggregate_depreciation_checks.csv", index=False)
    pd.DataFrame(industry_rows).to_csv(destination / "equipment_depreciation_by_industry.csv", index=False)
    pd.DataFrame(component_rows).to_csv(destination / "equipment_depreciation_crosswalk.csv", index=False)
    sensitivity_rows = []
    for name, st in diagnostic_stats.items():
        sensitivity_rows.append({"specification": name, "zbar": st["zbar"], "sqrt_VB": st["sqrt_V_B"],
                                 "sqrt_VW": st["sqrt_V_W"],
                                 "mean_change_pp": 100 * (st["zbar"] - baseline["zbar"]),
                                 "between_SD_change_pp": 100 * (st["sqrt_V_B"] - baseline["sqrt_V_B"]),
                                 "within_SD_change_pp": 100 * (st["sqrt_V_W"] - baseline["sqrt_V_W"])})
    pd.DataFrame(sensitivity_rows).to_csv(destination / "equipment_depreciation_sensitivity.csv", index=False)
    eq = main["wedges"].loc["Equipment"]
    zmin = P.S_MIXED / (P.S_MIXED + P.EQUIPMENT_DELTA_MAX) * eq["tau"]
    zmax = P.S_MIXED / (P.S_MIXED + P.EQUIPMENT_DELTA_MIN) * eq["tau"]
    return {"equipment_wedge_min": zmin, "equipment_wedge_max": zmax,
            "equipment_variance_bound_squared_pp": ((zmax - zmin) ** 2 / 4) * 10000,
            "equipment_delta_2022_min": min(r["equipment_delta"] for r in industry_rows if r["stock_year"] == 2022),
            "equipment_delta_2022_max": max(r["equipment_delta"] for r in industry_rows if r["stock_year"] == 2022)}


def land_audit(destination):
    """Record the actual derived controls, source observations, and assumptions."""
    import land_controls
    land_controls.control_inputs().to_csv(destination / "land_control_inputs.csv", index=False)
    land_controls.source_audit().to_csv(destination / "land_control_source_audit.csv", index=False)


def write_paper_outputs(baseline, no_credit, verbose=True):
    destination = Path(P.OUTPUT_DIR)
    values = []
    summaries = []

    def value(spec, metric, amount, unit):
        values.append({"specification": spec, "metric": metric, "value": amount, "unit": unit})

    for name, out in (("baseline", baseline), ("no_section41_credit", no_credit)):
        st = out["stats"]
        row = {"specification": name, "zbar": st["zbar"], "sqrt_VB": st["sqrt_V_B"],
               "sqrt_VW": st["sqrt_V_W"], "V_B": st["V_B"], "V_W": st["V_W"],
               "stock_total_billions": float(out["K"].to_numpy().sum()), "B_billions": st["B_total"]}
        row.update(welfare(st, P.EPSILON_BENCHMARK, P.ETA_BENCHMARK, P.SIGMA_BENCHMARK))
        summaries.append(row)
        for key, amount in row.items():
            if key == "specification": continue
            if key.endswith("billions"): unit = "billions of dollars"
            elif key in ("V_B", "V_W"): unit = "squared decimal units"
            else: unit = "decimal fraction"
            value(name, key, amount, unit)
        # Exact figure inputs and narrative extrema, without rounding stock weights.
        out["K"].to_csv(destination / f"K_ia_2022_unrounded_{name}.csv")
        st["B_ia"].to_csv(destination / f"capital_services_2022_{name}.csv")
        st["alpha"].to_csv(destination / f"within_industry_weights_{name}.csv")
        st["asset_shares"].rename("service_share").to_csv(destination / f"asset_service_shares_{name}.csv")
        industry = pd.DataFrame({"Z_i": st["Z_i"], "phi_i": st["phi"], "within_sd": st["within_sd"], "B_billions": st["B_i"]})
        industry.to_csv(destination / f"industry_detail_{name}.csv")
        for series_key, series in (("industry_wedge", st["Z_i"]), ("within_SD", st["within_sd"]), ("industry_service_share", st["phi"])):
            for extreme, amount in (("min", series.min()), ("max", series.max())):
                value(name, f"{series_key}_{extreme}", amount, "decimal fraction")
                value(name, f"{series_key}_{extreme}_industries", " | ".join(series.index[np.isclose(series, amount)]), "industry names")
        value(name, "industry_wedge_range", st["Z_i"].max() - st["Z_i"].min(), "decimal fraction")
        for metric, amount in (("manufacturing_wedge", st["Z_i"][P.SECTOR_NAMES["31-33"]]),
                               ("manufacturing_service_share", st["phi"][P.SECTOR_NAMES["31-33"]])):
            value(name, metric, amount, "decimal fraction")
        cal = calibration_table(st)
        cal.to_csv(destination / f"elasticity_sensitivity_{name}.csv", index=False)
        historical_contrasts(out["cells"]).to_csv(destination / f"historical_contrasts_{name}.csv", index=False)
    summary = pd.DataFrame(summaries)
    summary.to_csv(destination / "welfare_summary.csv", index=False)
    for year in (2016, 2022):
        stocks.build_K_historical(year).to_csv(destination / f"K_ia_{year}_historical_unrounded.csv")
    historical_schedule = pd.DataFrame({"pre_TCJA_m": P.EQUITY_HIST["eq_2017"],
                                        "post_OBBBA_m": P.EQUITY_HIST["eq_2025_obbba"], "delta": P.DELTA_HIST}).reindex(P.CATS_HIST)
    historical_schedule.index.name = "asset"
    historical_schedule.to_csv(destination / "historical_asset_schedule.csv")
    agg = aggregation_diagnostics(baseline, destination)
    for key, amount in agg.items():
        value("aggregation_diagnostics", key, amount,
              "squared percentage points" if "squared_pp" in key else "decimal fraction")
    land_audit(destination)
    for basis in P.LAND_BASES:
        for key in ("zbar", "sqrt_VB", "sqrt_VW", "land_share"):
            amount = float(baseline["dispersion"].set_index("land_basis").loc[basis, key])
            value(basis, key, amount, "decimal fraction")
    for year in (2016, 2022):
        for law in ("eq_2017", "eq_2025_obbba"):
            for key in ("zbar", "sqrt_V_B", "sqrt_V_W", "EB_over_B"):
                value(f"{year}_{law}", key, baseline["cells"][(year, law)][key], "decimal fraction")
    pd.DataFrame(values).to_csv(destination / "paper_values.csv", index=False)

    # All six numerical tables retained in the supplied manuscript.
    tables = []
    cal = calibration_table(baseline["stats"])[["specification", "epsilon", "eta", "sigma", "EB_over_B"]].copy()
    cal["EB_over_B"] = cal["EB_over_B"].map(lambda x: f"{100*x:.2f}%")
    cal.columns = ["Specification", "epsilon", "eta", "sigma", "EB/B"]
    tables.append(("Excess Burden under Alternative Elasticity Assumptions", "tab:eb", cal))
    hist = pd.read_csv(destination / "table_3_law_x_stockyear.csv")
    hist["law"] = hist["law"].map({"eq_2017": "Pre-TCJA", "eq_2025_obbba": "Post-OBBBA"})
    for col in ("zbar", "sqrt_VB", "sqrt_VW", "EB_over_B"):hist[col] = hist[col].map(lambda x: f"{100*x:.2f}")
    hist.columns = ["Stock year", "Law", "Mean (%)", "Between SD (pp)", "Within SD (pp)", "EB/B (%)"]
    tables.append(("Tax Law and Capital-Stock Composition", "tab:historical_comparison", hist))
    asset = baseline["wedges"][["m", "delta", "z"]].reset_index()
    for col in ("m", "delta", "z"):asset[col] = asset[col].map(lambda x: f"{100*x:.2f}")
    asset.columns = ["Asset", "METR (%)", "Depreciation (%)", "Wedge (%)"]
    tables.append(("Asset-Level User-Cost Wedges", "tab:asset_wedges_full", asset))
    hs = historical_schedule[["pre_TCJA_m", "post_OBBBA_m"]].reset_index()
    for col in ("pre_TCJA_m", "post_OBBBA_m"):hs[col] = hs[col].map(lambda x: f"{100*x:.1f}")
    hs.columns = ["Asset", "Pre-TCJA METR (%)", "Post-OBBBA METR (%)"]
    tables.append(("Asset Categories and METRs in the Historical Comparison", "tab:historical_metr_schedule", hs))
    land = baseline["dispersion"][["land_basis", "zbar", "sqrt_VB", "sqrt_VW", "land_share"]].copy()
    for col in land.columns[1:]:land[col] = land[col].map(lambda x: f"{100*x:.2f}")
    land.columns = ["Land valuation", "Mean (%)", "Between SD (pp)", "Within SD (pp)", "Land share (%)"]
    tables.append(("User-Cost Wedge Dispersion and Alternative Land Valuations", "tab:land_sensitivity", land))
    bridge = pd.read_csv(destination / "table_B3_specification_bridge.csv").drop(columns="EB_over_B")
    for col in bridge.columns[1:]:bridge[col] = bridge[col].map(lambda x: f"{100*x:.2f}")
    bridge.columns = ["Specification", "Mean (%)", "Between SD (pp)", "Within SD (pp)"]
    tables.append(("Effect of Financing and Asset Aggregation on Current-Law Wedges", "tab:specification_bridge", bridge))
    (destination / "paper_tables.tex").write_text("% Generated from unrounded stocks and parameters; percentages shown in headers.\n\n" +
                                                "\n".join(_latex_table(frame, title, label) for title, label, frame in tables), encoding="utf-8")
    fragments = destination / "paper_tables"
    fragments.mkdir(exist_ok=True)
    for title, label, frame in tables:
        (fragments / (label.replace(":", "_") + ".tex")).write_text(_latex_table(frame, title, label), encoding="utf-8")
    macros = ["% Generated scalar values. These commands replace stale hard-coded manuscript numbers."]
    macro_metrics = {"MeanWedge": "zbar", "BetweenSD": "sqrt_VB", "WithinSD": "sqrt_VW",
                     "ExcessBurden": "EB_over_B", "EquivalentUniformWedge": "equivalent_uniform_wedge",
                     "QuantityLossShare": "quantity_EB_share", "BetweenLossShare": "between_EB_share",
                     "WithinLossShare": "within_EB_share", "NonuniformLossShare": "nonuniform_EB_share",
                     "UniformAtMeanExcessBurden": "uniform_at_mean_EB_over_B"}
    for name, row in zip(("Baseline", "NoCredit"), summaries):
        for suffix, key in macro_metrics.items():
            macros.append("\\newcommand{\\Paper" + name + suffix + "}{" + f"{100*row[key]:.2f}" + r"\%}")
        macros.append("\\newcommand{\\Paper" + name + "CapitalServicesTrillions}{" + f"{row['B_billions']/1000:.3f}" + "}")
        macros.append("\\newcommand{\\Paper" + name + "ExcessBurdenBillions}{" + f"{row['EB_billions']:.2f}" + "}")
    (destination / "paper_values.tex").write_text("\n".join(macros) + "\n", encoding="utf-8")
    coverage = [
        ("Table tab:eb", "elasticity_sensitivity_baseline.csv; paper_tables.tex", "Generated"),
        ("Table tab:historical_comparison", "table_3_law_x_stockyear.csv; paper_tables.tex", "Generated"),
        ("Table tab:asset_wedges_full", "table_A1_asset_wedges.csv; paper_tables.tex", "Generated"),
        ("Table tab:historical_metr_schedule", "historical_asset_schedule.csv; paper_tables.tex", "Generated"),
        ("Table tab:land_sensitivity", "table_2_dispersion.csv; paper_tables.tex", "Generated from derived land multiples; coverage approximation disclosed"),
        ("Table tab:specification_bridge", "table_B3_specification_bridge.csv; paper_tables.tex", "Generated"),
        ("Figures and industry extrema / manufacturing values", "figure_1_between_industry.png; figure_2_within_composition.png; industry_detail_baseline.csv; paper_values.csv", "Generated"),
        ("Capital-service total, dollar welfare, welfare shares, uniform counterfactuals", "welfare_summary.csv; paper_values.csv; paper_values.tex", "Generated"),
        ("No-credit results including welfare and equivalent uniform wedge", "welfare_summary.csv; elasticity_sensitivity_no_section41_credit.csv; paper_values.csv", "Generated"),
        ("Historical mean / SD / welfare contrasts and relative reductions", "historical_contrasts_baseline.csv", "Generated"),
        ("Aggregate software and ordinary-structure depreciation checks", "aggregate_depreciation_checks.csv", "Derived checks; headline fixed inputs retained"),
        ("Equipment depreciation by industry and resulting moment changes", "equipment_depreciation_crosswalk.csv; equipment_depreciation_by_industry.csv; equipment_depreciation_sensitivity.csv", "Generated using explicit component crosswalk; proxies identified"),
        ("Structure-block aggregation comparison", "structure_aggregation_diagnostic.csv", "Generated"),
        ("Equipment wedge range and variance bound", "paper_values.csv; aggregation_diagnostics.csv", "Generated"),
        ("Current land controls and source arithmetic", "land_control_inputs.csv; land_control_source_audit.csv", "Derived from four archived Financial Accounts series; SOI population crosswalk approximate"),
        ("Original derivation of fixed aggregate equipment delta 0.126", "aggregate_depreciation_checks.csv; equipment_depreciation_crosswalk.csv", "Original upstream calculation not recovered; new diagnostic derivation shown"),
        ("Retired investment-flow METRs", "None", "Excluded from default run and paper outputs"),
    ]
    pd.DataFrame(coverage, columns=["paper_item", "output", "status"]).to_csv(destination / "paper_output_coverage.csv", index=False)
    summary_view = []
    percent_metrics = ["zbar", "sqrt_VB", "sqrt_VW", "EB_over_B", "quantity_EB_share", "between_EB_share",
                       "within_EB_share", "nonuniform_EB_share", "uniform_at_mean_EB_over_B", "equivalent_uniform_wedge"]
    for metric in percent_metrics:
        summary_view.append({"Metric in percent or pp": metric, "Baseline": f"{100*summaries[0][metric]:.4f}",
                             "No Section 41 credit": f"{100*summaries[1][metric]:.4f}"})
    for metric in ("B_billions", "EB_billions", "uniform_at_mean_EB_billions"):
        summary_view.append({"Metric in percent or pp": metric + " (billions of dollars)",
                             "Baseline": f"{summaries[0][metric]:.4f}", "No Section 41 credit": f"{summaries[1][metric]:.4f}"})
    report = ["# Stock based paper outputs", "", "These outputs include the EP3 duplication correction. All six retained numerical tables are generated below. Figures and exact numerical inputs are in the same directory.", "",
              "## Welfare and narrative values", "", _md(pd.DataFrame(summary_view)), ""]
    for title, label, frame in tables:report += ["## " + title, "", "Manuscript label: `" + label + "`", "", _md(frame), ""]
    report += ["## Historical contrasts", "", _md(historical_contrasts(baseline["cells"]).round(6)), "",
               "## Source and replication coverage", "", _md(pd.DataFrame(coverage, columns=["Paper item", "Output", "Status"])), "",
               "Land controls are derived from archived 2022 Financial Accounts observations. The total-real-estate residual uses nonfinancial corporate structures from the same source sector. A market/book multiple measured on SOI corporations excluding sector 52 is applied to all C-corporation industries and both stock years. This sector crosswalk and common valuation uplift are explicit approximations. The old 1654 / 2572 inputs are comparison values only; their original derivation remains unresolved.", "",
               "Equipment component diagnostics use CRS R48277 Table A-2 and an explicit BEA crosswalk. Nuclear fuel and household appliances use disclosed broad-class proxies. These diagnostic choices do not change the headline depreciation input of 0.126.", ""]
    (destination / "paper_report.md").write_text("\n".join(report), encoding="utf-8")
    if verbose:
        print("\n--- paper tables and narrative values ---")
        for row in summaries:
            print(f"  {row['specification']}: B=${row['B_billions']/1000:.3f}T; EB/B={100*row['EB_over_B']:.4f}%; EB=${row['EB_billions']:.2f}B")
            print(f"    EB shares: quantity={100*row['quantity_EB_share']:.2f}%, between={100*row['between_EB_share']:.2f}%, within={100*row['within_EB_share']:.2f}%")
            print(f"    Uniform at mean EB/B={100*row['uniform_at_mean_EB_over_B']:.4f}%; equivalent uniform wedge={100*row['equivalent_uniform_wedge']:.2f}%")
        for title, _label, frame in tables:
            print("\n  " + title + ":")
            print(frame.to_string(index=False))
        print("\n  Historical contrasts (pp; relative welfare reduction in percent):")
        print(historical_contrasts(baseline["cells"]).to_string(index=False))
        for key in ("industry_wedge_min", "industry_wedge_max", "manufacturing_wedge", "manufacturing_service_share", "within_SD_min", "within_SD_max"):
            item = next(v for v in values if v["specification"] == "baseline" and v["metric"] == key)
            print(f"  {key}: {100*item['value']:.4f}%")
        print("\n  All six retained tables: paper_tables.tex")
        print("  Full readable report: paper_report.md")
        print("  Narrative scalars: paper_values.csv and paper_values.tex")
        print("  Coverage and source gaps: paper_output_coverage.csv")
        print("  Land controls are derived; see land_control_inputs.csv and land_control_source_audit.csv for source/coverage details")
    return {"summary": summary, "values": pd.DataFrame(values), "coverage": coverage, "tables": tables}
