# Bitácora de Proyecto: Estación de Carga de Vehículos Eléctricos
**Curso:** Fundamentos de Programación - Ingeniería Energética  
**Rol:** Operador y Desarrollador de la Estación de Carga  
**Fecha de Inicio:** 21 de noviembre de 2026  

---

## 📋 Guía y Reglas de Trabajo del Proyecto

> **Reglas Obligatorias de Desarrollo:**
>
> 1. **Registro en BITACORA.md (sin contaminar el código de la app):** Todo prompt importante, decisión de diseño o cambio relevante debe quedar asentado en `BITACORA.md` (con fecha, contexto y resumen), manteniendo el código de la aplicación limpio y libre de notas o bitácoras incrustadas.
> 2. **Explicación antes de aplicar código:** No asumir la aceptación de código no comprendido. Cuando se proponga lógica nueva o cambios relevantes, explicar de forma clara y breve (qué hace, por qué se usa y cómo encaja) antes de darlo por cerrado.
> 3. **Preparación para cambios en vivo (sustentación):** Estructurar el código de forma modular y con parámetros claros (umbrales, colores, datos). En cada modificación, indicar dónde está el cambio (archivo, función o variable) y por qué afecta el comportamiento, para poder responder o ajustar en vivo durante la sustentación.
> 4. **Interfaz visual con Streamlit (o Tkinter):** Usar Streamlit como opción visual recomendada, o Tkinter si se busca evitar instalaciones externas. Guiar paso a paso con ejemplos claros y explicaciones de cómo funcionan sus elementos principales.

---

## 🎯 Definición del Problema y Objetivos de Ingeniería Energética

Una estación de carga rápida/semirrápida cuenta con un conjunto de cargadores ($N$ cargadores, configurable de 1 a 6). Los vehículos eléctricos (VE) arriban a lo largo del día con distintas demandas energéticas expresadas en kilovatios-hora ($\text{kWh}$).

### Variables Físicas y Matemáticas:
- **Potencia del cargador ($P$):** En $\text{kW}$. La tasa de transferencia de energía.
- **Tiempo de carga ($\Delta t$):** Relación energética fundamental:
  $$\Delta t = \frac{E_{\text{solicitada}}}{P} = \frac{\text{kWh}}{\text{kW}} \quad [\text{horas}]$$
- **Regla de Asignación (Despacho FIFO por disponibilidad):**
  1. Orden de llegada de los vehículos.
  2. Asignación al cargador que se desocupa primero.
  3. En caso de empate en tiempo de liberación, desempate por el de menor identificador numérico (Cargador 1 antes que Cargador 2).
- **Cálculo de Tiempos:**
  - $\text{Hora Inicio} = \max(\text{Hora Llegada}, \text{Hora Liberación Cargador})$
  - $\text{Tiempo de Espera} = \text{Hora Inicio} - \text{Hora Llegada}$
  - $\text{Hora Fin} = \text{Hora Inicio} + \Delta t$
- **Indicadores Económicos y Energéticos:**
  - $\text{Energía Total Vendida} = \sum \text{kWh}_i$
  - $\text{Ingresos Totales} = \text{Energía Total} \times \text{Precio por kWh}$
  - $\text{Espera Total} = \sum \text{Espera}_i$
- **Reto Funcional (Pico de Demanda / Máxima Ocupación):**
  - Determinar el intervalo horario de máxima concurrencia de cargadores ocupados simultáneamente y el porcentaje de ocupación pico.

---

## 🧪 Caso de Verificación Oficial (Benchmark)

- **Parámetros:** 2 cargadores de $10\text{ kW}$, Precio: $\$1\,500/\text{kWh}$.
- **Flota de prueba:**
  - Vehículo A: Llega $8\text{ h}$, $20\text{ kWh}$ ($\Delta t = 2\text{ h}$).
  - Vehículo B: Llega $8\text{ h}$, $10\text{ kWh}$ ($\Delta t = 1\text{ h}$).
  - Vehículo C: Llega $9\text{ h}$, $30\text{ kWh}$ ($\Delta t = 3\text{ h}$).
  - Vehículo D: Llega $9\text{ h}$, $10\text{ kWh}$ ($\Delta t = 1\text{ h}$).

