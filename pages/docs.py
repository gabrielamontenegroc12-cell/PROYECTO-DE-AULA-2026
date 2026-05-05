import streamlit as st
import duckdb
import pandas as pd
from pathlib import Path

# =========================
# CONFIGURACIÓN
# =========================

DATA_PATH = Path("Datos") / "Formato_351.csv"
EXCEL_PATH = "reporte_duckdb.xlsx"


# =========================
# FUNCIONES PIPELINE
# =========================

def crear_conexion_esquemas():
    con = duckdb.connect(database=":memory:")
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")
    con.execute("CREATE SCHEMA IF NOT EXISTS silver;")
    con.execute("CREATE SCHEMA IF NOT EXISTS gold;")
    return con


def cargar_datos_bronze(con):
    con.execute(
        """
        CREATE TABLE bronze.formato_351 AS 
        SELECT * FROM read_csv_auto(?);
        """,
        [str(DATA_PATH)]
    )
    return con


def procesar_datos_silver(con):
    con.execute("""
        CREATE TABLE silver.formato_351 AS 
        SELECT 
            "Nombre de Entidad",
            "Nombre Patrimonio",
            "Nemotecnico",
            "Razon_Social_Emisor",
            "Fecha de Corte",
            CAST(
                REPLACE(REPLACE("Valor_Mercado_O_Pres_Pesos", '$', ''), ',', '') 
                AS DOUBLE
            ) AS valor_mercado_limpio,
            "Codigo_Moneda",
            "Pais_Emisor"
        FROM bronze.formato_351 
        WHERE "Nombre Patrimonio" IS NOT NULL
            AND "Nemotecnico" IS NOT NULL
            AND "Nemotecnico" != 'N/A'
            AND "Valor_Mercado_O_Pres_Pesos" IS NOT NULL
            AND CAST(
                REPLACE(REPLACE("Valor_Mercado_O_Pres_Pesos", '$', ''), ',', '') 
                AS DOUBLE
            ) > 0
            AND "Codigo_Moneda" = 'USD';
    """)
    return con


def agregar_posiciones_silver(con):
    con.execute("""
        CREATE TABLE silver.posiciones AS 
        SELECT 
            "Nombre de Entidad",
            "Nombre Patrimonio",
            "Nemotecnico",
            "Fecha de Corte",
            SUM(valor_mercado_limpio) AS valor_mercado
        FROM silver.formato_351
        GROUP BY 
            "Nombre de Entidad",
            "Nombre Patrimonio",
            "Nemotecnico",
            "Fecha de Corte";
    """)
    return con


def calcular_pesos_silver(con):
    con.execute("""
        CREATE TABLE silver.posiciones_con_pesos AS 
        SELECT 
            "Nombre de Entidad",
            "Nombre Patrimonio",
            "Nemotecnico",
            "Fecha de Corte",
            valor_mercado,
            SUM(valor_mercado) OVER (
                PARTITION BY "Nombre de Entidad", "Nombre Patrimonio", "Fecha de Corte"
            ) AS valor_portafolio,
            ROUND(
                valor_mercado / SUM(valor_mercado) OVER (
                    PARTITION BY "Nombre de Entidad", "Nombre Patrimonio", "Fecha de Corte"
                ), 
                4
            ) AS peso
        FROM silver.posiciones;
    """)
    return con


def calcular_movimientos_silver(con):
    con.execute("""
        CREATE TABLE silver.movimientos AS 
        SELECT 
            "Nombre de Entidad",
            "Nombre Patrimonio",
            "Nemotecnico",
            "Fecha de Corte",
            valor_mercado,
            valor_portafolio,
            peso,
            LAG(peso) OVER (
                PARTITION BY "Nombre de Entidad", "Nombre Patrimonio", "Nemotecnico"
                ORDER BY "Fecha de Corte"
            ) AS peso_anterior,
            ROUND(
                peso - LAG(peso) OVER (
                    PARTITION BY "Nombre de Entidad", "Nombre Patrimonio", "Nemotecnico"
                    ORDER BY "Fecha de Corte"
                ), 
                4
            ) AS cambio_peso,
            ROUND(
                valor_mercado - LAG(valor_mercado) OVER (
                    PARTITION BY "Nombre de Entidad", "Nombre Patrimonio", "Nemotecnico"
                    ORDER BY "Fecha de Corte"
                ), 
                2
            ) AS cambio_valor,
            CASE 
                WHEN valor_mercado - LAG(valor_mercado) OVER (
                    PARTITION BY "Nombre de Entidad", "Nombre Patrimonio", "Nemotecnico"
                    ORDER BY "Fecha de Corte"
                ) > 0 THEN 'COMPRA'

                WHEN valor_mercado - LAG(valor_mercado) OVER (
                    PARTITION BY "Nombre de Entidad", "Nombre Patrimonio", "Nemotecnico"
                    ORDER BY "Fecha de Corte"
                ) < 0 THEN 'VENTA'

                ELSE 'SIN_CAMBIO'
            END AS tipo_movimiento
        FROM silver.posiciones_con_pesos;
    """)
    return con


