"""Team 05 Plotly Dash dashboard: tuition and seven-year earnings at U.S. four-year colleges.

Run from any folder after the notebook has produced ../data_clean and ../results:
    python dashboard/app.py
then open http://127.0.0.1:8051
"""
import json
import os
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parent.parent
CLEAN, RES = ROOT / "data_clean", ROOT / "results"

COLORS = {"Public": "#2a78d6", "Private nonprofit": "#eb6834", "Private for-profit": "#1baf7a"}
INK, INK2, GRID, NODATA = "#0b0b0b", "#52514e", "#e4e3df", "#c9c8c2"
SEQ_BLUE = [[0, "#cde2fb"], [0.25, "#86b6ef"], [0.5, "#3987e5"], [0.75, "#1c5cab"], [1, "#0d366b"]]
MIN_FIT = 10          # smaller selections show points only, without a fitted line
MIN_STATE = 5         # states with fewer institutions of a type are grey on the maps
SOURCE = "Source: U.S. Department of Education, College Scorecard; BEA Regional Price Parities; BLS CPI-U."

inst = pd.read_csv(CLEAN / "institution_clean.csv")
inst = inst[inst["in_q1_sample"]].copy()
field = pd.read_csv(CLEAN / "field_clean.csv", dtype={"cip4": str})
geo = json.loads((ROOT / "dataset" / "us-states.json").read_text(encoding="utf-8"))
q1_sens = pd.read_csv(RES / "q1_sensitivity.csv")
q2 = pd.read_csv(RES / "q2_slopes.csv")
q3 = pd.read_csv(RES / "q3_slopes.csv")
q4 = pd.read_csv(RES / "q4_field_slopes.csv", dtype={"cip4": str})
q4_differences = pd.read_csv(RES / "q4_slope_differences.csv", dtype={"cip4": str})
common_fields = pd.read_csv(RES / "q4_top8_fields.csv", dtype={"cip4": str}).sort_values("common_field_rank")

TYPES = list(COLORS)
MAIN_TYPES = TYPES[:2]
STATES = sorted(inst["STABBR"].unique())
FIELD_ORDER = common_fields["cip4"].tolist()
FIELD_OPTIONS = [{"label": f"{r.field_name} ({r.public} public, {r.private_nonprofit} private nonprofit)",
                  "value": r.cip4} for r in common_fields.itertuples()]


def money_ticks(values):
    return {"tickvals": values, "ticktext": [f"${v / 1000:,.0f}k" for v in values]}


X_TICKS = money_ticks([1000, 2000, 5000, 10000, 20000, 50000])
Y_TICKS = money_ticks([20000, 30000, 50000, 75000, 100000, 150000])


def base_layout(fig, title, height=460):
    fig.update_layout(
        title={"text": title, "x": 0.01, "xanchor": "left", "y": 0.98, "yanchor": "top", "font": {"size": 19, "color": INK}},
        height=height, margin={"l": 85, "r": 30, "t": 85, "b": 75}, plot_bgcolor="white", paper_bgcolor="white",
        font={"family": "Helvetica, Arial, sans-serif", "size": 15, "color": INK2},
        legend={"orientation": "h", "y": 1.02, "yanchor": "bottom", "x": 1, "xanchor": "right"},
        hoverlabel={"bgcolor": "white", "font": {"size": 15}},
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=INK2, tickfont={"size": 14}, title_font={"size": 15}, automargin=True)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=INK2, tickfont={"size": 14}, title_font={"size": 15}, automargin=True)
    return fig


def empty_figure(message):
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper", font={"size": 15, "color": INK2})
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return base_layout(fig, "", height=420)


def add_scatter_with_fit(fig, d, t, x, y, hover, row=None, col=None, name=None, fit=True):
    kwargs = {"row": row, "col": col} if row else {}
    fig.add_trace(go.Scatter(
        x=d[x], y=d[y], mode="markers", name=name or t, legendgroup=t,
        marker={"color": COLORS[t], "size": 7, "opacity": 0.45, "line": {"width": 0}},
        customdata=d[hover].values, hovertemplate=HOVER[hover[0]],
    ), **kwargs)
    if fit and len(d) >= MIN_FIT and d[x].nunique() >= 2:
        lx, ly = np.log(d[x]), np.log(d[y])
        slope, intercept = np.polyfit(lx, ly, 1)
        grid = np.linspace(lx.min(), lx.max(), 60)
        fig.add_trace(go.Scatter(
            x=np.exp(grid), y=np.exp(intercept + slope * grid), mode="lines", legendgroup=t, showlegend=False,
            line={"color": COLORS[t], "width": 2.5}, hovertemplate=f"{t}: simple log-log slope {slope:.3f}<extra></extra>",
        ), **kwargs)
        return slope
    return None


