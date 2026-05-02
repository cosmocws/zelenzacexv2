# features/calculator/electricidad.py
import pandas as pd
import json
import os
from typing import List, Dict, Optional

# --- Cargar configuración dinámica ---
def cargar_config():
    """Carga la configuración de precios, con valores por defecto si no existe."""
    try:
        with open('data/config_precios.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return {
            'ALQUILER_CONTADOR': config.get('alquiler_contador', 0.98),
            'PACK_IBERDROLA': config.get('pack_iberdrola', 11.50),
            'DESCUENTO_PRIMERA_FACTURA': config.get('descuento_primera_factura', 5.0),
            'IMPUESTO_ELECTRICO': config.get('impuesto_electrico', 5.1127) / 100,
            'IVA': config.get('iva', 21.0) / 100,
            'PRECIO_EXCEDENTE': config.get('precio_excedente', 0.06),
        }
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            'ALQUILER_CONTADOR': 0.98,
            'PACK_IBERDROLA': 11.50,
            'DESCUENTO_PRIMERA_FACTURA': 5.0,
            'IMPUESTO_ELECTRICO': 0.051127,
            'IVA': 0.21,
            'PRECIO_EXCEDENTE': 0.06,
        }

# Colores para la tabla
COLOR_CON_PI_PAR = '#e8f5e9'
COLOR_CON_PI_IMPAR = '#c8e6c9'
COLOR_SIN_PI_PAR = '#e3f2fd'
COLOR_SIN_PI_IMPAR = '#bbdefb'


def cargar_planes_activos(usuario_campaign: str = 'CAPTA') -> pd.DataFrame:
    """Carga los planes activos según la campaña del agente."""
    try:
        df = pd.read_csv("data/precios_luz.csv", encoding='utf-8')
        # Filtrar activos y por campaña
        mascara_activo = df['activo'] == True
        mascara_campana = (df['campaña'] == usuario_campaign) | (df['campaña'] == 'TODAS')
        return df[mascara_activo & mascara_campana].copy()
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()


def calcular_coste_plan(
    plan: pd.Series,
    consumo_kwh: float,
    potencia_kw: float,
    dias: int = 30,
    tiene_pi: bool = True,
    excedente_kwh: float = 0.0
) -> Dict:
    """
    Calcula el coste total para un plan específico.
    
    Retorna un diccionario con todos los detalles del cálculo.
    """
    cfg = cargar_config()
    
    # 1. Coste del consumo
    precio_kwh = plan['con_pi_kwh'] if tiene_pi else plan['sin_pi_kwh']
    coste_consumo = consumo_kwh * precio_kwh
    
    # 2. Coste de la potencia (punta + valle)
    coste_potencia = potencia_kw * plan['total_potencia'] * dias
    
    # 3. Pack Iberdrola (solo si tiene PI)
    coste_pack = cfg['PACK_IBERDROLA'] * (dias / 30) if tiene_pi else 0.0
    
    # 4. Alquiler del contador
    coste_alquiler = cfg['ALQUILER_CONTADOR'] * (dias / 30)
    
    # 5. Subtotal
    subtotal = coste_consumo + coste_potencia + coste_pack + coste_alquiler
    
    # 5b. Restar excedentes solares (€)
    ingreso_excedentes = excedente_kwh * cfg['PRECIO_EXCEDENTE']
    subtotal = max(0, subtotal - ingreso_excedentes)
    
    # 6. Impuesto eléctrico
    impuesto = subtotal * cfg['IMPUESTO_ELECTRICO']
    
    # 7. IVA
    iva = (subtotal + impuesto) * cfg['IVA']
    
    # 8. Total bruto
    total_bruto = subtotal + impuesto + iva
    
    # 9. Descuento primera factura
    total_neto = total_bruto - cfg['DESCUENTO_PRIMERA_FACTURA']
    
    # 10. Mensualizar (aproximado)
    coste_mensual = total_neto
    
    return {
        'coste_total': round(total_neto, 2),
        'coste_mensual': round(coste_mensual, 2),
        'desglose': {
            'consumo': round(coste_consumo, 2),
            'potencia': round(coste_potencia, 2),
            'pack_iberdrola': round(coste_pack, 2),
            'alquiler': round(coste_alquiler, 2),
            'excedentes': round(ingreso_excedentes, 2),
            'impuesto': round(impuesto, 2),
            'iva': round(iva, 2),
            'descuento': cfg['DESCUENTO_PRIMERA_FACTURA']
        }
    }