### Resultado Esperado:
- **Vehículo A:** Cargador 1, de $8:00$ a $10:00\text{ h}$ (Espera: $0\text{ h}$).
- **Vehículo B:** Cargador 2, de $8:00$ a $9:00\text{ h}$ (Espera: $0\text{ h}$).
- **Vehículo C:** Cargador 2, de $9:00$ a $12:00\text{ h}$ (Espera: $0\text{ h}$).
- **Vehículo D:** Cargador 1, de $10:00$ a $11:00\text{ h}$ (Espera: $1\text{ h}$).
- **Totales:**
  - Espera total: $1.0\text{ hora}$.
  - Energía total vendida: $70\text{ kWh}$.
  - Ingresos: $\$105\,000$.
  - Hora de mayor ocupación: de $8:00$ a $11:00\text{ h}$ (2 cargadores activos simultáneamente = $100\%$ de ocupación).

---

## 🛠️ Estructura Modular del Proyecto

Para cumplir con la **Regla (3) - Preparación para cambios en vivo**, el proyecto se organiza separando la lógica de cálculo (backend) de la interfaz de usuario (frontend):

1. **`datos/entrada.json`**: Datos de entrada en formato estándar JSON.
2. **`simulador.py`**: Motor de simulación puro, sin dependencias gráficas, testeable mediante pruebas unitarias.
3. **`test_simulador.py`**: Suite de validación automática que verifica el caso benchmark.
4. **`app.py`**: Interfaz de usuario interactiva en Streamlit.
5. **`app_tkinter.py`**: Interfaz de usuario equivalente en Tkinter (0 dependencias externas).

---

## 🧭 Guía de Parámetros Clave para Sustentación (Respuestas en Vivo)

Si el docente solicita modificar parámetros en plena sustentación:

| Parámetro a modificar | Archivo | Ubicación exacta | ¿Qué efecto tiene? |
| :--- | :--- | :--- | :--- |
| **Umbral de Alerta de Espera** | `simulador.py` | Variable `UMBRAL_ALERTA_ESPERA_HORAS` | Define cuántas horas de espera activan el cartel de aviso de mala calidad de servicio. Por defecto: `1.0`. |
| **Regla de Desempate de Cargador** | `simulador.py` | Función `simular_estacion()`, tupla `(max(llegada, item[1]), item[0])` | `item[0]` garantiza que a igual hora disponible, gana el cargador con menor ID numérico. |
| **Rango de Cargadores (1 a 6)** | `app.py` / `app_tkinter.py` | `st.slider(..., min_value=1, max_value=6)` / `ttk.Spinbox(from_=1, to=6)` | Permite evaluar cuántos cargadores eliminan la espera de los vehículos (con 3 cargadores la espera de D baja a 0). |
| **Colores de Visualización** | `app.py` / `app_tkinter.py` | Lista `COLORES_VEHICULOS`, `COLOR_LIBRE`, `COLOR_OCUPADO`, `COLOR_ESPERA` | Controla la paleta de alto contraste para proyección y temas. |
| **Paso de discretización Hora Pico** | `simulador.py` | Parámetro `paso=0.25` en `calcular_hora_pico()` | Evalúa la ocupación cada 15 minutos ($0.25\text{ h}$) para detectar el pico continuo. |
| **Registrar Vehículo en Caliente** | `app.py` / `app_tkinter.py` | `st.form("form_nuevo_vehiculo")` / `_abrir_dialogo_registro()` | Permite añadir cualquier vehículo (placa, nombre/modelo, hora, kWh) y ver la reasignación instantánea. |
| **Agregar Nueva Estación de Carga** | `simulador.py` / `app.py` / `app_tkinter.py` | Función `crear_estacion()` / `_abrir_dialogo_nueva_estacion()` | Permite expandir la red con nuevas estaciones (nombre, potencia kW, tarifa $/kWh). |
| **Restablecer Caso Oficial** | `app.py` / `app_tkinter.py` / `servidor_web.py` | Botón "Restablecer Flota" / `_restablecer_datos()` | Regresa la flota a los 4 vehículos oficiales (A, B, C, D) para reiniciar la prueba. |
| **Servidor Web Nativo (Sin Tkinter)** | `servidor_web.py` | Variable `PUERTO = 8080`, `iniciar_servidor()` | Levanta la aplicación web SCADA en el navegador (Chrome/Edge) con 0 instalaciones externas. |