HOVER = {
    "INSTNM": "<b>%{customdata[0]}</b><br>%{customdata[1]} · %{customdata[2]}<br>"
              "Tuition (2024 $): %{x:$,.0f}<br>Median earnings: %{y:$,.0f}<extra></extra>",
}

# ---------------------------------------------------------------- layout
app = Dash(__name__, title="Team 05 Tuition and Earnings")


def card(label, value_id):
    return html.Div([html.Div(label, className="card-label"), html.Div(id=value_id, className="card-value")], className="card")


controls = html.Div([
    html.Div([html.Label("Institution type"),
              dcc.Checklist(id="types", options=TYPES, value=MAIN_TYPES, inline=True)], className="control"),
    html.Div([html.Label("State"),
              dcc.Dropdown(id="states", options=STATES, value=[], multi=True, placeholder="All 50 states and DC")], className="control wide"),
    html.Div([html.Label("Sample"),
              dcc.RadioItems(id="sample", inline=True, value="wide", options=[
                  {"label": "Wider sample (Q1)", "value": "wide"},
                  {"label": "Nested-model sample (Q2-Q3)", "value": "nested"}])], className="control"),
], className="controls")

overview_tab = html.Div([
    controls,
    html.Div(id="active-filters", className="filters-text"),
    html.Div([card("Institutions shown", "n-total"), card("Public", "n-public"),
              card("Private nonprofit", "n-nonprofit"), card("Private for-profit", "n-forprofit"),
              card("Median earnings", "median-earn")], className="cards"),
    dcc.Graph(id="scatter", config={"displaylogo": False}),
    html.P(f"Lines are simple log-log fits for the current selection and appear only for groups with at least {MIN_FIT} institutions and at least two distinct tuition values. "
           "Q1-Q3 earnings include federally aided completers and are not restricted to bachelor's completers. "
           "Model estimates with clustered standard errors are on the Model results tab. " + SOURCE, className="note"),
])

maps_tab = html.Div([
    html.Div([html.Label("Institution type"),
              dcc.RadioItems(id="map-type", options=MAIN_TYPES, value="Public", inline=True)], className="control"),
    dcc.Graph(id="maps", config={"displaylogo": False}),
    html.P(f"Nested-model sample. Each state shows the median across its institutions; states with fewer than {MIN_STATE} "
           "institutions of the selected type are grey. Both maps share one colour scale. Graduates may work outside the "
           "institution's state, so RPP adjustment is approximate. DC is included in the analysis but is not drawn by the supplied boundary file. " + SOURCE, className="note"),
])

fields_tab = html.Div([
    html.P("Eight common fields: at least 30 reporting institutions in each sector, ranked by combined coverage "
           "(ties by CIP code). Adjacent public/private panels show the same field. "
           "Eight pooled interaction models yield 16 sector slopes.", className="note"),
    dcc.Graph(id="field-panels", config={"displaylogo": False}),
    html.Div([html.Label("Explore one of the eight common fields"),
              dcc.Dropdown(id="field", options=FIELD_OPTIONS, value=FIELD_ORDER[0], clearable=False)],
             className="control wide"),
    html.Div(id="field-counts", className="filters-text"),
    dcc.Graph(id="field-scatter", config={"displaylogo": False}),
    html.P("Lines come from one pooled model per field: log(earnings) = alpha + beta log(tuition) + gamma Private "
           "+ phi log(tuition) x Private. Public slope = beta; private nonprofit slope = beta + phi. "
           "Lines cover each sector's observed tuition range; grey bands show same-field tuition overlap. "
           "Program tuition is approximated by institution tuition. " + SOURCE, className="note"),
])

