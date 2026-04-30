import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Coffee Sales Analytics",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for a polished look ───────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(15, 15, 26, 0.95);
        border-right: 1px solid rgba(0, 188, 212, 0.15);
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: rgba(26, 26, 46, 0.8);
        border: 1px solid rgba(0, 188, 212, 0.2);
        border-radius: 12px;
        padding: 16px 20px;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: rgba(0, 188, 212, 0.5);
        box-shadow: 0 4px 20px rgba(0, 188, 212, 0.1);
    }
    div[data-testid="stMetric"] label {
        color: rgba(255, 255, 255, 0.6) !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #00bcd4 !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: rgba(255, 255, 255, 0.5) !important;
        font-size: 0.75rem !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(26, 26, 46, 0.6) !important;
        border-radius: 8px !important;
        border: 1px solid rgba(0, 188, 212, 0.15) !important;
    }

    /* Plotly chart containers */
    .stPlotlyChart {
        background: rgba(26, 26, 46, 0.4);
        border: 1px solid rgba(0, 188, 212, 0.1);
        border-radius: 12px;
        padding: 8px;
    }

    /* Headings */
    h1, h2, h3 {
        color: #e0e0e0 !important;
    }
    h1 {
        background: linear-gradient(90deg, #00bcd4, #26c6da, #4dd0e1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }

    /* Dividers */
    hr {
        border-color: rgba(0, 188, 212, 0.15) !important;
    }

    /* Multiselect tags */
    span[data-baseweb="tag"] {
        background-color: rgba(0, 188, 212, 0.2) !important;
        border: 1px solid rgba(0, 188, 212, 0.4) !important;
        color: #4dd0e1 !important;
    }

    /* Footer */
    .footer-text {
        text-align: center;
        color: rgba(255, 255, 255, 0.35);
        font-size: 0.8rem;
        padding: 2rem 0 1rem;
        border-top: 1px solid rgba(0, 188, 212, 0.1);
        margin-top: 2rem;
    }
    .footer-text a {
        color: #00bcd4;
        text-decoration: none;
    }
</style>
""", unsafe_allow_html=True)

# ── Plotly theme ─────────────────────────────────────────────
PLOT_TEMPLATE = "plotly_dark"
PLOT_BG = "rgba(0,0,0,0)"
PAPER_BG = "rgba(0,0,0,0)"
GRID_COLOR = "rgba(255,255,255,0.06)"
CYAN = "#00bcd4"
CYAN_LIGHT = "#4dd0e1"
CITY_COLORS = {"Melbourne": "#00bcd4", "Sydney": "#ff7043"}

PLOT_LAYOUT = dict(
    template=PLOT_TEMPLATE,
    plot_bgcolor=PLOT_BG,
    paper_bgcolor=PAPER_BG,
    font=dict(color="rgba(255,255,255,0.75)", size=12),
    title_font=dict(size=16, color="rgba(255,255,255,0.9)"),
    margin=dict(t=50, b=40, l=40, r=20),
    xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color="rgba(255,255,255,0.7)"),
    ),
    hoverlabel=dict(
        bgcolor="rgba(26,26,46,0.95)",
        font_size=13,
        font_color="white",
        bordercolor="rgba(0,188,212,0.3)",
    ),
)


# ── Data loading ─────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    csv_path = Path(__file__).parent / "data" / "Coffee_sales.csv"
    if not csv_path.exists():
        st.error(f"Dataset not found at `{csv_path}`.")
        st.stop()

    df = pd.read_csv(csv_path, parse_dates=["Date"])
    df["year"] = df["Date"].dt.year
    df["month_num"] = df["Date"].dt.month
    df["quarter"] = df["Date"].dt.quarter
    df["year_month"] = df["Date"].dt.to_period("M")
    return df


data = load_data()

# ── Sidebar filters ──────────────────────────────────────────
st.sidebar.markdown("## 🔎 Filters")
st.sidebar.markdown("---")

df = data.copy()

# Date range
min_date = data["Date"].min().date()
max_date = data["Date"].max().date()
available_years = sorted(data["Date"].dt.year.unique().tolist())

# Build dynamic filter options based on actual data
period_options = ["All Data"] + [str(y) for y in available_years] + ["Last 90 days", "Last 30 days", "Custom"]

date_preset = st.sidebar.selectbox("Quick Period", period_options, index=0)

if date_preset == "Last 30 days":
    start_date = max_date - pd.Timedelta(days=30)
    end_date = max_date
elif date_preset == "Last 90 days":
    start_date = max_date - pd.Timedelta(days=90)
    end_date = max_date
elif date_preset == "Custom":
    date_range = st.sidebar.date_input(
        "Select period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date
elif date_preset.isdigit():
    year = int(date_preset)
    start_date = pd.Timestamp(f"{year}-01-01").date()
    end_date = pd.Timestamp(f"{year}-12-31").date()
else:
    start_date, end_date = min_date, max_date

df = df[(df["Date"].dt.date >= pd.to_datetime(start_date).date()) & (df["Date"].dt.date <= pd.to_datetime(end_date).date())]

# Location
all_cities = sorted(data["City"].unique().tolist())
with st.sidebar.expander("📍 Location", expanded=True):
    cities = st.multiselect("Cities", options=all_cities, default=all_cities)
    df = df[df["City"].isin(cities)]

# Products
all_products = sorted(data["coffee_name"].unique().tolist())
with st.sidebar.expander("☕ Products", expanded=False):
    products = st.multiselect("Coffee Types", options=all_products, default=all_products)
    df = df[df["coffee_name"].isin(products)]

# Time of day
all_times = data["Time_of_Day"].unique().tolist()
with st.sidebar.expander("⏰ Time of Day", expanded=False):
    times = st.multiselect("Periods", options=all_times, default=all_times)
    df = df[df["Time_of_Day"].isin(times)]

# Payment
all_payments = sorted(data["cash_type"].unique().tolist())
with st.sidebar.expander("💳 Payment", expanded=False):
    payments = st.multiselect("Methods", options=all_payments, default=all_payments)
    df = df[df["cash_type"].isin(payments)]

st.sidebar.markdown("---")

# Language
if "language" not in st.session_state:
    st.session_state.language = "English"

lang = st.sidebar.radio(
    "🌐 Language / Idioma",
    ["English", "Português"],
    index=0 if st.session_state.language == "English" else 1,
)
if lang != st.session_state.language:
    st.session_state.language = lang
    st.rerun()

is_en = st.session_state.language == "English"

# ── Header ───────────────────────────────────────────────────
st.title("☕ Coffee Sales Dashboard")

if is_en:
    st.markdown(
        "**A strategic analysis of {:,} transactions** across Melbourne and Sydney — "
        "uncovering consumption patterns, peak hours, and growth opportunities.".format(len(data))
    )
else:
    st.markdown(
        "**Uma análise estratégica de {:,} transações** em Melbourne e Sydney — "
        "revelando padrões de consumo, horários de pico e oportunidades de crescimento.".format(len(data))
    )

# Executive summary
with st.expander(
    "📊 Executive Summary" if is_en else "📊 Resumo Executivo",
    expanded=False,
):
    if is_en:
        st.markdown("""
### Core Performance Indicators

| Metric | Melbourne | Sydney | Insight |
| :--- | :--- | :--- | :--- |
| **Avg. Transaction** | $14.90 | $15.20 | Sydney has 2% higher willingness to pay |
| **Peak Revenue Window** | 63% (1–4 PM) | 58% (1–4 PM) | Melbourne more dependent on peak hours |
| **Top Payment** | 67% Debit | 61% Credit | Sydney's mix suggests higher-spending demographic |
| **Product Concentration** | Top 2 = 48% | Top 2 = 42% | Melbourne more concentrated on core products |

### Key Takeaways

- **Latte** leads both markets at **28% of total revenue**
- Melbourne shows **23% higher Espresso consumption** — purist coffee culture
- Sydney shows **18% higher Cappuccino preference** — more experimental
- Credit card transactions correlate with **18% higher average spend**

### Strategic Profiles
- **Melbourne — The Connoisseur:** Optimize for frequency and operational excellence
- **Sydney — The Experience-Seeker:** Optimize for average ticket value and experience
        """)
    else:
        st.markdown("""
### Indicadores Principais

| Métrica | Melbourne | Sydney | Insight |
| :--- | :--- | :--- | :--- |
| **Ticket Médio** | $14,90 | $15,20 | Sydney tem disposição 2% maior para pagar |
| **Janela de Pico** | 63% (13–16h) | 58% (13–16h) | Melbourne mais dependente do horário de pico |
| **Pagamento Principal** | 67% Débito | 61% Crédito | Mix de Sydney sugere demografia de maior gasto |
| **Concentração** | Top 2 = 48% | Top 2 = 42% | Melbourne mais concentrada em produtos core |

### Principais Descobertas

- **Latte** lidera ambos os mercados com **28% da receita total**
- Melbourne mostra **23% mais consumo de Espresso** — cultura purista
- Sydney mostra **18% mais preferência por Cappuccino** — mais experimental
- Transações com cartão de crédito correlacionam com **18% mais gasto médio**

### Perfis Estratégicos
- **Melbourne — O Conhecedor:** Otimizar para frequência e excelência operacional
- **Sydney — O Buscador de Experiências:** Otimizar para ticket médio e experiência
        """)

st.markdown("---")

# ── Guard: empty data ────────────────────────────────────────
if df.empty:
    st.warning("No data for the selected filters." if is_en else "Sem dados para os filtros selecionados.")
    st.stop()

# ── KPI Metrics ──────────────────────────────────────────────
st.subheader("📈 Key Metrics" if is_en else "📈 Métricas Principais")

col1, col2, col3, col4, col5 = st.columns(5)

total_revenue = df["money"].sum()
total_txns = len(df)
avg_ticket = df["money"].mean()
top_product = df["coffee_name"].value_counts().index[0]
unique_days = df["Date"].dt.date.nunique()
daily_avg = total_revenue / unique_days if unique_days > 0 else 0

col1.metric("Total Revenue" if is_en else "Receita Total", f"${total_revenue:,.2f}")
col2.metric("Transactions" if is_en else "Transações", f"{total_txns:,}")
col3.metric("Avg. Ticket" if is_en else "Ticket Médio", f"${avg_ticket:,.2f}")
col4.metric("Top Product" if is_en else "Mais Vendido", top_product)
col5.metric("Daily Avg." if is_en else "Média Diária", f"${daily_avg:,.0f}")

st.markdown("---")

# ── Row 1: Sales by Product + Sales by Hour ──────────────────
st.subheader("☕ Sales Analysis" if is_en else "☕ Análise de Vendas")
col1, col2 = st.columns(2)

with col1:
    sales_product = (
        df.groupby("coffee_name")["money"]
        .sum()
        .sort_values(ascending=True)
        .reset_index()
    )
    fig = px.bar(
        sales_product,
        y="coffee_name",
        x="money",
        orientation="h",
        title="Revenue by Coffee Type" if is_en else "Receita por Tipo de Café",
        color="money",
        color_continuous_scale=["#004d40", "#00bcd4", "#4dd0e1"],
    )
    fig.update_layout(**PLOT_LAYOUT, coloraxis_showscale=False)
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>$%{x:,.2f}<extra></extra>",
        texttemplate="$%{x:,.0f}",
        textposition="outside",
        textfont=dict(color="rgba(255,255,255,0.7)", size=11),
    )
    fig.update_xaxes(title="", tickprefix="$", tickformat=",.0f")
    fig.update_yaxes(title="")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    sales_hour = df.groupby(["hour_of_day", "City"])["money"].sum().reset_index()
    fig = px.line(
        sales_hour,
        x="hour_of_day",
        y="money",
        color="City",
        title="Revenue by Hour" if is_en else "Receita por Hora",
        color_discrete_map=CITY_COLORS,
        markers=True,
    )
    fig.update_layout(**PLOT_LAYOUT, hovermode="x unified")
    fig.update_traces(
        hovertemplate="$%{y:,.2f}<extra></extra>",
        line=dict(width=2.5),
        marker=dict(size=6),
    )
    fig.update_xaxes(title="Hour" if is_en else "Hora", tickmode="linear", dtick=2)
    fig.update_yaxes(title="", tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig, use_container_width=True)

# ── Row 2: Time of Day + Payment Method ──────────────────────
col1, col2 = st.columns(2)

with col1:
    time_order = ["Morning", "Afternoon", "Evening", "Night"]
    sales_tod = df.groupby("Time_of_Day")["money"].sum().reset_index()
    sales_tod["Time_of_Day"] = pd.Categorical(sales_tod["Time_of_Day"], categories=time_order, ordered=True)
    sales_tod = sales_tod.sort_values("Time_of_Day")

    fig = px.pie(
        sales_tod,
        values="money",
        names="Time_of_Day",
        title="Revenue by Time of Day" if is_en else "Receita por Período do Dia",
        hole=0.5,
        color_discrete_sequence=["#00bcd4", "#26c6da", "#ff7043", "#455a64"],
    )
    fig.update_layout(**PLOT_LAYOUT)
    fig.update_traces(
        textinfo="percent+label",
        textfont=dict(size=12, color="white"),
        hovertemplate="<b>%{label}</b><br>$%{value:,.2f} (%{percent})<extra></extra>",
        marker=dict(line=dict(color="rgba(15,15,26,1)", width=2)),
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    sales_pay = df.groupby("cash_type")["money"].agg(["sum", "count"]).reset_index()
    sales_pay.columns = ["Method", "Revenue", "Count"]
    sales_pay = sales_pay.sort_values("Revenue", ascending=True)

    fig = px.bar(
        sales_pay,
        y="Method",
        x="Revenue",
        orientation="h",
        title="Revenue by Payment Method" if is_en else "Receita por Método de Pagamento",
        color="Method",
        color_discrete_sequence=["#00bcd4", "#ff7043", "#4dd0e1"],
    )
    fig.update_layout(**PLOT_LAYOUT, showlegend=False)
    fig.update_traces(
        texttemplate="$%{x:,.0f}",
        textposition="outside",
        textfont=dict(color="rgba(255,255,255,0.7)", size=11),
        hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.2f}<extra></extra>",
    )
    fig.update_xaxes(title="", tickprefix="$", tickformat=",.0f")
    fig.update_yaxes(title="")
    st.plotly_chart(fig, use_container_width=True)

# ── Row 3: Weekday + Monthly ─────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    sales_wd = df.groupby(["Weekday", "City"])["money"].sum().reset_index()
    sales_wd["Weekday"] = pd.Categorical(sales_wd["Weekday"], categories=day_order, ordered=True)
    sales_wd = sales_wd.sort_values("Weekday")

    fig = px.bar(
        sales_wd,
        x="Weekday",
        y="money",
        color="City",
        barmode="group",
        title="Revenue by Weekday" if is_en else "Receita por Dia da Semana",
        color_discrete_map=CITY_COLORS,
    )
    fig.update_layout(**PLOT_LAYOUT)
    fig.update_xaxes(title="", tickvals=day_order, ticktext=day_short)
    fig.update_yaxes(title="", tickprefix="$", tickformat=",.0f")
    fig.update_traces(hovertemplate="<b>%{x}</b><br>$%{y:,.2f}<extra></extra>")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    monthly = df.groupby(["year_month", "City"])["money"].sum().reset_index()
    monthly["date"] = monthly["year_month"].dt.to_timestamp()
    monthly["label"] = monthly["year_month"].dt.strftime("%b %Y")
    monthly = monthly.sort_values("date")

    fig = px.bar(
        monthly,
        x="label",
        y="money",
        color="City",
        barmode="group",
        title="Revenue by Month" if is_en else "Receita por Mês",
        color_discrete_map=CITY_COLORS,
    )
    fig.update_layout(**PLOT_LAYOUT, xaxis_tickangle=-45)
    fig.update_xaxes(title="")
    fig.update_yaxes(title="", tickprefix="$", tickformat=",.0f")
    fig.update_traces(hovertemplate="<b>%{x}</b><br>$%{y:,.2f}<extra></extra>")
    st.plotly_chart(fig, use_container_width=True)

# ── Row 4: Trend line ────────────────────────────────────────
st.subheader("📈 Sales Trend" if is_en else "📈 Tendência de Vendas")

trend = df.groupby(["year_month", "City"])["money"].sum().reset_index()
trend["date"] = trend["year_month"].dt.to_timestamp()
trend["label"] = trend["year_month"].dt.strftime("%b %Y")
trend = trend.sort_values("date")

fig = px.area(
    trend,
    x="date",
    y="money",
    color="City",
    title="Monthly Revenue Trend" if is_en else "Tendência Mensal de Receita",
    color_discrete_map=CITY_COLORS,
)
fig.update_layout(**PLOT_LAYOUT, hovermode="x unified")
fig.update_traces(
    hovertemplate="$%{y:,.2f}<extra></extra>",
    line=dict(width=2),
    fillcolor=None,
)
# Semi-transparent fill
for trace in fig.data:
    base_color = CITY_COLORS.get(trace.name, CYAN)
    trace.fillcolor = base_color.replace(")", ", 0.15)").replace("rgb", "rgba") if "rgb" in base_color else None
    if trace.fillcolor is None:
        # hex fallback
        r, g, b = int(base_color[1:3], 16), int(base_color[3:5], 16), int(base_color[5:7], 16)
        trace.fillcolor = f"rgba({r},{g},{b},0.12)"

fig.update_xaxes(title="")
fig.update_yaxes(title="", tickprefix="$", tickformat=",.0f")
st.plotly_chart(fig, use_container_width=True)

# ── Row 5: City comparison heatmap ───────────────────────────
st.subheader("🗺️ City Comparison" if is_en else "🗺️ Comparação entre Cidades")

col1, col2 = st.columns(2)

with col1:
    # Product x City heatmap
    heatmap_data = df.pivot_table(values="money", index="coffee_name", columns="City", aggfunc="sum", fill_value=0)
    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns.tolist(),
            y=heatmap_data.index.tolist(),
            colorscale=[[0, "#0f0f1a"], [0.5, "#00695c"], [1, "#00bcd4"]],
            hovertemplate="<b>%{y}</b> — %{x}<br>$%{z:,.2f}<extra></extra>",
            texttemplate="$%{z:,.0f}",
            textfont=dict(size=11, color="white"),
        )
    )
    fig.update_layout(
        **PLOT_LAYOUT,
        title="Revenue: Product × City" if is_en else "Receita: Produto × Cidade",
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Hour x City heatmap
    hour_city = df.pivot_table(values="money", index="hour_of_day", columns="City", aggfunc="sum", fill_value=0)
    fig = go.Figure(
        data=go.Heatmap(
            z=hour_city.values,
            x=hour_city.columns.tolist(),
            y=[f"{h}:00" for h in hour_city.index],
            colorscale=[[0, "#0f0f1a"], [0.5, "#bf360c"], [1, "#ff7043"]],
            hovertemplate="<b>%{y}</b> — %{x}<br>$%{z:,.2f}<extra></extra>",
            texttemplate="$%{z:,.0f}",
            textfont=dict(size=10, color="white"),
        )
    )
    fig.update_layout(
        **PLOT_LAYOUT,
        title="Revenue: Hour × City" if is_en else "Receita: Hora × Cidade",
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="")
    st.plotly_chart(fig, use_container_width=True)

# ── Footer ───────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div class="footer-text">'
    'Coffee Sales Dashboard · © 2025 '
    '<a href="https://github.com/LucasMilanez" target="_blank">Lucas Milanez</a>'
    " · All rights reserved"
    "</div>",
    unsafe_allow_html=True,
)