def filtrar_movimientos_gold(con):
    con.execute("""
        CREATE TABLE gold.movimientos_significativos AS 
        SELECT 
            "Nombre de Entidad",
            "Nombre Patrimonio",
            "Nemotecnico",
            "Fecha de Corte",
            valor_mercado,
            valor_portafolio,
            peso,
            peso_anterior,
            cambio_peso,
            cambio_valor,
            tipo_movimiento
        FROM silver.movimientos
        WHERE cambio_peso IS NOT NULL
            AND ABS(cambio_peso) > 0.01
            AND tipo_movimiento != 'SIN_CAMBIO'
        ORDER BY ABS(cambio_peso) DESC;
    """)
    return con


def crear_reportes_gold(con):
    con.execute("""
        CREATE TABLE gold.compras AS 
        SELECT *
        FROM gold.movimientos_significativos
        WHERE tipo_movimiento = 'COMPRA'
        ORDER BY cambio_valor DESC;
    """)

    con.execute("""
        CREATE TABLE gold.ventas AS 
        SELECT *
        FROM gold.movimientos_significativos
        WHERE tipo_movimiento = 'VENTA'
        ORDER BY ABS(cambio_valor) DESC;
    """)

    return con


def crear_consenso_gold(con):
    con.execute("""
        CREATE TABLE gold.consenso_inversion AS 
        SELECT 
            m."Nemotecnico",
            f."Razon_Social_Emisor",
            m.tipo_movimiento,
            COUNT(DISTINCT m."Nombre Patrimonio") AS cantidad_fondos,
            COUNT(*) AS total_movimientos,
            ROUND(AVG(m.valor_mercado), 2) AS promedio_inversion,
            ROUND(SUM(m.valor_mercado), 2) AS monto_total_invertido
        FROM silver.movimientos m
        LEFT JOIN silver.formato_351 f
            ON m."Nemotecnico" = f."Nemotecnico"
        WHERE m.tipo_movimiento IN ('COMPRA', 'VENTA')
        GROUP BY 
            m."Nemotecnico",
            f."Razon_Social_Emisor",
            m.tipo_movimiento
        ORDER BY monto_total_invertido DESC;
    """)
    return con


def verificar_resultados(con):
    resultados = {
        "bronze": con.execute("SELECT COUNT(*) FROM bronze.formato_351").fetchone()[0],
        "silver": con.execute("SELECT COUNT(*) FROM silver.movimientos WHERE cambio_peso IS NOT NULL").fetchone()[0],
        "compras": con.execute("SELECT COUNT(*) FROM gold.compras").fetchone()[0],
        "ventas": con.execute("SELECT COUNT(*) FROM gold.ventas").fetchone()[0],
    }
    return resultados


def exportar_excel(con):
    movimientos_df = con.execute("SELECT * FROM gold.movimientos_significativos").df()
    compras_df = con.execute("SELECT * FROM gold.compras").df()
    ventas_df = con.execute("SELECT * FROM gold.ventas").df()
    consenso_df = con.execute("SELECT * FROM gold.consenso_inversion").df()

    with pd.ExcelWriter(EXCEL_PATH, engine="xlsxwriter") as writer:
        movimientos_df.to_excel(writer, sheet_name="Movimientos", index=False)
        compras_df.to_excel(writer, sheet_name="Compras", index=False)
        ventas_df.to_excel(writer, sheet_name="Ventas", index=False)
        consenso_df.to_excel(writer, sheet_name="Consenso", index=False)

    return EXCEL_PATH


def ejecutar_pipeline():
    con = crear_conexion_esquemas()
    cargar_datos_bronze(con)
    procesar_datos_silver(con)
    agregar_posiciones_silver(con)
    calcular_pesos_silver(con)
    calcular_movimientos_silver(con)
    filtrar_movimientos_gold(con)
    crear_reportes_gold(con)
    crear_consenso_gold(con)

    resultados = verificar_resultados(con)
    archivo_excel = exportar_excel(con)

    return con, resultados, archivo_excel


# =========================
# STREAMLIT APP
# =========================

st.set_page_config(
    page_title="Análisis de Portafolios",
    layout="wide"
)

st.title("📊 Análisis de Portafolios con DuckDB")
st.write("Pipeline Bronze → Silver → Gold con exportación automática a Excel.")

if not DATA_PATH.exists():
    st.error(f"No se encontró el archivo: {DATA_PATH}")
    st.stop()

if st.button("Ejecutar Pipeline"):
    with st.spinner("Ejecutando análisis..."):
        con, resultados, archivo_excel = ejecutar_pipeline()

    st.success("Pipeline ejecutado correctamente.")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Registros Bronze", resultados["bronze"])
    col2.metric("Movimientos Silver", resultados["silver"])
    col3.metric("Compras Gold", resultados["compras"])
    col4.metric("Ventas Gold", resultados["ventas"])

    st.subheader("Movimientos Significativos")
    movimientos_df = con.execute("SELECT * FROM gold.movimientos_significativos").df()
    st.dataframe(movimientos_df, use_container_width=True)

    st.subheader("Compras")
    compras_df = con.execute("SELECT * FROM gold.compras").df()
    st.dataframe(compras_df, use_container_width=True)

    st.subheader("Ventas")
    ventas_df = con.execute("SELECT * FROM gold.ventas").df()
    st.dataframe(ventas_df, use_container_width=True)

    st.subheader("Consenso de Inversión")
    consenso_df = con.execute("SELECT * FROM gold.consenso_inversion").df()
    st.dataframe(consenso_df, use_container_width=True)

    with open(archivo_excel, "rb") as file:
        st.download_button(
            label="📥 Descargar Reporte Excel",
            data=file,
            file_name="reporte_duckdb.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )