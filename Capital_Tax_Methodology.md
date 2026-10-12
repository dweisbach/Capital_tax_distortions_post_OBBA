# Methodology for Measuring Capital Tax Distortions

This appendix documents the construction of the empirical estimates in Capital Tax Distortions after OBBBA. The analysis combines published asset-level marginal effective tax rates with an industry-by-asset matrix of capital stocks for C corporations. It converts the tax rates into proportional user-cost wedges, values the stocks at benchmark annual capital-service costs, and calculates the average wedge and its dispersion across and within industries. A separate comparison crosses two stock years with two tax regimes. Behavioral elasticities enter only when these measured moments are translated into approximate excess burden.

The main specification uses 2022 stocks, thirteen asset categories, and the post-OBBBA corporate mixed-finance tax schedule. The historical comparison uses 2016 and 2022 stocks, ten common asset categories, and equity-financed schedules for pre-TCJA and post-OBBBA law. The analysis covers nineteen NAICS sectors. It excludes pass-through businesses because the available noncorporate tax schedules cannot be matched consistently to stocks for particular legal forms and owners. Partnership balance sheets, investment flows, Form 4562 tabulations, and NSF research-expenditure files do not enter these estimates.

## 1 Objects being measured

Let i index industries, a index model asset categories, and y index the stock year. The stock matrix $K_{ia,y}$ measures capital in billions of dollars. Produced assets are measured at current replacement cost, net of economic depreciation. Land is measured under alternative valuation conventions; inventories remain at their SOI balance-sheet values. These differences in measurement are addressed below rather than concealed by labeling every entry a directly observed current-cost stock.

The asset-level tax input is a marginal effective tax rate $m_a$. Define $\rho_a$ as the real pretax return required on a marginal investment and s as the real after-tax return required by the saver. The METR and the required-return wedge satisfy

```math
m_a=\frac{\rho_a-s}{\rho_a},\qquad \rho_a=\frac{s}{1-m_a},\qquad \tau_a=\frac{m_a}{1-m_a}.
```

The user-cost wedge is a different object. With economic depreciation $\delta_a$, benchmark and taxed annual user costs per dollar of capital are $c_a^0=s+\delta_a$ and $c_a^T=\rho_a+\delta_a$. Hence

```math
z_a=\frac{c_a^T-c_a^0}{c_a^0}=\frac{s}{s+\delta_a}\frac{m_a}{1-m_a}.
```

A positive $z_a$ raises the price relevant to capital demand; a negative value lowers it. The annual capital-service value used for weighting is $B_{ia}=(s+\delta_a)K_{ia}$. It is a benchmark cost valuation of the stock, not observed rental revenue or a measure of tax receipts. The tax schedules are forward-looking marginal rates applied to the composition of observed stocks; the analysis does not reconstruct the taxes actually paid on each historical investment vintage.

## 2 Sources and the sequence of construction

The construction proceeds in a fixed order. First, BEA detailed stocks are combined into model asset categories and nineteen industries. Second, the produced-asset stocks are narrowed from all legal forms to corporations and then to C corporations. Third, inventories, land, and residential structures are added from their separate sources. Fourth, the asset-level METRs are converted to wedges using the financing-matched saver return and the economic depreciation schedule. Finally, benchmark capital-service weights determine the mean and dispersion statistics. The historical and sensitivity specifications repeat these steps while varying only the designated inputs.

Table 1 lists the sources used by this stock-based construction. Filenames are the canonical names expected by the scripts; upload suffixes such as (1) have no substantive meaning.

**Table 1 Input sources and their roles**

| Input | Source and file | Role |
| --- | --- | --- |
| Detailed produced-asset stocks | BEA current-cost net nonresidential stocks; `detailnonres_stk1.xlsx` | Industry and asset composition in 2016 and 2022 |
| Corporate shares | BEA Fixed Assets Table 4.1; `BEA_Table_4_1.csv` | Corporate share by broad industry group and asset class |
| Residential structures | BEA Fixed Assets Table 5.1; `BEA_Table_5_1.csv` | Corporate residential stock |
| Corporate balance sheets | SOI Complete Report Tables 5.1 and 6.1; `16co51ccr.xlsx`, `16co61ccr.xlsx`, `22co51ccr.xlsx`, `22co61ccr.xlsx` | C-corporation shares, land, inventories, and suppressed-cell allocation |
| Current-law METRs | CRS R48631, Tables 2 and 3 | Corporate mixed-finance and equity-finance schedules |
| Historical METRs | CRS R48153, Table 4 | Pre-TCJA corporate equity-finance schedule |
| Depreciation and financing inputs | CRS R48277, Tables A-1 and A-2; constants in `params.py` | Saver returns, economic depreciation, and parameter reconciliation |
| Land valuation controls | Financial Accounts real estate and structures; `NCBREMV.csv`, `BOGZ1FL105035033A.csv`, `RCSNNWMVBSNNCB.csv`, and `RCVSRNWMVBSNNCB.csv` | Residual land values and SOI market-to-book valuation multiples |

The BEA extracts used here were updated September 26, 2025. Both stock years are read from the same detailed workbook, so the historical comparison uses a common data revision. The supplied Table 4.1 and Table 5.1 extracts begin in 2017. Consequently, the 2016 construction uses 2017 corporate shares and the 2017 corporate residential total, together with 2016 detailed nonresidential stocks and 2016 SOI data. The 2022 construction uses 2022 observations throughout these sources.

All computations use unrounded inputs. BEA detailed stocks, reported in millions of dollars, are divided by 1,000; SOI balance-sheet amounts, reported in thousands, are divided by 1,000,000. BEA Tables 4.1 and 5.1 already report billions. The exported stock CSV is rounded to one decimal place for readability and should not be substituted for the unrounded matrix when seeking exact replication.

