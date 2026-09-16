"""TourisCam AI — MINTOUL tourism-intelligence dashboard (Streamlit).

Two views:
  - "Demo (simulated)": `demo_query_logs` — 6,200 synthetic WhatsApp interactions
    standing in for real usage until the bot has traffic. Always labeled as simulated.
  - "Live bot": anonymized `query_events` written by the n8n WhatsApp workflow.

Reads Supabase through the same direct Postgres connection as the RAG scripts
(rag/config.py), so it runs locally with the project .env.

Charts follow the dataviz method: one-hue sequential heatmap, single-colour bars,
blue<->red diverging sentiment with a neutral grey, validated categorical slots,
a legend plus direct labels, and a table view under every chart.

Run:
    rag/.venv/Scripts/python.exe -m streamlit run dashboard/app.py
"""
from __future__ import annotations

import hmac
import os
import sys
import time
from datetime import timedelta, timezone
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "rag"))
from config import pg_connect  # noqa: E402 — also loads the project .env

WAT = timezone(timedelta(hours=1))  # Cameroon time, no DST
PLOTLY_CONFIG = {"displayModeBar": False}
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
# Fixed slot order: colour follows the entity, never its rank.
LANGUAGES = [("fr", "French"), ("en", "English"), ("pidgin", "Pidgin")]

# Validated palette (see dataviz skill references/palette.md; both modes pass the
# six checks — light-mode aqua is under 3:1, hence direct labels + table views).
PALETTE = {
    "light": {"surface": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#898781",
              "grid": "#e1e0d9", "axis": "#c3c2b7",
              "series": ["#2a78d6", "#eb6834", "#1baf7a"],
              "positive": "#2a78d6", "negative": "#e34948", "neutral": "#c3c2b7",
              "sequential": ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]},
    "dark": {"surface": "#1a1a19", "ink": "#ffffff", "ink2": "#c3c2b7", "muted": "#898781",
             "grid": "#2c2c2a", "axis": "#383835",
             "series": ["#3987e5", "#d95926", "#199e70"],
             "positive": "#3987e5", "negative": "#e66767", "neutral": "#52514e",
             "sequential": ["#0d366b", "#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", "#cde2fb"]},
}


def palette() -> dict:
    try:  # Streamlit >= 1.46 exposes the viewer's theme
        return PALETTE["dark" if st.context.theme.type == "dark" else "light"]
    except Exception:
        return PALETTE["light"]


