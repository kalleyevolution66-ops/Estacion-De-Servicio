"""
app.py
------
Aplicación interactiva de supervisión y despacho energético para la
Estación de Carga de Vehículos Eléctricos.
Diseñada para Streamlit con interfaz profesional de alta intuición visual.
"""

import streamlit as st
import json
import os
from simulador import (
    cargar_datos,
    crear_estacion,
    simular_estacion,
    calcular_hora_pico,
    obtener_estado_en_instante,
    UMBRAL_ALERTA_ESPERA_HORAS
)

# ==============================================================================
# 1. CONFIGURACIÓN VISUAL Y PALETA DE COLORES (MODULAR PARA SUSTENTACIÓN)
# ==============================================================================
st.set_page_config(
    page_title="Centro de Control EV | Estación de Carga",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta armónica moderna con alto contraste (UI inspirada en sistemas SCADA modernos)
COLORES_VEHICULOS = [
    "#3B82F6",  # Azul royal (Vehículo 1)
    "#10B981",  # Verde esmeralda (Vehículo 2)
    "#8B5CF6",  # Púrpura moderno (Vehículo 3)
    "#F59E0B",  # Ámbar dorado (Vehículo 4)
    "#EC4899",  # Rosa moderno (Vehículo 5)
    "#06B6D4",  # Cian eléctrico (Vehículo 6)
]

COLOR_ESPERA = "#94A3B8"        # Gris pizarra para tramos de espera
COLOR_LIBRE = "#10B981"         # Verde estado disponible
COLOR_OCUPADO = "#2563EB"       # Azul estado cargando
COLOR_CURSOR_TIEMPO = "#DC2626" # Rojo carmín para la aguja de tiempo sincrónica

# Inyección de estilos CSS limpios y adaptables a tema claro/oscuro
st.markdown("""
<style>
    /* Tipografía y espaciado general */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
        max-width: 1250px;
    }
    
    /* Barra superior de bienvenida */
    .station-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 14px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.15);
    }
    .station-title {
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .station-subtitle {
        font-size: 0.95rem;
        opacity: 0.9;
        margin-top: 4px;
    }
    
    /* Tarjetas de Métricas Ejecutivas */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 20px;
    }
    .kpi-card {
        background: var(--secondary-background-color);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 12px;
        padding: 16px;
        text-align: left;
        position: relative;
        overflow: hidden;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        transition: transform 0.15s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
    }
    .kpi-header {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        color: var(--text-color);
        opacity: 0.7;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 4px;
    }
    .kpi-footer {
        font-size: 0.8rem;
        color: var(--text-color);
        opacity: 0.75;
    }

    /* Bahías de Carga (Charging Bays) */
    .bay-card {
        background: var(--secondary-background-color);
        border: 1.5px solid rgba(148, 163, 184, 0.25);
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
        min-height: 205px; /* Altura estable para evitar saltos entre estados */
    }
    .bay-card.bay-active {
        border-color: #3B82F6;
        background: var(--secondary-background-color);
    }
    .bay-card.bay-idle {
        border-color: #10B981;
    }
    .bay-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .bay-title {
        font-size: 1.1rem;
        font-weight: 700;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .bay-badge-idle {
        background: #DCFCE7;
        color: #15803D;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 20px;
        text-transform: uppercase;
    }
    .bay-badge-busy {
        background: #DBEAFE;
        color: #1D4ED8;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 20px;
        text-transform: uppercase;
    }
    .bay-meta {
        font-size: 0.88rem;
        margin: 4px 0;
        display: flex;
        justify-content: space-between;
    }
    .bay-meta-label {
        color: var(--text-color);
        opacity: 0.7;
    }
    .bay-meta-val {
        font-weight: 600;
    }

    /* Contenedor del Diagrama Gantt */
    .gantt-panel {
        background: var(--secondary-background-color);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 14px;
        padding: 20px;
        margin-top: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CARGA Y GESTIÓN DE DATOS (POR DEFECTO O PERSONALIZADO)
# ==============================================================================
RUTA_DEFAULT = os.path.join(os.path.dirname(__file__), "datos", "entrada.json")

# Inicializar red de estaciones en sesión
if "estaciones" not in st.session_state:
    estacion_base = cargar_datos(RUTA_DEFAULT)
    st.session_state["estaciones"] = {estacion_base.get("estacion", "Norte"): estacion_base}
if "estacion_activa" not in st.session_state:
    st.session_state["estacion_activa"] = "Norte"

# Barra lateral de configuración simplificada e intuitiva
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=500&auto=format&fit=crop&q=60", use_container_width=True)
    st.title("⚙️ Red de Carga Eléctrica")
    
    st.subheader("1. Gestión de Estaciones")
    lista_estaciones = list(st.session_state["estaciones"].keys())
    idx_activa = lista_estaciones.index(st.session_state["estacion_activa"]) if st.session_state["estacion_activa"] in lista_estaciones else 0
    estacion_seleccionada = st.selectbox(
        "Estación de Carga Activa:",
        options=lista_estaciones,
        index=idx_activa,
        help="Selecciona qué estación de la red deseas supervisar y simular."
    )
    st.session_state["estacion_activa"] = estacion_seleccionada

    with st.expander("🏢 Agregar Nueva Estación"):
        with st.form("form_nueva_estacion", clear_on_submit=True):
            nueva_est_nom = st.text_input("Nombre de la Estación:", value="Sur").strip()
            nueva_est_pot = st.number_input("Potencia (kW/cargador):", min_value=1.0, max_value=350.0, value=20.0, step=5.0)
            nueva_est_prec = st.number_input("Tarifa ($/kWh):", min_value=100.0, max_value=10000.0, value=1600.0, step=100.0)
            btn_crear_est = st.form_submit_button("Crear Estación")

            if btn_crear_est:
                if nueva_est_nom:
                    nueva_obj = crear_estacion(nueva_est_nom, nueva_est_pot, nueva_est_prec)
                    st.session_state["estaciones"][nueva_est_nom] = nueva_obj
                    st.session_state["estacion_activa"] = nueva_est_nom
                    st.success(f"Estación '{nueva_est_nom}' incorporada a la red.")
                    st.rerun()
                else:
                    st.warning("Ingrese un nombre para la nueva estación.")

    st.subheader("2. Capacidad de Carga")
    num_cargadores = st.slider(
        "Cargadores disponibles en la estación:",
        min_value=1,
        max_value=6,
        value=2,
        help="Ajusta el número de cargadores activos (1 a 6). Simula instantáneamente el impacto en esperas."
    )
    
    st.subheader("3. Flota de Vehículos")
    # Registro interactivo manual de vehículos
    with st.expander("➕ Registrar Nuevo Vehículo"):
        with st.form("form_nuevo_vehiculo", clear_on_submit=True):
            n_nombre = st.text_input("Nombre / Modelo:", value="Tesla Model 3").strip()
            n_placa = st.text_input("Placa del vehículo:", value="E").strip().upper()
            n_llegada = st.number_input("Hora de llegada (h):", min_value=0.0, max_value=24.0, value=10.0, step=0.5)
            n_kwh = st.number_input("Energía requerida (kWh):", min_value=1.0, max_value=150.0, value=15.0, step=5.0)
            btn_registrar = st.form_submit_button("Ingresar a la Fila")

            if btn_registrar:
                if n_placa:
                    nom_final = n_nombre if n_nombre else f"Vehículo {n_placa}"
                    st.session_state["estaciones"][st.session_state["estacion_activa"]]["vehiculos"].append({
                        "placa": n_placa,
                        "nombre": nom_final,
                        "llegada": float(n_llegada),
                        "kwh": float(n_kwh)
                    })
                    st.success(f"{nom_final} ({n_placa}) registrado en fila.")
                    st.rerun()
                else:
                    st.warning("Ingrese una placa válida.")

    col_btn_rst, _ = st.columns([1, 0.1])
    with col_btn_rst:
        if st.button("🔄 Restablecer Flota Oficial", help="Vuelve a los vehículos base de la estación"):
            if st.session_state["estacion_activa"] == "Norte":
                st.session_state["estaciones"]["Norte"] = cargar_datos(RUTA_DEFAULT)
            else:
                st.session_state["estaciones"][st.session_state["estacion_activa"]]["vehiculos"] = []
            st.rerun()

    st.subheader("4. Fuente Externa (.JSON)")
    archivo_subido = st.file_uploader(
        "Importar archivo JSON:",
        type=["json"],
        help="Carga una estación externa con sus vehículos."
    )
    if archivo_subido is not None:
        try:
            contenido_json = json.load(archivo_subido)
            cargada = cargar_datos(contenido_json)
            nom_carg = cargada.get("estacion", "Importada")
            st.session_state["estaciones"][nom_carg] = cargada
            st.session_state["estacion_activa"] = nom_carg
            st.success(f"Estación '{nom_carg}' importada con éxito.")
        except Exception as e:
            st.error(f"Error al leer JSON: {e}")

    datos_entrada = st.session_state["estaciones"][st.session_state["estacion_activa"]]

    st.markdown("---")
    st.markdown("### 📋 Ficha Técnica")
    st.caption(f"**Sede Activa:** {datos_entrada.get('estacion', 'Principal')}")
    st.caption(f"**Potencia Nominal:** {datos_entrada.get('potencia')} kW por cargador")
    st.caption(f"**Tarifa Regulada:** ${datos_entrada.get('precio'):,.0f} COP / kWh")
    st.caption(f"**Flota Programada:** {len(datos_entrada.get('vehiculos', []))} vehículos")

# ==============================================================================
# 3. MOTOR DE SIMULACIÓN Y CÁLCULOS
# ==============================================================================
resultado = simular_estacion(datos_entrada, num_cargadores=num_cargadores)
pico = calcular_hora_pico(resultado)
asignaciones = resultado["asignaciones"]

h_min = min(v["llegada"] for v in asignaciones) if asignaciones else 8.0
h_max = max(v["hora_fin"] for v in asignaciones) if asignaciones else 12.0

# ==============================================================================
# 4. ENCABEZADO PRINCIPAL (BANNER ESTILO SCADA)
# ==============================================================================
st.markdown(f"""
<div class="station-header">
    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <div>
            <h1 class="station-title">⚡ Estación de Carga "{resultado['estacion']}"</h1>
            <div class="station-subtitle">
                Sistema Inteligente de Despacho y Monitoreo de Recarga para Vehículos Eléctricos
            </div>
        </div>
        <div style="text-align: right; background: rgba(255,255,255,0.15); padding: 8px 16px; border-radius: 10px;">
            <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Infraestructura</div>
            <div style="font-size: 1.3rem; font-weight: 800;">{num_cargadores} Cargadores ({resultado['potencia']} kW c/u)</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 5. VISUALIZACIÓN 3: TARJETAS KPI EJECUTIVAS Y ALERTA INTUITIVA
# ==============================================================================
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    color_espera = "#EF4444" if resultado["espera_total"] > 0 else "#10B981"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">⏱️ Espera Total Acumulada</div>
        <div class="kpi-value" style="color: {color_espera};">{resultado['espera_total']:.1f} <span style="font-size: 1.1rem;">h</span></div>
        <div class="kpi-footer">{resultado['espera_total'] * 60:.0f} minutos totales en cola</div>
    </div>
    """, unsafe_allow_html=True)

with col_kpi2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">⚡ Energía Entregada</div>
        <div class="kpi-value" style="color: #2563EB;">{resultado['energia_total']:.1f} <span style="font-size: 1.1rem;">kWh</span></div>
        <div class="kpi-footer">Demanda suministrada al 100%</div>
    </div>
    """, unsafe_allow_html=True)

with col_kpi3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">💰 Facturación Total</div>
        <div class="kpi-value" style="color: #059669;">${resultado['ingresos_totales']:,.0f}</div>
        <div class="kpi-footer">Tarifa: ${resultado['precio']:,.0f} / kWh</div>
    </div>
    """, unsafe_allow_html=True)

with col_kpi4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">🔥 Reto: Hora de Mayor Ocupación</div>
        <div class="kpi-value" style="color: #D97706; font-size: 1.6rem;">{pico['intervalo_pico']}</div>
        <div class="kpi-footer">{pico['max_vehiculos_simultaneos']} de {num_cargadores} cargadores ({pico['porcentaje_ocupacion_pico']}%)</div>
    </div>
    """, unsafe_allow_html=True)