## 3 Industry and asset classification

### 3.1 Industry concordance

The BEA workbook’s readme sheet supplies a concordance from BEA industries to NAICS. The code reads the leading two digits of each NAICS designation and combines manufacturing into 31–33, retail trade into 44–45, and transportation and warehousing into 48–49. SOI sector headings are matched to the same canonical industries. Where several SOI columns belong to one sector, their published amounts are added. The detailed workbook’s Datasets sheet supplies the numerical BEA series; separate industry worksheets are not added again.

**Table 2 Industry concordance and corporate share group**

| NAICS | Industry | BEA share group |
| --- | --- | --- |
| 11 | Agriculture forestry fishing and hunting | Farms |
| 21 | Mining quarrying and oil and gas extraction | Nonfarm nonmanufacturing |
| 22 | Utilities | Nonfarm nonmanufacturing |
| 23 | Construction | Nonfarm nonmanufacturing |
| 31–33 | Manufacturing | Manufacturing |
| 42 | Wholesale trade | Nonfarm nonmanufacturing |
| 44–45 | Retail trade | Nonfarm nonmanufacturing |
| 48–49 | Transportation and warehousing | Nonfarm nonmanufacturing |
| 51 | Information | Nonfarm nonmanufacturing |
| 52 | Finance and insurance | Nonfarm nonmanufacturing |
| 53 | Real estate and rental and leasing | Nonfarm nonmanufacturing |
| 54 | Professional scientific and technical services | Nonfarm nonmanufacturing |
| 55 | Management of companies and enterprises | Nonfarm nonmanufacturing |
| 56 | Administrative support and waste management | Nonfarm nonmanufacturing |
| 61 | Educational services | Nonfarm nonmanufacturing |
| 62 | Health care and social assistance | Nonfarm nonmanufacturing |
| 71 | Arts entertainment and recreation | Nonfarm nonmanufacturing |
| 72 | Accommodation and food services | Nonfarm nonmanufacturing |
| 81 | Other services | Nonfarm nonmanufacturing |

Industries outside this concordance are not assigned to a residual sector. The estimates therefore refer to this constructed C-corporation capital universe, rather than the entire economy’s productive wealth.

### 3.2 Main asset concordance

Table 3 records the implemented mapping in the order in which the rules are applied. BEA series beginning with K1N are parsed into an industry identifier and a four-character asset code. Equipment is taken from the EQ00 total rather than added from its detailed components. The roll-up codes ST00, IP00, and IPP0 are excluded. Unmapped codes contribute no stock. In particular, BEA entertainment originals with AE codes are excluded.

**Table 3 BEA asset codes and model categories**

| Source code or rule | Main category | Corporate share class |
| --- | --- | --- |
| EQ00 | Equipment | Equipment |
| ENS1, ENS2 | Purchased software | Intellectual property products |
| Remaining EN codes and RD codes | Research and own-account software | Intellectual property products |
| SI00 | Manufacturing structures | Structures |
| SU20 | Communications structures | Structures |
| SN00 | Farm structures | Structures |
| SB31, SB32, SC01–SC04, SOO1, SOO2 | Commercial and health care structures | Structures |
| SM01, SM02 | Oil gas and mining structures | Structures |
| SU30, SU40, SU50, SU60 | Power structures | Structures |
| Other structure codes beginning with S | Other nonresidential structures | Structures |
| SOI land and inventory rows | Land and inventories | Direct C-corporation subtraction |
| BEA Table 5.1 corporate residential row | Residential structures | Separate residential construction |

The research category combines BEA research-and-development codes with own-account software (ENS3). Purchased software (ENS1 and ENS2) is classified separately. Physical equipment codes EP31, EP34, EP35, and EP36 remain in the EQ00 equipment total and are not added to research. These codes respectively identify photocopy and related equipment, nonelectromedical instruments, electromedical instruments, and nonmedical instruments. The main and historical stock builders apply the same rule, so equipment is counted once. Stocks in the research category receive its METR, depreciation rate, and intellectual-property corporate-share adjustment. The Section 41 sensitivity applies to research and own-account software rather than to physical equipment.

SOO1 and SOO2, which identify offices and medical buildings, use the letter O. They are distinct from SO01 and SO02, which identify water supply and sewage and waste disposal and enter other nonresidential structures. Manufacturing structures are an asset classification wherever held; the code does not infer structure type solely from the owner’s industry or test firm-level eligibility for expensing.

## 4 Converting produced stocks to C corporations

Let $\widetilde K_{ia,y}$ denote the sum of BEA current-cost net stocks assigned to industry i and category a, before legal-form adjustments. The detailed series cover all legal forms. Two multiplicative shares narrow those stocks to the empirical universe.

### 4.1 Corporate share by broad industry and asset class

For industry group g and asset class h, define

```math
q_{gh,y}=\frac{\text{BEA corporate stock}_{gh,y}}{\text{BEA all legal form stock}_{gh,y}}.
```

The groups are farms, manufacturing, and nonfarm nonmanufacturing; the asset classes are equipment, structures, and intellectual property products. Table 4 gives the exact Table 4.1 line pairs. The IPP share is applied to both purchased software and the research category. Every industry in the same broad group receives the same class-specific corporate share.

**Table 4 BEA Table 4 1 corporate share calculations**

| Group | Equipment lines | Structures lines | IPP lines |
| --- | --- | --- | --- |
| Farms | 22 / 6 | 23 / 7 | 24 / 8 |
| Manufacturing | 26 / 10 | 27 / 11 | 28 / 12 |
| Nonfarm nonmanufacturing | 30 / 14 | 31 / 15 | 32 / 16 |

