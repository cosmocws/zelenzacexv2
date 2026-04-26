# admin/gestion_planes.py
import streamlit as st
import pandas as pd
import os
import shutil
import json

# =============================================
# CONFIGURACIÓN DE PRECIOS
# =============================================

def cargar_config_precios():
    """Carga la configuración de precios desde JSON."""
    try:
        with open('data/config_precios.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "pack_iberdrola": 11.50,
            "iva": 21.0,
            "impuesto_electrico": 5.1127,
            "alquiler_contador": 0.98,
            "descuento_primera_factura": 5.0
        }

def guardar_config_precios(config):
    """Guarda la configuración de precios en JSON."""
    os.makedirs('data', exist_ok=True)
    with open('data/config_precios.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    os.makedirs("data_backup", exist_ok=True)
    shutil.copy("data/config_precios.json", "data_backup/config_precios.json")

def seccion_configuracion_precios():
    """Sección de configuración de precios generales."""
    st.subheader("⚙️ Configuración de Precios Generales")
    st.caption("Estos valores afectan a todos los cálculos de la calculadora.")
    
    config = cargar_config_precios()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pack = st.number_input(
            "Pack Iberdrola (€/mes)",
            min_value=0.0,
            value=config.get('pack_iberdrola', 11.50),
            step=0.50,
            format="%.2f"
        )
    
    with col2:
        iva = st.number_input(
            "IVA (%)",
            min_value=0.0,
            max_value=100.0,
            value=config.get('iva', 21.0),
            step=0.5,
            format="%.1f"
        )
    
    with col3:
        ie = st.number_input(
            "Impuesto Eléctrico (%)",
            min_value=0.0,
            max_value=100.0,
            value=config.get('impuesto_electrico', 5.1127),
            step=0.01,
            format="%.4f"
        )
    
    col4, col5 = st.columns(2)
    with col4:
        alquiler = st.number_input(
            "Alquiler Contador (€/mes)",
            min_value=0.0,
            value=config.get('alquiler_contador', 0.98),
            step=0.01,
            format="%.2f"
        )
        
        precio_excedente = st.number_input(
            "Precio Excedentes (€/kWh)",
            min_value=0.0,
            value=config.get('precio_excedente', 0.06),
            step=0.01,
            format="%.4f",
            help="Precio al que se pagan los kWh de excedentes solares"
        )
    
    with col5:
        descuento = st.number_input(
            "Descuento Bienvenida (€)",
            min_value=0.0,
            value=config.get('descuento_primera_factura', 5.0),
            step=0.50,
            format="%.2f"
        )
    
    if st.button("💾 Guardar Configuración de Precios", type="primary"):
        nueva_config = {
            "pack_iberdrola": pack,
            "iva": iva,
            "impuesto_electrico": ie,
            "alquiler_contador": alquiler,
            "descuento_primera_factura": descuento,
            "precio_excedente": precio_excedente
        }
        guardar_config_precios(nueva_config)
        st.success("✅ Configuración de precios guardada correctamente")
        st.rerun()

# =============================================
# FUNCIÓN PRINCIPAL DEL PANEL DE ADMIN
# =============================================
def gestion_electricidad():
    """Panel de administración para gestionar los planes de electricidad."""
    st.title("⚡ Gestión de Planes de Electricidad")
    st.write("Administra los precios y avisos que verán los agentes en su calculadora.")
    
    # --- Carga segura del CSV ---
    columnas_necesarias = [
        'plan', 'precio_original_kwh', 'con_pi_kwh', 'sin_pi_kwh',
        'punta', 'valle', 'total_potencia', 'activo', 'campaña', 'aviso_agente'
    ]
    
    try:
        df_luz = pd.read_csv("data/precios_luz.csv", encoding='utf-8')
        # Si el CSV es viejo, le añadimos las columnas nuevas
        for col in columnas_necesarias:
            if col not in df_luz.columns:
                if col == 'campaña':
                    df_luz[col] = 'TODAS'
                elif col == 'aviso_agente':
                    df_luz[col] = ''
                else:
                    df_luz[col] = 0.0
    except (FileNotFoundError, pd.errors.EmptyDataError):
        st.warning("⚠️ No se encontró 'precios_luz.csv'. Se creará uno nuevo al guardar.")
        df_luz = pd.DataFrame(columns=columnas_necesarias)
    
    # =============================================
    # VISTA DE PLANES ACTUALES
    # =============================================
    st.subheader("📊 Planes Configurados")
    
    if not df_luz.empty:
        # Filtros rápidos
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_estado = st.selectbox("Estado:", ["Todos", "Activos", "Inactivos"])
        with col_f2:
            campanas_unicas = ['Todas'] + sorted(df_luz['campaña'].unique().tolist())
            filtro_campana = st.selectbox("Campaña:", campanas_unicas)
        
        # Aplicar filtros
        df_view = df_luz.copy()
        if filtro_estado == "Activos":
            df_view = df_view[df_view['activo'] == True]
        elif filtro_estado == "Inactivos":
            df_view = df_view[df_view['activo'] == False]
        if filtro_campana != 'Todas':
            df_view = df_view[df_view['campaña'] == filtro_campana]
        
        # --- TABLA CON BOTONES DE EDITAR Y ELIMINAR ---
        st.write("**Haz clic en ✏️ para editar o en 🗑️ para eliminar:**")
        
        for idx, row in df_view.iterrows():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 2, 2, 1, 1.5, 2, 1])
            
            with col1:
                st.write(f"**{row['plan']}**")
            with col2:
                st.write(f"PI: {row['con_pi_kwh']:.4f}€")
            with col3:
                st.write(f"No PI: {row['sin_pi_kwh']:.4f}€")
            with col4:
                st.write("✅" if row['activo'] else "❌")
            with col5:
                st.write(row['campaña'])
            with col6:
                aviso = row.get('aviso_agente', '')
                if aviso and isinstance(aviso, str) and aviso.strip():
                    st.write(f"⚠️ {aviso[:30]}...")
            
            with col7:
                col_edit, col_del = st.columns(2)
                with col_edit:
                    if st.button("✏️", key=f"edit_{idx}"):
                        st.session_state.editing_plan = row.to_dict()
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"del_{idx}"):
                        if st.session_state.get(f"confirm_del_{idx}", False):
                            df_luz = df_luz.drop(idx)
                            df_luz.to_csv("data/precios_luz.csv", index=False, encoding='utf-8')
                            os.makedirs("data_backup", exist_ok=True)
                            shutil.copy("data/precios_luz.csv", "data_backup/precios_luz.csv")
                            st.success(f"✅ Plan '{row['plan']}' eliminado")
                            st.rerun()
                        else:
                            st.session_state[f"confirm_del_{idx}"] = True
                            st.warning(f"¿Seguro? Pulsa 🗑️ otra vez para confirmar")
                            st.stop()
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Activos", len(df_luz[df_luz['activo'] == True]))
        with col2: st.metric("Inactivos", len(df_luz[df_luz['activo'] == False]))
        with col3: st.metric("Total", len(df_luz))
    else:
        st.info("No hay planes configurados aún. Crea el primero abajo.")
    
    # =============================================
    # FORMULARIO PARA CREAR/EDITAR
    # =============================================
    st.markdown("---")
    st.subheader("➕ Añadir / ✏️ Editar Plan")
    
    if 'editing_plan' not in st.session_state:
        st.session_state.editing_plan = None
    
    if st.session_state.editing_plan is not None:
        st.warning(f"✏️ Editando: **{st.session_state.editing_plan['plan']}**")
        if st.button("❌ Cancelar Edición", key="cancel_edit"):
            st.session_state.editing_plan = None
            st.rerun()
    
    with st.form("form_plan_electricidad"):
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.session_state.editing_plan is not None:
                nombre_plan = st.text_input(
                    "Nombre del Plan*",
                    value=st.session_state.editing_plan['plan'],
                    disabled=True
                )
            else:
                nombre_plan = st.text_input("Nombre del Plan*", placeholder="Ej: IMPULSA 24h")
            
            con_pi = st.number_input(
                "€/kWh CON Iberdrola*",
                min_value=0.0, format="%.4f",
                value=st.session_state.editing_plan.get('con_pi_kwh', 0.1200) if st.session_state.editing_plan else 0.1200
            )
        
        with col_b:
            precio_original = st.number_input(
                "Precio Original kWh",
                min_value=0.0, format="%.4f",
                value=st.session_state.editing_plan.get('precio_original_kwh', 0.1500) if st.session_state.editing_plan else 0.1500
            )
            sin_pi = st.number_input(
                "€/kWh SIN Iberdrola*",
                min_value=0.0, format="%.4f",
                value=st.session_state.editing_plan.get('sin_pi_kwh', 0.1280) if st.session_state.editing_plan else 0.1280
            )
        
        with col_c:
            punta = st.number_input(
                "Precio Punta (€/kW/día)*",
                min_value=0.0, format="%.4f",
                value=st.session_state.editing_plan.get('punta', 0.1190) if st.session_state.editing_plan else 0.1190
            )
            valle = st.number_input(
                "Precio Valle (€/kW/día)*",
                min_value=0.0, format="%.4f",
                value=st.session_state.editing_plan.get('valle', 0.0510) if st.session_state.editing_plan else 0.0510
            )
            
            total_potencia = round(punta + valle, 4)
            st.number_input(
                "Total Potencia (auto)",
                value=total_potencia, disabled=True
            )
        
        col_d, col_e = st.columns(2)
        with col_d:
            activo = st.checkbox(
                "✅ Plan Activo",
                value=st.session_state.editing_plan.get('activo', True) if st.session_state.editing_plan else True
            )
        with col_e:
            campana = st.selectbox(
                "Campaña",
                ["CAPTA", "WINBACK", "TODAS"],
                index=0 if not st.session_state.editing_plan else ["CAPTA", "WINBACK", "TODAS"].index(
                    st.session_state.editing_plan.get('campaña', 'TODAS')
                )
            )
        
        aviso_agente = st.text_input(
            "⚠️ Aviso para Agentes (visible en calculadora)",
            value=st.session_state.editing_plan.get('aviso_agente', '') if st.session_state.editing_plan else '',
            placeholder="Ej: Comprobar ZONA antes de ofertar / PERMANENCIA 12 MESES",
            help="Este texto aparecerá junto al plan en la tabla de resultados del agente."
        )
        
        submitted = st.form_submit_button("💾 Guardar Plan", type="primary", use_container_width=True)
        
        if submitted:
            if not nombre_plan:
                st.error("❌ El nombre del plan es obligatorio")
            else:
                nuevo_plan = {
                    'plan': nombre_plan,
                    'precio_original_kwh': precio_original,
                    'con_pi_kwh': con_pi,
                    'sin_pi_kwh': sin_pi,
                    'punta': punta,
                    'valle': valle,
                    'total_potencia': total_potencia,
                    'activo': activo,
                    'campaña': campana,
                    'aviso_agente': aviso_agente
                }
                
                if nombre_plan in df_luz['plan'].values:
                    idx = df_luz[df_luz['plan'] == nombre_plan].index[0]
                    for k, v in nuevo_plan.items():
                        df_luz.at[idx, k] = v
                    st.success(f"✅ Plan '{nombre_plan}' actualizado")
                else:
                    df_luz = pd.concat([df_luz, pd.DataFrame([nuevo_plan])], ignore_index=True)
                    st.success(f"✅ Plan '{nombre_plan}' creado")
                
                # Guardar y backup
                os.makedirs("data", exist_ok=True)
                df_luz.to_csv("data/precios_luz.csv", index=False, encoding='utf-8')
                os.makedirs("data_backup", exist_ok=True)
                shutil.copy("data/precios_luz.csv", "data_backup/precios_luz.csv")
                                               
                st.session_state.editing_plan = None
                st.rerun()

    # =============================================
    # CONFIGURACIÓN DE PRECIOS GENERALES
    # =============================================
    st.markdown("---")
    seccion_configuracion_precios()

