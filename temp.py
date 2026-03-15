import pandas as pd

# Rutas
ruta_hist = r"Datos\Formato_351.csv"
ruta_enero = r"Datos\2026_1portainvdeta.xls"
ruta_febrero = r"Datos\2026_2portainvdeta.xls"
ruta_reporte = r"Datos\Reporte_Movimientos_AFP.xlsx"


# ================================
# Lectura de datos
# ================================

cols_hist = [
    "Nombre de Entidad",
    "Fecha de Corte",
    "Nombre Patrimonio",
    "Razon_Social_Emisor",
    "Nemotecnico",
    "Codigo_Moneda",
    "Pais_Emisor",
    "Valor_Mercado_O_Pres_Pesos"
]

df_hist = pd.read_csv(
    ruta_hist,
    usecols=cols_hist,
    encoding="latin1",
    low_memory=False
)

df_hist = df_hist.rename(columns={
    "Valor_Mercado_O_Pres_Pesos": "Valor_Mercado"
})


cols_excel = [
    "Nombre de Entidad",
    "Fecha de Corte",
    "Nombre Patrimonio",
    "Razon Social Emisor",
    "Nemotecnico",
    "Código Moneda",
    "Pais_Emisor",
    "Vr. mercado o Vr presente en $"
]


def cargar_excel(ruta):

    df = pd.read_excel(
        ruta,
        sheet_name="Formato_351",
        usecols=cols_excel
    )

    df = df.rename(columns={
        "Razon Social Emisor": "Razon_Social_Emisor",
        "Código Moneda": "Codigo_Moneda",
        "Vr. mercado o Vr presente en $": "Valor_Mercado"
    })

    return df


df_enero = cargar_excel(ruta_enero)
df_febrero = cargar_excel(ruta_febrero)

df = pd.concat([df_hist, df_enero, df_febrero], ignore_index=True)

print("Observaciones totales:", df.shape[0])


# ================================
# Limpieza
# ================================

df["Fecha de Corte"] = pd.to_datetime(df["Fecha de Corte"])

df["Valor_Mercado"] = (
    df["Valor_Mercado"]
    .astype(str)
    .str.replace("$", "", regex=False)
    .str.replace(",", "", regex=False)
)

df["Valor_Mercado"] = pd.to_numeric(df["Valor_Mercado"], errors="coerce")

df = df.dropna(subset=["Nemotecnico", "Valor_Mercado"])

df = df[df["Codigo_Moneda"] == "USD"]

print("Observaciones en USD:", df.shape[0])


# ================================
# Construcción de posiciones
# ================================

df = (
    df.groupby(
        [
            "Nombre de Entidad",
            "Nombre Patrimonio",
            "Nemotecnico",
            "Fecha de Corte"
        ]
    )["Valor_Mercado"]
    .sum()
    .reset_index()
)

df = df.sort_values(
    [
        "Nombre de Entidad",
        "Nombre Patrimonio",
        "Nemotecnico",
        "Fecha de Corte"
    ]
)


df["Valor_Portafolio"] = df.groupby(
    ["Nombre de Entidad", "Nombre Patrimonio", "Fecha de Corte"]
)["Valor_Mercado"].transform("sum")

df["Peso"] = df["Valor_Mercado"] / df["Valor_Portafolio"]


# ================================
# Cambios en posiciones
# ================================

df["Cambio_Peso"] = df.groupby(
    ["Nombre de Entidad", "Nombre Patrimonio", "Nemotecnico"]
)["Peso"].diff()

df["Cambio_Valor"] = df.groupby(
    ["Nombre de Entidad", "Nombre Patrimonio", "Nemotecnico"]
)["Valor_Mercado"].diff()

df["Tipo_Movimiento"] = df["Cambio_Valor"].apply(
    lambda x: "COMPRA" if x > 0 else "VENTA"
)


umbral = 0.01

movimientos = df[df["Cambio_Peso"].abs() > umbral].copy()

movimientos = movimientos.sort_values(
    "Cambio_Peso",
    key=abs,
    ascending=False
)


reporte = movimientos[
    [
        "Nombre de Entidad",
        "Nombre Patrimonio",
        "Nemotecnico",
        "Fecha de Corte",
        "Valor_Mercado",
        "Valor_Portafolio",
        "Peso",
        "Cambio_Peso",
        "Cambio_Valor",
        "Tipo_Movimiento"
    ]
]


compras = reporte[reporte["Tipo_Movimiento"] == "COMPRA"]
ventas = reporte[reporte["Tipo_Movimiento"] == "VENTA"]


# ================================
# Exportar reporte
# ================================

with pd.ExcelWriter(ruta_reporte, engine="xlsxwriter") as writer:

    reporte.to_excel(writer, sheet_name="Movimientos", index=False)
    compras.to_excel(writer, sheet_name="Compras", index=False)
    ventas.to_excel(writer, sheet_name="Ventas", index=False)

    workbook = writer.book

    header = workbook.add_format({
        "bold": True,
        "align": "center",
        "border": 1,
        "bg_color": "#E7E6E6"
    })

    money = workbook.add_format({
        "num_format": "$#,##0",
        "border": 1
    })

    percent = workbook.add_format({
        "num_format": "0.00%",
        "border": 1
    })

    text = workbook.add_format({"border": 1})

    def formato(nombre, df):

        ws = writer.sheets[nombre]

        for i, col in enumerate(df.columns):
            ws.write(0, i, col, header)

        ws.set_column("A:A", 22, text)
        ws.set_column("B:B", 30, text)
        ws.set_column("C:C", 12, text)
        ws.set_column("D:D", 14, text)

        ws.set_column("E:E", 18, money)
        ws.set_column("F:F", 18, money)

        ws.set_column("G:G", 12, percent)
        ws.set_column("H:H", 12, percent)

        ws.set_column("I:I", 18, money)
        ws.set_column("J:J", 14, text)

        ws.freeze_panes(1, 0)
        ws.autofilter(0, 0, len(df), len(df.columns) - 1)

    formato("Movimientos", reporte)
    formato("Compras", compras)
    formato("Ventas", ventas)


print("Reporte generado.")
print(ruta_reporte)