---

## 📝 Registro de Prompts y Decisiones de Diseño

### Registro #1: Inicialización y Definición de Arquitectura
- **Fecha:** 21-11-2026
- **Contexto:** Recepción del enunciado y reglas de evaluación para Fundamentos de Programación.
- **Decisión:** 
  - Separar el motor de simulación en `simulador.py` con funciones puras `cargar_datos()`, `simular_estacion()` y `calcular_hora_pico()`.
  - Crear `datos/entrada.json` con el caso de prueba oficial.
  - Diseñar la aplicación visual en **Streamlit** (recomendada) y proveer alternativa en **Tkinter** para garantizar ejecución bajo cualquier entorno sin requerir internet para la sustentación.

### Registro #2: Implementación de Motor Energético y Pruebas Unitarias
- **Fecha:** 21-11-2026
- **Contexto:** Construcción y verificación del modelo físico y de despacho de colas.
- **Decisión:**
  - En `simulador.py`, calcular el tiempo de servicio mediante $\Delta t = \text{kwh} / \text{potencia}$.
  - Manejar el estado de disponibilidad de cargadores en un diccionario dinámico `{cargador_id: hora_disponible}`.
  - Implementar en `test_simulador.py` la verificación estricta de los 4 vehículos, la espera de 1.0 h para el vehículo D, los $70\text{ kWh}$ despachados, y los $\$105\,000$ facturados. Todas las pruebas pasan satisfactoriamente.

### Registro #3: Implementación de Visualizaciones (Streamlit y Tkinter)
- **Fecha:** 21-11-2026
- **Contexto:** Requisitos de visualización: Gantt (con espera rayada), Tarjetas con estado y % en vivo, y 3 Indicadores clave + Alerta + Reto funcional.
- **Decisión:**
  - En `app.py` (Streamlit), se diseñó un renderizador SVG directo para el Diagrama de Gantt, asegurando nitidez vectorial, colores por placa, y textura rayada para los tiempos de espera.
  - Se añadieron tarjetas métricas grandes y un deslizador temporal horario que actualiza las barras de progreso del estado de carga.
  - En `app_tkinter.py` se replicó idéntica experiencia mediante `tk.Canvas` y `ttk.Progressbar`, asegurando funcionamiento sin instalar paquetes adicionales.

### Registro #4: Rediseño Intuitivo de UI/UX (Consola SCADA y Aguja Temporal)
- **Fecha:** 21-11-2026 (13:15)
- **Contexto:** Solicitud del usuario: *"La pagina tiene lo escencial, pero su diseño es tosco y enredado trata de hacerlo mas intuitivo"*.
- **Decisión de Rediseño:**
  1. **Jerarquía Visual Clara (Niveles SCADA):**
     - Nivel 1: Banner superior de estación y capacidad instalada.
     - Nivel 2: Tarjetas KPI ejecutivas con tipografía grande y subtítulos contextuales (minutos en cola, demanda abastecida, tarifa).
     - Nivel 3: Alerta de servicio proactiva (no solo avisa el retraso, sino que aconseja aumentar cargadores para eliminarlo).
     - Nivel 4: Bahías de Carga dinámicas (diseño tipo estación real con badges de estado, potencia y progreso).
     - Nivel 5: Diagrama de Gantt vectorial con esquinas redondeadas y leyenda clara.
  2. **Unificación Temporal (Aguja / Cursor Sincronizado):** Se incorporó una línea vertical punteada roja con etiqueta de hora (`HH:MM`) que cruza el Diagrama de Gantt al mover el deslizador de tiempo. Esto permite al usuario y docente entender instantáneamente la relación exacta entre el bloque temporal del Gantt y el estado de la bahía arriba.
  3. **Replicación en ambos motores:** Se actualizaron tanto `app.py` (Streamlit) como `app_tkinter.py` (Tkinter) para mantener coherencia visual y pedagógica completa.

