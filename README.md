# Team 05 project: tuition and graduate earnings

Public repository: https://github.com/ChenJiayi-DS/CISC7204-Team05-Tuition-Earnings

## Full submission and raw data

Download the complete submission ZIP from this repository’s **Releases** page and extract it to obtain all raw datasets and the original folder structure. Large raw data are distributed as a release asset rather than browser-uploaded CSVs. The repository also contains the analysis code, cleaned data, figures and results for browsing.

After extracting the full submission, run commands from the extracted project folder.


CISC7204 Data Science and Data Visualization, Class F Team 05.

## Folders

| Folder | Contents |
|---|---|
| `dataset/` | All raw data: College Scorecard files, BEA RPP, BLS CPI-U (`CPI_2011-2024(1).xlsx`) and the state boundary file. Never edited. |
| `notebook/Team05_Analysis.ipynb` | Full pipeline: cleaning, merging, Q1-Q4 analysis, figures and interpretation. |
| `data_clean/` | Cleaned and merged data created by the notebook (see below). |
| `results/` | Result tables (CSV) and `findings_summary.md`. |
| `figures/` | Static figures 1-8 and a diagnostic plot (PNG, 200 dpi). |
| `dashboard/app.py` | Plotly Dash dashboard. |

### Cleaned data (`data_clean/`)

| File | Rows | Description |
|---|---:|---|
| `institution_clean.csv` | 2,098 | Every PREDDEG = 3 institution in the 50 states and DC, with tuition, SAT, family income, earnings, RPP and sample flags (`in_q1_sample`, `in_main_sample`, `in_nested_sample`) |
| `field_clean.csv` | 22,614 | Bachelor's program earnings linked to institution tuition (main sample); `top8_field` marks the same eight common fields in both sectors; sector counts, common-field eligibility and combined-coverage ranks are included |
| `state_rpp.csv` | 51 | BEA all-items RPP, 2022, 2023 and their mean |
| `cpi_annual.csv` | 14 | CPI-U annual averages 2011-2024 |
| `sample_flow.csv`, `field_sample_flow.csv` | | Counts after each sample rule |
| `data_dictionary.csv`, `source_log.csv` | | Variable definitions and data sources |

## How to run

Needs Python 3.11 or newer (tested with 3.11 and 3.14; results are identical). Keep the folder structure as it is: every path is relative to this folder.

1. Install the packages once, from inside this folder:

   ```bash
   pip install -r requirements.txt
   ```

   With Anaconda, most of them are already installed; usually only `plotly` and `dash` are missing.

2. Optional: rebuild everything from the raw data (about 10 seconds). The cleaned data, results and figures are already included, so this step is only needed after changing the notebook.

   ```bash
   cd notebook
   jupyter nbconvert --to notebook --execute --inplace Team05_Analysis.ipynb
   ```

   or open `notebook/Team05_Analysis.ipynb` in Jupyter or VS Code and choose *Run All*.

3. If you used `cd notebook` above, run `cd ..` first. Start the dashboard from the project root:

   ```bash
   python dashboard/app.py
   ```

   then open http://127.0.0.1:8051 in a browser and stop it with Ctrl+C. The state maps load their base map from the Plotly CDN, so they need an internet connection. If port 8051 is busy, close the other dashboard first.

## Dashboard

- **Institutions (Q1-Q2):** filter by institution type, state and sample; shows counts, median earnings and a scatter plot. Lines appear only for groups with at least 10 institutions; empty selections show a message.
- **State prices (Q3):** published and RPP-adjusted state medians side by side on one colour scale; states with fewer than 5 institutions of the selected type are grey.
- **Fields of study (Q4):** 16 panels for eight common fields, plus a shared field selector for the two sectors. Require at least 30 reporting institutions in each sector, then rank by combined coverage (ties by CIP code). Lines use the pooled interaction models; grey bands describe same-field tuition overlap.
- **Model results:** coefficient plots for Q1 sensitivity checks, Q2-Q3 and Q4; one combined Q4 plot pairs public (beta) and private nonprofit (beta + phi) slopes within each common field, with 95% confidence intervals from eight pooled interaction models. A table reports within-field slope differences (phi) with unadjusted p-values.
- **Methods:** data construction and limitations.

## V2 audit changes

V2 is an independent copy of V1. The dashboard uses port 8051 so both versions can run at once. Map colours now span the displayed state-by-type medians, and DC is explicitly identified as absent from the supplied boundary file. Q4 uses eight common fields with adequate coverage in both sectors; invalid selections display a clear message, and overlap bands appear only when the tuition ranges overlap. Methods distinguish institution-level completion earnings from bachelor's field earnings. Source modification dates are not download dates; undocumented download dates and releases are marked unknown.

