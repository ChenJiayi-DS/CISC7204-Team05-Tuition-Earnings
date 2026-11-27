# Findings summary (Team 05)

All numbers come from `notebook/Team05_Analysis.ipynb`. Slopes are log-log elasticities with 95% confidence intervals; institution-level standard errors are clustered by state, field-level ones are HC1. Every result is an association across institutions, not a causal effect.

## Samples

| Sample | Institutions | Public | Private nonprofit | Private for-profit |
|---|---:|---:|---:|---:|
| PREDDEG = 3, 50 states and DC | 2,098 | 578 | 1,225 | 295 |
| Seven-year earnings reported | 1,626 | 543 | 998 | 85 |
| All five years of in-state tuition (Q1 sample) | 1,542 | 520 | 953 | 69 |
| Main analysis, wider sample | 1,473 | 520 | 953 | - |
| Nested-model sample (Q2-Q3) | 1,230 | 473 | 757 | - |

Q4 uses 22,614 bachelor's program records from 1,406 institutions. 58 fields have at least 30 reporting institutions in each sector. Rank these common fields by combined reporting institutions (ties by CIP code) and select eight. Eight pooled interaction models yield 16 sector slopes. Graduate counts do not determine the ranking.

## Q1 Main relationship (wider sample)

- Public 0.261 [0.130, 0.391]; private nonprofit 0.366 [0.268, 0.465]. A 10% tuition difference goes with about 2.5% and 3.5% higher median earnings.
- Difference φ = 0.106 [-0.104, 0.315], p = 0.32: the slopes are not statistically different.
- Sensitivity checks (out-of-state tuition, nominal tuition, state fixed effects, nested sample, adding for-profit institutions) all keep both slopes positive.
- Level scale: $1,821 (public) and $839 (private nonprofit) more earnings per $1,000 tuition; public tuition is much lower, so $1,000 is a larger proportional change.
- For-profit (69 institutions): 0.148 [-0.114, 0.410], imprecise.
- Influence: the U.S. Merchant Marine Academy (public, tuition about $900) has Cook's distance 1.14; without it the public slope is 0.318 [0.260, 0.376]. It stays in the main analysis.
- Overlap: only 139 of 953 private nonprofit institutions fall in the public tuition range ($5,190 to $23,132).

## Q2 Student background (nested sample, 1,230 institutions)

| | Model 1 | Model 2 (+ SAT, family income) |
|---|---|---|
| Public | 0.326 [0.262, 0.390] | 0.215 [0.136, 0.294] |
| Private nonprofit | 0.416 [0.325, 0.506] | 0.238 [0.154, 0.322] |
| Difference φ | 0.090 (p = 0.15) | 0.023 (p = 0.67) |

- On the same sample, adding SAT and family income reduces the estimated slope by about 34% (public) and 43% (private nonprofit); this is not a causal decomposition.
- 100 SAT points go with about 6.7% higher earnings; family income is not significant in Model 2 (p = 0.25).
- R-squared rises from 0.369 to 0.478.

## Q3 Regional prices (nested sample)

| | Model 2 | Model 3 (+ log RPP) |
|---|---|---|
| Public | 0.215 [0.136, 0.294] | 0.153 [0.054, 0.252] |
| Private nonprofit | 0.238 [0.154, 0.322] | 0.166 [0.096, 0.237] |

- λ (log RPP) = 0.768 [0.615, 0.921]: the estimated cross-sectional association with state prices is less than proportional, so dividing by RPP adjusts slightly more than the estimated relationship.
- Maps: high-price states move down after adjustment (e.g. NJ, CA, MA); lower-price states move up (e.g. NE, IA, the Dakotas). 34 public state groups and 37 private nonprofit state/DC groups have at least five institutions; the supplied map displays 34 and 36 states respectively, since DC has no polygon.

## Q4 Field of study (8 common fields; 8 interaction models, 16 sector slopes)