q4_difference_table = html.Div([
    html.H3("Q4: within-field slope differences (private nonprofit minus public)"),
    html.Table([
        html.Thead(html.Tr([html.Th(label) for label in ("Field", "Phi [95% CI], HC1", "Unadjusted p-value")])),
        html.Tbody([html.Tr([
            html.Td(r.field_name.split(",")[0]),
            html.Td(f"{r.estimate:.3f} [{r.ci_low:.3f}, {r.ci_high:.3f}]"),
            html.Td(f"{r.p_value:.4f}"),
        ]) for r in q4_differences.sort_values("common_field_rank").itertuples()]),
    ], className="result-table"),
    html.P("Phi is the log(tuition) x Private interaction. These eight within-field tests are exploratory; "
           "p-values are unadjusted for multiple testing. Cross-field differences require separate tests.", className="note"),
], className="methods")

results_tab = html.Div([
    dcc.Graph(id="coef-q1", config={"displaylogo": False}),
    dcc.Graph(id="coef-q2", config={"displaylogo": False}),
    dcc.Graph(id="coef-q3", config={"displaylogo": False}),
    html.P("Q2 connectors show coefficient changes after adding SAT and family income; the percentage reduction refers to point estimates. "
           "Q3 connects Model 1, Model 2 and Model 3 on the same sample. These are specification changes, not time trends or causal decompositions. "
           "All error bars show 95% confidence intervals, with standard errors clustered by state for Q1-Q3.", className="note"),
    dcc.Graph(id="coef-q4", config={"displaylogo": False}),
    q4_difference_table,
    html.P("Q1-Q3 use institution-level earnings for eligible completers, including credentials other than bachelor's. "
           "Q4 uses bachelor's field earnings. N appears on hover. Public and private nonprofit slopes come from "
           "the same interaction model within each field; their difference is tested in the table. " + SOURCE, className="note"),
])

methods_tab = html.Div([
    html.H3("How the data were built"),
    html.Ul([
        html.Li("Institutions: predominantly bachelor's (PREDDEG = 3) in the 2012-13 Scorecard file, located in the 50 states or DC, "
                "with seven-year earnings in the 2022-23 file and all five years of in-state tuition."),
        html.Li("Earnings: MD_EARN_WNE_7YR, median earnings of federally aided completers working and not enrolled, pooled "
                "award-year 2014-15 and 2015-16 cohorts, measured in 2022 and 2023, in 2024 dollars."),
        html.Li("Tuition: published in-state tuition for 2011-12 to 2015-16, converted to 2024 dollars with CPI-U and weighted "
                "1:2:2:2:1 to cover the two cohorts' assumed four-year study periods. It is the published price, not the net price."),
        html.Li("Background (Q2): average SAT for Fall 2011 and Fall 2012; median family income (2011-12 and 2012-13 entry cohorts) in 2024 dollars."),
        html.Li("Prices (Q3): mean of 2022 and 2023 all-items BEA Regional Price Parities for the institution's state."),
        html.Li("Institution earnings (Q1-Q3) include eligible completers at institutions predominantly awarding bachelor's degrees; they are not restricted to bachelor's completers. Fields (Q4) are restricted to bachelor's programs (CREDLEV = 3)."),
        html.Li("Q4 requires at least 30 reporting institutions in each sector, then selects eight common fields by combined coverage (ties by CIP code). Graduate counts are not used for ranking."),
        html.Li("Each Q4 field uses log(earnings) = alpha + beta log(tuition) + gamma Private + phi log(tuition) x Private, with HC1 covariance. Public slope is beta; private nonprofit slope is beta + phi. The private slope's confidence interval includes the beta/phi covariance. Eight models yield 16 sector slopes; Q4 does not add SAT, family income or RPP controls."),
    ]),
    html.H3("Reading the results"),
    html.P("All results describe associations across institutions. They do not show that paying more tuition causes higher "
           "earnings for any student, and they cover only completers who received federal aid."),
    html.P(SOURCE, className="note"),
], className="methods")

app.layout = html.Div([
    html.Header([
        html.H1("Is higher college tuition associated with higher graduate earnings?"),
        html.P("U.S. four-year colleges · CISC7204 Class F Team 05"),
    ]),
    html.P("Hover over data points or map regions to see detailed values.",
           id="hover-guide", className="hover-guide"),
    dcc.Tabs(value="overview", children=[
        dcc.Tab(label="Institutions (Q1-Q2)", value="overview", children=overview_tab),
        dcc.Tab(label="State prices (Q3)", value="maps", children=maps_tab),
        dcc.Tab(label="Fields of study (Q4)", value="fields", children=fields_tab),
        dcc.Tab(label="Model results", value="results", children=results_tab),
        dcc.Tab(label="Methods", value="methods", children=methods_tab),
    ]),
], className="page")