For example, the 2022 manufacturing corporate shares are 0.912659 for equipment, 0.940026 for structures, and 0.922683 for IPP. This step assumes that the corporate fraction for the broad class is applicable to the detailed assets and industries within that group. It does not identify a separate corporate fraction for each detailed BEA series.

### 4.2 C corporation share within corporations

SOI Complete Report Table 5.1 covers all corporations and Table 6.1 covers S corporations. Let $D_{i,y}^{all}$ and $D_{i,y}^{S}$ denote their reported depreciable assets. Define

```math
h_{i,y}=\frac{D_{i,y}^{all}-D_{i,y}^{S}}{D_{i,y}^{all}}.
```

The produced-asset construction is therefore

```math
K_{ia,y}=\widetilde K_{ia,y}\,q_{g(i)h(a),y}\,h_{i,y}.
```

This second share is industry-specific but common to all produced categories within an industry, including research and software. The SOI measure is the balance-sheet row labeled depreciable assets, not depreciable assets minus accumulated depreciation. It supplies a legal-form ratio; its book dollars are not substituted for BEA current-cost stock levels. When the all-corporation denominator is nonpositive, the implemented fallback is a share of one.

The adjustment assumes that C and S corporations within an industry have the same proportional mix of produced assets. It also uses the tangible depreciable-asset share as a proxy for the C-corporation share of IPP. These are measurement assumptions, not identities. They may be less accurate where legal forms differ substantially in intangible intensity. No partnership amounts are added after this conversion.

For illustration, 2022 manufacturing has $h_i=0.898472$. A \$100 billion all-legal-form equipment stock in that industry becomes approximately $100\times0.912659\times0.898472=81.999$ billion of C-corporation equipment. The same industry’s research stock instead uses the IPP corporate share before applying $h_i$.

## 5 SOI levels and suppressed cells

### 5.1 C corporation subtraction

For each industry and balance-sheet item j, the C-corporation level is

```math
X_{ij,y}^{C}=X_{ij,y}^{all}-\widehat X_{ij,y}^{S}.
```

Published numeric sector cells are summed directly. A nonnumeric cell is recorded as suppressed, rather than converted into a genuine zero. The reader also retrieves total assets because their legal-form shares are used in the imputation. Land and inventory stocks are levels in a single year; consecutive balance sheets are not differenced.

### 5.2 Allocating the withheld residual

The S-corporation All Industries total identifies the amount not assigned to published sector cells. Let $P_{ij}$ denote the sum of the published parts of sector i for item j, let $T_j^S$ be the All Industries total, and let $H_j$ be the set of sectors containing a suppressed cell. The residual is

```math
R_j=T_j^S-\sum_i P_{ij}.
```

For sectors in $H_j$, the allocation weights are

```math
w_{ij}=\max\left\{0,\frac{A_i^S}{A_i^{all}}X_{ij}^{all}\right\}.
```

where $A_i$ denotes total assets. If the residual is positive and the weights sum to a positive amount, the estimate is

```math
\widehat X_{ij}^{S}=P_{ij}+R_j\frac{w_{ij}}{\sum_{k\in H_j}w_{kj}},\qquad i\in H_j.
```

Sectors without suppression retain their published amounts. If all allocation weights are zero, the residual is divided equally among affected sectors. If the residual is nonpositive or the All Industries total is unavailable, the code makes no residual allocation. Total assets are processed before other items; in the 2016 and 2022 inputs, total assets and depreciable assets do not require this imputation.

The imputed amount is added to any published part of a sector. Replacing that published part would discard information when SOI divides a sector across several columns. Weighting by the S-corporation total-asset share also avoids treating an almost entirely C-corporation industry as though it had the same S-corporation fraction as other industries. The national residual is identified by the table; its allocation among suppressed sectors remains an estimate.

**Table 5 Suppressed S corporation amounts in the two stock years**

| Year and item | Sectors affected | Withheld residual in billions | Allocation in billions |
| --- | --- | --- | --- |
| 2016 land | Utilities and management | 1.907 | 0.034 and 1.873 |
| 2016 inventories | Wholesale trade and finance | 139.518 | 139.456 and 0.062 |
| 2022 land | Utilities and real estate | 65.028 | 0.041 and 64.987 |
| 2022 inventories | Finance and management | 0.121 | 0.006 and 0.115 |

The 2022 land imputation is quantitatively important. Reading the suppressed S-corporation land cells as zero would increase the constructed C-corporation book-land total by about \$65 billion. The unscaled C-corporation land total after imputation is \$721.315 billion. The corresponding inventory total is \$2,264.619 billion. For 2016, these totals are \$545.880 billion and \$1,482.363 billion.

## 6 Land inventories and residential structures

### 6.1 Land valuation

SOI land largely reflects historical acquisition values. The analysis preserves the SOI distribution of C-corporation book land across industries while applying alternative common valuation multiples.

Let $L_{i,y}^{book}$ be C-corporation book land after S-corporation subtraction and suppressed-cell imputation. For current-value basis $b$, let $L_{2022}^{Z.1,b}$ be the Financial Accounts nonfinancial corporate land residual and $L_{2022}^{SOI,NF}$ be SOI all-corporation book land excluding Finance and Insurance, NAICS sector 52. The scaling factor and industry land stock are

```math
f_b=\frac{L_{2022}^{Z.1,b}}{L_{2022}^{SOI,NF}},\qquad K_{i,Land,y}^{b}=f_bL_{i,y}^{book}.
```

