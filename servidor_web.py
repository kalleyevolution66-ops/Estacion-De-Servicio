"""
servidor_web.py
---------------
Servidor web nativo en Python (Librería Estándar: http.server).
Permite ejecutar y visualizar la aplicación completa de la Estación de Carga
directamente en el navegador web (Chrome, Edge, Firefox) sin necesidad de
instalar Streamlit ni usar Tkinter.
"""

import http.server
import socketserver
import socket
import json
import os
import urllib.parse
import webbrowser
from simulador import (
    cargar_datos,
    crear_estacion,
    simular_estacion,
    calcular_hora_pico,
    obtener_estado_en_instante,
    UMBRAL_ALERTA_ESPERA_HORAS
)

PUERTO = 8080
DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_JSON_DEFAULT = os.path.join(DIRECTORIO_BASE, "datos", "entrada.json")
ARCHIVO_HTML = os.path.join(DIRECTORIO_BASE, "web", "index.html")

# Estado global en memoria para la red de estaciones
estacion_inicial = cargar_datos(RUTA_JSON_DEFAULT)
RED_ESTACIONES = {
    estacion_inicial.get("estacion", "Norte"): estacion_inicial
}
ESTACION_ACTIVA = estacion_inicial.get("estacion", "Norte")
NUM_CARGADORES = 2


class ManejadorEstacionCarga(http.server.BaseHTTPRequestHandler):

    def _responder_json(self, datos: dict, codigo: int = 200):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _responder_html(self, ruta_archivo: str):
        if not os.path.exists(ruta_archivo):
            self.send_error(404, "Archivo HTML no encontrado")
            return
        with open(ruta_archivo, "rb") as f:
            contenido = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)

    def do_GET(self):
        global ESTACION_ACTIVA, NUM_CARGADORES

        parsed = urllib.parse.urlparse(self.path)
        ruta = parsed.path

        if ruta in ["/", "/index.html"]:
            self._responder_html(ARCHIVO_HTML)

        elif ruta == "/api/estado":
            datos_estacion = RED_ESTACIONES.get(ESTACION_ACTIVA, estacion_inicial)
            res_sim = simular_estacion(datos_estacion, num_cargadores=NUM_CARGADORES)
            pico = calcular_hora_pico(res_sim)

            respuesta = {
                "estaciones": list(RED_ESTACIONES.keys()),
                "estacion_activa": ESTACION_ACTIVA,
                "num_cargadores": NUM_CARGADORES,
                "resultado": res_sim,
                "pico": pico
            }
            self._responder_json(respuesta)

        elif ruta == "/api/estado_instante":
            params = urllib.parse.parse_qs(parsed.query)
            t_val = float(params.get("t", [8.0])[0])
            datos_estacion = RED_ESTACIONES.get(ESTACION_ACTIVA, estacion_inicial)
            res_sim = simular_estacion(datos_estacion, num_cargadores=NUM_CARGADORES)
            estados = obtener_estado_en_instante(res_sim, t_val)
            self._responder_json({"tiempo": t_val, "estados": estados})

        else:
            self.send_error(404, "Ruta no encontrada")

    def do_POST(self):
        global ESTACION_ACTIVA, NUM_CARGADORES

        parsed = urllib.parse.urlparse(self.path)
        ruta = parsed.path
        longitud = int(self.headers.get("Content-Length", 0))
        cuerpo_raw = self.rfile.read(longitud).decode("utf-8") if longitud > 0 else "{}"
        try:
            datos_post = json.loads(cuerpo_raw)
        except json.JSONDecodeError:
            datos_post = {}

        if ruta == "/api/cambiar_estacion":
            nueva_est = datos_post.get("estacion")
            if nueva_est in RED_ESTACIONES:
                ESTACION_ACTIVA = nueva_est
                self._responder_json({"exito": True, "estacion": ESTACION_ACTIVA})
            else:
                self._responder_json({"exito": False, "error": "Estación no encontrada"}, 400)

        elif ruta == "/api/cargadores":
            n = int(datos_post.get("num_cargadores", 2))
            NUM_CARGADORES = max(1, min(6, n))
            self._responder_json({"exito": True, "num_cargadores": NUM_CARGADORES})

        elif ruta == "/api/nueva_estacion":
            nombre = datos_post.get("nombre", "").strip()
            potencia = float(datos_post.get("potencia", 10.0))
            precio = float(datos_post.get("precio", 1500.0))
            if nombre:
                RED_ESTACIONES[nombre] = crear_estacion(nombre, potencia, precio)
                ESTACION_ACTIVA = nombre
                self._responder_json({"exito": True, "estacion": nombre})
            else:
                self._responder_json({"exito": False, "error": "Nombre requerido"}, 400)

        elif ruta == "/api/nuevo_vehiculo":
            placa = datos_post.get("placa", "").strip().upper()
            nombre = datos_post.get("nombre", f"Vehículo {placa}").strip()
            llegada = float(datos_post.get("llegada", 8.0))
            kwh = float(datos_post.get("kwh", 10.0))

            if placa and kwh > 0:
                RED_ESTACIONES[ESTACION_ACTIVA]["vehiculos"].append({
                    "placa": placa,
                    "nombre": nombre,
                    "llegada": llegada,
                    "kwh": kwh
                })
                self._responder_json({"exito": True})
            else:
                self._responder_json({"exito": False, "error": "Datos inválidos"}, 400)

        elif ruta == "/api/restablecer":
            if ESTACION_ACTIVA == "Norte":
                RED_ESTACIONES["Norte"] = cargar_datos(RUTA_JSON_DEFAULT)
            else:
                RED_ESTACIONES[ESTACION_ACTIVA]["vehiculos"] = []
            self._responder_json({"exito": True})

        else:
            self.send_error(404, "Endpoint no encontrado")

    def log_message(self, format, *args):
        # Desactivar logs ruidosos en consola para mantenerla limpia
        pass


def obtener_ip_local():
    """Detecta la IP local de este equipo en la red LAN / Wi-Fi."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def iniciar_servidor():
    url_local = f"http://localhost:{PUERTO}"
    ip_red = obtener_ip_local()
    url_red = f"http://{ip_red}:{PUERTO}"

    print("=" * 72)
    print("⚡ SISTEMA WEB SCADA - ESTACIÓN DE CARGA DE VEHÍCULOS ELÉCTRICOS")
    print("=" * 72)
    print(f" 💻 Acceso local (en este PC):       {url_local}")
    print(f" 📶 Acceso en misma red Wi-Fi / LAN: {url_red}")
    print("-" * 72)
    print(" 🌐 ¿CÓMO HACERLA PÚBLICA PARA COMPARTIR EN CUALQUIER LUGAR?")
    print(f"    Ejecuta en OTRA terminal de PowerShell el comando de túnel:")
    print(f"    ssh -p 443 -R0:localhost:{PUERTO} a.pinggy.io")
    print("    (Te entregará un enlace https://... público gratis al instante)")
    print("=" * 72)
    print(" Abriendo aplicación en tu navegador...")
    print(" Para detener el servidor presiona Ctrl + C en esta consola.")
    print("=" * 72)

    # Abrir navegador automáticamente
    try:
        webbrowser.open(url)
    except Exception:
        pass

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PUERTO), ManejadorEstacionCarga) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n Servidor web detenido correctamente.")


if __name__ == "__main__":
    iniciar_servidor()