def ink_on(fill: str) -> str:
    """Ink or white for a label set inside a coloured fill, by its luminance."""
    r, g, b = (int(fill[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return "#0b0b0b" if 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.45 else "#ffffff"


@st.cache_data(ttl=300, show_spinner="Reading Supabase…")
def fetch(sql: str) -> pd.DataFrame:
    last: Exception | None = None
    for attempt in range(3):  # the local network drops DNS intermittently
        try:
            conn = pg_connect()
            try:
                with conn.cursor() as cur:
                    cur.execute("set transaction read only")
                    cur.execute(sql)
                    cols = [d[0] for d in cur.description]
                    return pd.DataFrame(cur.fetchall(), columns=cols)
            finally:
                conn.close()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Could not reach Supabase: {last}")


def style(fig: go.Figure, pal: dict, height: int) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=8, b=8), bargap=0.45,
        paper_bgcolor=pal["surface"], plot_bgcolor=pal["surface"],
        font=dict(family=FONT, size=13, color=pal["ink2"]),
        hoverlabel=dict(bgcolor=pal["surface"], bordercolor=pal["axis"],
                        font=dict(family=FONT, color=pal["ink"])),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
    )
    axis = dict(gridcolor=pal["grid"], linecolor=pal["axis"], zerolinecolor=pal["axis"],
                tickfont=dict(color=pal["muted"]), title_font=dict(color=pal["muted"]))
    fig.update_xaxes(**axis)
    fig.update_yaxes(**axis)
    return fig


def table_view(df: pd.DataFrame, label: str = "Table view") -> None:
    with st.expander(label):
        st.dataframe(df, width="stretch", hide_index=True)


# ----------------------------------------------------------------- charts ----
def heatmap_region_week(df: pd.DataFrame, pal: dict):
    weekly = df.groupby(["region_referenced", "week"]).size().rename("queries").reset_index()
    order = df["region_referenced"].value_counts().index.tolist()
    grid = (weekly.pivot(index="region_referenced", columns="week", values="queries")
            .reindex(order).fillna(0))
    steps = pal["sequential"]
    fig = go.Figure(go.Heatmap(
        z=grid.values, x=grid.columns, y=grid.index, xgap=2, ygap=2,
        colorscale=[[i / (len(steps) - 1), c] for i, c in enumerate(steps)],
        colorbar=dict(title=dict(text="Queries", font=dict(color=pal["muted"])),
                      outlinewidth=0, thickness=10, tickfont=dict(color=pal["muted"])),
        hovertemplate="%{y}<br>Week of %{x|%d %b %Y}<br>%{z:,.0f} queries<extra></extra>"))
    style(fig, pal, 420)
    fig.update_xaxes(showgrid=False, tickformat="%d %b")
    fig.update_yaxes(showgrid=False, autorange="reversed")
    table = grid.astype(int).reset_index().rename(columns={"region_referenced": "Region"})
    # All-string column names: mixed str/Timestamp headers don't round-trip to Arrow.
    table.columns = [c if isinstance(c, str) else f"w/c {pd.Timestamp(c):%d %b}" for c in table.columns]
    return fig, table


def bar_top_sites(df: pd.DataFrame, pal: dict):
    top = df["site_referenced"].dropna().value_counts().head(10).sort_values()
    fig = go.Figure(go.Bar(
        x=top.values, y=top.index, orientation="h", cliponaxis=False,
        marker=dict(color=pal["series"][0], cornerradius=4),
        text=[f"{v:,}" for v in top.values], textposition="outside",
        textfont=dict(color=pal["ink2"], family=FONT),
        hovertemplate="%{y}<br>%{x:,} queries<extra></extra>"))
    style(fig, pal, 420)
    fig.update_xaxes(title_text="Queries")
    fig.update_yaxes(showgrid=False)
    table = (top.sort_values(ascending=False).rename("Queries")
             .rename_axis("Site").reset_index())
    return fig, table


def bar_languages(df: pd.DataFrame, pal: dict):
    counts = df["language"].value_counts()
    total = int(counts.sum()) or 1
    fig = go.Figure()
    rows = []
    for i, (code, label) in enumerate(LANGUAGES):
        n = int(counts.get(code, 0))
        pct = 100 * n / total
        fill = pal["series"][i]
        fig.add_trace(go.Bar(
            x=[pct], y=["Queries"], orientation="h", name=label,
            marker=dict(color=fill, line=dict(color=pal["surface"], width=2)),  # 2px surface gap
            text=[f"{label} {pct:.0f}%" if pct >= 12 else f"{pct:.0f}%"],
            textposition="inside", insidetextanchor="middle",
            textfont=dict(color=ink_on(fill), family=FONT),
            hovertemplate=f"{label}: {n:,} queries ({pct:.1f}%)<extra></extra>"))
        rows.append({"Language": label, "Queries": n, "Share": f"{pct:.1f}%"})
    style(fig, pal, 150)
    fig.update_layout(barmode="stack")
    fig.update_xaxes(range=[0, 100], ticksuffix="%", showgrid=False)
    fig.update_yaxes(showticklabels=False, showgrid=False)
    return fig, pd.DataFrame(rows)


def diverging_sentiment(df: pd.DataFrame, pal: dict):
    """Ordered-scale share -> diverging stacked bar centred on neutral."""
    share = pd.crosstab(df["query_type"], df["sentiment"], normalize="index") * 100
    for col in ("negative", "neutral", "positive"):
        if col not in share:
            share[col] = 0.0
    share = share.sort_values("negative")
    labels = [t.replace("_", " ").capitalize() for t in share.index]
    counts = pd.crosstab(df["query_type"], df["sentiment"]).reindex(share.index)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels, x=share["negative"], base=-(share["neutral"] / 2 + share["negative"]),
        orientation="h", name="Negative", marker=dict(color=pal["negative"]),
        customdata=counts.get("negative", pd.Series(0, index=share.index)),
        hovertemplate="%{y} — negative: %{customdata:,} (%{x:.1f}%)<extra></extra>"))
    fig.add_trace(go.Bar(
        y=labels, x=share["neutral"], base=-share["neutral"] / 2,
        orientation="h", name="Neutral", marker=dict(color=pal["neutral"]),
        customdata=counts.get("neutral", pd.Series(0, index=share.index)),
        hovertemplate="%{y} — neutral: %{customdata:,} (%{x:.1f}%)<extra></extra>"))
    fig.add_trace(go.Bar(
        y=labels, x=share["positive"], base=share["neutral"] / 2,
        orientation="h", name="Positive", marker=dict(color=pal["positive"]),
        customdata=counts.get("positive", pd.Series(0, index=share.index)),
        hovertemplate="%{y} — positive: %{customdata:,} (%{x:.1f}%)<extra></extra>"))

    # Direct-label only the story: the negative share, outside the left end.
    for label, neg, neutral in zip(labels, share["negative"], share["neutral"]):
        fig.add_annotation(x=-(neutral / 2 + neg) - 1.5, y=label, text=f"{neg:.0f}%",
                           showarrow=False, xanchor="right",
                           font=dict(color=pal["ink2"], family=FONT, size=12))
    style(fig, pal, 420)
    fig.update_layout(barmode="overlay")
    span = float((share["neutral"] / 2 + share[["negative", "positive"]].max(axis=1)).max()) + 12
    fig.update_xaxes(range=[-span, span], ticksuffix="%", title_text="Share of queries")
    fig.update_yaxes(showgrid=False)

    table = counts.fillna(0).astype(int)
    table.index = labels
    return fig, table.rename_axis("Query type").reset_index()


