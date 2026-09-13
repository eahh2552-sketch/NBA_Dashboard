import glob
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="NBA Analytic Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Carga de archivos (.csv o .xlsx)
def cargar_archivos_carpeta():
  archivos = glob.glob("*.csv") + glob.glob("*.xlsx")
  df_j, df_e = None, None
  for f in archivos:
    df_temp = pd.read_csv(f) if f.endswith(".csv") else pd.read_excel(f)
    cols = [str(c).lower() for c in df_temp.columns]

    # Identificar dataset de jugadores vs equipos
    if any(k in cols for k in ["player", "jugador", "pts"]):
      df_j = df_temp
    elif any(
        k in cols
        for k in [
            "team",
            "win%",
            "w-l%",
            "franchise",
        ]
    ):
      df_e = df_temp
  return df_j, df_e


df_jugadores, df_equipos = cargar_archivos_carpeta()

if df_jugadores is None:
  st.error(
      f"Archivos detectados en la carpeta actual ({os.getcwd()}):"
      f" {os.listdir('.')}"
  )
  st.stop()

# ---------------------------------------------------------
# BARRA LATERAL (FILTROS INDEPENDIENTES)
# ---------------------------------------------------------
st.sidebar.title("Filtros del Dashboard")

# FILTRO 1: EQUIPOS 
st.sidebar.markdown("### 🏀 Filtro de Equipos")
col_team_e = None
df_e_filtrado = df_equipos.copy() if df_equipos is not None else None

if df_equipos is not None:
  col_team_e = next(
      (
          c
          for c in df_equipos.columns
          if c.lower() in ["team"]
      ),
      df_equipos.columns[0],
  )
  equipos_disponibles = sorted(df_equipos[col_team_e].dropna().unique())
  equipos_sel = st.sidebar.multiselect(
      "Seleccionar Equipo(s):",
      options=equipos_disponibles,
      default=equipos_disponibles,
      key="filtro_equipos_sidebar",
  )
  df_e_filtrado = df_equipos[df_equipos[col_team_e].isin(equipos_sel)]

st.sidebar.divider()

# --- FILTRO 2: JUGADORES ---
st.sidebar.markdown("### 👤 Filtro de Jugadores")
col_player = next(
    (
        c
        for c in df_jugadores.columns
        if c.lower() in ["player"]
    ),
    df_jugadores.columns[0],
)
col_team_j = next(
    (
        c
        for c in df_jugadores.columns
        if c.lower() in ["team"]
    ),
    None,
)

df_j_filtrado = df_jugadores.copy()
if col_team_j and df_equipos is not None and "equipos_sel" in locals():
  df_j_filtrado = df_j_filtrado[df_j_filtrado[col_team_j].isin(equipos_sel)]

jugadores_disponibles = sorted(df_j_filtrado[col_player].dropna().unique())
jugadores_sel = st.sidebar.multiselect(
    "Seleccionar/Comparar Jugador(es):",
    options=jugadores_disponibles,
    default=jugadores_disponibles,
    key="filtro_jugadores_sidebar",
)
df_j_filtrado = df_j_filtrado[df_j_filtrado[col_player].isin(jugadores_sel)]

# ---------------------------------------------------------
# ENCABEZADO Y KPIS
# ---------------------------------------------------------
st.title("NBA ANALYTIC DASHBOARD")

st.subheader("KPI's de Temporada")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

col_pts = next(
    (
        c
        for c in df_jugadores.columns
        if c.strip().lower() in ["pts"]
    ),
    None,
)
if not col_pts:
  col_pts = next(
      (
          c
          for c in df_jugadores.columns
          if "pts" in c.lower() and "36" not in c and "ts" not in c.lower()
      ),
      df_jugadores.columns[1],
  )