The book-value specification sets $f_b=1$. The current-value numerator and denominator both include C and S corporations. The multiple is then applied to C-corporation book land in every industry. The implied C-corporation total is therefore an allocated estimate rather than the observed Financial Accounts total. A change in the SOI inputs changes the measured denominator and the resulting multiple; the calculation does not target a previously fixed C-corporation control.

The main total-real-estate residual is calculated from 2022 year-end Financial Accounts observations. In billions of dollars, total real estate at market value is 16,281.440, nonresidential structures at current cost are 13,051.255, and residential structures at current cost are 334.272. Thus

```math
L_{2022}^{Z.1,total}=16{,}281.440-13{,}051.255-334.272=2{,}895.913.
```

The SOI denominator is $880.334826$ billion. The resulting multiple is approximately $3.289559$; applied to $721.315422$ billion of C-corporation book land, it gives an implied C-corporation total of approximately $2{,}372.809352$ billion.

The nonresidential sensitivity subtracts the same nonresidential structures series from nonresidential real estate at market value:

```math
L_{2022}^{Z.1,nonres}=14{,}871.049-13{,}051.255=1{,}819.794.
```

Using the same SOI denominator gives a multiple of approximately $2.067161$ and implied C-corporation land of approximately $1{,}491.075257$ billion.

**Table 6 Land valuations and scaling factors**

| Valuation basis | Implied C corporation land in 2022 billions | Factor applied in both years |
| --- | --- | --- |
| SOI book value | 721.315 | 1.000000 |
| Nonresidential real estate sensitivity | 1,491.075 | 2.067161 |
| Total real estate main specification | 2,372.809 | 3.289559 |

All four residual inputs come from the Financial Accounts nonfinancial corporate sector. Total real estate uses NCBREMV, nonresidential real estate BOGZ1FL105035033A, nonresidential structures RCSNNWMVBSNNCB, and residential structures RCVSRNWMVBSNNCB. The source files report millions of dollars and are divided by 1,000. Quarterly series require the exact fourth-quarter label, October 1, 2022; that label represents the end-of-period fourth-quarter level. The annual nonresidential-real-estate series uses its January 1, 2022 label for that year's year-end level. The reader rejects missing or duplicate expected dates, incorrect series headers, and invalid residuals or denominators. The source audit retains the selected observations, file hashes, and October 12, 2026 capture date; the CSV files do not embed a release vintage.

Excluding sector 52 approximates the Financial Accounts nonfinancial population. Financial holding companies in sector 55 and consolidation differences are not separately reconciled. Applying one multiple also assumes that the measured market-to-book relationship is applicable across legal forms and industries, including C-corporation finance. The nonresidential sensitivity excludes residential land from its numerator although the SOI denominator includes it. Total real estate is therefore the main basis.

The same 2022 factor is applied to both stock years. The 2016 estimate uses its own book-land distribution and amount multiplied by that factor; no separate 2016 market-value factor is estimated. Industry-specific land prices and differential appreciation are not observed. The default calculation is regenerated by `land_controls.py` from the archived files and SOI levels. BEA structure comparisons and the earlier 1,654 and 2,572 billion controls are retained as labeled diagnostics or historical comparisons and do not enter the default stock weights.

### 6.2 Inventories

Inventory is Table 5.1 less the completed Table 6.1 inventory row. It remains at reported balance-sheet value. No inventory valuation adjustment is made to convert historical-cost accounting to replacement cost, and the stock pipeline does not zero out industries merely because another, legacy flow specification classified their inventories as negligible. The price-level and FIFO/LIFO assumptions inside the CRS inventory tax calculation affect the rate, not the empirical inventory valuation.

### 6.3 Residential structures

The nonresidential detailed workbook does not supply the residential stock. The code reads the corporate row in BEA Table 5.1, assigns the entire amount to Real Estate and Rental and Leasing, and multiplies it by that industry’s SOI C-corporation depreciable-asset share. There is no additional Table 4.1 corporate-share adjustment because this source row is already corporate.

The 2022 corporate residential stock is \$341.4 billion; multiplying by the real-estate share of 0.853015 gives \$291.219 billion. For the 2016 matrix, the available 2017 corporate total of \$234.8 billion is multiplied by the 2016 real-estate share of 0.801533, giving \$188.200 billion. The source-year substitution and assignment to one industry are approximations that affect the historical composition comparison.

## 7 Tax depreciation and financing inputs

### 7.1 Main tax schedule

The main rate vector is the corporate post-OBBBA mixed-finance schedule transcribed from CRS R48631. The replication takes these published METRs as inputs; it does not solve the full CRS model asset by asset or apply separate industry tax rates. Corporate mixed finance uses a common debt share of 0.3226. Observed SOI leverage does not determine industry-specific financing weights.

Table 7 gives all inputs and the resulting user-cost wedges. The rates retain the published precision; values expressed as percentages in the table are stored as decimal fractions in the code.

**Table 7 Main asset parameters and user cost wedges**

| Category | METR percent | Depreciation percent | Wedge percent |
| --- | --- | --- | --- |
| Equipment | 3.3 | 12.60 | 1.049 |
| Purchased software | 1.8 | 51.00 | 0.181 |
| Research category | −47.2 | 17.45 | -7.782 |
| Inventories | 24.9 | 0 | 33.156 |
| Land | 22.4 | 0 | 28.866 |
| Manufacturing structures | 1.8 | 3.14 | 1.174 |
| Communications structures | 1.8 | 2.37 | 1.287 |
| Farm structures | 1.8 | 2.39 | 1.284 |
| Commercial and health care structures | 22.1 | 2.47 | 19.678 |
| Other nonresidential structures | 22.6 | 2.72 | 19.644 |
| Oil gas and mining structures | 12.2 | 4.50 | 7.700 |
| Power structures | 11.6 | 2.11 | 9.527 |
| Residential structures | 17.7 | 1.40 | 17.201 |