# ------------------------------------------------------------------ views ----
def demo_view(pal: dict) -> None:
    df = fetch("""
        select occurred_at, channel, language, visitor_type, visitor_origin, query_type,
               site_referenced, region_referenced, sentiment, response_time_seconds,
               resolved, is_emergency
        from demo_query_logs
    """)
    st.info("**Simulated demo data** — 6,200 synthetic WhatsApp interactions "
            "(1 Jun – 8 Sep 2026) standing in for real usage until the bot has traffic. "
            "Not real visitors. Live traffic appears in the **Live bot** tab.")

    local = pd.to_datetime(df["occurred_at"], utc=True).dt.tz_convert(WAT).dt.tz_localize(None)
    df["day"] = local.dt.date
    df["week"] = (local - pd.to_timedelta(local.dt.weekday, unit="D")).dt.normalize()
    for col in ("resolved", "is_emergency"):  # psycopg2 hands these back as objects
        df[col] = df[col].astype(bool)

    first, last = min(df["day"]), max(df["day"])
    c1, c2, c3 = st.columns([2, 3, 2])
    dates = c1.date_input("Date range", value=(first, last), min_value=first, max_value=last)
    regions = c2.multiselect("Region", sorted(df["region_referenced"].dropna().unique()),
                             placeholder="All regions")
    visitors = c3.multiselect("Visitor type", ["domestic", "foreign"], placeholder="All visitors")

    d = df
    if isinstance(dates, (list, tuple)) and len(dates) == 2:
        d = d[(d["day"] >= dates[0]) & (d["day"] <= dates[1])]
    if regions:
        d = d[d["region_referenced"].isin(regions)]
    if visitors:
        d = d[d["visitor_type"].isin(visitors)]
    if d.empty:
        st.warning("No queries match these filters.")
        return

    k = st.columns(6)
    k[0].metric("Queries", f"{len(d):,}")
    k[1].metric("Foreign visitors", f"{(d['visitor_type'] == 'foreign').mean():.0%}")
    k[2].metric("Resolved", f"{d['resolved'].mean():.1%}")
    k[3].metric("Avg response", f"{d['response_time_seconds'].astype(float).mean():.1f} s")
    k[4].metric("Voice notes", f"{(d['channel'] == 'voice_note').mean():.0%}")
    k[5].metric("SOS alerts", f"{int(d['is_emergency'].sum()):,}")

    st.subheader("Demand by region and week")
    fig, table = heatmap_region_week(d, pal)
    st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)
    table_view(table)

    left, right = st.columns(2)
    with left:
        st.subheader("Most asked-about sites")
        fig, table = bar_top_sites(d, pal)
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)
        table_view(table)
    with right:
        st.subheader("Sentiment by query type")
        fig, table = diverging_sentiment(d, pal)
        totals = table[["negative", "neutral", "positive"]].sum(axis=1).replace(0, pd.NA)
        worst = (table.assign(share=100 * table["negative"] / totals)
                 .nlargest(2, "share")[["Query type", "share"]])
        st.caption("Most negative question types: "
                   + ", ".join(f"{r['Query type'].lower()} ({r['share']:.0f}%)"
                               for _, r in worst.iterrows())
                   + " — where complaints concentrate.")
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)
        table_view(table)

    st.subheader("Language of queries")
    fig, table = bar_languages(d, pal)
    st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)
    table_view(table)

    st.subheader("Emergency (SOS) queries")
    sos = (d[d["is_emergency"]].sort_values("occurred_at", ascending=False)
           .head(20)[["occurred_at", "site_referenced", "region_referenced", "language",
                      "visitor_type", "resolved"]])
    if sos.empty:
        st.caption("No SOS queries in this slice.")
    else:
        st.caption(f"⚠ {int(d['is_emergency'].sum()):,} SOS queries in this slice — "
                   "latest 20 shown. These drive the alert/broadcast demo.")
        st.dataframe(sos, width="stretch", hide_index=True)