col_ts = next(
    (
        c
        for c in df_jugadores.columns
        if "ts%" in c.lower()
        or "ts_pct" in c.lower()
        or "true_shooting" in c.lower()
        or c.strip().lower() == "ts"
    ),
    None,
)
if not col_ts:
  col_ts = next(
      (
          c
          for c in df_jugadores.columns
          if "ts" in c.lower() and "pts" not in c.lower()
      ),
      col_pts,
  )

col_ast = next(
    (
        c
        for c in df_jugadores.columns
        if c.strip().lower() in ["ast"]
        and "36" not in c
    ),
    None,
)
if not col_ast:
  col_ast = next(
      (
          c
          for c in df_jugadores.columns
          if "ast" in c.lower() and "36" not in c
      ),
      df_jugadores.columns[2],
  )

col_reb = next(
    (
        c
        for c in df_jugadores.columns
        if c.strip().lower() in ["trb"]
        and "36" not in c
    ),
    None,
)
if not col_reb:
  col_reb = next(
      (
          c
          for c in df_jugadores.columns
          if ("trb" in c.lower() or "reb" in c.lower()) and "36" not in c
      ),
      df_jugadores.columns[3],
  )

if not df_j_filtrado.empty:
  lider_pts = df_j_filtrado.loc[df_j_filtrado[col_pts].idxmax()]
  lider_ts = df_j_filtrado.loc[df_j_filtrado[col_ts].idxmax()]
  lider_ast = df_j_filtrado.loc[df_j_filtrado[col_ast].idxmax()]
  lider_reb = df_j_filtrado.loc[df_j_filtrado[col_reb].idxmax()]

  val_ts = lider_ts[col_ts]
  str_ts = f"{val_ts * 100:.1f}%" if val_ts <= 1.0 else f"{val_ts:.1f}%"

  with kpi1:
    st.metric(
        label="Líder PTS",
        value=f"{lider_pts[col_pts]:.1f}",
        delta=str(lider_pts[col_player]),
    )
  with kpi2:
    st.metric(label="Líder TS%", value=str_ts, delta=str(lider_ts[col_player]))
  with kpi3:
    st.metric(
        label="Líder AST",
        value=f"{lider_ast[col_ast]:.1f}",
        delta=str(lider_ast[col_player]),
    )
  with kpi4:
    st.metric(
        label="Líder REB",
        value=f"{lider_reb[col_reb]:.1f}",
        delta=str(lider_reb[col_player]),
    )

st.divider()

# ---------------------------------------------------------
# GRÁFICAS 1 Y 2: JUGADORES
# ---------------------------------------------------------
st.subheader("Rendimiento de Jugadores")
col1, col2 = st.columns(2)

if not df_j_filtrado.empty:
  fig1 = px.scatter(
      df_j_filtrado,
      x=col_ts,
      y=col_pts,
      color=col_player,
      hover_name=col_player,
      title="Gráfica 1: Eficiencia de Tiro (TS%) vs Puntos",
      template="plotly_dark",
  )
  fig1.update_layout(showlegend=False)
  col1.plotly_chart(fig1, use_container_width=True)

  top10 = df_j_filtrado.nlargest(
      min(10, len(df_j_filtrado)), col_pts
  ).sort_values(col_pts, ascending=True)
  fig2 = px.bar(
      top10,
      x=col_pts,
      y=col_player,
      orientation="h",
      color=col_pts,
      color_continuous_scale="Purples",
      title="Gráfica 2: Top 10 Anotadores",
      template="plotly_dark",
  )
  fig2.update_layout(coloraxis_showscale=False)
  col2.plotly_chart(fig2, use_container_width=True)
else:
  st.warning("No hay datos de jugadores seleccionados.")

st.divider()

# ---------------------------------------------------------
# GRÁFICAS 3 Y 4: EQUIPOS
# ---------------------------------------------------------
st.subheader("Rendimiento Colectivo de Equipos")