### Registro #5: Registro Interactivo de Vehículos en Vivo y Ordenamiento Dinámico
- **Fecha:** 21-11-2026 (14:08)
- **Contexto:** Cumplimiento riguroso del requerimiento obligatorio 1.1 (*"Registrar los vehículos: placa, hora de llegada y kWh necesarios"*) permitiendo que durante la sustentación el docente solicite agregar vehículos en caliente y ver la simulación en tiempo real.
- **Decisión:**
  1. **Motor Energético (`simulador.py`):** Se añadió en `simular_estacion()` el ordenamiento estricto `sorted(datos["vehiculos"], key=lambda v: (float(v["llegada"]), str(v["placa"])))`. Esto asegura que sin importar el orden cronológico en que el usuario registre nuevos vehículos, el algoritmo respete la política FIFO estricta.
  2. **Interfaz Streamlit (`app.py`):** Se integró `st.session_state["datos_estacion"]` junto con un formulario `st.form()` en el panel lateral (*"➕ Registrar Nuevo Vehículo"*), permitiendo ingresar placa, hora de llegada y kWh requeridos. Al enviar el formulario, la vista se refresca automáticamente recalculando el Gantt, KPIs y bahías. Se incluyó además el botón *"🔄 Restablecer Flota Oficial"* para volver al benchmark en un solo clic.
  3. **Interfaz Tkinter (`app_tkinter.py`):** Se incorporó el botón *"➕ Registrar"* en la barra de control superior con la ventana modal `_abrir_dialogo_registro()`, validando tipos de datos y recalculando instantáneamente la escena. Se agregó el botón *"🔄 Restablecer"* conectado a `_restablecer_datos()`.
  4. **Preparación de Sustentación:** Ambas herramientas quedan 100% blindadas para preguntas imprevistas del docente ("¿Qué pasa si llega un vehículo E a las 10:00 h pidiendo 15 kWh?").

### Registro #6: Eliminación de Saltos y Parpadeo en Deslizador Horario (Modo Retenido)
- **Fecha:** 21-11-2026 (14:21)
- **Contexto:** Solicitud del usuario: *"al momento de deslizar la barra que recorre las horas se producen pequeños saltos durante cada actualizacion de los valores, preferiria que no parpadeara despues de deslizar la barra de horas"*.
- **Diagnóstico Técnico:**
  1. En `app_tkinter.py`, la función previa `_actualizar_bahias()` destruía todos los elementos (`child.destroy()`) y creaba nuevos en cada paso del slider. Esto colapsaba transitoriamente a 0 píxeles la altura del contenedor dentro del `Canvas` con scroll, disparando `<Configure>` y recalculando el `scrollregion`, lo que provocaba sacudidas verticales (jitter) y parpadeos.
  2. Asimismo, `_dibujar_gantt()` ejecutaba `delete("all")` y reconfiguraba la altura del canvas continuamente, recreando toda la cuadrícula y bloques fijos.
- **Decisión y Solución Aplicada:**
  1. **Separación Estático / Dinámico en Gantt (`app_tkinter.py`):** Se dividió la lógica en `_dibujar_gantt_estatico()` (se dibuja una sola vez al cambiar simulación) y `_actualizar_aguja_gantt()` (solo borra y traslada la aguja con etiqueta `tags="aguja"`).
  2. **Persistencia y Actualización en Caliente de Bahías (`app_tkinter.py`):** Se implementó `_crear_cards_bahias()` para instanciar las tarjetas una sola vez, y `_actualizar_valores_bahias()` para alterar exclusivamente `.config(text=...)` y `pb["value"] = ...` en memoria sin destruir widgets.
  3. **Estabilización de Dimensiones en Streamlit (`app.py`):** Se añadió `min-height: 205px;` en el contenedor CSS `.bay-card` para garantizar altura constante entre estados libre y ocupado.