The raw datasets are preserved. Confirm actual source release versions and download dates from the original download records before final submission. A local file timestamp is not proof of either.

## Additional checks merged from Checked

The notebook now verifies merge cardinality, availability of both RPP years, sample alignment, conversions and model counts. It records the current environment in `results/reproducibility_check.json`. Run `python run_notebook.py` from the project folder to rebuild the notebook and outputs with that Python environment. Q2/Q3 static chart layout was adjusted.

The dashboard avoids fitting a line when tuition has only one distinct value and shows a message for unknown fields or a missing institution type. Default port is 8051; to change it, use `PORT=8052 python dashboard/app.py` on macOS or Linux. In PowerShell use `$env:PORT="8052"` followed by `python dashboard/app.py`.

The combined V2 was originally tested on macOS. The Q4 interaction-model revision has also been executed and dashboard-checked on Windows with Python 3.13. Internet access is required for the dashboard's Plotly map base layer; use the included static map for offline presentation. Source release and original download dates remain unknown pending original records.

## Q4 common fields and interaction models

Require at least 30 reporting institutions in each sector, rank eligible fields by the combined number of valid institution-program observations (descending, ties by CIP code), and select eight common fields. Graduate counts do not determine the ranking. `results/q4_top8_fields.csv` records one shared list with counts for both sectors.

For each field, fit `log_earn ~ log_tuition + private + log_tuition:private`, with HC1 covariance. Public slope is beta; private nonprofit slope is beta + phi. The private confidence interval includes the beta/phi covariance. Eight models yield 16 sector slopes, not 16 separate regressions. The interaction phi directly tests the within-field private-minus-public slope difference; its eight p-values are unadjusted and exploratory. Q4 does not add SAT, family income or RPP controls.

`results/q4_field_slopes.csv` contains the 16 derived slopes and intercepts; `q4_slope_differences.csv` contains eight interaction tests; `q4_model_coefficients.csv` contains all 32 fitted coefficients. The combined `model_coefficients.csv` also includes these eight Q4 models.

Figure 7 retains its 4 x 4 panel layout, with adjacent public/private panels for the same field. Figure 8 combines the former Figures 8a and 8b into `figures/fig8_q4_coefficients.png`: blue circles and orange diamonds pair both sector slopes within each common field, with aligned estimate and sample-size columns. Re-running the notebook rebuilds these figures, tables, report summary and embedded outputs.

## Coefficient chart styles

Q1 sensitivity checks use a compact white-background forest plot with light row gridlines and aligned numerical columns. Q2 uses a before/after dumbbell with both 95% confidence intervals and point-estimate percentage reductions. Q3 follows Model 1 to Model 2 to Model 3 on the same nested sample, with connecting lines and 95% confidence intervals. These connections indicate specification changes, not time or causal decomposition. Q4 uses one paired sector forest plot with wrapped labels and estimate/N columns. Blue always denotes public; orange denotes private nonprofit. The dashboard uses the same chart roles.

Q4 parameter notation follows the proposal: beta is the public tuition slope, gamma multiplies Private, and phi multiplies log(tuition) x Private; the private nonprofit slope is beta + phi. Delta is reserved for SAT, theta for family income and lambda for RPP in Q1-Q3. This notation update leaves all fitted specifications and numerical estimates unchanged.

Coefficient figures omit redundant introductory subtitles. Notebook Figures 2 and 8 show only point estimates and institution counts in their numeric columns; error bars retain the full 95% confidence intervals. The dashboard's Q1 and Q4 forest plots omit the right-hand numeric columns; exact estimates, interval bounds and institution counts remain available on hover. Notebook result tables and CSV exports retain the full numerical results.

Notebook figure titles use one shared style: 13 pt bold, top-left aligned at the same figure-relative position. Main labels and legends use about 11 pt, and ticks use 10.5 pt. Figures 2 and 8 use compact 10-inch canvases with 11 pt estimate/N labels and column headings. Figure 7 panel titles use 10 pt with wrapped field names. Footnotes use 9 pt and wrap within the canvas to avoid widening the exported image. The layout is informed by the original V21 notebook; the reference folder remains unchanged.

Dashboard typography uses 19 px chart titles, 15 px chart/legend/hover text, 14 px axis ticks, 16 px body and option text, and 15 px notes and control headings. The 16-panel field overview uses 13 px panel titles and 12 px ticks with more vertical space and wrapped field names. Q1/Q4 exact estimates, confidence bounds and N remain on hover.