# ---------------------------------------------------------------- callbacks
@app.callback(
    Output("scatter", "figure"), Output("active-filters", "children"), Output("n-total", "children"),
    Output("n-public", "children"), Output("n-nonprofit", "children"), Output("n-forprofit", "children"),
    Output("median-earn", "children"),
    Input("types", "value"), Input("states", "value"), Input("sample", "value"),
)
def update_overview(types, states, sample):
    d = inst[inst["inst_type"].isin(types or [])]
    if sample == "nested":
        d = d[d["in_nested_sample"]]
    if states:
        d = d[d["STABBR"].isin(states)]
    counts = d["inst_type"].value_counts()
    sample_label = "nested-model sample" if sample == "nested" else "wider sample"
    if sample == "nested" and "Private for-profit" in (types or []):
        sample_label += " (for-profit institutions are not in this sample)"
    filters = f"Showing: {', '.join(types) if types else 'no institution type'} · {', '.join(states) if states else 'all states'} · {sample_label}"
    stats = [f"{len(d):,}"] + [f"{int(counts.get(t, 0)):,}" for t in TYPES]
    stats.append(f"${d['earn_7yr'].median():,.0f}" if len(d) else "-")
    if d.empty:
        return (empty_figure("No institutions match this selection. Add an institution type or clear the state filter."),
                filters, *stats)
    fig = go.Figure()
    for t in TYPES:
        sub = d[d["inst_type"] == t]
        if len(sub):
            add_scatter_with_fit(fig, sub, t, "tuition_in_real", "earn_7yr", ["INSTNM", "STABBR", "inst_type"],
                                 name=f"{t} (n = {len(sub)})")
    fig.update_xaxes(type="log", title="Weighted in-state tuition, 2011-12 to 2015-16 (2024 $, log scale)", **X_TICKS)
    fig.update_yaxes(type="log", title="Median earnings 7 years after completion (2024 $, log scale)", **Y_TICKS)
    return base_layout(fig, "Tuition and seven-year earnings by institution", height=520), filters, *stats


@app.callback(Output("maps", "figure"), Input("map-type", "value"))
def update_maps(t):
    d = inst[inst["in_nested_sample"] & (inst["inst_type"] == t)]
    stats = (d.groupby("STABBR").agg(n=("UNITID", "size"), published=("earn_7yr", "median"),
                                     adjusted=("earn_rpp_adjusted", "median"), rpp=("rpp_avg", "first")).reset_index())
    shown, grey = stats[stats["n"] >= MIN_STATE], stats[stats["n"] < MIN_STATE]
    missing = sorted(set(f["id"] for f in geo["features"]) - set(stats["STABBR"]))
    # Use the displayed sector-specific state medians, with one fixed scale across both types and maps.
    all_stats = (inst[inst["in_nested_sample"]].groupby(["STABBR", "inst_type"])
                 .agg(n=("UNITID", "size"), published=("earn_7yr", "median"), adjusted=("earn_rpp_adjusted", "median")))
    mapped_ids = {feature["id"] for feature in geo["features"]}
    eligible = all_stats[(all_stats["n"] >= MIN_STATE) & all_stats.index.get_level_values("STABBR").isin(mapped_ids)]
    zmin = eligible[["published", "adjusted"]].min().min()
    zmax = eligible[["published", "adjusted"]].max().max()
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "choropleth"}] * 2],
                        subplot_titles=("Published earnings", "Earnings x 100 / state RPP"), horizontal_spacing=0.02)
    for c, col in enumerate(("published", "adjusted"), start=1):
        fig.add_trace(go.Choropleth(
            geojson=geo, featureidkey="id", locations=shown["STABBR"], z=shown[col], zmin=zmin, zmax=zmax,
            colorscale=SEQ_BLUE, marker_line_color="white", marker_line_width=0.6,
            showscale=c == 2, colorbar={"title": "2024 $", "tickprefix": "$", "len": 0.8},
            customdata=shown[["n", "rpp", "published", "adjusted"]].values,
            hovertemplate="<b>%{location}</b><br>Institutions: %{customdata[0]}<br>RPP: %{customdata[1]:.1f}"
                          "<br>Published median: %{customdata[2]:$,.0f}<br>RPP-adjusted median: %{customdata[3]:$,.0f}<extra></extra>",
        ), row=1, col=c)
        low = pd.concat([grey[["STABBR", "n"]], pd.DataFrame({"STABBR": missing, "n": 0})])
        fig.add_trace(go.Choropleth(
            geojson=geo, featureidkey="id", locations=low["STABBR"], z=np.zeros(len(low)),
            colorscale=[[0, NODATA], [1, NODATA]], showscale=False, marker_line_color="white", marker_line_width=0.6,
            customdata=low[["n"]].values,
            hovertemplate=f"<b>%{{location}}</b><br>%{{customdata[0]}} institutions: fewer than {MIN_STATE}, not compared<extra></extra>",
        ), row=1, col=c)
    fig.update_geos(scope="usa", visible=False)
    mapped = int(shown["STABBR"].isin(mapped_ids).sum())
    title = f"{t}: {mapped} mapped states with at least {MIN_STATE} institutions"
    return base_layout(fig, title, height=480)


