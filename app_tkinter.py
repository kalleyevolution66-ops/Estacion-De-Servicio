"""
app_tkinter.py
--------------
Aplicación de escritorio interactiva en Tkinter (Librería Estándar de Python).
Diseño intuitivo y profesional con bahías de carga dinámicas y sincronización
visual de la aguja temporal en el diagrama de Gantt.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
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
# CONFIGURACIÓN Y PALETA DE COLORES (MODULAR PARA SUSTENTACIÓN)
# ==============================================================================
COLORES_VEHICULOS = [
    "#2563EB",  # Azul eléctrico
    "#10B981",  # Verde esmeralda
    "#8B5CF6",  # Púrpura moderno
    "#F59E0B",  # Ámbar dorado
    "#EC4899",  # Rosa moderno
    "#06B6D4"   # Cian eléctrico
]

COLOR_BG = "#F8FAFC"
COLOR_CARD = "#FFFFFF"
COLOR_TEXT = "#0F172A"
COLOR_TEXT_MUTED = "#64748B"
COLOR_LIBRE = "#10B981"
COLOR_OCUPADO = "#2563EB"
COLOR_ESPERA = "#94A3B8"
COLOR_AGUJA = "#DC2626"


class AppEstacionCarga(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⚡ Centro de Control EV - Estación de Carga")
        self.geometry("1120x860")
        self.minsize(980, 750)
        self.configure(bg=COLOR_BG)

        # Cargar datos base y soporte multi-estación
        self.ruta_archivo = os.path.join(os.path.dirname(__file__), "datos", "entrada.json")
        estacion_base = cargar_datos(self.ruta_archivo)
        self.estaciones = {estacion_base.get("estacion", "Norte"): estacion_base}
        self.var_estacion_activa = tk.StringVar(value=estacion_base.get("estacion", "Norte"))
        self.datos = self.estaciones[self.var_estacion_activa.get()]

        # Variables reactivas
        self.var_num_cargadores = tk.IntVar(value=2)
        self.var_tiempo_slider = tk.DoubleVar(value=8.0)

        self.resultado = None
        self.pico = None
        self.cards_bahias = []
        self.gantt_params = {}

        self._crear_interfaz()
        self.ejecutar_simulacion()

    def _crear_interfaz(self):
        # 1. Barra Superior (Header moderno)
        frame_header = tk.Frame(self, bg="#1E3A8A", padx=20, pady=14)
        frame_header.pack(fill=tk.X, side=tk.TOP)

        self.lbl_tit = tk.Label(
            frame_header,
            text=f"⚡ Red EV | Estación {self.var_estacion_activa.get()}",
            font=("Helvetica", 15, "bold"),
            bg="#1E3A8A",
            fg="#FFFFFF"
        )
        self.lbl_tit.pack(side=tk.LEFT)

        frame_controles_top = tk.Frame(frame_header, bg="#1E3A8A")
        frame_controles_top.pack(side=tk.RIGHT)

        # Selector de Estación
        lbl_sel_est = tk.Label(frame_controles_top, text="Estación:", font=("Helvetica", 9, "bold"), bg="#1E3A8A", fg="#E2E8F0")
        lbl_sel_est.pack(side=tk.LEFT, padx=(2, 2))

        self.combo_estaciones = ttk.Combobox(
            frame_controles_top,
            textvariable=self.var_estacion_activa,
            values=list(self.estaciones.keys()),
            state="readonly",
            width=9,
            font=("Helvetica", 9, "bold")
        )
        self.combo_estaciones.pack(side=tk.LEFT, padx=3)
        self.combo_estaciones.bind("<<ComboboxSelected>>", self._al_cambiar_estacion)

        btn_nueva_est = tk.Button(
            frame_controles_top,
            text="🏢 + Estación",
            command=self._abrir_dialogo_nueva_estacion,
            font=("Helvetica", 9, "bold"),
            bg="#0284C7",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=8,
            pady=3,
            cursor="hand2"
        )
        btn_nueva_est.pack(side=tk.LEFT, padx=3)

        btn_cargar = tk.Button(
            frame_controles_top,
            text="📂 JSON",
            command=self._cargar_archivo_dialogo,
            font=("Helvetica", 9, "bold"),
            bg="#3B82F6",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=8,
            pady=3,
            cursor="hand2"
        )
        btn_cargar.pack(side=tk.LEFT, padx=3)

        btn_registrar = tk.Button(
            frame_controles_top,
            text="➕ Vehículo",
            command=self._abrir_dialogo_registro,
            font=("Helvetica", 9, "bold"),
            bg="#10B981",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=8,
            pady=3,
            cursor="hand2"
        )
        btn_registrar.pack(side=tk.LEFT, padx=3)

        btn_reset = tk.Button(
            frame_controles_top,
            text="🔄 Reset",
            command=self._restablecer_datos,
            font=("Helvetica", 9, "bold"),
            bg="#475569",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=8,
            pady=3,
            cursor="hand2"
        )
        btn_reset.pack(side=tk.LEFT, padx=3)

        lbl_carg = tk.Label(frame_controles_top, text="Cargadores:", font=("Helvetica", 9, "bold"), bg="#1E3A8A", fg="#E2E8F0")
        lbl_carg.pack(side=tk.LEFT, padx=(6, 2))

        spin_carg = ttk.Spinbox(
            frame_controles_top,
            from_=1,
            to=6,
            width=3,
            textvariable=self.var_num_cargadores,
            command=self.ejecutar_simulacion,
            font=("Helvetica", 10, "bold")
        )
        spin_carg.pack(side=tk.LEFT, padx=2)

        # 2. Contenedor Principal con Scroll
        self.canvas_scroll = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas_scroll.yview)
        self.frame_contenido = tk.Frame(self.canvas_scroll, bg=COLOR_BG, padx=20, pady=14)

        self.frame_contenido.bind(
            "<Configure>",
            lambda e: self.canvas_scroll.configure(scrollregion=self.canvas_scroll.bbox("all"))
        )
        self.canvas_scroll.create_window((0, 0), window=self.frame_contenido, anchor="nw", width=1070)
        self.canvas_scroll.configure(yscrollcommand=self.scrollbar.set)

        self.canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Secciones
        self._crear_seccion_kpis()
        self._crear_seccion_monitoreo_vivo()
        self._crear_seccion_gantt()

    def _crear_seccion_kpis(self):
        # Banner de Alerta (oculto por defecto)
        self.frame_alerta = tk.Frame(self.frame_contenido, bg="#FEF2F2", bd=1, relief=tk.SOLID, padx=14, pady=8)
        self.lbl_alerta = tk.Label(
            self.frame_alerta,
            text="",
            font=("Helvetica", 10, "bold"),
            bg="#FEF2F2",
            fg="#991B1B",
            justify=tk.LEFT
        )
        self.lbl_alerta.pack(anchor="w")

        # Tarjetas de Métricas Ejecutivas
        self.frame_kpis = tk.Frame(self.frame_contenido, bg=COLOR_BG)
        self.frame_kpis.pack(fill=tk.X, pady=(6, 12))

        self.card_espera = self._crear_card_metrica(self.frame_kpis, "⏱️ ESPERA TOTAL", "0.0 h", "#EF4444", "Tiempo en cola")
        self.card_espera.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

        self.card_energia = self._crear_card_metrica(self.frame_kpis, "⚡ ENERGÍA VENDIDA", "0.0 kWh", "#2563EB", "Demanda total")
        self.card_energia.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

        self.card_ingresos = self._crear_card_metrica(self.frame_kpis, "💰 INGRESOS TOTALES", "$0", "#059669", "Facturación")
        self.card_ingresos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

        self.card_pico = self._crear_card_metrica(self.frame_kpis, "🔥 HORA PICO (RETO)", "--", "#D97706", "Máxima ocupación")
        self.card_pico.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

    def _crear_card_metrica(self, parent, titulo, valor, color_val, subtitulo):
        f = tk.Frame(parent, bg=COLOR_CARD, relief=tk.FLAT, bd=1, padx=14, pady=10)
        # Borde simulado sutil
        f.configure(highlightbackground="#E2E8F0", highlightthickness=1)
        lbl_t = tk.Label(f, text=titulo, font=("Helvetica", 8, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD)
        lbl_t.pack(anchor="w")
        lbl_v = tk.Label(f, text=valor, font=("Helvetica", 17, "bold"), fg=color_val, bg=COLOR_CARD)
        lbl_v.pack(anchor="w", pady=2)
        lbl_sub = tk.Label(f, text=subtitulo, font=("Helvetica", 8), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD)
        lbl_sub.pack(anchor="w")
        f.lbl_valor = lbl_v
        f.lbl_sub = lbl_sub
        return f

    def _crear_seccion_monitoreo_vivo(self):
        lbl_sec = tk.Label(
            self.frame_contenido,
            text="🔌 Monitoreo de Bahías en Tiempo Real (Deslizador Horario)",
            font=("Helvetica", 12, "bold"),
            bg=COLOR_BG,
            fg=COLOR_TEXT
        )
        lbl_sec.pack(anchor="w", pady=(8, 4))

        frame_ctrl_tiempo = tk.Frame(self.frame_contenido, bg=COLOR_CARD, padx=16, pady=10)
        frame_ctrl_tiempo.configure(highlightbackground="#E2E8F0", highlightthickness=1)
        frame_ctrl_tiempo.pack(fill=tk.X, pady=4)

        self.lbl_reloj = tk.Label(
            frame_ctrl_tiempo,
            text="🕒 Hora de Inspección: 08:00 h",
            font=("Helvetica", 11, "bold"),
            bg=COLOR_CARD,
            fg="#2563EB"
        )
        self.lbl_reloj.pack(side=tk.LEFT, padx=(0, 16))

        self.slider_tiempo = ttk.Scale(
            frame_ctrl_tiempo,
            from_=8.0,
            to=12.0,
            orient=tk.HORIZONTAL,
            variable=self.var_tiempo_slider,
            command=self._al_mover_slider
        )
        self.slider_tiempo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Contenedor de las tarjetas de cargadores (Bahías)
        self.frame_cards_bays = tk.Frame(self.frame_contenido, bg=COLOR_BG)
        self.frame_cards_bays.pack(fill=tk.X, pady=8)

    def _crear_seccion_gantt(self):
        lbl_sec = tk.Label(
            self.frame_contenido,
            text="📅 Programación y Despacho Temporal (Diagrama de Gantt)",
            font=("Helvetica", 12, "bold"),
            bg=COLOR_BG,
            fg=COLOR_TEXT
        )
        lbl_sec.pack(anchor="w", pady=(10, 4))

        frame_gantt = tk.Frame(self.frame_contenido, bg=COLOR_CARD, padx=12, pady=12)
        frame_gantt.configure(highlightbackground="#E2E8F0", highlightthickness=1)
        frame_gantt.pack(fill=tk.X, pady=4)

        self.canvas_gantt = tk.Canvas(frame_gantt, height=210, bg="#FAFAFA", highlightthickness=0)
        self.canvas_gantt.pack(fill=tk.BOTH, expand=True)

        lbl_leyenda = tk.Label(
            frame_gantt,
            text="Leyenda:  [🟦 Bloque de Color = Vehículo Cargando]   [🏁 Tramo Gris = Espera en Cola]   [📍 Línea Roja = Hora Seleccionada]",
            font=("Helvetica", 9),
            bg=COLOR_CARD,
            fg=COLOR_TEXT_MUTED
        )
        lbl_leyenda.pack(anchor="w", pady=(8, 0))

    def _al_cambiar_estacion(self, event=None):
        """Cambia la estación activa seleccionada en el combo."""
        nom = self.var_estacion_activa.get()
        if nom in self.estaciones:
            self.datos = self.estaciones[nom]
            self.lbl_tit.config(text=f"⚡ Red EV | Estación {nom}")
            self.ejecutar_simulacion()

    def _abrir_dialogo_nueva_estacion(self):
        """Abre un diálogo modal para crear una nueva estación de carga en la red."""
        dialogo = tk.Toplevel(self)
        dialogo.title("🏢 Nueva Estación de Carga")
        dialogo.geometry("340x260")
        dialogo.resizable(False, False)
        dialogo.configure(bg="#FFFFFF")
        dialogo.transient(self)
        dialogo.grab_set()

        tk.Label(dialogo, text="Registrar Nueva Estación", font=("Helvetica", 11, "bold"), bg="#FFFFFF", fg="#1E3A8A").pack(pady=(12, 8))

        f_form = tk.Frame(dialogo, bg="#FFFFFF", padx=16)
        f_form.pack(fill=tk.BOTH, expand=True)

        tk.Label(f_form, text="Nombre:", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg=COLOR_TEXT).grid(row=0, column=0, sticky="w", pady=4)
        entry_nom = tk.Entry(f_form, font=("Helvetica", 10))
        entry_nom.insert(0, "Sur")
        entry_nom.grid(row=0, column=1, sticky="ew", pady=4, padx=(8, 0))

        tk.Label(f_form, text="Potencia (kW):", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg=COLOR_TEXT).grid(row=1, column=0, sticky="w", pady=4)
        entry_pot = tk.Entry(f_form, font=("Helvetica", 10))
        entry_pot.insert(0, "20.0")
        entry_pot.grid(row=1, column=1, sticky="ew", pady=4, padx=(8, 0))

        tk.Label(f_form, text="Precio ($/kWh):", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg=COLOR_TEXT).grid(row=2, column=0, sticky="w", pady=4)
        entry_prec = tk.Entry(f_form, font=("Helvetica", 10))
        entry_prec.insert(0, "1600.0")
        entry_prec.grid(row=2, column=1, sticky="ew", pady=4, padx=(8, 0))

        def confirmar_estacion():
            nom = entry_nom.get().strip()
            if not nom:
                messagebox.showwarning("Dato requerido", "Por favor ingrese un nombre de estación.", parent=dialogo)
                return
            try:
                pot = float(entry_pot.get().strip())
                prec = float(entry_prec.get().strip())
                if pot <= 0 or prec <= 0:
                    messagebox.showwarning("Dato inválido", "Potencia y precio deben ser mayores a 0.", parent=dialogo)
                    return
                nueva = crear_estacion(nom, pot, prec)
                self.estaciones[nom] = nueva
                self.combo_estaciones["values"] = list(self.estaciones.keys())
                self.var_estacion_activa.set(nom)
                self.datos = self.estaciones[nom]
                self.lbl_tit.config(text=f"⚡ Red EV | Estación {nom}")
                dialogo.destroy()
                self.ejecutar_simulacion()
                messagebox.showinfo("Estación Creada", f"Estación '{nom}' creada exitosamente ({pot} kW, ${prec:,.0f}/kWh).")
            except ValueError:
                messagebox.showerror("Error", "Potencia y precio deben ser valores numéricos.", parent=dialogo)

        btn_crear = tk.Button(dialogo, text="Crear Estación", command=confirmar_estacion, bg="#0284C7", fg="#FFFFFF", font=("Helvetica", 10, "bold"), relief=tk.FLAT, pady=4)
        btn_crear.pack(fill=tk.X, padx=16, pady=(0, 14))

    def _cargar_archivo_dialogo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo JSON",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
        )
        if ruta:
            try:
                datos_cargados = cargar_datos(ruta)
                self.ruta_archivo = ruta
                nom = datos_cargados.get("estacion", "Importada")
                self.estaciones[nom] = datos_cargados
                self.combo_estaciones["values"] = list(self.estaciones.keys())
                self.var_estacion_activa.set(nom)
                self.datos = self.estaciones[nom]
                self.lbl_tit.config(text=f"⚡ Red EV | Estación {nom}")
                messagebox.showinfo("Éxito", f"Datos cargados para estación '{nom}'.")
                self.ejecutar_simulacion()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")

    def _abrir_dialogo_registro(self):
        """Abre un diálogo modal para registrar un vehículo manualmente con nombre y hora."""
        dialogo = tk.Toplevel(self)
        dialogo.title("➕ Registrar Vehículo")
        dialogo.geometry("340x280")
        dialogo.resizable(False, False)
        dialogo.configure(bg="#FFFFFF")
        dialogo.transient(self)
        dialogo.grab_set()

        nom_est = self.datos.get("estacion", "Estación")
        tk.Label(dialogo, text=f"Registrar Vehículo en {nom_est}", font=("Helvetica", 11, "bold"), bg="#FFFFFF", fg="#1E3A8A").pack(pady=(10, 6))

        f_form = tk.Frame(dialogo, bg="#FFFFFF", padx=16)
        f_form.pack(fill=tk.BOTH, expand=True)

        tk.Label(f_form, text="Nombre/Modelo:", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg=COLOR_TEXT).grid(row=0, column=0, sticky="w", pady=3)
        entry_nombre = tk.Entry(f_form, font=("Helvetica", 10))
        entry_nombre.insert(0, "Tesla Model 3")
        entry_nombre.grid(row=0, column=1, sticky="ew", pady=3, padx=(8, 0))

        tk.Label(f_form, text="Placa:", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg=COLOR_TEXT).grid(row=1, column=0, sticky="w", pady=3)
        entry_placa = tk.Entry(f_form, font=("Helvetica", 10))
        entry_placa.insert(0, "E")
        entry_placa.grid(row=1, column=1, sticky="ew", pady=3, padx=(8, 0))

        tk.Label(f_form, text="Hora Llegada (h):", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg=COLOR_TEXT).grid(row=2, column=0, sticky="w", pady=3)
        entry_llegada = tk.Entry(f_form, font=("Helvetica", 10))
        entry_llegada.insert(0, "10.0")
        entry_llegada.grid(row=2, column=1, sticky="ew", pady=3, padx=(8, 0))

        tk.Label(f_form, text="Energía (kWh):", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg=COLOR_TEXT).grid(row=3, column=0, sticky="w", pady=3)
        entry_kwh = tk.Entry(f_form, font=("Helvetica", 10))
        entry_kwh.insert(0, "15.0")
        entry_kwh.grid(row=3, column=1, sticky="ew", pady=3, padx=(8, 0))

        def confirmar():
            nombre = entry_nombre.get().strip()
            placa = entry_placa.get().strip().upper()
            try:
                llegada = float(entry_llegada.get().strip())
                kwh = float(entry_kwh.get().strip())
                if not placa:
                    messagebox.showwarning("Dato requerido", "Por favor ingrese una placa.", parent=dialogo)
                    return
                if not nombre:
                    nombre = f"Vehículo {placa}"
                if kwh <= 0:
                    messagebox.showwarning("Dato inválido", "Los kWh deben ser mayores a 0.", parent=dialogo)
                    return
                self.datos["vehiculos"].append({
                    "placa": placa,
                    "nombre": nombre,
                    "llegada": llegada,
                    "kwh": kwh
                })
                dialogo.destroy()
                self.ejecutar_simulacion()
            except ValueError:
                messagebox.showerror("Error de formato", "Hora y kWh deben ser valores numéricos.", parent=dialogo)

        btn_guardar = tk.Button(dialogo, text="Guardar en Fila", command=confirmar, bg="#10B981", fg="#FFFFFF", font=("Helvetica", 10, "bold"), relief=tk.FLAT, pady=4)
        btn_guardar.pack(fill=tk.X, padx=16, pady=(0, 12))

    def _restablecer_datos(self):
        """Restaura los datos iniciales de la estación activa o la red."""
        nom_activa = self.var_estacion_activa.get()
        if nom_activa == "Norte":
            self.estaciones["Norte"] = cargar_datos(self.ruta_archivo)
            self.datos = self.estaciones["Norte"]
            messagebox.showinfo("Restablecido", "Estación 'Norte' restablecida a la flota oficial (A, B, C, D).")
        else:
            self.datos["vehiculos"] = []
            messagebox.showinfo("Restablecido", f"Flota de estación '{nom_activa}' limpiada.")
        self.ejecutar_simulacion()

    def ejecutar_simulacion(self):
        try:
            n_cargadores = int(self.var_num_cargadores.get())
        except ValueError:
            n_cargadores = 2

        self.resultado = simular_estacion(self.datos, num_cargadores=n_cargadores)
        self.pico = calcular_hora_pico(self.resultado)

        # Actualizar KPIs
        self.card_espera.lbl_valor.config(
            text=f"{self.resultado['espera_total']:.1f} h",
            fg="#EF4444" if self.resultado["espera_total"] > 0 else "#10B981"
        )
        self.card_espera.lbl_sub.config(text=f"{self.resultado['espera_total'] * 60:.0f} min acumulados")

        self.card_energia.lbl_valor.config(text=f"{self.resultado['energia_total']:.1f} kWh")
        self.card_ingresos.lbl_valor.config(text=f"${self.resultado['ingresos_totales']:,.0f}")
        self.card_pico.lbl_valor.config(
            text=f"{self.pico['intervalo_pico']}"
        )
        self.card_pico.lbl_sub.config(
            text=f"{self.pico['max_vehiculos_simultaneos']} cargadores ({self.pico['porcentaje_ocupacion_pico']}%)"
        )

        # Alerta
        if self.resultado["alertas_espera"]:
            placas = ", ".join([f"{v['placa']} ({v['espera']:.1f} h)" for v in self.resultado["alertas_espera"]])
            self.lbl_alerta.config(
                text=f"🚨 ALERTA DE SERVICIO: Vehículo(s) {placas} superan el umbral de 1 hora de espera.\n"
                     f"💡 Sugerencia: Aumente los cargadores a {min(6, n_cargadores + 1)} para eliminar demoras."
            )
            self.frame_alerta.pack(fill=tk.X, pady=(2, 8), before=self.frame_kpis)
        else:
            self.frame_alerta.pack_forget()

        # Ajuste de límites temporales
        asigs = self.resultado["asignaciones"]
        h_min = min(v["llegada"] for v in asigs) if asigs else 8.0
        h_max = max(v["hora_fin"] for v in asigs) if asigs else 12.0

        self.slider_tiempo.config(from_=h_min, to=h_max)
        if self.var_tiempo_slider.get() < h_min or self.var_tiempo_slider.get() > h_max:
            self.var_tiempo_slider.set(h_min)

        # 1. Dibujar estructura estática del diagrama de Gantt (una sola vez por simulación)
        self._dibujar_gantt_estatico(h_min, h_max)
        # 2. Crear las tarjetas de bahías (una sola vez por simulación)
        self._crear_cards_bahias()
        # 3. Posicionar aguja y valores iniciales
        t_inicial = float(self.var_tiempo_slider.get())
        self._actualizar_aguja_gantt(t_inicial)
        self._actualizar_valores_bahias(t_inicial)

    def _al_mover_slider(self, val=None):
        """Manejador ultrarrápido sin parpadeo: actualiza exclusivamente valores en memoria."""
        try:
            t = float(self.var_tiempo_slider.get())
        except (ValueError, TypeError):
            return
        self._actualizar_aguja_gantt(t)
        self._actualizar_valores_bahias(t)

    def _dibujar_gantt_estatico(self, h_min, h_max):
        """Dibuja las pistas y bloques de carga estáticos una sola vez (fondo permanente)."""
        self.canvas_gantt.delete("all")
        asigs = self.resultado["asignaciones"]
        n_carg = self.resultado["num_cargadores"]

        w_canvas = 990
        alto_fila = 42
        margen_izq = 110
        margen_der = 50
        margen_sup = 28
        h_total = margen_sup + (n_carg * alto_fila) + 38

        self.canvas_gantt.config(height=h_total)

        duracion_total = max(1.0, h_max - h_min)
        ancho_util = w_canvas - margen_izq - margen_der

        # Parámetros almacenados para traslación inmediata de la aguja
        self.gantt_params = {
            "h_min": h_min,
            "h_max": h_max,
            "duracion_total": duracion_total,
            "margen_izq": margen_izq,
            "ancho_util": ancho_util,
            "margen_sup": margen_sup,
            "h_total": h_total
        }

        def x_pos(h):
            return margen_izq + ((h - h_min) / duracion_total) * ancho_util

        # Líneas guía de horas
        h_tick = int(h_min)
        while h_tick <= int(h_max) + 1:
            if h_min <= h_tick <= h_max:
                xt = x_pos(h_tick)
                self.canvas_gantt.create_line(xt, margen_sup, xt, h_total - 25, fill="#E2E8F0", dash=(2, 2))
                self.canvas_gantt.create_text(xt, h_total - 12, text=f"{h_tick:02d}:00", font=("Helvetica", 9, "bold"), fill=COLOR_TEXT_MUTED)
            h_tick += 1

        # Carriles de cargadores
        for c in range(1, n_carg + 1):
            yc = margen_sup + (c - 1) * alto_fila
            self.canvas_gantt.create_rectangle(margen_izq, yc + 4, margen_izq + ancho_util, yc + alto_fila - 4, fill="#F8FAFC", outline="#E2E8F0")
            self.canvas_gantt.create_text(18, yc + (alto_fila / 2), anchor="w", text=f"Cargador {c}", font=("Helvetica", 10, "bold"), fill=COLOR_TEXT)

        # Colores por vehículo
        placas = sorted(list({v["placa"] for v in asigs}))
        color_map = {p: COLORES_VEHICULOS[i % len(COLORES_VEHICULOS)] for i, p in enumerate(placas)}

        for v in asigs:
            c = v["cargador"]
            yc = margen_sup + (c - 1) * alto_fila
            y1 = yc + 6
            y2 = yc + alto_fila - 6

            # Espera rayada
            if v["espera"] > 0:
                x_arr = x_pos(v["llegada"])
                x_ini = x_pos(v["hora_inicio"])
                self.canvas_gantt.create_rectangle(x_arr, y1, x_ini, y2, fill=COLOR_ESPERA, outline="#64748B", stipple="gray50")
                if (x_ini - x_arr) > 28:
                    self.canvas_gantt.create_text((x_arr + x_ini) / 2, (y1 + y2) / 2, text=f"Esp. {v['placa']}", font=("Helvetica", 8, "bold"), fill="#0F172A")

            # Carga activa
            x_ini = x_pos(v["hora_inicio"])
            x_fin = x_pos(v["hora_fin"])
            col_v = color_map.get(v["placa"], "#2563EB")
            self.canvas_gantt.create_rectangle(x_ini, y1, x_fin, y2, fill=col_v, outline="#1E40AF", width=1)
            
            w_box = x_fin - x_ini
            nom_v = v.get("nombre", v["placa"])
            if nom_v != v["placa"] and w_box > 100:
                txt_v = f"🚗 {v['placa']} - {nom_v} ({v['kwh']:.0f}k)"
            elif w_box > 50:
                txt_v = f"🚗 {v['placa']} ({v['kwh']:.0f} kWh)"
            else:
                txt_v = f"🚗 {v['placa']}"
            self.canvas_gantt.create_text((x_ini + x_fin) / 2, (y1 + y2) / 2, text=txt_v, font=("Helvetica", 8, "bold"), fill="#FFFFFF")

    def _actualizar_aguja_gantt(self, t_cursor):
        """Mueve exclusivamente la aguja y badge temporal sin redibujar el fondo."""
        self.canvas_gantt.delete("aguja")
        if not self.gantt_params:
            return

        h_min = self.gantt_params["h_min"]
        h_max = self.gantt_params["h_max"]
        margen_izq = self.gantt_params["margen_izq"]
        ancho_util = self.gantt_params["ancho_util"]
        duracion_total = self.gantt_params["duracion_total"]
        margen_sup = self.gantt_params["margen_sup"]
        h_total = self.gantt_params["h_total"]

        if h_min <= t_cursor <= h_max:
            x_cur = margen_izq + ((t_cursor - h_min) / duracion_total) * ancho_util
            self.canvas_gantt.create_line(x_cur, margen_sup - 8, x_cur, h_total - 25, fill=COLOR_AGUJA, width=2, dash=(4, 2), tags="aguja")
            h_c = int(t_cursor)
            m_c = int((t_cursor - h_c) * 60)
            self.canvas_gantt.create_rectangle(x_cur - 26, margen_sup - 22, x_cur + 26, margen_sup - 4, fill=COLOR_AGUJA, outline="", tags="aguja")
            self.canvas_gantt.create_text(x_cur, margen_sup - 13, text=f"{h_c:02d}:{m_c:02d}", font=("Helvetica", 8, "bold"), fill="#FFFFFF", tags="aguja")

    def _crear_cards_bahias(self):
        """Construye las tarjetas de bahías una sola vez al cambiar cargadores (evita destruir widgets)."""
        for child in self.frame_cards_bays.winfo_children():
            child.destroy()
        self.cards_bahias = []

        num_carg = self.resultado["num_cargadores"]
        for c_id in range(1, num_carg + 1):
            f_card = tk.Frame(self.frame_cards_bays, bg=COLOR_CARD, padx=14, pady=12)
            f_card.configure(highlightbackground="#E2E8F0", highlightthickness=1.5)
            f_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            # Encabezado
            f_head = tk.Frame(f_card, bg=COLOR_CARD)
            f_head.pack(fill=tk.X, pady=(0, 6))

            lbl_titulo = tk.Label(f_head, text=f"⚡ Bahía {c_id}", font=("Helvetica", 11, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT)
            lbl_titulo.pack(side=tk.LEFT)

            lbl_badge = tk.Label(f_head, text="DISPONIBLE", font=("Helvetica", 8, "bold"), bg="#DCFCE7", fg="#15803D", padx=8, pady=2)
            lbl_badge.pack(side=tk.RIGHT)

            # Contenido informativo con alturas estables
            lbl_estado_veh = tk.Label(f_card, text="Estado: Libre para conectar", font=("Helvetica", 9, "bold"), bg=COLOR_CARD, fg="#10B981")
            lbl_estado_veh.pack(anchor="w")

            lbl_energia = tk.Label(f_card, text=f"Potencia disponible: {self.resultado['potencia']} kW", font=("Helvetica", 8), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED)
            lbl_energia.pack(anchor="w")

            lbl_fin = tk.Label(f_card, text="Flujo: 0.0 kW", font=("Helvetica", 8), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED)
            lbl_fin.pack(anchor="w")

            lbl_bateria = tk.Label(f_card, text="Batería: 0.0%", font=("Helvetica", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT)
            lbl_bateria.pack(anchor="w", pady=(6, 2))

            pb = ttk.Progressbar(f_card, value=0.0, maximum=100)
            pb.pack(fill=tk.X, expand=True)

            self.cards_bahias.append({
                "cargador": c_id,
                "frame": f_card,
                "lbl_badge": lbl_badge,
                "lbl_estado_veh": lbl_estado_veh,
                "lbl_energia": lbl_energia,
                "lbl_fin": lbl_fin,
                "lbl_bateria": lbl_bateria,
                "progressbar": pb
            })

    def _actualizar_valores_bahias(self, t):
        """Actualiza el texto y las barras de progreso sin alterar el layout ni destruir widgets."""
        h_ent = int(t)
        mins = int((t - h_ent) * 60)
        self.lbl_reloj.config(text=f"🕒 Hora Seleccionada: {h_ent:02d}:{mins:02d} ({t:.2f} h)")

        estados = obtener_estado_en_instante(self.resultado, t)

        for i, est in enumerate(estados):
            if i >= len(self.cards_bahias):
                break
            card = self.cards_bahias[i]
            es_ocupado = est["estado"] == "Ocupado"

            if es_ocupado:
                card["frame"].configure(highlightbackground="#93C5FD")
                card["lbl_badge"].config(
                    text=f"CARGANDO ({est['placa']})",
                    bg="#DBEAFE",
                    fg="#1D4ED8"
                )
                nombre_mostrado = est.get("nombre", f"Vehículo {est['placa']}")
                card["lbl_estado_veh"].config(
                    text=f"{nombre_mostrado} ({est['placa']})",
                    fg="#2563EB"
                )
                card["lbl_energia"].config(
                    text=f"Energía: {est['kwh_entregados']:.1f} / {est['kwh_totales']:.1f} kWh"
                )
                card["lbl_fin"].config(
                    text=f"Fin Estimado: {est['hora_fin']:.2f} h"
                )
                card["lbl_bateria"].config(
                    text=f"Batería: {est['progreso_pct']:.1f}%"
                )
                card["progressbar"]["value"] = est["progreso_pct"]
            else:
                card["frame"].configure(highlightbackground="#86EFAC")
                card["lbl_badge"].config(
                    text="DISPONIBLE",
                    bg="#DCFCE7",
                    fg="#15803D"
                )
                card["lbl_estado_veh"].config(
                    text="Estado: Libre para conectar",
                    fg="#10B981"
                )
                card["lbl_energia"].config(
                    text=f"Potencia disponible: {self.resultado['potencia']} kW"
                )
                card["lbl_fin"].config(
                    text="Flujo: 0.0 kW"
                )
                card["lbl_bateria"].config(
                    text="Batería: 0.0%"
                )
                card["progressbar"]["value"] = 0.0


if __name__ == "__main__":
    app = AppEstacionCarga()
    app.mainloop()
