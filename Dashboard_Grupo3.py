import io
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Configuración básica
st.set_page_config(page_title="NBA ANALYTIC DASHBOARD", layout="wide")
st.title("NBA ANALYTIC DASHBOARD")
st.subheader("KPI's de Temporada")


def to_excel(df_eq, df_jug):
  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df_eq.to_excel(writer, sheet_name="Equipos_Filtrados", index=False)
    df_jug.to_excel(writer, sheet_name="Jugadores_Filtrados", index=False)
  processed_data = output.getvalue()
  return processed_data


# Cargar datos
df_eq = pd.read_csv("nba_equipos_limpio_av.csv")
df_jug = pd.read_csv("nba_jugadores_limpio_av.csv")
player_col = "Player" if "Player" in df_jug.columns else df_jug.columns[0]

# Filtros de barra lateral
st.sidebar.header("Filtros")
eq_opts = [
    t for t in df_eq["Team"].unique() if str(t).lower() != "league average"
]
sel_eq = st.sidebar.multiselect("Equipos:", eq_opts, default=eq_opts[:30])
sel_jug = st.sidebar.multiselect(
    "Jugadores:",
    df_jug[player_col].unique(),
    default=df_jug[player_col].unique()[:5],
)
st.sidebar.markdown("---")
st.sidebar.subheader("Exportar")

df_e_f = (
    df_eq[df_eq["Team"].isin(sel_eq)]
    if sel_eq
    else pd.DataFrame(columns=df_eq.columns)
)
df_j_f = (
    df_jug[df_jug[player_col].isin(sel_jug)]
    if sel_jug
    else pd.DataFrame(columns=df_jug.columns)
)

if not sel_eq:
  st.sidebar.warning("Selecciona al menos un equipo.")
if not sel_jug:
  st.sidebar.warning("Selecciona al menos un jugador.")

if not df_e_f.empty or not df_j_f.empty:
  excel_data = to_excel(df_e_f, df_j_f)
  st.sidebar.download_button(
      label="📥 Descargar Estadísticas Descriptivas",
      data=excel_data,
      file_name="nba_estadisticas_descriptivas.xlsx",
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  )
else:
  st.sidebar.warning("No hay datos para ser exportados.")

# KPIs
k1, k2, k3, k4 = st.columns(4)
row_pts = df_jug.loc[df_jug["PTS"].idxmax()]
row_ts = df_jug.loc[df_jug["TS%"].idxmax()]
row_ast = df_jug.loc[df_jug["AST"].idxmax()]
row_trb = df_jug.loc[df_jug["TRB"].idxmax()]
ts_val = row_ts["TS%"] * 100 if row_ts["TS%"] <= 1 else row_ts["TS%"]

k1.metric("Líder PTS", row_pts["PTS"], row_pts[player_col])
k2.metric("Líder TS%", f"{ts_val:.1f}%", row_ts[player_col])
k3.metric("Líder AST", row_ast["AST"], row_ast[player_col])
k4.metric("Líder TRB", row_trb["TRB"], row_trb[player_col])
st.markdown("---")

# Tabs
tab_jugadores, tab_equipos, tab_stats = st.tabs([
    " Rendimiento de Jugadores",
    " Rendimiento de Equipos",
    " Estadísticas Descriptivas",
])

# Tab 1: Estadisticas de Jugadores

with tab_jugadores:
  st.header("Rendimiento de jugadores")
  c1, c2 = st.columns(2)

# Grafico 1 TS% v PTS
  with c1:
    st.subheader("■  True Shooting % vs PTS ")
    if not df_j_f.empty:
      fig1 = px.scatter(
          df_j_f, x="TS%", y="PTS", color=player_col, template="plotly_dark"
      )
      st.plotly_chart(fig1, use_container_width=True)
      corr_global = round(df_jug["TS%"].corr(df_jug["PTS"]), 2)
      st.caption(f"Correlación global: {corr_global} o 3%")
    else:
      st.info("Sin jugadores seleccionados.")

# Grafico 2 Puntos por Partido
  with c2:
    st.subheader("■  Puntos por Partido ")
    df_top_pts = df_jug.sort_values("PTS", ascending=True).tail(10)
    fig2 = px.bar(
        df_top_pts,
        x="PTS",
        y=player_col,
        orientation="h",
        template="plotly_dark",
    )
    st.plotly_chart(fig2, use_container_width=True)

  st.markdown("---")

# Impacto de jugador por 36 minutos
  st.header("■  Impacto de jugador por 36 minutos")
  st.subheader(
      "5. Puntos Rebotes y Asistencias por 36 minutos (Máx. 10 jug.)"
  )

  if not df_j_f.empty:
    if len(df_j_f) > 10:
      st.warning("Limitado a 10 jugadores.")
      df_subset = df_j_f.head(10)
    else:
      df_subset = df_j_f

    cols_36 = [
        c for c in ["PTS_36", "AST_36", "TRB_36"] if c in df_subset.columns
    ]
    if cols_36:
      df_melted = df_subset.melt(
          id_vars=[player_col],
          value_vars=cols_36,
          var_name="Var",
          value_name="Cant",
      )
      fig5 = px.bar(
          df_melted,
          x=player_col,
          y="Cant",
          color="Var",
          barmode="group",
          template="plotly_dark",
      )
      st.plotly_chart(fig5, use_container_width=True)
    else:
      st.info("Sin variables 36 min disponibles.")
  else:
    st.info("Sin jugadores seleccionados para esta gráfica.")


# Tab 2: Estadísticas Equipos

with tab_equipos:
  st.header("Rendimiento de Equipos")
  c3, c4 = st.columns(2)

# Grafico 3 Ast v Win %
  with c3:
    st.subheader("■  Asistencias v Win % ")
    if not df_e_f.empty:
      fig3 = px.scatter(
          df_e_f,
          x="AST",
          y="Win %",
          hover_name="Team",
          trendline="ols",
          template="plotly_dark",
      )
      st.plotly_chart(fig3, use_container_width=True)
    else:
      st.info("Sin equipos seleccionados.")

  # Grafico 4 Puntos Permitidos por Equipo
  with c4:
    st.subheader("■  Puntos Permitidos por Equipo ")
    if not df_e_f.empty:
      df_es = df_e_f.sort_values("PTS_Permitidos")
      fig4 = px.line(
          df_es,
          x="Team",
          y="PTS_Permitidos",
          markers=True,
          template="plotly_dark",
      )
      fig4.add_hline(
          y=115.6,
          line_dash="dash",
          line_color="red",
          annotation_text="115.6",
      )
      fig4.update_xaxes(showticklabels=False, title=None)
      fig4.update_yaxes(title_text="Puntos Permitidos")
      st.plotly_chart(fig4, use_container_width=True)
    else:
      st.info("Sin equipos seleccionados.")


# Tab 3: Estadisticas Descriptivas

with tab_stats:
  st.markdown("---")
  st.header("Estadísticas Descriptivas")
  col_desc1, col_desc2 = st.columns(2)

  with col_desc1:
    st.subheader("Equipos filtrados")
    if not df_e_f.empty:
      st.dataframe(df_e_f.describe(), use_container_width=True)
    else:
      st.info("Sin equipos seleccionados.")

  with col_desc2:
    st.subheader("Jugadores filtrados")
    if not df_j_f.empty:
      st.dataframe(df_j_f.describe(), use_container_width=True)
    else:
      st.info("Sin jugadores seleccionados.")
