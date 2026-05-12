import streamlit as st
import duckdb
import pandas as pd
from pathlib import Path

DATA_PATH = Path("Datos") / "Formato_351.csv"

# =========================
# PIPELINE
# =========================

@st.cache_data
def ejecutar_pipeline():

    con = duckdb.connect(database=":memory:")

    con.execute("""
        CREATE TABLE data AS 
        SELECT * FROM read_csv_auto(?);
    """, [str(DATA_PATH)])

    df = con.execute("""
        SELECT 
            "Nombre Patrimonio",
            "Nemotecnico",
            "Fecha de Corte",
            CAST(REPLACE(REPLACE("Valor_Mercado_O_Pres_Pesos", '$', ''), ',', '') AS DOUBLE) AS valor_mercado
        FROM data
        WHERE "Codigo_Moneda" = 'USD'
          AND "Nemotecnico" IS NOT NULL
          AND "Nemotecnico" != 'N/A'
          AND "Nombre Patrimonio" IS NOT NULL
    """).df()

    df = df[df["Nemotecnico"].notna()]
    df = df[df["Nemotecnico"] != "N/A"]

    df = df.sort_values(["Nombre Patrimonio", "Nemotecnico", "Fecha de Corte"])

    df["cambio_valor"] = df.groupby(
        ["Nombre Patrimonio", "Nemotecnico"]
    )["valor_mercado"].diff()

    df["tipo_movimiento"] = df["cambio_valor"].apply(
        lambda x: "COMPRA" if x > 0 else ("VENTA" if x < 0 else "SIN_CAMBIO")
    )

    df = df.dropna()

    compras = df[df["tipo_movimiento"] == "COMPRA"]
    ventas = df[df["tipo_movimiento"] == "VENTA"]

    return df, compras, ventas


# =========================
# APP
# =========================

st.set_page_config(layout="wide")

st.title("📊 Análisis de Portafolios")
st.write("Dashboard de compras, ventas y consenso entre fondos")

if not DATA_PATH.exists():
    st.error("No se encontró el archivo CSV")
    st.stop()

with st.spinner("Cargando datos..."):
    df, compras, ventas = ejecutar_pipeline()

# =========================
# MÉTRICAS
# =========================

col1, col2, col3 = st.columns(3)
col1.metric("Movimientos", len(df))
col2.metric("Compras", len(compras))
col3.metric("Ventas", len(ventas))

# =========================
# GRÁFICAS PRINCIPALES
# =========================

st.subheader("📊 Principales insights")

col_g1, col_g2 = st.columns(2)

with col_g1:
    st.write("🟢 Activos más comprados")
    top_compras = compras.groupby("Nemotecnico")["cambio_valor"].sum().sort_values(ascending=False).head(10)
    st.bar_chart(top_compras)

with col_g2:
    st.write("🔴 Activos más vendidos")
    top_ventas = ventas.groupby("Nemotecnico")["cambio_valor"].sum().abs().sort_values(ascending=False).head(10)
    st.bar_chart(top_ventas)

# =========================
# CONSENSO
# =========================

st.subheader("🤝 Consenso de inversión")

consenso = (
    df.groupby(["Nemotecnico", "tipo_movimiento"])
    .agg(
        cantidad_fondos=("Nombre Patrimonio", "nunique"),
        monto_total=("valor_mercado", "sum")
    )
    .reset_index()
)

col_c1, col_c2 = st.columns(2)

with col_c1:
    consenso_compra = consenso[consenso["tipo_movimiento"] == "COMPRA"]
    consenso_compra = consenso_compra.sort_values("cantidad_fondos", ascending=False).head(10)
    st.write("🟢 Consenso de compra")
    st.bar_chart(consenso_compra.set_index("Nemotecnico")["cantidad_fondos"])

with col_c2:
    consenso_venta = consenso[consenso["tipo_movimiento"] == "VENTA"]
    consenso_venta = consenso_venta.sort_values("cantidad_fondos", ascending=False).head(10)
    st.write("🔴 Consenso de venta")
    st.bar_chart(consenso_venta.set_index("Nemotecnico")["cantidad_fondos"])

# =========================
# CONCLUSIONES AVANZADAS
# =========================

st.subheader("🧠 Conclusiones del mercado")

if not df.empty:

    total_compras = compras["cambio_valor"].sum()
    total_ventas = ventas["cambio_valor"].sum()

    if total_compras > abs(total_ventas):
        st.success("📈 Tendencia general: mercado comprador")
    else:
        st.error("📉 Tendencia general: mercado vendedor")

    if not top_compras.empty:
        st.info(f"Mayor compra: **{top_compras.index[0]}**")

    if not top_ventas.empty:
        st.warning(f"Mayor venta: **{top_ventas.index[0]}**")

    top_valor = df.groupby("Nemotecnico")["valor_mercado"].sum().sort_values(ascending=False)

    if not top_valor.empty:
        st.write(f"Activo dominante: **{top_valor.index[0]}**")

    if not consenso_compra.empty:
        mayor_compra = consenso_compra.iloc[0]
        st.success(
            f"Consenso compra en **{mayor_compra['Nemotecnico']}** "
            f"({mayor_compra['cantidad_fondos']} fondos)"
        )

    if not consenso_venta.empty:
        mayor_venta = consenso_venta.iloc[0]
        st.error(
            f"Consenso venta en **{mayor_venta['Nemotecnico']}** "
            f"({mayor_venta['cantidad_fondos']} fondos)"
        )

    st.markdown("---")

    if not top_compras.empty and not top_ventas.empty:
        st.write(
            f"Rotación de capital desde **{top_ventas.index[0]}** hacia **{top_compras.index[0]}**"
        )

# =========================
# TABLAS
# =========================

tab1, tab2, tab3, tab4 = st.tabs(["Movimientos", "Compras", "Ventas", "Consenso"])

with tab1:
    st.dataframe(df)

with tab2:
    st.dataframe(compras)

with tab3:
    st.dataframe(ventas)

with tab4:
    st.dataframe(consenso)

# =========================
# DESCARGA
# =========================

archivo = "reporte.xlsx"

with pd.ExcelWriter(archivo) as writer:
    df.to_excel(writer, sheet_name="Movimientos", index=False)
    compras.to_excel(writer, sheet_name="Compras", index=False)
    ventas.to_excel(writer, sheet_name="Ventas", index=False)
    consenso.to_excel(writer, sheet_name="Consenso", index=False)

with open(archivo, "rb") as f:
    st.download_button("📥 Descargar Excel", f, file_name=archivo)