For each field: log(earnings) = alpha + beta log(tuition) + gamma Private + phi log(tuition) x Private + error.
Public slope = beta; private nonprofit slope = beta + phi. Confidence intervals use HC1 covariance, including the beta/phi covariance for the private slope.

### Public

| Common rank | Field | Institutions | Tuition slope [95% CI] |
|---:|---|---:|---|
| 1 | Psychology, General | 452 | 0.214 [0.175, 0.253] |
| 2 | Business Administration, Management and Operations | 412 | 0.422 [0.357, 0.487] |
| 3 | Biology, General | 432 | 0.199 [0.160, 0.239] |
| 4 | Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing | 342 | 0.008 [-0.035, 0.051] |
| 5 | Accounting and Related Services | 334 | 0.375 [0.315, 0.436] |
| 6 | Teacher Education and Professional Development, Specific Levels and Methods | 326 | 0.062 [0.019, 0.105] |
| 7 | Communication and Media Studies | 321 | 0.259 [0.191, 0.327] |
| 8 | English Language and Literature, General | 340 | 0.164 [0.110, 0.217] |

### Private nonprofit

| Common rank | Field | Institutions | Tuition slope [95% CI] |
|---:|---|---:|---|
| 1 | Psychology, General | 553 | 0.312 [0.238, 0.387] |
| 2 | Business Administration, Management and Operations | 525 | 0.346 [0.241, 0.452] |
| 3 | Biology, General | 447 | 0.258 [0.193, 0.323] |
| 4 | Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing | 351 | 0.145 [0.089, 0.200] |
| 5 | Accounting and Related Services | 293 | 0.319 [0.179, 0.460] |
| 6 | Teacher Education and Professional Development, Specific Levels and Methods | 295 | 0.237 [0.158, 0.315] |
| 7 | Communication and Media Studies | 259 | 0.476 [0.311, 0.641] |
| 8 | English Language and Literature, General | 224 | 0.295 [0.160, 0.430] |

### Within-field slope differences (private nonprofit minus public)

| Field | Phi [95% CI] | Unadjusted p-value |
|---|---|---:|
| Psychology, General | 0.098 [0.014, 0.182] | 0.0217 |
| Business Administration, Management and Operations | -0.076 [-0.200, 0.048] | 0.2320 |
| Biology, General | 0.059 [-0.017, 0.135] | 0.1281 |
| Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing | 0.136 [0.066, 0.207] | 0.0001 |
| Accounting and Related Services | -0.056 [-0.209, 0.097] | 0.4742 |
| Teacher Education and Professional Development, Specific Levels and Methods | 0.175 [0.085, 0.264] | 0.0001 |
| Communication and Media Studies | 0.217 [0.038, 0.396] | 0.0174 |
| English Language and Literature, General | 0.132 [-0.014, 0.277] | 0.0765 |

- 15 of 16 sector slopes have confidence intervals above zero; public nursing is close to flat.
- The same fields and combined-coverage order are used in both sectors. Figure 7 has 16 panels; Figure 8 pairs the public and private nonprofit slopes within each field on one x-axis scale.
- Phi directly tests the within-field sector slope difference. The eight tests have unadjusted p-values and are exploratory; cross-field comparisons require separate tests.
- Grey bands describe same-field tuition overlap. Limited common support and observational data prevent a causal interpretation.

## Limits to state with the results

Observational institution-level associations; federally aided completers only; published rather than net tuition; SAT and family income are partial controls; institution state is a proxy for work location; limited tuition overlap between sectors; suppression removes many small programs.

## Notes on interpretation

- Q4 interaction terms directly test within-field sector slope differences, with exploratory unadjusted p-values across eight fields. Different significance levels alone do not establish a slope difference. Cross-field comparisons and multiple testing require separate consideration.
- Q1-Q3 institution-level earnings include federally aided completers of credentials other than bachelor's degrees; Q4 includes only bachelor's programs.
- Some branch campuses share the same published earnings value, so campus records are not always independent earnings measures.