Equipment has a published aggregate METR; it is not assigned the exact-expensing rate of purchased software. The structures categories retain the distinctions in the published tax schedule. Assignment of a schedule to a BEA asset category abstracts from firm-level eligibility restrictions, foreign versus domestic research, heterogeneous credit use, losses, and other tax attributes.

### 7.2 Matching the saver return to financing

The saver return in the transformation must match the financing basis underlying the METR. The implemented investor returns are $s_D=0.04209269$ for debt and $s_E=0.062508481792$ for equity. With debt share $d=0.3226$,

```math
s_{mixed}=d s_D+(1-d)s_E=0.055922347360.
```

The historical comparison and equity bridge instead use $s=s_E$. The same equity saver return is used under both tax regimes because it is an investor-side required return. The pre-TCJA corporate statutory rate of 0.34 and post-OBBBA rate of 0.21 enter parameter-reconciliation calculations rather than an additional tax adjustment to the published METRs.

The firm discount rate is distinct from the saver return. The code uses nominal interest $i_n=0.0682$, inflation $\pi=0.02$, deductible-interest fraction $\lambda=0.9808$, and required real corporate equity return $E_C=0.0361+0.0317=0.0678$. For corporate rate t, it calculates

```math
r(d,t)=d\{i_n(1-\lambda t)-\pi\}+(1-d)E_C.
```

Under post-OBBBA mixed finance, $r=0.056945472122$; under equity finance, $r=0.0678$. These discount rates are used for the no-credit research sensitivity and reconciliation checks. The saver return s, rather than r, enters benchmark capital-service values and the METR-to-wedge transformation.

### 7.3 Economic depreciation and aggregation

Economic depreciation measures loss of productive value, not the statutory tax recovery period. The main specification retains common category depreciation inputs across industries: equipment 0.126, purchased software 0.510, and pooled ordinary nonresidential structures in the historical comparison 0.027. Purchased software pools prepackaged and custom software in the main specification; the historical specification separates them and uses rates 0.7083 and 0.3813.

The corresponding stock-weighted component rate is

```math
\bar\delta_{c,y}=\frac{\sum_i\sum_{a\in c}K_{ia,y}\delta_a}{\sum_i\sum_{a\in c}K_{ia,y}}.
```

The replication now calculates component-weighted diagnostics directly from the detailed BEA stocks, using the same corporate and C-corporation adjustments as the main stock construction. Detailed equipment is mapped to the CRS R48277 Table A-2 depreciation classes through the explicit concordance in `params.py`. Equipment components are used for this diagnostic and are not added to the EQ00 equipment total. The crosswalk, component stocks, and industry-specific equipment rates are exported with the results.

The computed equipment rates are 0.126608 in 2016 and 0.123644 in 2022. The purchased-software rates are 0.493057 and 0.511176; the pooled ordinary-structure rates are 0.026552 and 0.026584. These are diagnostic rates; they do not replace the fixed common rates used in the headline calculations. Nuclear fuel uses the CRS other-nonresidential-equipment rate and household appliances the other-electrical-equipment rate because the CRS table has no separate lines for those items. The proxy assignments are recorded in the exported concordance.

Using industry-specific equipment depreciation changes the baseline mean wedge by approximately +0.024 percentage point, between-industry standard deviation by -0.063 percentage point, and within-industry standard deviation by +0.054 percentage point. Varying the common equipment rate from 0.10 to 0.18 changes the mean from 5.83 to 5.06 percent, between-industry standard deviation from 5.47 to 4.78 percentage points, and within-industry standard deviation from 10.16 to 9.82 percentage points. The diagnostics document the component weighting and its quantitative effects while preserving the stated calibration.

The aggregation issue differs for means and variances. Multiplying an asset’s weight by its wedge gives

```math
B_{ia}z_a=(s+\delta_a)K_{ia}\frac{s}{s+\delta_a}\tau_a=sK_{ia}\tau_a.
```

If all detailed assets in a category share a common METR and the category uses their stock-weighted mean depreciation, grouping preserves its total capital-service value and dollar tax wedge exactly. Consequently, it preserves the economy-wide mean. A common depreciation rate across industries is an approximation to each industry’s detailed stock-weighted rate. When component METRs differ, a single published category rate need not preserve the dollar wedge exactly.

Grouping also omits dispersion among the components. Exact preservation of a mean therefore does not establish exact preservation of within-industry variance. The equipment diagnostic holds its mixed-finance METR at 3.3 percent and varies depreciation over the CRS range 0.0500–0.3333. The implied wedges range from about 0.490 to 1.801 percent. This isolates depreciation heterogeneity; it does not test heterogeneity in equipment tax treatment.

### 7.4 Land and inventory user costs

Both categories have $\delta=0$, so $z=m/(1-m)$ and $B_{ia}=sK_{ia}$. For inventory, the relevant annual cost is the opportunity cost of holding working capital. The inventory METR already incorporates the holding-period model and is annualized. The code therefore applies no additional holding-period multiplier to z or B.

As a check, $B_{i,Inv}z_{Inv}=(\rho_{Inv}-s)K_{i,Inv}$. CRS’s gross inventory sale-value factor, which includes recovery of principal, is not substituted for the annual rental-cost measure. A separate reconciliation calculation uses holding period 0.385 years, FIFO share 0.50, inflation, the firm discount rate, and the corporate statutory rate to recover an inventory METR close to the published rounded value.

## 8 Capital service weights and dispersion

For each specification, the unrounded matrix and the appropriate saver return determine

