"""
test_simulador.py
-----------------
Pruebas unitarias para validar los requerimientos obligatorios y el
caso de verificación oficial del proyecto de Ingeniería Energética.
"""

import unittest
from simulador import cargar_datos, simular_estacion, calcular_hora_pico, obtener_estado_en_instante


class TestEstacionCarga(unittest.TestCase):

    def setUp(self):
        # Datos del caso oficial de verificación
        self.datos = {
            "estacion": "Norte",
            "potencia": 10,
            "precio": 1500,
            "vehiculos": [
                {"placa": "A", "llegada": 8, "kwh": 20},
                {"placa": "B", "llegada": 8, "kwh": 10},
                {"placa": "C", "llegada": 9, "kwh": 30},
                {"placa": "D", "llegada": 9, "kwh": 10}
            ]
        }

    def test_caso_verificacion_oficial(self):
        """Valida exactamente los resultados del benchmark establecido."""
        resultado = simular_estacion(self.datos, num_cargadores=2)
        asignaciones = {v["placa"]: v for v in resultado["asignaciones"]}

        # 1. Vehículo A: cargador 1, de 8 a 10 h, espera 0 h
        self.assertEqual(asignaciones["A"]["cargador"], 1)
        self.assertEqual(asignaciones["A"]["hora_inicio"], 8.0)
        self.assertEqual(asignaciones["A"]["hora_fin"], 10.0)
        self.assertEqual(asignaciones["A"]["espera"], 0.0)

        # 2. Vehículo B: cargador 2, de 8 a 9 h, espera 0 h
        self.assertEqual(asignaciones["B"]["cargador"], 2)
        self.assertEqual(asignaciones["B"]["hora_inicio"], 8.0)
        self.assertEqual(asignaciones["B"]["hora_fin"], 9.0)
        self.assertEqual(asignaciones["B"]["espera"], 0.0)

        # 3. Vehículo C: cargador 2, de 9 a 12 h, espera 0 h
        self.assertEqual(asignaciones["C"]["cargador"], 2)
        self.assertEqual(asignaciones["C"]["hora_inicio"], 9.0)
        self.assertEqual(asignaciones["C"]["hora_fin"], 12.0)
        self.assertEqual(asignaciones["C"]["espera"], 0.0)

        # 4. Vehículo D: cargador 1, de 10 a 11 h, espera 1 h
        self.assertEqual(asignaciones["D"]["cargador"], 1)
        self.assertEqual(asignaciones["D"]["hora_inicio"], 10.0)
        self.assertEqual(asignaciones["D"]["hora_fin"], 11.0)
        self.assertEqual(asignaciones["D"]["espera"], 1.0)

        # Totales globales
        self.assertEqual(resultado["espera_total"], 1.0)
        self.assertEqual(resultado["energia_total"], 70.0)
        self.assertEqual(resultado["ingresos_totales"], 105000.0)

        # Alerta de espera
        alertas = [v["placa"] for v in resultado["alertas_espera"]]
        self.assertIn("D", alertas)

    def test_reto_funcional_hora_pico(self):
        """Valida el cálculo de máxima ocupación horaria."""
        resultado = simular_estacion(self.datos, num_cargadores=2)
        pico = calcular_hora_pico(resultado)

        # En el caso de prueba, entre las 8 y las 11 están ambos cargadores ocupados
        self.assertEqual(pico["max_vehiculos_simultaneos"], 2)
        self.assertEqual(pico["porcentaje_ocupacion_pico"], 100.0)

    def test_estados_dinamicos_tarjetas(self):
        """Valida que el cálculo dinámico del tiempo reporte el estado y % correcto."""
        resultado = simular_estacion(self.datos, num_cargadores=2)

        # A las 8.5 h:
        # Cargador 1: Vehículo A (8 a 10 h) -> transcurrido 0.5 de 2 h = 25% progreso
        # Cargador 2: Vehículo B (8 a 9 h) -> transcurrido 0.5 de 1 h = 50% progreso
        estados_8_5 = {e["cargador"]: e for e in obtener_estado_en_instante(resultado, 8.5)}
        self.assertEqual(estados_8_5[1]["estado"], "Ocupado")
        self.assertEqual(estados_8_5[1]["placa"], "A")
        self.assertAlmostEqual(estados_8_5[1]["progreso_pct"], 25.0)

        self.assertEqual(estados_8_5[2]["estado"], "Ocupado")
        self.assertEqual(estados_8_5[2]["placa"], "B")
        self.assertAlmostEqual(estados_8_5[2]["progreso_pct"], 50.0)

        # A las 11.5 h:
        # Cargador 1: Libre (D terminó a las 11)
        # Cargador 2: Ocupado por C (9 a 12 h)
        estados_11_5 = {e["cargador"]: e for e in obtener_estado_en_instante(resultado, 11.5)}
        self.assertEqual(estados_11_5[1]["estado"], "Libre")
        self.assertEqual(estados_11_5[2]["estado"], "Ocupado")
        self.assertEqual(estados_11_5[2]["placa"], "C")

    def test_vehiculos_con_nombre_y_multi_estacion(self):
        """Valida soporte para nombres descriptivos de vehículos y nuevas estaciones."""
        from simulador import crear_estacion
        est_sur = crear_estacion(
            nombre="Sur - Terminal",
            potencia=20.0,
            precio=1800.0,
            vehiculos=[
                {"placa": "BUS-01", "nombre": "Bus Articulado", "llegada": 10.0, "kwh": 40.0},
                {"placa": "TAXI-05", "nombre": "Taxi Urbano", "llegada": 10.0, "kwh": 20.0}
            ]
        )
        self.assertEqual(est_sur["estacion"], "Sur - Terminal")
        self.assertEqual(est_sur["potencia"], 20.0)

        res = simular_estacion(est_sur, num_cargadores=2)
        asigs = {v["placa"]: v for v in res["asignaciones"]}
        self.assertEqual(asigs["BUS-01"]["nombre"], "Bus Articulado")
        self.assertEqual(asigs["BUS-01"]["duracion"], 2.0)  # 40 kWh / 20 kW = 2.0 h
        self.assertEqual(asigs["TAXI-05"]["nombre"], "Taxi Urbano")
        self.assertEqual(asigs["TAXI-05"]["duracion"], 1.0)  # 20 kWh / 20 kW = 1.0 h


if __name__ == "__main__":
    unittest.main()