def field_overlap(cip):
    same_field = field[field["cip4"] == cip]
    ranges = [same_field.loc[same_field["inst_type"] == t, "tuition_in_real"] for t in MAIN_TYPES]
    if any(d.empty for d in ranges):
        return None
    lo, hi = max(d.min() for d in ranges), min(d.max() for d in ranges)
    return (lo, hi) if lo <= hi else None


def add_field_panel(fig, cip, t, row, col):
    d = field[(field["cip4"] == cip) & (field["inst_type"] == t)].assign(type_label=t)
    add_scatter_with_fit(fig, d, t, "tuition_in_real", "earn_7yr_field",
                         ["INSTNM", "STABBR", "type_label"], row=row, col=col, fit=False)
    r = q4[(q4["cip4"] == cip) & (q4["type"] == t)].iloc[0]
    grid = np.linspace(np.log(r["tuition_min"]), np.log(r["tuition_max"]), 60)
    slope_label = "beta" if t == "Public" else "beta + phi"
    fig.add_trace(go.Scatter(
        x=np.exp(grid), y=np.exp(r["intercept"] + r["estimate"] * grid), mode="lines",
        name=t, legendgroup=t, showlegend=False, line={"color": COLORS[t], "width": 2.5},
        hovertemplate=f"{t}: pooled-model slope ({slope_label}) {r['estimate']:.3f}<extra></extra>",
    ), row=row, col=col)
    overlap = field_overlap(cip)
    if overlap is not None:
        fig.add_vrect(x0=overlap[0], x1=overlap[1], fillcolor=GRID, opacity=0.6,
                      line_width=0, layer="below", row=row, col=col)