def calcular_ahorro(coste_actual: float, coste_nuevo: float) -> float:
    """Calcula el ahorro (positivo = ahorro, negativo = pagas más)."""
    return round(coste_actual - coste_nuevo, 2)


def comparar_planes(
    consumo_kwh: float,
    potencia_kw: float,
    coste_actual: float,
    dias: int = 30,
    campana: str = 'CAPTA',
    excedente_kwh: float = 0.0
) -> List[Dict]:
    """
    Función PRINCIPAL. Compara todos los planes activos y devuelve
    una lista ordenada lista para mostrar en la UI del agente.
    
    Returns:
        Lista de diccionarios ordenados: PRIMERO CON PI, LUEGO SIN PI.
        Dentro de cada grupo, ordenado por ahorro (mayor primero).
    """
    df_planes = cargar_planes_activos(campana)
    
    if df_planes.empty:
        return []
    
    resultados_con_pi = []
    resultados_sin_pi = []
    
    for _, plan in df_planes.iterrows():
        # Calcular CON Pack Iberdrola
        coste_con = calcular_coste_plan(plan, consumo_kwh, potencia_kw, dias, tiene_pi=True, excedente_kwh=excedente_kwh)
        ahorro_con = calcular_ahorro(coste_actual, coste_con['coste_mensual'])
        
        resultados_con_pi.append({
            'plan': plan['plan'],
            'tiene_pi': True,
            'pack_iberdrola': '✅ CON',
            'precio_kwh': plan['con_pi_kwh'],
            'coste_nuevo': coste_con['coste_mensual'],
            'ahorro_mensual': ahorro_con,
            'ahorro_anual': round(ahorro_con * 12, 2),
            'ahorra': ahorro_con > 0,
            'aviso_agente': plan.get('aviso_agente', ''),
            'desglose': coste_con['desglose']
        })
        
        # Calcular SIN Pack Iberdrola
        coste_sin = calcular_coste_plan(plan, consumo_kwh, potencia_kw, dias, tiene_pi=False, excedente_kwh=excedente_kwh)
        ahorro_sin = calcular_ahorro(coste_actual, coste_sin['coste_mensual'])
        
        resultados_sin_pi.append({
            'plan': plan['plan'],
            'tiene_pi': False,
            'pack_iberdrola': '❌ SIN',
            'precio_kwh': plan['sin_pi_kwh'],
            'coste_nuevo': coste_sin['coste_mensual'],
            'ahorro_mensual': ahorro_sin,
            'ahorro_anual': round(ahorro_sin * 12, 2),
            'ahorra': ahorro_sin > 0,
            'aviso_agente': plan.get('aviso_agente', ''),
            'desglose': coste_sin['desglose']
        })
    
    # Ordenar: primero por ahorro (mayor a menor)
    resultados_con_pi.sort(key=lambda x: x['ahorro_mensual'], reverse=True)
    resultados_sin_pi.sort(key=lambda x: x['ahorro_mensual'], reverse=True)
    
    # Unir: primero CON PI, luego SIN PI
    return resultados_con_pi + resultados_sin_pi


def colorear_fila_por_tipo(tiene_pi: bool, indice: int) -> str:
    """Devuelve el color CSS según si es CON PI o SIN PI y el índice (para alternar)."""
    if tiene_pi:
        return COLOR_CON_PI_PAR if indice % 2 == 0 else COLOR_CON_PI_IMPAR
    else:
        return COLOR_SIN_PI_PAR if indice % 2 == 0 else COLOR_SIN_PI_IMPAR