def live_view(pal: dict) -> None:
    ev = fetch("""
        select occurred_at, destination, intent, language, query_category,
               tool_used, response_status, complaint_flag
        from query_events order by occurred_at desc limit 5000
    """)
    if ev.empty:
        st.info("No live WhatsApp traffic logged yet. Rows appear here once real messages "
                "reach the bot — it writes one anonymized event per message "
                "(no phone numbers, hashed session ids).")
        return

    k = st.columns(4)
    k[0].metric("Events", f"{len(ev):,}")
    k[1].metric("Answered", f"{(ev['response_status'] == 'ok').mean():.0%}")
    k[2].metric("Tariff Guard", f"{int((ev['tool_used'] == 'tariff_guard').sum()):,}")
    k[3].metric("Non-text messages", f"{int((ev['response_status'] == 'unsupported_media').sum()):,}")

    st.subheader("Questions by category")
    counts = ev["query_category"].value_counts().sort_values()
    fig = go.Figure(go.Bar(x=counts.values, y=counts.index, orientation="h", cliponaxis=False,
                           marker=dict(color=pal["series"][0], cornerradius=4),
                           text=[f"{v:,}" for v in counts.values], textposition="outside",
                           textfont=dict(color=pal["ink2"], family=FONT),
                           hovertemplate="%{y}<br>%{x:,} questions<extra></extra>"))
    style(fig, pal, 320)
    fig.update_xaxes(title_text="Questions")
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)
    table_view(counts.sort_values(ascending=False).rename("Questions")
               .rename_axis("Category").reset_index())

    st.subheader("Latest events")
    st.dataframe(ev.head(25), width="stretch", hide_index=True)


def main() -> None:
    st.set_page_config(page_title="TourisCam AI — MINTOUL dashboard",
                       page_icon="🇨🇲", layout="wide")
    expected = os.getenv("DASHBOARD_PASSWORD")
    if expected:
        if not st.session_state.get("authenticated"):
            entered = st.text_input("Dashboard password", type="password")
            if entered and hmac.compare_digest(entered, expected):
                st.session_state["authenticated"] = True
                st.rerun()
            elif entered:
                st.error("Wrong password.")
            st.stop()
    else:  # no password by design for the local demo; set DASHBOARD_PASSWORD to enable the gate
        st.sidebar.caption("Local demo — open access.")

    st.title("TourisCam AI — tourism intelligence")
    st.caption("Anonymous WhatsApp demand signals for MINTOUL. No phone numbers are stored; "
               "sessions are hashed.")
    pal = palette()
    demo_tab, live_tab = st.tabs(["Demo (simulated)", "Live bot"])
    with demo_tab:
        demo_view(pal)
    with live_tab:
        live_view(pal)


if __name__ == "__main__":
    main()