# Alerta de servicio clara y accionable
if resultado["alertas_espera"]:
    placas = ", ".join([f"**{v['placa']}** ({v['espera']:.1f} h)" for v in resultado["alertas_espera"]])
    st.error(
        f"⚠️ **Alerta de Nivel de Servicio:** Vehículo(s) {placas} superan el umbral máximo de espera de "
        f"{UMBRAL_ALERTA_ESPERA_HORAS:.1f} h.  \n"
        f"💡 **Recomendación Energética:** Aumente el número de cargadores a **{min(6, num_cargadores + 1)}** "
        f"en la barra lateral para optimizar la rotación y eliminar las esperas.",
        icon="🚨"
    )
else:
    st.success("✅ **Excelente Desempeño:** Todos los vehículos ingresaron a carga sin superar el umbral de espera.", icon="✅")

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# 6. SECCIÓN CENTRAL: MONITOREO DINÁMICO EN TIEMPO REAL (TARJETAS + DESLIZADOR)
# ==============================================================================
st.markdown("### 🔌 Bahías de Carga y Monitoreo en Tiempo Real")
st.caption(
    "Mueva el control horario para ver cómo avanza el llenado de baterías y el estado de cada bahía. "
    "La aguja roja vertical en el diagrama inferior se moverá en simultáneo con esta hora."
)

