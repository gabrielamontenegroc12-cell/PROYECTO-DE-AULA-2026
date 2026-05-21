import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from pathlib import Path

# =========================
# CONFIGURACIÓN
# =========================

st.set_page_config(
    page_title="Análisis de Portafolios",
    layout="wide"
)

DATA_PATH = Path("Datos") / "Formato_351.csv"

st.title("📊 Dashboard de Análisis de Portafolios")
st.markdown("Análisis de compras, ventas y consenso institucional")

# =========================
# PIPELINE
# =========================

@st.cache_data
def ejecutar_pipeline():

    con = duckdb.connect(database=":memory:")

    # Leer CSV
    con.execute("""
        CREATE TABLE data AS 
        SELECT * FROM read_csv_auto(?);
    """, [str(DATA_PATH)])

    # Limpiar datos
    df = con.execute("""
        SELECT 
            "Nombre Patrimonio",
            "Nemotecnico",
            "Fecha de Corte",
            
            CAST(
                REPLACE(
                    REPLACE("Valor_Mercado_O_Pres_Pesos", '$', ''),
                ',', '') 
            AS DOUBLE) AS valor_mercado

        FROM data

        WHERE "Codigo_Moneda" = 'USD'
          AND "Nemotecnico" IS NOT NULL
          AND "Nemotecnico" != 'N/A'
          AND "Nombre Patrimonio" IS NOT NULL
    """).df()

    # =========================
    # LIMPIEZA
    # =========================

    df["Fecha de Corte"] = pd.to_datetime(df["Fecha de Corte"])

    df = df[df["Nemotecnico"].notna()]
    df = df[df["Nemotecnico"] != "N/A"]

    # =========================
    # ORDENAR
    # =========================

    df = df.sort_values(
        ["Nombre Patrimonio", "Nemotecnico", "Fecha de Corte"]
    )

    # =========================
    # CALCULAR CAMBIOS
    # =========================

    df["cambio_valor"] = df.groupby(
        ["Nombre Patrimonio", "Nemotecnico"]
    )["valor_mercado"].diff()

    # =========================
    # TIPO MOVIMIENTO
    # =========================

    df["tipo_movimiento"] = df["cambio_valor"].apply(
        lambda x:
            "COMPRA" if x > 0 else
            ("VENTA" if x < 0 else "SIN_CAMBIO")
    )

    # Eliminar NaN SOLO del diff
    df = df[df["cambio_valor"].notna()]

    # =========================
    # DATAFRAMES
    # =========================

    compras = df[df["tipo_movimiento"] == "COMPRA"].copy()

    ventas = df[df["tipo_movimiento"] == "VENTA"].copy()

    ventas["monto_venta"] = ventas["cambio_valor"].abs()

    # =========================
    # CONSENSO
    # =========================

    consenso = (
        df.groupby(["Nemotecnico", "tipo_movimiento"])
        .agg(
            cantidad_fondos=("Nombre Patrimonio", "nunique"),
            monto_total=("cambio_valor", "sum")
        )
        .reset_index()
    )

    return df, compras, ventas, consenso


# =========================
# VALIDACIÓN ARCHIVO
# =========================

if not DATA_PATH.exists():
    st.error("❌ No se encontró el archivo CSV")
    st.stop()

# =========================
# CARGAR DATOS
# =========================

with st.spinner("Cargando información..."):

    df, compras, ventas, consenso = ejecutar_pipeline()

# =========================
# FILTROS
# =========================

st.sidebar.header("🎛️ Filtros")

fondos = ["Todos"] + sorted(df["Nombre Patrimonio"].unique())

fondo_seleccionado = st.sidebar.selectbox(
    "Seleccionar Fondo",
    fondos
)

if fondo_seleccionado != "Todos":

    df = df[df["Nombre Patrimonio"] == fondo_seleccionado]

    compras = compras[
        compras["Nombre Patrimonio"] == fondo_seleccionado
    ]

    ventas = ventas[
        ventas["Nombre Patrimonio"] == fondo_seleccionado
    ]

# =========================
# MÉTRICAS
# =========================

st.subheader("📌 Métricas Generales")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Movimientos",
    len(df)
)

col2.metric(
    "Compras",
    len(compras)
)

col3.metric(
    "Ventas",
    len(ventas)
)

col4.metric(
    "Activos",
    df["Nemotecnico"].nunique()
)

# =========================
# TOP COMPRAS
# =========================

st.subheader("🟢 Activos Más Comprados")