```math
B_{ia}=(s+\delta_a)K_{ia},\qquad B_i=\sum_a B_{ia},\qquad B=\sum_i B_i.
```

The within-industry and industry weights are

```math
\alpha_{ia}=\frac{B_{ia}}{B_i},\qquad \phi_i=\frac{B_i}{B}.
```

Every industry must have positive $B_i$. A zero asset stock receives zero weight. Assets with faster depreciation require greater annual service cost per dollar of net stock and accordingly receive more weight than they would under stock-dollar weighting. Land and inventory receive only the saver-return component. The capital-service weights are based on benchmark untaxed costs; taxed costs are not used to increase the weight of high-wedge assets.

An industry’s mean wedge and the aggregate mean are

```math
Z_i=\sum_a\alpha_{ia}z_a,\qquad \bar z=\sum_i\phi_i Z_i=\frac{\sum_{i,a}B_{ia}z_a}{B}.
```

The between-industry variance and aggregate within-industry variance are

```math
\mathcal V_B^z=\sum_i\phi_i(Z_i-\bar z)^2,
```

```math
\mathcal V_W^z=\sum_i\phi_i\sum_a\alpha_{ia}(z_a-Z_i)^2.
```

They satisfy the weighted variance identity $\mathcal V^z=\mathcal V_B^z+\mathcal V_W^z$. The reported within-industry standard deviation for industry i is the square root of its own conditional variance. The aggregate within-industry standard deviation is $\sqrt{\mathcal V_W^z}$, not the average of industry standard deviations. Land’s reported share is $\sum_i B_{i,Land}/B$, rather than land dollars divided by total stock dollars.

The mean is reported as a percentage and standard deviations in percentage points, each by multiplying its decimal value by 100. The variances remain in squared decimal units for the welfare calculation. A ratio of the two variances by itself does not give their relative welfare importance because they enter with different elasticities.

## 9 Excess burden and research credit sensitivity

### 9.1 Translating measured moments into welfare

The framework gives the local quadratic approximation

```math
\frac{EB}{B}\approx\frac12\left[\varepsilon\bar z^2+\eta\mathcal V_B^z+\sigma\mathcal V_W^z\right].
```

The benchmark is $(\varepsilon,\eta,\sigma)=(0.6,1,1)$. These are calibration parameters, not estimated from the stock matrix. The three terms correspond to aggregate capital demand, reallocation across industry capital aggregates, and substitution among assets within industries. Separate contributions are $EB_Q/B=\varepsilon\bar z^2/2$, $EB_B/B=\eta\mathcal V_B^z/2$, and $EB_W/B=\sigma\mathcal V_W^z/2$. Contribution shares divide each term by their sum.

With a positive aggregate-capital elasticity, the equivalent uniform positive wedge is

```math
z_{uniform}=\sqrt{\bar z^2+\frac{\eta}{\varepsilon}\mathcal V_B^z+\frac{\sigma}{\varepsilon}\mathcal V_W^z}.
```

Multiplying EB/B by B gives annual dollars within the model’s capital-service normalization. Under the main specification, B is about \$3.166 trillion, and benchmark excess burden is approximately \$23.25 billion annually. This is a model-based welfare calculation, not lost tax revenue or an empirical estimate of the realized change in output.

The paper’s elasticity sensitivity uses low values (0.3,0.5,0.5), high values (0.9,2,2), and high within-industry substitution (0.6,1,3). Only the elasticity multipliers change in these exercises. Observed shares approximate counterfactual undistorted shares within the local expansion; under its regularity conditions, the resulting welfare difference enters at third order. Large wedges, heterogeneous substitution possibilities, and corrective externalities limit the quantitative interpretation.

### 9.2 Removing the Section 41 credit

The sensitivity retains expensing and removes the research credit from the rate assigned to the research category. With expensing and no credit, the required pretax return equals the firm discount rate r, yielding

```math
m_{research}^{no\ credit}=\frac{r-s}{r}.
```

The calculated value is approximately 1.8 percent for mixed finance and 7.8 percent for equity finance. The implementation uses the unrounded expression rather than replacing the rate with its rounded published counterpart. It holds the stock matrix, depreciation schedule, saver return, and every other category’s METR fixed. Thus the service weights are unchanged, while the mean and variances respond to the changed research wedge.

In the main mixed-finance specification, the research wedge moves from approximately −7.78 percent to +0.44 percent. The resulting mean is 6.97 percent, between-industry standard deviation 4.24 percentage points, and within-industry standard deviation 9.07 percentage points. Benchmark excess burden is about 0.65 percent of annual capital-service costs. This sensitivity changes the rate on research and own-account software, as defined in Section 3, while leaving physical equipment unchanged. It does not identify an optimal research subsidy or estimate spillovers.

## 10 Historical comparison and specification bridge

### 10.1 Common historical categories

The historical matrix is constructed from the raw BEA series rather than by merging purchased software with equipment. Prepackaged and custom software are kept separate. Manufacturing, communications, farm, commercial and health care, and other ordinary nonresidential structures are pooled into one category. Oil gas and mining structures, power structures, and residential structures remain separate. The legal-form adjustments, land factors, inventory construction, and residential assignment otherwise follow the procedures above.

**Table 8 Historical equity finance parameters**

| Category | Pre TCJA METR percent | Post OBBBA METR percent | Depreciation percent |
| --- | --- | --- | --- |
| Equipment | 19.8 | 9.3 | 12.60 |
| Prepackaged software | 32.0 | 7.8 | 70.83 |
| Custom software | 23.6 | 7.8 | 38.13 |
| Research category | −35.8 | −30.3 | 17.45 |
| Inventories | 41.6 | 29.0 | 0 |
| Land | 39.2 | 27.1 | 0 |
| Ordinary nonresidential structures | 37.6 | 22.1 | 2.70 |
| Oil gas and mining structures | 24.0 | 17.1 | 4.50 |
| Power structures | 20.6 | 17.3 | 2.11 |
| Residential structures | 33.5 | 23.2 | 1.40 |