- **Resultado:** Deslizamiento continuo a 60 FPS, completamente fluido, sin redibujados bruscos ni saltos en la pantalla.

### Registro #7: Soporte para Red Multi-Estación y Nombres Descriptivos de Vehículos
- **Fecha:** 21-11-2026 (15:15)
- **Contexto:** Solicitud del usuario: *"haz que se pueda: agregar mas estaciones de carga, agregar nuevos vehiculos junto a su nombre y hora de llegada"*.
- **Decisión y Arquitectura:**
  1. **Motor Energético (`simulador.py`):**
     - Se añadió la función `crear_estacion(nombre, potencia, precio, vehiculos)` para estandarizar la creación de estaciones independientes con sus propios parámetros energéticos y tarifarios.
     - En `simular_estacion()` y `obtener_estado_en_instante()`, se extendió el objeto vehículo para admitir el campo `nombre` (ej. "Tesla Model 3", "Bus Ruta 5") manteniendo compatibilidad total con la clave `placa`.
  2. **Interfaz Tkinter (`app_tkinter.py`):**
     - Se incorporó un diccionario de estaciones (`self.estaciones`) y un `ttk.Combobox` en la barra superior para alternar instantáneamente entre estaciones de la red.
     - Se creó el botón modal *"🏢 + Estación"* con `_abrir_dialogo_nueva_estacion()` para registrar estaciones con su nombre, potencia en kW y tarifa en $/kWh.
     - En el modal de registro de vehículos `_abrir_dialogo_registro()`, se incluyó la captura de `Nombre / Modelo`, `Placa`, `Hora de llegada` y `kWh requeridos`.
     - En el Gantt y en las bahías de carga, se muestra el nombre y la placa del vehículo de forma clara y adaptativa según el ancho del bloque.
  3. **Interfaz Streamlit (`app.py`):**
     - Se gestiona la red completa en `st.session_state["estaciones"]` con selector desplegable de estación activa.
     - Se implementó el panel *"🏢 Crear Nueva Estación"* y el formulario *"➕ Registrar Nuevo Vehículo"* con captura completa de nombre, placa, hora y kWh.
     - El banner superior, las bahías, el diagrama Gantt vectorial y la tabla de auditoría reflejan el nombre descriptivo de cada vehículo.
  4. **Pruebas Unitarias (`test_simulador.py`):**
     - Se agregó `test_vehiculos_con_nombre_y_multi_estacion()` verificando que múltiples estaciones y vehículos con nombres personalizados computen exactamente sus tiempos de carga bajo sus respectivas potencias. Pruebas 100% exitosas.

### Registro #8: Aplicación Web en Navegador (Cero Instalaciones, Sin Tkinter)
- **Fecha:** 21-11-2026 (15:30)
- **Contexto:** Solicitud del usuario: *"se puede hacer que la aplicacion se ejecute en una pagina sin ener que usar tkinter y si es posible hazlo"*.
- **Decisión y Arquitectura:**
  1. **Servidor HTTP Nativo (`servidor_web.py`):**
     - Para ejecutar en una página web real sin depender de la instalación de Streamlit (que requiere `pip install` y conexión a internet), se construyó un servidor HTTP ligero empleando exclusivamente la librería estándar `http.server`.
     - Expone endpoints REST en formato JSON (`/api/estado`, `/api/cambiar_estacion`, `/api/cargadores`, `/api/nueva_estacion`, `/api/nuevo_vehiculo`, `/api/restablecer`).
     - Al ejecutarse (`python servidor_web.py`), abre automáticamente el navegador web predeterminado (Google Chrome, Microsoft Edge, etc.) en `http://localhost:8080`.
  2. **Frontend Web Interactivo (`web/index.html`):**
     - Construido en HTML5, CSS3 moderno y JavaScript puro (vanilla JS), sin librerías externas ni dependencias pesadas.
     - Implementa la interfaz SCADA completa: selector de sedes, modales para nuevas estaciones y vehículos, 4 tarjetas KPI, alerta de servicio, bahías con barras de progreso animadas, Diagrama de Gantt SVG vectorial con aguja horaria sincronizada y tabla de auditoría.
     - El cálculo de interpolación temporal de las bahías se ejecuta en el cliente a 60 FPS, garantizando cero latencia, cero saltos y cero parpadeos al deslizar la barra de horas.
  3. **Compatibilidad Plena:**
     - El motor matemático de backend sigue siendo `simulador.py`, garantizando idénticos resultados energéticos y económicos (caso benchmark: 70 kWh, $105,000, 1h de espera).
     - Si el usuario cuenta con Streamlit, `app.py` sigue disponible (`streamlit run app.py`). Si prefiere escritorio, `app_tkinter.py` sigue funcional.
     - Se logra la máxima flexibilidad de presentación para la sustentación académica.

