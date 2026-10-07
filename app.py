"""Dashboard DMAIC (dados 100% fictícios): OTIF, dispersão de KM e Pareto."""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent
META_OTIF, META_DISP = 90.0, 5.0

st.set_page_config(page_title="DMAIC Logística (simulado)", layout="wide")


@st.cache_data
def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    return pd.read_csv(DATA / "entregas.csv"), pd.read_csv(DATA / "faltas_sku.csv")


def kpis(df: pd.DataFrame) -> pd.Series:
    return pd.Series({
        "OT": df.ot.mean() * 100,
        "IF": df.if_.mean() * 100,
        "OTIF": df.otif.mean() * 100,
        "Dispersão de KM": df.disp_km_pct.mean(),
    })


def pareto(counts: pd.Series, title: str) -> go.Figure:
    pct = counts / counts.sum() * 100
    fig = go.Figure([
        go.Bar(x=counts.index, y=counts.values, name="Ocorrências"),
        go.Scatter(x=counts.index, y=pct.cumsum(), name="% acumulado", yaxis="y2", mode="lines+markers"),
    ])
    fig.update_layout(
        title=title,
        yaxis2=dict(overlaying="y", side="right", range=[0, 105], dtick=20, ticksuffix="%", showgrid=False),
        legend=dict(orientation="h", y=-0.25),
        margin=dict(t=50, b=10),
    )
    return fig


entregas, faltas = load()

st.title("Caso DMAIC: atrasos e falta em distribuição")
st.warning("Projeto de demonstração: todos os dados são fictícios (gerados por `generate_data.py`).")

revendas = st.sidebar.multiselect("Revenda", sorted(entregas.revenda.unique()), default=sorted(entregas.revenda.unique()))
df = entregas[entregas.revenda.isin(revendas)]
antes, depois = df[df.periodo == "antes"], df[df.periodo == "depois"]
k_a, k_d = kpis(antes), kpis(depois)

st.subheader("Antes vs depois")
cols = st.columns(4)
for col, nome in zip(cols, k_a.index):
    # Para dispersão, menor é melhor: inverte a cor do delta.
    col.metric(nome, f"{k_d[nome]:.1f}%", f"{k_d[nome] - k_a[nome]:+.1f} p.p.",
               delta_color="inverse" if nome == "Dispersão de KM" else "normal")
st.caption(f"Metas ilustrativas: OTIF ≥ {META_OTIF:.0f}% e dispersão de KM < {META_DISP:.0f}%.")

por_rev = df.groupby(["revenda", "periodo"]).otif.mean().mul(100).unstack().reindex(columns=["antes", "depois"])
fig = go.Figure([go.Bar(x=por_rev.index, y=por_rev[p], name=p) for p in por_rev.columns])
fig.add_hline(y=META_OTIF, line_dash="dash", annotation_text="Meta")
fig.update_layout(title="OTIF por revenda (%)", barmode="group", margin=dict(t=50, b=10))
st.plotly_chart(fig, width="stretch")

left, right = st.columns(2)
left.plotly_chart(pareto(antes.motivo_atraso.value_counts(), "Pareto: motivos de atraso (período antes)"), width="stretch")
right.plotly_chart(pareto(faltas.sku.value_counts(), "Pareto: falta por SKU"), width="stretch")

with st.expander("Base fictícia (amostra)"):
    st.dataframe(df.head(200))
