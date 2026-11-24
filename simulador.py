"""
simulador.py
------------
Motor de simulación y lógica energética para la estación de carga.
Mantiene las funciones de cálculo matemático, asignación de cargadores,
y análisis de ocupación sin acoplamiento a librerías gráficas.
"""

import json
from typing import Dict, List, Any, Tuple

# ==============================================================================
# PARÁMETROS GLOBALES AJUSTABLES EN SUSTENTACIÓN
# ==============================================================================
UMBRAL_ALERTA_ESPERA_HORAS = 1.0  # Alerta si espera >= este umbral (horas)


def cargar_datos(ruta_o_contenido) -> Dict[str, Any]:
    """
    Carga y valida los datos de entrada de la estación de carga.
    Acepta una ruta de archivo (str) o un diccionario ya parseado.
    """
    if isinstance(ruta_o_contenido, str):
        with open(ruta_o_contenido, "r", encoding="utf-8") as f:
            datos = json.load(f)
    elif isinstance(ruta_o_contenido, dict):
        datos = ruta_o_contenido
    else:
        raise ValueError("Formato de entrada no soportado. Debe ser ruta o dict.")

    # Validar campos obligatorios
    campos_requeridos = ["estacion", "potencia", "precio", "vehiculos"]
    for campo in campos_requeridos:
        if campo not in datos:
            raise KeyError(f"Falta el campo obligatorio '{campo}' en los datos.")

    # Ordenar vehículos por hora de llegada (política FIFO estricta)
    datos["vehiculos"] = sorted(datos["vehiculos"], key=lambda v: (v["llegada"], v["placa"]))
    return datos


