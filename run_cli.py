#!/usr/bin/env python
"""Ejecutor del pipeline de análisis de portafolios en modo CLI."""

import sys
import os
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

# Importar las funciones del pipeline
from proyecto_st import (
    DATA_PATH,
    pipeline_analisis_portafolios,
)

def main():
    """Función principal para ejecutar el pipeline en modo consola."""
    print("\n" + "="*80)
    print("ANÁLISIS DE PORTAFOLIOS CON DUCKDB")
    print("="*80)
    
    if not DATA_PATH.exists():
        print(f"❌ Error: No se encontró el archivo de datos: {DATA_PATH}")
        return
    
    try:
        print("\n[*] Ejecutando pipeline...")
        con, resultados, excel_buffer = pipeline_analisis_portafolios()
        
        print("\n[OK] Pipeline completado exitosamente!")
        print(f"\n[STATS] ESTADISTICAS:")
        print(f"  • Registros en BRONZE: {resultados['bronze']:,}")
        print(f"  • Movimientos en SILVER: {resultados['silver']:,}")
        print(f"  • Senales de COMPRA: {resultados['compras']:,}")
        print(f"  • Senales de VENTA: {resultados['ventas']:,}")
        
        print(f"\n[DATA] MUESTRAS DE RESULTADOS:")
        
        # Movimientos significativos
        print(f"\n  [1] Movimientos Significativos (primeros 3)")
        movimientos = con.execute("SELECT * FROM gold.movimientos_significativos LIMIT 3").fetchall()
        for row in movimientos:
            print(f"     {row}")
        
        # Compras
        print(f"\n  [2] Top 3 Compras")
        compras = con.execute("SELECT * FROM gold.compras LIMIT 3").fetchall()
        for row in compras:
            print(f"     {row}")
        
        # Ventas
        print(f"\n  [3] Top 3 Ventas")
        ventas = con.execute("SELECT * FROM gold.ventas LIMIT 3").fetchall()
        for row in ventas:
            print(f"     {row}")
        
        # Consenso
        print(f"\n  [4] Top 3 Consenso de Inversion")
        consenso = con.execute("SELECT * FROM gold.consenso_inversion LIMIT 3").fetchall()
        for row in consenso:
            print(f"     {row}")
        
        print("\n" + "="*80)
        print("[SUCCESS] Analisis completado. Los datos estan listos en DuckDB.")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n[ERROR] Error durante la ejecucion: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