top_compras = (
    compras.groupby("Nemotecnico")["cambio_valor"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

if not top_compras.empty:

    fig_compras = px.bar(
        top_compras,
        x="Nemotecnico",
        y="cambio_valor",
        title="Top Compras"
    )

    st.plotly_chart(fig_compras, use_container_width=True)

# =========================
# TOP VENTAS
# =========================

st.subheader("🔴 Activos Más Vendidos")

top_ventas = (
    ventas.groupby("Nemotecnico")["monto_venta"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

if not top_ventas.empty:

    fig_ventas = px.bar(
        top_ventas,
        x="Nemotecnico",
        y="monto_venta",
        title="Top Ventas"
    )

    st.plotly_chart(fig_ventas, use_container_width=True)

# =========================
# CONSENSO
# =========================

st.subheader("🤝 Consenso Institucional")

col_c1, col_c2 = st.columns(2)

with col_c1:

    consenso_compra = consenso[
        consenso["tipo_movimiento"] == "COMPRA"
    ]

    consenso_compra = consenso_compra.sort_values(
        "cantidad_fondos",
        ascending=False
    ).head(10)

    if not consenso_compra.empty:

        fig_consenso_compra = px.bar(
            consenso_compra,
            x="Nemotecnico",
            y="cantidad_fondos",
            title="Consenso de Compra"
        )

        st.plotly_chart(
            fig_consenso_compra,
            use_container_width=True
        )

with col_c2:

    consenso_venta = consenso[
        consenso["tipo_movimiento"] == "VENTA"
    ]

    consenso_venta = consenso_venta.sort_values(
        "cantidad_fondos",
        ascending=False
    ).head(10)

    if not consenso_venta.empty:

        fig_consenso_venta = px.bar(
            consenso_venta,
            x="Nemotecnico",
            y="cantidad_fondos",
            title="Consenso de Venta"
        )

        st.plotly_chart(
            fig_consenso_venta,
            use_container_width=True
        )

# =========================
# FLUJO NETO
# =========================

st.subheader("💰 Flujo Neto Institucional")

flujo = (
    df.groupby("Nemotecnico")["cambio_valor"]
    .sum()
    .sort_values(ascending=False)
    .head(15)
    .reset_index()
)

fig_flujo = px.bar(
    flujo,
    x="Nemotecnico",
    y="cambio_valor",
    title="Flujo Neto"
)

st.plotly_chart(fig_flujo, use_container_width=True)

# =========================
# CONCLUSIONES
# =========================

st.subheader("🧠 Conclusiones Automáticas")

if not df.empty:

    total_compras = compras["cambio_valor"].sum()

    total_ventas = ventas["monto_venta"].sum()

    if total_compras > total_ventas:

        st.success(
            "📈 El mercado presenta una tendencia compradora."
        )

    else:

        st.error(
            "📉 El mercado presenta una tendencia vendedora."
        )

    if not top_compras.empty:

        st.info(
            f"Mayor presión compradora en: "
            f"**{top_compras.iloc[0]['Nemotecnico']}**"
        )

    if not top_ventas.empty:

        st.warning(
            f"Mayor presión vendedora en: "
            f"**{top_ventas.iloc[0]['Nemotecnico']}**"
        )

    activo_dominante = (
        df.groupby("Nemotecnico")["valor_mercado"]
        .sum()
        .sort_values(ascending=False)
    )

    if not activo_dominante.empty:

        st.write(
            f"🏆 Activo dominante del portafolio: "
            f"**{activo_dominante.index[0]}**"
        )

# =========================
# TABLAS
# =========================

st.subheader("📋 Tablas")

tab1, tab2, tab3, tab4 = st.tabs([
    "Movimientos",
    "Compras",
    "Ventas",
    "Consenso"
])

with tab1:
    st.dataframe(df, use_container_width=True)

with tab2:
    st.dataframe(compras, use_container_width=True)

with tab3:
    st.dataframe(ventas, use_container_width=True)

with tab4:
    st.dataframe(consenso, use_container_width=True)

# =========================
# EXPORTAR EXCEL
# =========================

st.subheader("📥 Exportar Reporte")

archivo = "reporte_portafolios.xlsx"

with pd.ExcelWriter(archivo) as writer:

    df.to_excel(
        writer,
        sheet_name="Movimientos",
        index=False
    )

    compras.to_excel(
        writer,
        sheet_name="Compras",
        index=False
    )

    ventas.to_excel(
        writer,
        sheet_name="Ventas",
        index=False
    )

    consenso.to_excel(
        writer,
        sheet_name="Consenso",
        index=False
    )

with open(archivo, "rb") as f:

    st.download_button(
        "⬇️ Descargar Reporte Excel",
        f,
        file_name=archivo
    )