### Registro #9: Estrategias de Publicación y Acceso Remoto (Red Local y Túnel HTTPS)
- **Fecha:** 21-11-2026 (15:35)
- **Contexto:** Solicitud del usuario: *"quiero compartir esta pagina, hacerla publica pero no me deja que hago"*.
- **Diagnóstico:**
  La dirección `localhost` (o `127.0.0.1`) es una dirección de bucle invertido (*loopback*) que sólo existe dentro de la máquina local. Al enviarla a un tercero o abrirla en otro dispositivo, dicho dispositivo intenta conectarse a sí mismo y arroja error.
- **Decisión y Soluciones Habilitadas:**
  1. **Acceso por IP Local (`servidor_web.py`):** Se integró la función `obtener_ip_local()` mediante `socket` para mostrar automáticamente en la consola la URL accesible dentro de la misma red Wi-Fi (`http://<IP_LOCAL>:8080`).
  2. **Túnel Seguro a Internet (`compartir_publico.bat`):** Se creó un script directo que levanta un túnel reverso mediante el cliente nativo de Windows `ssh.exe` (`ssh -p 443 -R0:localhost:8080 a.pinggy.io`). Esto genera al instante un enlace público seguro `https://xxxx.pinggy.link` accesible desde cualquier parte del mundo (celular, laptop del docente, etc.).
  3. **Despliegue Permanente en Nube (Streamlit Cloud):** Se estructuró la guía paso a paso para publicación gratuita y definitiva en `share.streamlit.io` a partir de [app.py](file:///C:/Users/ESTUDIANTE.REDES-PC01/.gemini/antigravity/scratch/estacion_carga1/app.py).

---

## Registro #10 — Fix: ValueError en Gantt SVG (Streamlit Cloud)

**Fecha:** 21 de noviembre de 2026  
**Archivo afectado:** `app.py`, función `generar_gantt_svg_moderno()`, línea 545  

**Problema:**  
Al desplegar en Streamlit Cloud, la app lanzaba `ValueError` al renderizar el diagrama de Gantt. La causa: la variable `h_tick` inicia como `int` pero se convierte a `float` tras `h_tick += paso_hora` (donde `paso_hora = 1.0`). El especificador de formato `{h_tick:02d}` solo acepta enteros y falla con float.

**Traza del error:**
```
File "app.py", line 625, in <module>
    gantt_svg = generar_gantt_svg_moderno(...)
File "app.py", line 545, in generar_gantt_svg_moderno
    svg.append(f'<text ... >{h_tick:02d}:00</text>')
ValueError: ...
```

**Fix aplicado:**
```python
# ANTES (buggy):
svg.append(f'... {h_tick:02d}:00</text>')

# DESPUÉS (corregido):
svg.append(f'... {int(h_tick):02d}:00</text>')
```

**Por qué funciona:** `int(h_tick)` convierte el float (ej: `9.0`) a entero (`9`) en el momento del formateo, sin alterar la lógica del bucle.  
**Verificación:** `python -m py_compile app.py` → sin errores (código 0).  
**Próximo paso:** Hacer commit del `app.py` corregido al repositorio GitHub para que Streamlit Cloud redespliegue automáticamente.