def crear_estacion(nombre: str, potencia: float = 10.0, precio: float = 1500.0, vehiculos: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Crea la estructura estandarizada para una nueva estación de carga en la red.
    """
    return {
        "estacion": nombre.strip() if nombre else "Nueva Estación",
        "potencia": float(potencia),
        "precio": float(precio),
        "vehiculos": vehiculos if vehiculos is not None else []
    }


def simular_estacion(datos: Dict[str, Any], num_cargadores: int = 2) -> Dict[str, Any]:
    """
    Ejecuta el despacho de vehículos hacia los cargadores disponibles.

    Reglas de asignación:
    1. Orden de llegada (FIFO).
    2. Cargador que se desocupa primero.
    3. En empate, el de menor número de identificador (1 antes que 2).
    """
    potencia = float(datos["potencia"])  # kW
    precio = float(datos["precio"])      # $/kWh
    # Ordenar vehículos estrictamente por orden de llegada (política FIFO)
    vehiculos = sorted(datos["vehiculos"], key=lambda v: (float(v["llegada"]), str(v["placa"])))

    # Estado de cada cargador: registra a qué hora quedará desocupado
    cargadores_disp = {i: 0.0 for i in range(1, num_cargadores + 1)}

    asignaciones = []
    espera_total = 0.0
    energia_total = 0.0

    for vehiculo in vehiculos:
        placa = str(vehiculo["placa"])
        nombre = str(vehiculo.get("nombre", f"Vehículo {placa}"))
        llegada = float(vehiculo["llegada"])
        kwh = float(vehiculo["kwh"])

        # Tiempo de carga: Δt = kWh / Potencia [horas]
        duracion = kwh / potencia

        # Buscar el cargador disponible más temprano
        # En empate, min() elige la clave menor (1, 2, ...) por el orden de tuplas
        cargador_id, prox_disp = min(
            cargadores_disp.items(),
            key=lambda item: (max(llegada, item[1]), item[0])
        )

        hora_inicio = max(llegada, prox_disp)
        espera = hora_inicio - llegada
        hora_fin = hora_inicio + duracion

        # Actualizar disponibilidad del cargador asignado
        cargadores_disp[cargador_id] = hora_fin

        asignacion = {
            "placa": placa,
            "nombre": nombre,
            "llegada": llegada,
            "kwh": kwh,
            "cargador": cargador_id,
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "duracion": duracion,
            "espera": espera
        }
        asignaciones.append(asignacion)

        espera_total += espera
        energia_total += kwh

    ingresos_totales = energia_total * precio

    # Detectar vehículos con espera mayor o igual al umbral
    alertas_espera = [
        v for v in asignaciones if v["espera"] >= UMBRAL_ALERTA_ESPERA_HORAS
    ]

    return {
        "estacion": datos.get("estacion", "Estación Principal"),
        "potencia": potencia,
        "precio": precio,
        "num_cargadores": num_cargadores,
        "asignaciones": asignaciones,
        "espera_total": espera_total,
        "energia_total": energia_total,
        "ingresos_totales": ingresos_totales,
        "alertas_espera": alertas_espera,
        "umbral_espera": UMBRAL_ALERTA_ESPERA_HORAS
    }


def calcular_hora_pico(resultado_simulacion: Dict[str, Any], paso: float = 0.25) -> Dict[str, Any]:
    """
    Reto Funcional: Determina el intervalo de máxima ocupación horaria.
    Evalúa paso a paso (ej. cada 15 min = 0.25 h) cuántos cargadores están activos.
    """
    asignaciones = resultado_simulacion["asignaciones"]
    num_cargadores = resultado_simulacion["num_cargadores"]

    if not asignaciones:
        return {
            "max_vehiculos_simultaneos": 0,
            "porcentaje_ocupacion_pico": 0.0,
            "intervalo_pico": "Sin actividad",
            "detalles": []
        }

    h_min = min(v["llegada"] for v in asignaciones)
    h_max = max(v["hora_fin"] for v in asignaciones)

    # Discretización temporal
    tiempos = []
    t = h_min
    while t <= h_max:
        tiempos.append(round(t, 2))
        t += paso

    ocupaciones = []
    for t_actual in tiempos:
        activos = [
            v for v in asignaciones
            if v["hora_inicio"] <= t_actual < v["hora_fin"]
        ]
        ocupaciones.append({
            "tiempo": t_actual,
            "activos": len(activos),
            "vehiculos": [v["placa"] for v in activos]
        })

    max_activos = max(item["activos"] for item in ocupaciones)
    puntos_pico = [item for item in ocupaciones if item["activos"] == max_activos]

    t_inicio_pico = puntos_pico[0]["tiempo"]
    t_fin_pico = puntos_pico[-1]["tiempo"] + paso

    pct_pico = (max_activos / num_cargadores) * 100.0 if num_cargadores > 0 else 0.0

    return {
        "max_vehiculos_simultaneos": max_activos,
        "porcentaje_ocupacion_pico": round(pct_pico, 1),
        "hora_inicio_pico": t_inicio_pico,
        "hora_fin_pico": round(t_fin_pico, 2),
        "intervalo_pico": f"{t_inicio_pico:.2f} h a {t_fin_pico:.2f} h",
        "curva_ocupacion": ocupaciones
    }


def obtener_estado_en_instante(resultado_simulacion: Dict[str, Any], t_consulta: float) -> List[Dict[str, Any]]:
    """
    Devuelve el estado de cada cargador (1..N) en el instante de tiempo t_consulta:
    - Estado: Libre u Ocupado
    - Placa del vehículo si está ocupado
    - Porcentaje de carga acumulado [0% a 100%]
    - kWh transferidos hasta ese momento
    """
    asignaciones = resultado_simulacion["asignaciones"]
    num_cargadores = resultado_simulacion["num_cargadores"]
    potencia = resultado_simulacion["potencia"]

    estados = []

    for c_id in range(1, num_cargadores + 1):
        # Buscar si hay un vehículo cargando en c_id en el instante t_consulta
        vehiculo_en_carga = None
        for v in asignaciones:
            if v["cargador"] == c_id and (v["hora_inicio"] <= t_consulta < v["hora_fin"]):
                vehiculo_en_carga = v
                break

        if vehiculo_en_carga:
            tiempo_transcurrido = t_consulta - vehiculo_en_carga["hora_inicio"]
            progreso = min(100.0, max(0.0, (tiempo_transcurrido / vehiculo_en_carga["duracion"]) * 100.0))
            kwh_entregados = min(vehiculo_en_carga["kwh"], tiempo_transcurrido * potencia)
            estados.append({
                "cargador": c_id,
                "estado": "Ocupado",
                "placa": vehiculo_en_carga["placa"],
                "nombre": vehiculo_en_carga.get("nombre", f"Vehículo {vehiculo_en_carga['placa']}"),
                "progreso_pct": round(progreso, 1),
                "kwh_entregados": round(kwh_entregados, 2),
                "kwh_totales": vehiculo_en_carga["kwh"],
                "hora_fin": vehiculo_en_carga["hora_fin"]
            })
        else:
            estados.append({
                "cargador": c_id,
                "estado": "Libre",
                "placa": None,
                "nombre": None,
                "progreso_pct": 0.0,
                "kwh_entregados": 0.0,
                "kwh_totales": 0.0,
                "hora_fin": None
            })

    return estados