if df_e_filtrado is not None and not df_e_filtrado.empty:
  # 1. Asistencias (AST)
  col_eq_ast = next(
      (
          c
          for c in df_e_filtrado.columns
          if c.strip().lower() in ["ast"]
          or "ast" in c.lower()
      ),
      df_e_filtrado.columns[1],
  )

  # 2. Porcentaje de victorias (Win%)
  col_eq_win = next(
      (
          c
          for c in df_e_filtrado.columns
          if any(k in c.lower() for k in ["win%"])
          and not any(
              x in c.lower() for x in ["reb", "trb", "ast", "pts", "opp"]
          )
      ),
      None,
  )
  if not col_eq_win:
    posibles_wins = [
        c
        for c in df_e_filtrado.columns
        if c.strip().lower() in ["w%", "win%", "w_pct", "pct", "w"]
    ]
    col_eq_win = posibles_wins[0] if posibles_wins else df_e_filtrado.columns[2]

  # 3. Puntos Permitidos (Opp PTS / PTS_Opp)
  col_eq_opp = next(
      (
          c
          for c in df_e_filtrado.columns
          if any(
              k in c.lower()
              for k in [
                  "pts_permitidos",
              ]
          )
      ),
      None,
  )
  if not col_eq_opp:
    col_eq_opp = [
        c
        for c in df_e_filtrado.columns
        if df_e_filtrado[c].dtype in ["float64", "int64"]
        and c not in [col_eq_ast, col_eq_win]
    ][0]

  col3, col4 = st.columns(2)

  # Gráfica 3: AST vs Win%
  fig3 = px.scatter(
      df_e_filtrado,
      x=col_eq_ast,
      y=col_eq_win,
      color=col_team_e,
      hover_name=col_team_e,
      title=f"Gráfica 3: {col_eq_ast} vs {col_eq_win} (Porcentaje de Victorias)",
      template="plotly_dark",
  )
  fig3.update_layout(showlegend=False)
  col3.plotly_chart(fig3, use_container_width=True)

# GRÁFICA 4 Puntos Permitidos
col_eq_opp = "PTS_Permitidos"

df_eq_sorted = df_e_filtrado.sort_values(
    by=col_eq_opp, ascending=True
).reset_index(drop=True)
promedio_opp_pts = df_eq_sorted[col_eq_opp].mean()

fig4 = go.Figure()

fig4.add_trace(
    go.Scatter(
        x=df_eq_sorted[col_team_e],
        y=df_eq_sorted[col_eq_opp],
        mode="lines+markers",
        name=col_eq_opp,
        line=dict(color="#a855f7", width=2),
        marker=dict(size=8, color="#c084fc"),
    )
)

fig4.add_trace(
    go.Scatter(
        x=df_eq_sorted[col_team_e],
        y=[promedio_opp_pts] * len(df_eq_sorted),
        mode="lines",
        name=f"Promedio ({promedio_opp_pts:.1f})",
        line=dict(color="#ef4444", width=2, dash="dash"),
    )
)

fig4.update_layout(
    title=f"Gráfica 4: Puntos Permitidos por Equipo",
    template="plotly_dark",
    xaxis=dict(
        showticklabels=False, title=""
    ),  
    yaxis_title=col_eq_opp,
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
    ),
)
col4.plotly_chart(fig4, use_container_width=True)


# ---------------------------------------------------------
# GRÁFICA 5: NORMALIZADO POR 36 MINUTOS
# ---------------------------------------------------------
st.subheader("Gráfica 5: Impacto Combinado por 36 Minutos")
if not df_j_filtrado.empty:
  top10_36m = df_j_filtrado.nlargest(min(10, len(df_j_filtrado)), col_pts)
  cols_36 = [c for c in df_jugadores.columns if "36" in c]
  if not cols_36:
    cols_36 = [col_pts, col_ast, col_reb]

  fig5 = px.bar(
      top10_36m,
      x=col_player,
      y=cols_36,
      barmode="group",
      template="plotly_dark",
      color_discrete_sequence=["#a855f7", "#f97316", "#3b82f6"],
  )
  st.plotly_chart(fig5, use_container_width=True)