### 10.2 Four cell design

For each stock year $y\in\{2016,2022\}$ and law $l\in\{pre,post\}$, calculate wedges from that law’s schedule and then all moments from $K_y$. Within a stock year, the two laws have identical service weights because $s_E$ and the historical depreciation schedule are held fixed. Across stock years, the weights change with the constructed composition.

For any statistic $F(y,l)$, a law contrast holds stocks fixed and a composition contrast holds law fixed:

```math
\Delta_{law}(y)=F(y,post)-F(y,pre),
```

```math
\Delta_{composition}(l)=F(2022,l)-F(2016,l).
```

The diagonal change can be written as the law effect at 2016 stocks plus the composition effect under post-OBBBA law, or as the composition effect under pre-TCJA law plus the law effect at 2022 stocks. Differences between the two law contrasts reflect interaction with composition. The replication exports these mean-wedge contrasts in percentage points; the historical cell table also reports both standard deviations and benchmark EB/B.

This exercise is an accounting comparison of tax schedules at observed compositions. It does not identify a causal stock response to OBBBA, simulate an equilibrium reallocation, or measure the effect of OBBBA alone. The law contrast encompasses changes from the pre-TCJA regime to the post-OBBBA schedule. The 2022 stock year predates OBBBA.

### 10.3 Bridge to the main specification

The main and historical levels differ in financing and classification. A three-row bridge holds 2022 stocks and post-OBBBA law fixed. The first row uses thirteen categories and mixed finance. The second retains those categories and changes the entire rate vector and saver return to equity finance. This change also affects capital-service weights. The third uses ten categories on the same equity basis, showing the effect of pooling ordinary structures and separating purchased software.

Pooling the structures imposes a common METR on categories with different current-law treatment and industry distributions. Consequently, its small effect on the mean does not imply a small effect on between-industry variance. The bridge makes that difference visible.

## 11 Numerical replication benchmarks

Tables 9–11 report benchmarks produced from the uploaded inputs using the procedures above. They are checkpoints for construction, rather than additional fitted moments. Percentages and percentage points are rounded only for presentation.

**Table 9 Main mixed finance results by land valuation**

| Land valuation | Mean percent | Between SD pp | Within SD pp | Land service share percent |
| --- | --- | --- | --- | --- |
| SOI book value | 4.86 | 4.71 | 9.65 | 1.31 |
| Nonresidential real estate sensitivity | 5.19 | 4.94 | 9.86 | 2.68 |
| Total real estate main specification | 5.56 | 5.22 | 10.05 | 4.19 |

**Table 10 Historical four cell results**

| Stock year | Law | Mean percent | Between SD pp | Within SD pp | EB over B percent |
| --- | --- | --- | --- | --- | --- |
| 2016 | Pre TCJA | 19.49 | 8.52 | 20.46 | 3.60 |
| 2016 | Post OBBBA | 9.66 | 4.84 | 11.68 | 1.08 |
| 2022 | Pre TCJA | 19.52 | 8.82 | 20.80 | 3.70 |
| 2022 | Post OBBBA | 9.53 | 5.00 | 11.83 | 1.10 |

The mean-wedge law contrasts are -9.83 percentage points at 2016 stocks and -10.00 at 2022 stocks. Composition changes the mean by +0.03 percentage point under pre-TCJA law and -0.13 under post-OBBBA law. The diagonal change is -9.96 percentage points.

**Table 11 Post OBBBA bridge using 2022 stocks**

| Specification | Mean percent | Between SD pp | Within SD pp | EB over B percent |
| --- | --- | --- | --- | --- |
| Thirteen categories mixed finance | 5.56 | 5.22 | 10.05 | 0.73 |
| Thirteen categories equity finance | 9.53 | 6.26 | 12.13 | 1.20 |
| Ten categories equity finance | 9.53 | 5.00 | 11.83 | 1.10 |

## 12 Replication files and checks

Run `python reproduce.py` from the replication package. The default driver runs the baseline and no-Section-41 stock specifications and generates all retained paper outputs. The `--z` argument remains a compatibility alias for the same stock-only run. `params.py` contains schedules, constants, concordances, and filenames; `soi.py` reads and completes balance-sheet levels; `land_controls.py` calculates the land residuals and valuation multiples; `stocks.py` builds the matrices; `wedges.py` transforms rates; `distortion.py` calculates weights and moments; `paper_reporting.py` generates the retained tables, narrative scalars, source audits, and aggregation diagnostics; and `reproduce.py` coordinates the runs. Function names containing 12 are legacy names; the main matrix has thirteen columns. The eight-category compatibility objects are not the historical specification.

**Table 12 Stock based replication outputs**