# Selector de tiempo con formato claro HH:MM
col_ctrl1, col_ctrl2 = st.columns([3, 1])

with col_ctrl1:
    t_inspeccion = st.slider(
        "🕒 Selecciona la Hora del Día para Inspección:",
        min_value=float(h_min),
        max_value=float(h_max),
        value=float(h_min),
        step=0.25,
        format="%.2f h"
    )

with col_ctrl2:
    h_int = int(t_inspeccion)
    m_int = int((t_inspeccion - h_int) * 60)
    st.markdown(f"""
    <div style="text-align: center; background: var(--secondary-background-color); border: 1px solid rgba(148,163,184,0.3); border-radius: 12px; padding: 12px;">
        <div style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; opacity: 0.7;">Hora Seleccionada</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #2563EB;">{h_int:02d}:{m_int:02d}</div>
    </div>
    """, unsafe_allow_html=True)

# Obtener estado en ese instante
estados_cargadores = obtener_estado_en_instante(resultado, t_inspeccion)

# Renderizar bahías de carga en columnas ordenadas (2 o 3 por fila según cantidad)
cols_bays = st.columns(min(num_cargadores, 3))

for idx, est in enumerate(estados_cargadores):
    c_idx = idx % min(num_cargadores, 3)
    es_ocupado = est["estado"] == "Ocupado"
    
    with cols_bays[c_idx]:
        if es_ocupado:
            st.markdown(f"""
            <div class="bay-card bay-active">
                <div class="bay-header">
                    <h4 class="bay-title">⚡ Bahía {est['cargador']}</h4>
                    <span class="bay-badge-busy">Cargando ({est['placa']})</span>
                </div>
                <div class="bay-meta">
                    <span class="bay-meta-label">Vehículo en Carga:</span>
                    <span class="bay-meta-val" style="color: #2563EB;">{est.get('nombre', 'Vehículo ' + est['placa'])} (Placa {est['placa']})</span>
                </div>
                <div class="bay-meta">
                    <span class="bay-meta-label">Energía Transferida:</span>
                    <span class="bay-meta-val">{est['kwh_entregados']:.1f} / {est['kwh_totales']:.1f} kWh</span>
                </div>
                <div class="bay-meta">
                    <span class="bay-meta-label">Hora Estimada Fin:</span>
                    <span class="bay-meta-val">{est['hora_fin']:.2f} h</span>
                </div>
                <div style="margin-top: 10px; margin-bottom: 4px; display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 700;">
                    <span>Progreso Batería</span>
                    <span style="color: #2563EB;">{est['progreso_pct']:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(float(est["progreso_pct"]) / 100.0)
        else:
            st.markdown(f"""
            <div class="bay-card bay-idle">
                <div class="bay-header">
                    <h4 class="bay-title">⚡ Bahía {est['cargador']}</h4>
                    <span class="bay-badge-idle">Disponible</span>
                </div>
                <div class="bay-meta">
                    <span class="bay-meta-label">Estado Operativo:</span>
                    <span class="bay-meta-val" style="color: #10B981;">Libre para conectar</span>
                </div>
                <div class="bay-meta">
                    <span class="bay-meta-label">Potencia en Espera:</span>
                    <span class="bay-meta-val">{resultado['potencia']} kW</span>
                </div>
                <div class="bay-meta">
                    <span class="bay-meta-label">Flujo Activo:</span>
                    <span class="bay-meta-val">0.0 kW</span>
                </div>
                <div style="margin-top: 10px; margin-bottom: 4px; display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 700; color: #64748B;">
                    <span>Bahía Desocupada</span>
                    <span>0.0%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(0.0)

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# 7. VISUALIZACIÓN 1: GANTT INTERACTIVO CON AGUJA TEMPORAL SINCRONIZADA
# ==============================================================================
st.markdown("### 📅 Programación y Despacho Temporal (Diagrama de Gantt)")
st.caption(
    "Visualiza la asignación secuencial de cada vehículo en su respectivo cargador. "
    "La **línea roja vertical** marca el instante que estás observando en las bahías de arriba."
)

def generar_gantt_svg_moderno(asignaciones, num_cargadores, h_min, h_max, t_cursor):
    """
    Genera un diagrama de Gantt vectorial SVG con:
    - Aguja de tiempo roja sincronizada con el deslizador.
    - Tramos de espera con rayas diagonales suaves.
    - Bloques de carga redondeados con contraste óptimo para proyector.
    """
    margen_izq = 130
    margen_der = 50
    margen_sup = 35
    margen_inf = 50
    alto_fila = 58
    ancho_total = 960
    alto_total = margen_sup + (num_cargadores * alto_fila) + margen_inf

    duracion_total = max(1.0, h_max - h_min)
    ancho_util = ancho_total - margen_izq - margen_der

    def x_pos(h):
        return margen_izq + ((h - h_min) / duracion_total) * ancho_util

    svg = [
        f'<svg width="100%" height="{alto_total}" viewBox="0 0 {ancho_total} {alto_total}" '
        f'xmlns="http://www.w3.org/2000/svg" style="font-family: system-ui, -apple-system, BlinkMacSystemFont, \'Segoe UI\', sans-serif;">',
        '''<defs>
            <pattern id="wait-hatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
                <line x1="0" y1="0" x2="0" y2="8" stroke="#94A3B8" stroke-width="2.5" />
                <rect x="0" y="0" width="8" height="8" fill="#F1F5F9" opacity="0.6"/>
            </pattern>
            <filter id="shadow" x="-5%" y="-10%" width="110%" height="130%">
                <feDropShadow dx="0" dy="2" stdDeviation="2" flood-opacity="0.12"/>
            </filter>
        </defs>'''
    ]

    # Guías verticales de horas
    paso_hora = 1.0 if duracion_total <= 8 else 2.0
    h_tick = int(h_min)
    while h_tick <= int(h_max) + 1:
        if h_min <= h_tick <= h_max:
            xt = x_pos(h_tick)
            svg.append(f'<line x1="{xt}" y1="{margen_sup}" x2="{xt}" y2="{alto_total - margen_inf}" stroke="#E2E8F0" stroke-width="1.2" stroke-dasharray="3 3"/>')
            svg.append(f'<text x="{xt}" y="{alto_total - margen_inf + 22}" text-anchor="middle" fill="#64748B" font-size="12px" font-weight="600">{int(h_tick):02d}:00</text>')
        h_tick += paso_hora

    # Filas de cargadores con esquinas suaves
    for c in range(1, num_cargadores + 1):
        yc = margen_sup + (c - 1) * alto_fila
        # Fondo de carril
        svg.append(f'<rect x="{margen_izq}" y="{yc + 6}" width="{ancho_util}" height="{alto_fila - 12}" fill="#F8FAFC" rx="8" stroke="#E2E8F0" stroke-width="1"/>')
        # Etiqueta lateral
        svg.append(f'<text x="20" y="{yc + (alto_fila/2) + 4}" fill="#1E293B" font-size="13px" font-weight="700">Cargador {c}</text>')

    # Mapa de colores por vehículo
    placas = sorted(list({v["placa"] for v in asignaciones}))
    color_map = {p: COLORES_VEHICULOS[i % len(COLORES_VEHICULOS)] for i, p in enumerate(placas)}

    # Dibujar asignaciones (esperas y cargas)
    for v in asignaciones:
        c = v["cargador"]
        yc = margen_sup + (c - 1) * alto_fila
        y_b = yc + 9
        h_b = alto_fila - 18

        # 1. Tramo de espera si existe
        if v["espera"] > 0:
            x_arr = x_pos(v["llegada"])
            w_esp = x_pos(v["hora_inicio"]) - x_arr
            svg.append(
                f'<rect x="{x_arr}" y="{y_b}" width="{w_esp}" height="{h_b}" '
                f'fill="url(#wait-hatch)" stroke="#94A3B8" stroke-width="1.5" rx="6"/>'
            )
            if w_esp > 35:
                svg.append(
                    f'<text x="{x_arr + w_esp/2}" y="{y_b + h_b/2 + 4}" text-anchor="middle" '
                    f'fill="#334155" font-size="11px" font-weight="700">Espera {v["placa"]}</text>'
                )

        # 2. Bloque de carga activa
        x_ini = x_pos(v["hora_inicio"])
        w_car = max(16, x_pos(v["hora_fin"]) - x_ini)
        col_v = color_map.get(v["placa"], "#3B82F6")

        svg.append(
            f'<rect x="{x_ini}" y="{y_b}" width="{w_car}" height="{h_b}" '
            f'fill="{col_v}" rx="6" filter="url(#shadow)"/>'
        )
        # Texto del vehículo con alto contraste
        nom_veh = v.get("nombre", v["placa"])
        if nom_veh != v["placa"] and w_car > 110:
            txt_label = f'🚗 {v["placa"]} - {nom_veh} ({v["kwh"]:.0f}k)'
        else:
            txt_label = f'🚗 {v["placa"]} ({v["kwh"]:.0f} kWh)'
        svg.append(
            f'<text x="{x_ini + w_car/2}" y="{y_b + h_b/2 + 4}" text-anchor="middle" '
            f'fill="#FFFFFF" font-size="12px" font-weight="700">'
            f'{txt_label}'
            f'</text>'
        )

    # 3. AGUJA DE TIEMPO SINCRONIZADA (CURSOR TEMPORAL)
    if h_min <= t_cursor <= h_max:
        x_cur = x_pos(t_cursor)
        # Línea vertical indicadora
        svg.append(
            f'<line x1="{x_cur}" y1="{margen_sup - 10}" x2="{x_cur}" y2="{alto_total - margen_inf}" '
            f'stroke="{COLOR_CURSOR_TIEMPO}" stroke-width="2.5" stroke-dasharray="4 2"/>'
        )
        # Badge superior indicador
        h_c_int = int(t_cursor)
        m_c_int = int((t_cursor - h_c_int) * 60)
        svg.append(
            f'<rect x="{x_cur - 32}" y="{margen_sup - 24}" width="64" height="20" rx="4" fill="{COLOR_CURSOR_TIEMPO}"/>'
        )
        svg.append(
            f'<text x="{x_cur}" y="{margen_sup - 10}" text-anchor="middle" fill="#FFFFFF" font-size="11px" font-weight="800">'
            f'{h_c_int:02d}:{m_c_int:02d}</text>'
        )

    svg.append('</svg>')
    return "".join(svg)

gantt_svg = generar_gantt_svg_moderno(asignaciones, num_cargadores, h_min, h_max, t_inspeccion)
st.markdown(f'<div class="gantt-panel">{gantt_svg}</div>', unsafe_allow_html=True)

# Leyenda visual unificada y comprensible
col_l1, col_l2, col_l3 = st.columns([1, 1, 1.5])
with col_l1:
    st.markdown("🟦 **Bloques Sólidos:** Vehículo en proceso de carga activa.")
with col_l2:
    st.markdown("🏁 **Tramo Rayado:** Tiempo en fila de espera hasta disponibilidad.")
with col_l3:
    st.markdown("📍 **Línea Roja Punteada:** Hora actual inspeccionada en las bahías.")

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# 8. DETALLE OPERATIVO Y MATRIZ DE DESPACHO
# ==============================================================================
with st.expander("📊 Consultar Registro Detallado de Despacho (Flota Completa)"):
    st.dataframe(
        [
            {
                "Placa": v['placa'],
                "Nombre / Modelo": v.get('nombre', f"Vehículo {v['placa']}"),
                "Hora Llegada": f"{v['llegada']:05.2f} h",
                "Bahía Asignada": f"Cargador {v['cargador']}",
                "Hora Inicio": f"{v['hora_inicio']:05.2f} h",
                "Hora Fin": f"{v['hora_fin']:05.2f} h",
                "Tiempo Carga": f"{v['duracion']:.2f} h",
                "Tiempo Espera": f"{v['espera']:.2f} h",
                "Energía": f"{v['kwh']:.1f} kWh",
                "Facturación": f"${v['kwh'] * resultado['precio']:,.0f}"
            }
            for v in asignaciones
        ],
        use_container_width=True
    )