# =============================================
# GESTIÓN DE GAS (Mantendremos la misma estructura)
# =============================================
def gestion_gas():
    """Panel de administración para gestionar los planes de gas."""
    st.title("🔥 Gestión de Planes de Gas")
    
    # Cargar datos actuales
    try:
        with open('data/planes_gas.json', 'r', encoding='utf-8') as f:
            planes_gas = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        planes_gas = {
            "RL1": {
                "rango": "Consumo ≤ 5.000 kWh/año",
                "termino_fijo_con_pmg": 4.75, "termino_variable_con_pmg": 0.059,
                "termino_fijo_sin_pmg": 5.50, "termino_variable_sin_pmg": 0.065,
                "precio_original_kwh": 0.065, "activo": True
            },
            "RL2": {
                "rango": "5.000 < Consumo ≤ 15.000 kWh/año",
                "termino_fijo_con_pmg": 4.75, "termino_variable_con_pmg": 0.049,
                "termino_fijo_sin_pmg": 5.50, "termino_variable_sin_pmg": 0.055,
                "precio_original_kwh": 0.055, "activo": True
            },
            "RL3": {
                "rango": "Consumo > 15.000 kWh/año",
                "termino_fijo_con_pmg": 4.75, "termino_variable_con_pmg": 0.045,
                "termino_fijo_sin_pmg": 5.50, "termino_variable_sin_pmg": 0.051,
                "precio_original_kwh": 0.051, "activo": True
            }
        }
    
    # Configuración PMG
    st.subheader("⚙️ Configuración PMG (Pack Mantenimiento Gas)")
    col_a, col_b = st.columns(2)
    with col_a:
        pmg_coste = st.number_input("Coste PMG (€/mes):", value=4.75, min_value=0.0, format="%.2f")
    with col_b:
        pmg_iva = st.number_input("IVA PMG (%):", value=21.0, min_value=0.0, max_value=100.0, format="%.1f") / 100
    
    if st.button("💾 Guardar PMG"):
        os.makedirs('data', exist_ok=True)
        with open('data/config_pmg.json', 'w', encoding='utf-8') as f:
            json.dump({"coste": pmg_coste, "iva": pmg_iva}, f, indent=4)
        st.success("✅ Configuración PMG guardada")
    
    st.markdown("---")
    st.subheader("📊 Planes de Gas por RL")
    
    for rl, plan in planes_gas.items():
        with st.expander(f"**{rl}** - {plan['rango']}", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                st.write("**CON PMG**")
                plan["termino_fijo_con_pmg"] = st.number_input(
                    f"Fijo (€/mes):", value=float(plan["termino_fijo_con_pmg"]), min_value=0.0, format="%.4f",
                    key=f"f_c_{rl}"
                )
                plan["termino_variable_con_pmg"] = st.number_input(
                    f"Variable (€/kWh):", value=float(plan["termino_variable_con_pmg"]), min_value=0.0, format="%.4f",
                    key=f"v_c_{rl}"
                )
            with c2:
                st.write("**SIN PMG**")
                plan["termino_fijo_sin_pmg"] = st.number_input(
                    f"Fijo (€/mes):", value=float(plan["termino_fijo_sin_pmg"]), min_value=0.0, format="%.4f",
                    key=f"f_s_{rl}"
                )
                plan["termino_variable_sin_pmg"] = st.number_input(
                    f"Variable (€/kWh):", value=float(plan["termino_variable_sin_pmg"]), min_value=0.0, format="%.4f",
                    key=f"v_s_{rl}"
                )
            plan["precio_original_kwh"] = st.number_input(
                f"Precio original (€/kWh):", value=float(plan["precio_original_kwh"]), min_value=0.0, format="%.4f",
                key=f"p_{rl}"
            )
            plan["activo"] = st.checkbox("Activo", value=plan["activo"], key=f"act_{rl}")
    
    if st.button("💾 Guardar Planes de Gas", type="primary", use_container_width=True):
        os.makedirs('data', exist_ok=True)
        with open('data/planes_gas.json', 'w', encoding='utf-8') as f:
            json.dump(planes_gas, f, indent=4, ensure_ascii=False)
        os.makedirs("data_backup", exist_ok=True)
        shutil.copy("data/planes_gas.json", "data_backup/planes_gas.json")
        st.success("✅ Planes de gas guardados")
        st.rerun()