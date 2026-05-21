import streamlit as st

# =========================
# CONFIGURACIÓN
# =========================

st.set_page_config(
    page_title="MSFI - Modelo de Señales de Flujo Institucional",
    layout="wide"
)

# =========================
# TÍTULO PRINCIPAL
# =========================

st.title("📊 Modelo de Señales de Flujo Institucional (MSFI)")

st.markdown("""
Sistema de análisis institucional basado en el Formato 351 de la 
Superintendencia Financiera de Colombia.
""")

st.markdown("---")

# =========================
# INTRODUCCIÓN
# =========================

st.header("Introducción")

st.write("""
Este proyecto consiste en el desarrollo de un dashboard financiero interactivo 
llamado Modelo de Señales de Flujo Institucional (MSFI), cuyo objetivo es 
analizar el comportamiento de inversión de fondos institucionales utilizando 
información histórica del Formato 351 de la Superintendencia Financiera de Colombia.
""")

# =========================
# FORMATO 351
# =========================

st.header("¿Qué es el Formato 351?")

st.write("""
El Formato 351 corresponde a la composición del portafolio de inversiones 
reportado mensualmente por entidades financieras a la Superintendencia 
Financiera de Colombia.
""")

st.write("""
Este formato contiene información sobre:
""")

st.markdown("""
- Activos financieros
- Valor de mercado
- Fondos de inversión
- Monedas
- Posiciones de portafolios institucionales
""")

# =========================
# DATOS UTILIZADOS
# =========================

st.header("Datos Utilizados")

st.write("""
Para este proyecto se trabajó con datos históricos mensuales desde el año 
2016 hasta el 2025, permitiendo analizar cómo evolucionan las decisiones 
de inversión de los fondos a lo largo del tiempo.
""")

# =========================
# IDEA PRINCIPAL
# =========================

st.header("Idea Principal del Modelo")

st.write("""
La idea principal del modelo es aprovechar la inteligencia colectiva de los 
fondos institucionales, siguiendo sus decisiones de compra y venta para 
identificar señales relevantes del mercado.
""")

# =========================
# TECNOLOGÍAS
# =========================

st.header("Tecnologías Utilizadas")

st.markdown("""
- Python como lenguaje principal
- Streamlit para construir el dashboard interactivo
- Pandas para manipulación de datos
- DuckDB para procesamiento eficiente
- Plotly para gráficas interactivas
- Prefect para automatización del pipeline ETL
""")

# =========================
# ETL
# =========================

st.header("Proceso ETL del Proyecto")

st.write("""
El proyecto sigue una arquitectura ETL tipo Bronze, Silver y Gold.
""")

# =========================
# BRONZE
# =========================

st.subheader("Datos Bronze")

st.write("""
Se trabajó inicialmente con datos crudos provenientes de la 
Superintendencia Financiera.
""")

st.markdown("""
- Renta fija
- Renta variable
- Monedas
- Movimientos completos de portafolios
""")

# =========================
# SILVER
# =========================

st.subheader("Datos Silver")

st.write("""
Luego se realizó limpieza y filtrado especializado:
""")

st.markdown("""
- Eliminación de ruido
- Validación de datos
- Filtrado de renta variable en USD
- Clasificación de compras y ventas
""")

# =========================
# GOLD
# =========================

st.subheader("Datos Gold")

st.write("""
Finalmente se construyeron señales de inversión:
""")

st.markdown("""
- Consenso entre fondos
- Rankings institucionales
- Flujo neto institucional
- Señales de compra y venta
""")

# =========================
# QUÉ HACE EL CÓDIGO
# =========================

st.header("¿Qué hace el código?")

# -------------------------

st.subheader("1. Carga y limpieza de datos")

st.write("""
El código carga el archivo del Formato 351 y realiza limpieza de datos 
para eliminar valores nulos y registros inválidos.
""")

# -------------------------

st.subheader("2. Organización de información")

st.write("""
Después organiza la información por:
""")

st.markdown("""
- Fondo
- Activo
- Fecha
""")

# -------------------------

st.subheader("3. Cálculo de movimientos")

st.write("""
El sistema compara los valores entre períodos para identificar cambios 
en posiciones.
""")

# -------------------------

st.subheader("4. Clasificación de movimientos")

st.write("""
Los movimientos se clasifican automáticamente en:
""")

st.markdown("""
- Compras
- Ventas
- Sin cambios
""")

# -------------------------

st.subheader("5. Construcción del dashboard")

st.write("""
Finalmente se generan:
""")

st.markdown("""
- Métricas
- Gráficas
- Tablas
- Conclusiones automáticas
- Exportación de reportes
""")

# =========================
# FILTROS
# =========================

st.header("Filtros Interactivos")

st.write("""
El dashboard permite seleccionar un fondo específico o analizar todos 
los fondos al mismo tiempo.
""")

st.write("""
Esto permite realizar análisis personalizados para cada portafolio institucional.
""")

# =========================
# MÉTRICAS
# =========================

st.header("Métricas Generales")

st.subheader("Movimientos")

st.write("""
Muestra la cantidad total de cambios detectados.
""")

# -------------------------

st.subheader("Compras")

st.write("""
Cantidad de movimientos donde aumentaron posiciones.
""")

# -------------------------

st.subheader("Ventas")

st.write("""
Cantidad de movimientos donde disminuyeron posiciones.
""")

# -------------------------

st.subheader("Activos")

st.write("""
Número total de activos analizados.
""")

# =========================
# GRÁFICAS
# =========================

st.header("Activos Más Comprados")

st.write("""
Esta gráfica muestra los activos que recibieron mayor entrada 
de capital institucional.
""")

# -------------------------

st.header("Activos Más Vendidos")

st.write("""
Muestra los activos con mayor salida de capital.
""")

# -------------------------

st.header("Flujo Neto Institucional")

st.write("""
Esta gráfica muestra el balance entre compras y ventas para identificar 
tendencias del mercado.
""")

# -------------------------

st.header("Consenso Institucional")

st.write("""
El consenso identifica cuando varios fondos realizan el mismo movimiento 
sobre un activo.
""")

# =========================
# CONCLUSIONES
# =========================

st.header("Conclusiones Automáticas")

st.write("""
El sistema genera interpretaciones automáticas sobre:
""")

st.markdown("""
- Tendencia del mercado
- Activos dominantes
- Presión compradora o vendedora
""")

# =========================
# EXPORTACIÓN
# =========================

st.header("Exportación")

st.write("""
El dashboard permite descargar automáticamente un reporte en Excel 
con toda la información procesada.
""")

# =========================
# CONCLUSIÓN FINAL
# =========================

st.header("Conclusión Final")

st.write("""
En conclusión, este proyecto transforma datos históricos del Formato 351 
en señales de inversión útiles, permitiendo analizar el comportamiento 
institucional y apoyar la toma de decisiones en el mercado de capitales.
""")