@app.callback(Output("field-panels", "figure"), Input("field-panels", "id"))
def update_field_panels(_):
    panels = [(t, r) for r in common_fields.itertuples() for t in MAIN_TYPES]
    titles = [textwrap.fill(r.field_name.split(",")[0], 27).replace("\n", "<br>") + f"<br>{t}, n = {r.public if t == 'Public' else r.private_nonprofit}"
              for t, r in panels]
    fig = make_subplots(rows=4, cols=4, shared_xaxes="all", shared_yaxes="all",
                        subplot_titles=titles, horizontal_spacing=0.045, vertical_spacing=0.11)
    for i, (t, r) in enumerate(panels):
        add_field_panel(fig, r.cip4, t, i // 4 + 1, i % 4 + 1)
    fig.update_xaxes(type="log", **money_ticks([5000, 10000, 20000, 50000]))
    fig.update_yaxes(type="log", **Y_TICKS)
    for col in range(1, 5):
        fig.update_xaxes(title="Tuition (2024 $, log)", row=4, col=col)
    for row in range(1, 5):
        fig.update_yaxes(title="Field earnings (2024 $, log)", row=row, col=1)
    fig = base_layout(fig, "Q4: eight common fields, eight pooled interaction models", height=1440)
    fig.update_annotations(font_size=13)
    fig.update_xaxes(tickfont={"size": 12}, title_font={"size": 13})
    fig.update_yaxes(tickfont={"size": 12}, title_font={"size": 13})
    fig.update_layout(showlegend=False, margin={"l": 75, "r": 20, "t": 135, "b": 80})
    return fig


@app.callback(Output("field-scatter", "figure"), Output("field-counts", "children"),
              Input("field", "value"))
def update_field(cip):
    if cip not in FIELD_ORDER:
        return empty_figure("Select one of the eight common fields."), "No matching selection."
    selections = [(t, cip) for t in MAIN_TYPES]
    titles, counts = [], []
    for t, cip in selections:
        r = q4[(q4["type"] == t) & (q4["cip4"] == cip)].iloc[0]
        titles.append(f"{t} (n = {r.n})<br>" + textwrap.fill(r.field_name.split(",")[0], 40).replace("\n", "<br>"))
        counts.append(f"{t}: {r.field_name}, {r.n} reporting institutions")
    difference = q4_differences[q4_differences["cip4"] == cip].iloc[0]
    counts.append(f"Slope difference (private - public): {difference.estimate:.3f} "
                  f"[{difference.ci_low:.3f}, {difference.ci_high:.3f}], p = {difference.p_value:.4f} (unadjusted)")
    fig = make_subplots(rows=1, cols=2, shared_xaxes=True, shared_yaxes=True,
                        subplot_titles=titles, horizontal_spacing=0.08)
    for col, (t, cip) in enumerate(selections, start=1):
        add_field_panel(fig, cip, t, 1, col)
    fig.update_xaxes(type="log", title="Institution in-state tuition (2024 $, log)", **X_TICKS)
    fig.update_xaxes(matches="x")
    fig.update_yaxes(type="log", **Y_TICKS)
    fig.update_yaxes(title="Field median earnings, 7 years<br>(2024 $, log)", row=1, col=1)
    fig = base_layout(fig, "Common field: tuition and seven-year earnings, pooled interaction model", height=480)
    fig.update_annotations(font_size=15)
    fig.update_layout(margin={"l": 95, "r": 35, "t": 125, "b": 85})
    fig.update_layout(showlegend=False)
    return fig, " · ".join(counts)


def dot_plot(rows, label_col, title, x_title, height, types=MAIN_TYPES, x_range=None):
    fig = go.Figure()
    rows = rows[rows["type"].isin(types)]
    labels = list(dict.fromkeys(rows[label_col]))
    for yi in range(0, len(labels), 2):
        fig.add_hrect(y0=yi-0.48, y1=yi+0.48, fillcolor="#f4f6f8", line_width=0, layer="below")
    for i, t in enumerate(types):
        d = rows[rows["type"] == t].set_index(label_col).loc[labels].reset_index()
        positions = np.arange(len(labels)) + ((i - 0.5) * 0.3 if len(types) > 1 else 0)
        fig.add_trace(go.Scatter(
            x=d["estimate"], y=positions, mode="markers", name=t,
            marker={"color": COLORS[t], "size": 10},
            error_x={"type": "data", "symmetric": False, "array": d["ci_high"] - d["estimate"],
                     "arrayminus": d["estimate"] - d["ci_low"], "color": COLORS[t], "thickness": 2, "width": 0},
            customdata=d[["ci_low", "ci_high", "n"]].values,
            text=labels,
            hovertemplate="%{text}<br>" + t + ": %{x:.3f} [%{customdata[0]:.3f}, %{customdata[1]:.3f}], n = %{customdata[2]}<extra></extra>",
        ))
    fig.add_vline(x=0, line_dash="dash", line_color=INK2, line_width=1)
    fig.update_yaxes(range=[len(labels)-0.5, -0.5], tickvals=list(range(len(labels))),
                     ticktext=[textwrap.fill(label, 31).replace("\n", "<br>") for label in labels],
                     automargin=True, showgrid=False, showline=False, ticks="")
    fig.update_xaxes(title=x_title, range=x_range)
    fig = base_layout(fig, title, height=height)
    fig.update_xaxes(showline=False, gridcolor="#e6ebf0", ticks="")
    fig.update_yaxes(showline=False)
    fig.update_layout(margin={"l": 340, "r": 35, "t": 110, "b": 80},
                      legend={"orientation": "h", "x": 0, "xanchor": "left", "y": 1.02})
    return fig


def q2_dumbbell():
    fig = go.Figure()
    counts = []
    for i, t in enumerate(MAIN_TYPES):
        rows = q2[q2["type"] == t].set_index("model").loc[["Model 1", "Model 2"]]
        before, after = rows["estimate"]
        counts.append(int(rows["n"].iloc[0]))
        fig.add_trace(go.Scatter(x=[before, after], y=[i, i], mode="lines", showlegend=False,
                                 line={"color": COLORS[t], "width": 7}, opacity=0.25, hoverinfo="skip"))
        for stage, (model, r) in enumerate(rows.iterrows()):
            fig.add_trace(go.Scatter(
                x=[r["estimate"]], y=[i + (stage-0.5)*0.16], mode="markers", name=f"{t}: {model}", showlegend=False,
                marker={"color": COLORS[t], "size": 12, "symbol": "circle-open" if stage == 0 else "circle",
                        "line": {"color": COLORS[t], "width": 2}},
                error_x={"type": "data", "symmetric": False, "array": [r["ci_high"]-r["estimate"]],
                         "arrayminus": [r["estimate"]-r["ci_low"]], "color": COLORS[t], "thickness": 1.5, "width": 4},
                customdata=[[r["ci_low"], r["ci_high"], r["n"]]],
                hovertemplate=f"{t} / {model}<br>" + "%{x:.3f} [%{customdata[0]:.3f}, %{customdata[1]:.3f}]<br>n = %{customdata[2]}<extra></extra>",
            ))
        fig.add_annotation(x=1.035, y=i, xref="paper", yref="y", xanchor="left", showarrow=False,
                           text=f"<b>{(1-after/before)*100:.1f}% lower</b><br>{before:.3f} to {after:.3f}",
                           font={"size": 16, "color": COLORS[t]})
    fig.add_vline(x=0, line_dash="dash", line_color="#87939f", line_width=1)
    fig.update_yaxes(range=[1.5, -0.5], tickvals=[0, 1],
                     ticktext=[f"{t}<br>n = {n:,}" for t, n in zip(MAIN_TYPES, counts)], showgrid=False)
    fig.update_xaxes(range=[-0.02, 0.55], title="Tuition slope (log-log elasticity)")
    fig = base_layout(fig, "Q2: tuition slopes before and after background controls", height=420)
    for stage, label in enumerate(["Model 1", "Model 2 (+ SAT and family income)"]):
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=label, showlegend=True,
                                 marker={"color": INK2, "size": 10,
                                         "symbol": "circle-open" if stage == 0 else "circle"}, hoverinfo="skip"))
    fig.update_layout(legend={"orientation": "h", "x": 0, "xanchor": "left", "y": 1.02})
    fig.update_layout(margin={"l": 175, "r": 190, "t": 135, "b": 80})
    fig.update_xaxes(showline=False, gridcolor="#e6ebf0")
    fig.update_yaxes(showline=False)
    return fig


def q3_trajectory():
    rows = pd.concat([q2, q3[q3["model"] == "Model 3"]], ignore_index=True)
    fig = go.Figure()
    for i, t in enumerate(MAIN_TYPES):
        d = rows[rows["type"] == t].set_index("model").loc[["Model 1", "Model 2", "Model 3"]]
        fig.add_trace(go.Scatter(
            x=np.arange(3)+(i-0.5)*0.07, y=d["estimate"], mode="lines+markers+text", name=t,
            line={"color": COLORS[t], "width": 3}, marker={"color": COLORS[t], "size": 10},
            text=[f"{v:.3f}" for v in d["estimate"]], textposition="bottom left" if i == 0 else "top right",
            textfont={"size": 15, "color": COLORS[t]}, cliponaxis=False,
            error_y={"type": "data", "symmetric": False, "array": d["ci_high"]-d["estimate"],
                     "arrayminus": d["estimate"]-d["ci_low"], "color": COLORS[t], "thickness": 1.3, "width": 4},
            customdata=d[["ci_low", "ci_high", "n"]].values,
            hovertemplate=t + ": %{y:.3f} [%{customdata[0]:.3f}, %{customdata[1]:.3f}]<br>n = %{customdata[2]}<extra></extra>",
        ))
    fig.update_xaxes(range=[-0.35, 2.4], tickvals=[0, 1, 2],
                     ticktext=["Model 1<br>Tuition + school type", "Model 2<br>+ SAT + family income", "Model 3<br>+ State prices (RPP)"],
                     showgrid=False)
    fig.update_yaxes(range=[0, 0.56], title="Tuition slope (log-log elasticity)")
    fig = base_layout(fig, "Q3: coefficient progression across models (same 1,230 institutions)", height=490)
    fig.update_layout(margin={"l": 100, "r": 65, "t": 110, "b": 100},
                      legend={"orientation": "h", "x": 0, "xanchor": "left", "y": 1.02})
    fig.update_xaxes(showline=False)
    fig.update_yaxes(showline=False, gridcolor="#e6ebf0")
    return fig