| Output in the results directory | Contents |
| --- | --- |
| `table_A1_asset_wedges.csv` | METRs required-return wedges depreciation and user-cost wedges |
| `K_ia_2022_ccorp.csv` | Main stock matrix rounded to one decimal billion |
| `industry_wedges.csv` | Industry means service shares and within-industry SDs |
| `table_2_dispersion.csv` | Three land valuations and their moments |
| `table_3_law_x_stockyear.csv` | Four historical cells and benchmark excess burden |
| `table_3_decomposition.csv` | Mean-wedge law composition and diagonal contrasts |
| `table_B3_specification_bridge.csv` | Financing and category bridge |
| `aggregation_diagnostics.csv` | Equipment depreciation range and implied wedges |
| `aggregate_depreciation_checks.csv` | Component weighted equipment software and structure rates |
| `equipment_depreciation_crosswalk.csv` | CRS to BEA component mapping and proxy assignments |
| `equipment_depreciation_by_industry.csv` | Detailed equipment stocks and depreciation by industry |
| `equipment_depreciation_sensitivity.csv` | Effects of industry specific and alternative equipment rates |
| `land_control_inputs.csv` | Residuals book totals valuation factors and implied C corporation controls |
| `land_control_source_audit.csv` | Exact source observations dates units file hashes and coverage notes |
| `paper_report.md` and `paper_tables.tex` | All retained tables and readable results |
| `paper_values.csv` and `paper_values.tex` | Unrounded narrative values |
| `welfare_summary.csv` | Annual service costs excess burden components and uniform comparisons |
| Files with _ex_s41 suffix | Corresponding no-credit sensitivity outputs |

The first figure displays $Z_i$ and $\phi_i$; the composition figure displays $\alpha_{ia}$ and each industry’s conditional standard deviation. The output matrices and table records, rather than measurements read off the plotted figures, are the numerical basis for reported values.

The stock checks reconcile imputed S-corporation sector totals to their published All Industries totals, verify that constructed C-corporation land and inventory amounts lie between zero and the corresponding all-corporation amount, and confirm that each 2022 land valuation hits its aggregate control. The algebraic checks verify that industry and asset weights sum to one, the mean agrees with direct service weighting, total variance equals between plus within variance, and uniform wedges produce zero dispersion. Parameter checks recover the saver return from the published land rate, reconcile inventory rates with the holding-period calculation, and compare the no-credit research rate with other expensed assets. Published-rate rounding explains small reconciliation differences.

The supplied stock inputs reproduce the benchmarks in Section 11. Run `python tests/test_land_controls.py`, `python tests/test_all.py`, and `python tests/test_paper_reporting.py --check-outputs` for the land, stock, and reporting checks. The land checks require exact year-end observations, validate units and residual arithmetic, verify matched-population scaling, confirm that both stock years use the 2022 factor, and establish that changing legacy controls does not alter current stock construction. Reporting checks reconcile the generated tables and welfare identities. The default driver requires no flow workbooks. Numerical checks establish internal consistency; legal-form conversion, the common land-valuation multiple, and the component depreciation proxies remain stated measurement assumptions. Land controls and component depreciation diagnostics are regenerated from the archived source files.

## 13 Interpretation and measurement limits

The constructed stocks provide a common basis for measuring how a tax schedule interacts with capital composition. Legal-form conversion relies on broad BEA corporate shares and industry-level SOI depreciable-asset ratios. Those adjustments cannot recover legal-form differences in every detailed asset mix. The research category and structure assignments also require matching tax-model categories to statistical asset categories; the exact concordance is consequential and is reported above.

Land rescaling corrects an aggregate valuation discrepancy without observing the current-value distribution across industries. It preserves historical-cost industry shares, uses a common 2022 factor across stock years, and uses Financial Accounts real estate and structures from one source sector, with an approximate SOI population match and a common valuation multiple across legal forms and industries. Inventory remains at book value. Residential structures are assigned to one industry, with a 2017 total substituted in the 2016 matrix. These conventions are part of the composition comparison.

The METRs apply common marginal financing and tax assumptions within each schedule. They do not incorporate every firm’s losses, financing constraints, eligibility, credit use, or tax-planning opportunities. Economic-depreciation aggregation can preserve means under the conditions stated above while omitting finer dispersion. Observed stocks need not equal the allocation that would arise under the tax schedule being applied to them.

Finally, the moment estimates and the welfare calibration should be kept distinct. The average and variances do not require estimated elasticities. Excess burden and equivalent uniform wedges require behavioral assumptions, a local approximation, and a judgment about whether tax preferences correct externalities. The Section 41 sensitivity addresses one part of that judgment without estimating the external benefit of research.

## Source references

Congressional Research Service. Marginal Effective Tax Rates Changes in P L 119 21 the 2025 Reconciliation Act. Report R48631. Tables 2 and 3 provide the current-law rate schedules used in the replication.

Congressional Research Service. CRS Model Estimates of Marginal Effective Tax Rates on Investment Under Current Law. Report R48277. Tables A-1 and A-2 document financing parameters and economic depreciation inputs.

Congressional Research Service. Marginal Effective Tax Rates on Investment and the Expiring 2017 Tax Cuts. Report R48153. Table 4 supplies the pre-TCJA equity-finance rates.

Bureau of Economic Analysis. Detailed Fixed Assets Data. Current-cost net stocks of private nonresidential fixed assets. The workbook contains industry and asset metadata in readme and series in Datasets.

Bureau of Economic Analysis. Fixed Assets Accounts. Table 4.1, Current-Cost Net Stock of Private Nonresidential Fixed Assets by Industry Group and Legal Form of Organization; Table 5.1, Current-Cost Net Stock of Residential Fixed Assets by Type of Owner Legal Form of Organization and Tenure.

Internal Revenue Service Statistics of Income. Corporation Complete Report. Tax years 2016 and 2022. Tables 5.1 and 6.1 report all-corporation and S-corporation balance sheets by industry.

Board of Governors of the Federal Reserve System. Financial Accounts of the United States. Nonfinancial corporate real estate and structures series archived through FRED as NCBREMV, BOGZ1FL105035033A, RCSNNWMVBSNNCB, and RCVSRNWMVBSNNCB. The selected 2022 observations are used to derive the residuals and valuation multiples in Section 6 and Table 6.
