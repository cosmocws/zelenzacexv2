# core/monitorizaciones.py
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# =============================================
# PUNTOS CLAVE DISPONIBLES
# =============================================
OPCIONES_PUNTOS_CLAVE = [
    "LOPD", "Comunicación", "Cierre de venta", "Argumentación", 
    "Resolución objeciones", "Proceso venta", "Escucha activa", "Tono",
    "Estructura", "Detección", "Habilidades venta", "Verificación", "Otros",
    "Actitud", "Sondeo", "Oportunidad venta", "Resumen beneficios",
    "Gestión BBDD", "Textos legales",
    "Argumentación ¡CUIDADO!", "Textos legales ¡CUIDADO!",
    "LOPD ¡CUIDADO!", "Sondeo ¡CUIDADO!", "Gestión BBDD ¡CUIDADO!"
]

# =============================================
# CARGA/GUARDADO
# =============================================

def cargar_monitorizaciones() -> Dict:
    """Carga todas las monitorizaciones."""
    try:
        with open('data/monitorizaciones.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def guardar_monitorizaciones(datos: Dict):
    """Guarda las monitorizaciones."""
    os.makedirs('data', exist_ok=True)
    with open('data/monitorizaciones.json', 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

def obtener_ultima_monitorizacion(id_empleado: str) -> Optional[Dict]:
    todas = cargar_monitorizaciones()
    monitorizaciones_agente = []
    
    for id_mon, mon in todas.items():
        if mon.get('id_empleado') == id_empleado or mon.get('username') == id_empleado:
            monitorizaciones_agente.append(mon)
    
    if not monitorizaciones_agente:
        return None
    
    monitorizaciones_agente.sort(key=lambda x: x.get('fecha_monitorizacion', ''), reverse=True)
    return monitorizaciones_agente[0]

def obtener_monitorizaciones_empleado(id_empleado: str) -> List[Dict]:
    """Obtiene todas las monitorizaciones de un agente."""
    todas = cargar_monitorizaciones()
    resultado = []
    for id_mon, mon in todas.items():
        if mon.get('id_empleado') == id_empleado or mon.get('username') == id_empleado:
            resultado.append(mon)
    resultado.sort(key=lambda x: x.get('fecha_monitorizacion', ''), reverse=True)
    return resultado

def guardar_monitorizacion(datos: Dict, supervisor_id: str) -> str:
    """Guarda una nueva monitorización y devuelve su ID."""
    todas = cargar_monitorizaciones()
    
    # Generar ID único
    ahora = datetime.now().strftime('%Y%m%d%H%M%S')
    id_empleado = datos.get('id_empleado', '0000')
    id_mon = f"MON_{ahora}_{id_empleado}"
    
    # Añadir metadata
    datos['supervisor_id'] = supervisor_id
    datos['fecha_creacion'] = datetime.now().isoformat()
    datos['id_monitorizacion'] = id_mon
    
    # Asegurar campos numéricos
    campos_numericos = ['nota_global', 'objetivo', 'experiencia', 'comunicacion',
                       'deteccion', 'habilidades_venta', 'resolucion_objeciones', 'cierre_contacto']
    for campo in campos_numericos:
        if campo in datos:
            try:
                datos[campo] = float(datos[campo])
            except:
                datos[campo] = 0.0
    
    # Asegurar listas
    if 'puntos_clave' not in datos or not isinstance(datos['puntos_clave'], list):
        datos['puntos_clave'] = []
    if 'objetivos_7d' not in datos or not isinstance(datos['objetivos_7d'], dict):
        datos['objetivos_7d'] = {
            'ventas': 0,
            'llamadas_5m': 0,
            'llamadas_15m': 0,
            'otros': ''
        }
    
    todas[id_mon] = datos
    guardar_monitorizaciones(todas)
    from core.github_sync import sync_archivo
    sync_archivo("data/monitorizaciones.json")
    return id_mon

# =============================================
# EXTRACCIÓN DE PDF
# =============================================

def analizar_pdf_monitorizacion(uploaded_file) -> Dict[str, Any]:
    """Extrae datos de un PDF de monitorización."""
    try:
        import fitz
        
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        texto_completo = ""
        for page in range(len(doc)):
            texto_completo += doc.load_page(page).get_text() + "\n"
        doc.close()
        
        if not texto_completo.strip():
            return _datos_vacios()
        
        return _analizar_texto(texto_completo)
    
    except ImportError:
        return _datos_vacios()
    except Exception:
        return _datos_vacios()

def _datos_vacios() -> Dict:
    """Estructura vacía de monitorización."""
    return {
        'id_empleado': '',
        'fecha_monitorizacion': datetime.now().strftime('%Y-%m-%d'),
        'fecha_proxima_monitorizacion': '',
        'nota_global': 0.0,
        'objetivo': 85.0,
        'experiencia': 0.0,
        'comunicacion': 0.0,
        'deteccion': 0.0,
        'habilidades_venta': 0.0,
        'resolucion_objeciones': 0.0,
        'cierre_contacto': 0.0,
        'feedback': '',
        'plan_accion': '',
        'puntos_clave': [],
        'objetivos_7d': {'ventas': 0, 'llamadas_5m': 0, 'llamadas_15m': 0, 'otros': ''}
    }

def _analizar_texto(texto: str) -> Dict:
    """Analiza texto extraído del PDF."""
    datos = _datos_vacios()
    texto_upper = texto.upper()
    
    # ID Empleado
    match = re.search(r'ID\s*EMPLEADO\s*(\d+)', texto_upper)
    if match:
        datos['id_empleado'] = match.group(1)
    
    # Fecha
    match = re.search(r'FECHA\s*MONITORIZACI[OÓ]N\s*(\d+)[-/](\d+)', texto_upper)
    if match:
        dia, mes = int(match.group(1)), int(match.group(2))
        año = datetime.now().year
        if mes > datetime.now().month:
            año -= 1
        datos['fecha_monitorizacion'] = f"{año:04d}-{mes:02d}-{dia:02d}"
    
    # Nota global
    match = re.search(r'NOTA\s*GLOBAL\s*([\d,]+)%', texto)
    if match:
        try:
            datos['nota_global'] = float(match.group(1).replace(',', '.'))
        except:
            pass
    
    # Objetivo
    match = re.search(r'OBJETIVO\s*(\d+)%', texto_upper)
    if match:
        datos['objetivo'] = float(match.group(1))
    
    # Puntuaciones
    patrones = {
        'experiencia': r'1\.\s*EXPERIENCIA\s*([\d,]+)%',
        'comunicacion': r'1\.1\.\s*COMUNICACI[OÓ]N\s*(\d+)%',
        'deteccion': r'2\.1\s*DETECCI[OÓ]N\s*(\d+)%',
        'habilidades_venta': r'2\.2\s*HABILIDADES\s*DE\s*VENTA\s*(\d+)%',
        'resolucion_objeciones': r'2\.3\s*RESOLUCI[OÓ]N\s*DE\s*OBJECIONES\s*(\d+)%',
        'cierre_contacto': r'2\.4\s*CIERRE\s*DE\s*CONTACTO\s*(\d+)%'
    }
    
    for campo, patron in patrones.items():
        match = re.search(patron, texto)
        if match:
            try:
                datos[campo] = float(match.group(1).replace(',', '.'))
            except:
                pass
    
    # Puntos clave
    datos['puntos_clave'] = _detectar_puntos_clave(texto)
    
    # Separar feedback y plan de acción
    if 'FECHA Y FIRMA' in texto:
        partes = texto.split('FECHA Y FIRMA', 1)
        if len(partes) > 1:
            resto = partes[1].strip()
            # Intentar separar por "Plan de acción" o similar
            if 'Plan de acción' in resto or 'PLAN DE ACCIÓN' in resto.upper():
                sep = re.split(r'Plan de acci[oó]n', resto, flags=re.IGNORECASE)
                datos['feedback'] = sep[0].strip()[:2000]
                datos['plan_accion'] = ('Plan de acción ' + sep[1]).strip()[:2000] if len(sep) > 1 else ''
            else:
                datos['feedback'] = resto[:2000]
    
    return datos

def _detectar_puntos_clave(texto: str) -> List[str]:
    """Detecta puntos clave del texto."""
    puntos = []
    
    # Mapeo de patrones a puntos clave
    patrones_puntos = {
        r'LOPD\s*NO': 'LOPD ¡CUIDADO!',
        r'LOPD\s*SI': 'LOPD',
        r'AGENTE\s*DE\s*ZELENZA\s*NO': 'Comunicación',
        r'SONDEO\s*NO': 'Sondeo',
        r'CIERRE\s*NO': 'Cierre de venta',
        r'ARGUMENTACI[OÓ]N\s*NO': 'Argumentación',
        r'TONO\s*NO': 'Tono',
        r'ESCUCHA\s*ACTIVA\s*NO': 'Escucha activa',
    }
    
    for patron, punto in patrones_puntos.items():
        if re.search(patron, texto, re.IGNORECASE):
            if punto not in puntos:
                puntos.append(punto)
    
    return puntos