@app.callback(Output("coef-q1", "figure"), Output("coef-q2", "figure"), Output("coef-q3", "figure"),
              Output("coef-q4", "figure"), Input("coef-q1", "id"))
def update_results(_):
    s = q1_sens[(q1_sens["scale"] == "log-log elasticity") & q1_sens["type"].isin(MAIN_TYPES)]
    s = s.assign(model=s["model"].str.replace(" (same institutions)", "", regex=False)
                 .str.replace("Main: in-state tuition, 2024 dollars", "Main: in-state tuition", regex=False))
    f1 = dot_plot(s, "model", "Q1: tuition slopes across sensitivity checks", "Tuition slope (log-log elasticity), 95% CI", 540)
    f2, f3 = q2_dumbbell(), q3_trajectory()
    # The same eight pooled models yield public beta and private beta + phi slopes.
    x_range = [min(q4["ci_low"].min(), 0) - 0.05, q4["ci_high"].max() + 0.05]
    rows4 = q4.sort_values("common_field_rank", kind="stable")
    rows4 = rows4.assign(label=rows4["field_name"].str.split(",").str[0])
    f4 = dot_plot(rows4, "label", "Q4: public and private nonprofit slopes within eight common fields",
                  "Tuition slope (log-log elasticity), 95% CI, HC1", 700, x_range=x_range)
    for trace, t in zip(f4.data, MAIN_TYPES):
        trace.name = "Public (beta)" if t == "Public" else "Private nonprofit (beta + phi)"
        trace.marker.symbol = "circle" if t == "Public" else "diamond"
    f4.update_layout(legend={"orientation": "h", "x": 0, "xanchor": "left", "y": 1.02, "yanchor": "bottom"})
    return f1, f2, f3, f4


app.index_string = """<!DOCTYPE html>
<html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}
<style>
  body { margin: 0; background: #f6f6f4; font-family: Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.5; color: #0b0b0b; }
  .page { max-width: 1180px; margin: 0 auto; padding: 16px 20px 40px; }
  header h1 { font-size: 22px; margin: 8px 0 2px; }
  header p { margin: 0 0 14px; color: #52514e; }
  .hover-guide { margin: 0 0 12px; color: #52514e; font-size: 15px; }
  .controls { display: flex; flex-wrap: wrap; gap: 18px; margin: 14px 0 6px; align-items: flex-end; }
  .control { margin: 12px 0 6px; }
  .control label { display: block; font-size: 15px; color: #52514e; margin-bottom: 4px; font-weight: 600; }
  .control.wide { min-width: 320px; flex: 1; }
  .control > label { font-weight: 600; }
  .control label:has(input) { display: inline-flex !important; align-items: center; font-size: 16px; font-weight: 400; color: #0b0b0b; margin-right: 12px; }
  .control .Select-control, .control .Select-menu-outer { font-size: 16px; }
  .control .Select-value-label { white-space: normal !important; line-height: 1.4 !important; }
  .control .Select-control { min-height: 40px; }
  .control input { margin-right: 4px; margin-left: 10px; }
  .filters-text { font-size: 15px; color: #52514e; margin: 6px 0 10px; }
  .cards { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 8px; }
  .card { background: white; border: 1px solid #e4e3df; border-radius: 6px; padding: 8px 14px; min-width: 130px; }
  .card-label { font-size: 15px; color: #52514e; }
  .card-value { font-size: 20px; font-weight: 600; }
  .note { font-size: 15px; color: #52514e; }
  .methods { background: white; padding: 6px 20px 16px; border: 1px solid #e4e3df; border-radius: 6px; margin-top: 14px; }
  .methods h3 { font-size: 19px; }
  .result-table { width: 100%; border-collapse: collapse; font-size: 15px; }
  .result-table th, .result-table td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #e4e3df; }
  ._dash-graph, .dash-graph { background: white; }
</style></head>
<body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>"""

if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=int(os.environ.get("PORT", "8051")))
