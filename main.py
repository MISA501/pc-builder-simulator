# -*- coding: utf-8 -*-
"""
====================================================================
 PC BUILDER PRO 2D - Simulador de armado de PC ultra realista
====================================================================
Un solo archivo, solo Python + Pygame. Todos los "assets" se dibujan
con pygame.draw (nada de imágenes externas). Los sonidos se generan
matemáticamente con el módulo estándar `array` (onda cuadrada),
así que tampoco dependemos de archivos .wav externos.

Controles:
  - Click izquierdo: arrastrar componentes y puntas de cables
  - Click en el botón POWER del gabinete: intenta encender la PC
  - R: reiniciar la partida
  - ESC: salir

Ejecutar con:  python main.py
====================================================================
"""

import sys
import math
import random
import array
import colorsys
import pygame

# ------------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ------------------------------------------------------------------
ANCHO, ALTO = 1280, 720
FPS = 60

# Paleta de colores
NEGRO = (10, 10, 12)
GRIS_OSCURO = (35, 37, 42)
GRIS = (70, 74, 82)
GRIS_CLARO = (140, 145, 155)
BLANCO = (235, 238, 240)
VERDE = (60, 210, 110)
ROJO = (220, 60, 60)
AMARILLO = (240, 200, 60)
AZUL = (70, 140, 230)
NARANJA = (230, 140, 40)
VIOLETA = (150, 90, 220)
COBRE = (190, 120, 70)
VERDE_PCB = (30, 90, 55)
DORADO = (200, 170, 60)

pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=1)
    AUDIO_OK = True
except pygame.error:
    AUDIO_OK = False

pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("PC Builder Pro 2D")
reloj = pygame.time.Clock()

fuente_chica = pygame.font.SysFont("consolas", 14)
fuente_normal = pygame.font.SysFont("consolas", 18)
fuente_grande = pygame.font.SysFont("consolas", 28, bold=True)
fuente_titulo = pygame.font.SysFont("consolas", 46, bold=True)
fuente_mono = pygame.font.SysFont("couriernew", 16, bold=True)


# ------------------------------------------------------------------
# GENERADOR DE SONIDOS PROCEDURALES (onda cuadrada simple)
# ------------------------------------------------------------------
def generar_beep(frecuencia=440, duracion=0.12, volumen=0.25, tipo="square"):
    """Genera un pygame.mixer.Sound sin usar archivos externos ni numpy."""
    if not AUDIO_OK:
        return None
    sample_rate = 44100
    n_samples = int(sample_rate * duracion)
    buf = array.array("h")
    amplitud = int(32767 * volumen)
    for i in range(n_samples):
        t = i / sample_rate
        # fade out para evitar "clicks"
        env = 1.0 - (i / n_samples)
        if tipo == "square":
            valor = amplitud if math.sin(2 * math.pi * frecuencia * t) >= 0 else -amplitud
        elif tipo == "noise":
            valor = random.randint(-amplitud, amplitud)
        else:  # sine
            valor = int(amplitud * math.sin(2 * math.pi * frecuencia * t))
        buf.append(int(valor * env))
    try:
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except pygame.error:
        return None


SND_CLICK = generar_beep(880, 0.05, 0.2, "square")
SND_ERROR = generar_beep(140, 0.25, 0.3, "square")
SND_SNAP = generar_beep(1200, 0.06, 0.25, "square")
SND_POST = generar_beep(1000, 0.35, 0.3, "sine")
SND_EXPLOSION = generar_beep(90, 0.6, 0.4, "noise")
SND_POWERON = generar_beep(200, 0.4, 0.15, "sine")


def sonar(snd):
    if snd is not None:
        snd.play()


# ------------------------------------------------------------------
# UTILIDADES DE DIBUJO
# ------------------------------------------------------------------
def bezier_cuadratico(p0, p1, p2, pasos=24):
    """Devuelve una lista de puntos que forman una curva bezier cuadrática."""
    puntos = []
    for i in range(pasos + 1):
        t = i / pasos
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        puntos.append((x, y))
    return puntos


def dibujar_texto(sup, texto, fuente, color, pos, centrado=False):
    render = fuente.render(texto, True, color)
    rect = render.get_rect()
    if centrado:
        rect.center = pos
    else:
        rect.topleft = pos
    sup.blit(render, rect)
    return rect


def rect_con_sombra(sup, rect, color, radio=6, sombra=True):
    """Dibuja una sombra suave debajo del rect y luego el rect."""
    if sombra:
        s = pygame.Surface((rect.width + 20, rect.height + 14), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 90), (0, rect.height - 6, rect.width + 20, 20))
        sup.blit(s, (rect.x - 10, rect.y + 6))
    pygame.draw.rect(sup, color, rect, border_radius=radio)


# ------------------------------------------------------------------
# PARTÍCULAS (polvo al instalar piezas / humo al explotar)
# ------------------------------------------------------------------
class Particula:
    def __init__(self, x, y, color, vida=0.8, tipo="polvo"):
        self.x, self.y = x, y
        self.tipo = tipo
        ang = random.uniform(0, math.pi * 2)
        vel = random.uniform(20, 90) if tipo == "polvo" else random.uniform(10, 40)
        self.vx = math.cos(ang) * vel
        self.vy = math.sin(ang) * vel - (10 if tipo == "polvo" else 30)
        self.vida_total = vida
        self.vida = vida
        self.color = color
        self.radio = random.uniform(2, 5) if tipo == "polvo" else random.uniform(6, 14)

    def actualizar(self, dt):
        self.vida -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.tipo == "polvo":
            self.vy += 120 * dt  # gravedad
        else:
            self.vy -= 15 * dt  # el humo sube
            self.radio += 12 * dt
        return self.vida > 0

    def dibujar(self, sup):
        alpha = max(0, int(255 * (self.vida / self.vida_total)))
        s = pygame.Surface((int(self.radio * 2) + 2, int(self.radio * 2) + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (int(self.radio), int(self.radio)), int(self.radio))
        sup.blit(s, (self.x - self.radio, self.y - self.radio))


# ------------------------------------------------------------------
# COMPONENTE ARRASTRABLE
# ------------------------------------------------------------------
class Componente:
    """
    Representa una pieza física de PC que el jugador puede arrastrar
    con el mouse hasta un slot compatible en la motherboard/gabinete.
    """

    def __init__(self, id_, nombre, tipo, watts, tam, pos_estante):
        self.id = id_
        self.nombre = nombre
        self.tipo = tipo              # socket_compatible: "cpu", "ram", "gpu", "ssd", "psu", "cooler"
        self.watts = watts
        self.rect = pygame.Rect(pos_estante[0], pos_estante[1], tam[0], tam[1])
        self.pos_estante = pos_estante
        self.tam = tam
        self.colocado = False
        self.arrastrando = False
        self.offset = (0, 0)
        # animación de rebote cuando el drop es inválido
        self.rebotando = False
        self.rebote_t = 0.0
        self.rebote_origen = pos_estante
        self.rebote_destino = pos_estante

    def contiene(self, pos):
        return self.rect.collidepoint(pos)

    def iniciar_arrastre(self, pos):
        if self.colocado:
            return
        self.arrastrando = True
        self.offset = (pos[0] - self.rect.x, pos[1] - self.rect.y)

    def mover(self, pos):
        if self.arrastrando:
            self.rect.x = pos[0] - self.offset[0]
            self.rect.y = pos[1] - self.offset[1]

    def soltar_en_estante(self):
        """Vuelve suavemente a su lugar en el estante (drop inválido)."""
        self.rebotando = True
        self.rebote_t = 0.0
        self.rebote_origen = self.rect.topleft
        self.rebote_destino = self.pos_estante

    def actualizar(self, dt):
        if self.rebotando:
            self.rebote_t += dt * 3.2
            if self.rebote_t >= 1.0:
                self.rect.topleft = self.rebote_destino
                self.rebotando = False
            else:
                # easing con un pequeño "overshoot" para que se sienta un rebote real
                t = self.rebote_t
                ease = 1 - (1 - t) ** 3
                sacudida = math.sin(t * math.pi * 4) * (1 - t) * 6
                x = self.rebote_origen[0] + (self.rebote_destino[0] - self.rebote_origen[0]) * ease
                y = self.rebote_origen[1] + (self.rebote_destino[1] - self.rebote_origen[1]) * ease + sacudida
                self.rect.topleft = (x, y)

    def dibujar(self, sup, tiempo, cpu_instalada=True):
        r = self.rect
        if self.tipo == "cpu":
            rect_con_sombra(sup, r, (60, 60, 65))
            pygame.draw.rect(sup, DORADO, r, 3, border_radius=6)
            # pines dorados
            for i in range(6):
                pygame.draw.circle(sup, DORADO, (r.x + 8 + i * ((r.width - 16) // 5), r.y + r.height - 6), 2)
            dibujar_texto(sup, "i7-14700K", fuente_chica, BLANCO, r.center, centrado=True)

        elif self.tipo == "ram":
            rect_con_sombra(sup, r, (20, 90, 70))
            pygame.draw.rect(sup, (10, 60, 45), r, 2, border_radius=3)
            for i in range(5):
                y = r.y + 8 + i * (r.height - 16) // 4
                pygame.draw.rect(sup, DORADO, (r.x + 2, y, r.width - 4, 4))

        elif self.tipo == "gpu":
            rect_con_sombra(sup, r, (25, 25, 30))
            pygame.draw.rect(sup, GRIS, r, 2, border_radius=8)
            # fans de la GPU
            for cx in (r.x + r.width * 0.28, r.x + r.width * 0.72):
                cy = r.y + r.height * 0.55
                pygame.draw.circle(sup, (15, 15, 18), (int(cx), int(cy)), 18)
                ang0 = tiempo * (250 if self.colocado else 40)
                for k in range(3):
                    a = math.radians(ang0 + k * 120)
                    ex = cx + math.cos(a) * 14
                    ey = cy + math.sin(a) * 14
                    pygame.draw.line(sup, GRIS_CLARO, (cx, cy), (ex, ey), 4)
            dibujar_texto(sup, "RTX 4070", fuente_chica, BLANCO, (r.centerx, r.y + 12), centrado=True)
            # conectores pcie visibles arriba
            pygame.draw.rect(sup, NEGRO, (r.x + 18, r.y - 6, 22, 10))
            pygame.draw.rect(sup, NEGRO, (r.x + 58, r.y - 6, 22, 10))

        elif self.tipo == "ssd":
            rect_con_sombra(sup, r, (20, 20, 25))
            pygame.draw.rect(sup, (40, 150, 90), (r.x, r.y, r.width, r.height), border_radius=2)
            dibujar_texto(sup, "NVMe", fuente_chica, BLANCO, r.center, centrado=True)

        elif self.tipo == "psu":
            rect_con_sombra(sup, r, (30, 30, 34))
            pygame.draw.rect(sup, GRIS, r, 2, border_radius=6)
            pygame.draw.circle(sup, (15, 15, 18), (r.centerx, r.centery - 10), 30)
            ang0 = tiempo * (180 if self.colocado else 20)
            for k in range(4):
                a = math.radians(ang0 + k * 90)
                ex = r.centerx + math.cos(a) * 22
                ey = r.centery - 10 + math.sin(a) * 22
                pygame.draw.line(sup, GRIS_CLARO, (r.centerx, r.centery - 10), (ex, ey), 5)
            dibujar_texto(sup, "750W MODULAR", fuente_chica, BLANCO, (r.centerx, r.bottom - 14), centrado=True)

        elif self.tipo == "cooler":
            rect_con_sombra(sup, r, (50, 52, 58))
            pygame.draw.circle(sup, (18, 18, 22), r.center, r.width // 2 - 4)
            pygame.draw.circle(sup, GRIS_CLARO, r.center, r.width // 2 - 4, 2)
            ang0 = tiempo * (300 if self.colocado else 30)
            for k in range(5):
                a = math.radians(ang0 + k * 72)
                ex = r.centerx + math.cos(a) * (r.width // 2 - 10)
                ey = r.centery + math.sin(a) * (r.width // 2 - 10)
                pygame.draw.line(sup, GRIS_CLARO, r.center, (ex, ey), 5)

        # etiqueta bajo la pieza si está en el estante
        if not self.colocado and not self.arrastrando:
            dibujar_texto(sup, self.nombre, fuente_chica, GRIS_CLARO,
                          (r.centerx, r.bottom + 10), centrado=True)


# ------------------------------------------------------------------
# CABLE FÍSICO (curva bezier deformable)
# ------------------------------------------------------------------
class Cable:
    """
    Un cable tiene un extremo FIJO (sale de un componente ya instalado,
    p.ej. la fuente) y un extremo LIBRE que el jugador debe arrastrar
    y encajar ("snap") en su conector de destino en la motherboard/GPU/etc.
    """

    def __init__(self, id_, nombre, fuente_id, offset_fuente, destino_pos,
                 requiere=None, color=(30, 30, 30)):
        self.id = id_
        self.nombre = nombre
        self.fuente_id = fuente_id          # "psu" o "panel" (mazo del panel frontal)
        self.offset_fuente = offset_fuente
        self.destino_pos = destino_pos      # punto fijo del conector en la MB/GPU/SSD
        self.requiere = requiere            # id de componente que debe estar colocado para que el destino exista
        self.color = color
        self.conectado = False
        self.arrastrando = False
        self.punta_libre = None             # se inicializa cuando la fuente aparece
        self.inicializado = False
        self.bonus_estetico_dado = False

    def punto_fuente(self, componentes, panel_pos):
        if self.fuente_id == "panel":
            return (panel_pos[0] + self.offset_fuente[0], panel_pos[1] + self.offset_fuente[1])
        comp = componentes.get(self.fuente_id)
        if comp and comp.colocado:
            return (comp.rect.x + self.offset_fuente[0], comp.rect.y + self.offset_fuente[1])
        return None

    def destino_disponible(self, componentes):
        if self.requiere is None:
            return True
        comp = componentes.get(self.requiere)
        return comp is not None and comp.colocado

    def actualizar(self, componentes, panel_pos):
        origen = self.punto_fuente(componentes, panel_pos)
        if origen is None:
            return
        if not self.inicializado and not self.conectado:
            # el cable "sale" enroscado cerca de la fuente hasta que lo agarren
            self.punta_libre = (origen[0] + 34, origen[1] + 18)
            self.inicializado = True
        if self.conectado:
            self.punta_libre = self.destino_pos

    def cerca_de_punta(self, pos, radio=15):
        if self.punta_libre is None or self.conectado:
            return False
        dx = pos[0] - self.punta_libre[0]
        dy = pos[1] - self.punta_libre[1]
        return (dx * dx + dy * dy) ** 0.5 <= radio

    def intentar_conectar(self, componentes, radio=26):
        """Devuelve (exito, bonus_estetico) al soltar la punta libre."""
        if not self.destino_disponible(componentes):
            return False, False
        dx = self.punta_libre[0] - self.destino_pos[0]
        dy = self.punta_libre[1] - self.destino_pos[1]
        dist = (dx * dx + dy * dy) ** 0.5
        if dist <= radio:
            self.conectado = True
            self.punta_libre = self.destino_pos
            return True, self._chequear_bonus_estetico(componentes)
        return False, False

    def _chequear_bonus_estetico(self, componentes):
        """+100 puntos de estética si el cable se enruta por el canal
        trasero de gestión de cables del gabinete (ver Game.canal_cables)."""
        if self.bonus_estetico_dado:
            return False
        origen = self.punto_fuente(componentes, (0, 0)) or self.destino_pos
        medio_y = (origen[1] + self.destino_pos[1]) / 2 + 40  # el "combado" natural del cable
        canal = pygame.Rect(190, 538, 860, 28)
        if canal.collidepoint((self.destino_pos[0], medio_y)) or medio_y > 538:
            self.bonus_estetico_dado = True
            return True
        return False

    def dibujar(self, sup, componentes, panel_pos):
        origen = self.punto_fuente(componentes, panel_pos)
        if origen is None:
            return  # el cable ni siquiera existe todavía (falta la fuente)
        destino = self.punta_libre if self.punta_libre else origen
        # control point: el cable "cuelga" por gravedad si no está tenso
        medio_x = (origen[0] + destino[0]) / 2
        medio_y = (origen[1] + destino[1]) / 2
        combado = 0 if self.conectado else min(70, math.hypot(destino[0]-origen[0], destino[1]-origen[1]) * 0.28)
        control = (medio_x, medio_y + combado)

        activo = self.destino_disponible(componentes)
        color = self.color if activo else (60, 60, 60)
        puntos = bezier_cuadratico(origen, control, destino)
        if len(puntos) > 1:
            pygame.draw.lines(sup, color, False, puntos, 6)
            pygame.draw.lines(sup, tuple(min(255, c + 40) for c in color), False, puntos, 2)

        # conector de destino (contorno visual)
        col_conector = VERDE if self.conectado else (AMARILLO if activo else GRIS)
        pygame.draw.circle(sup, col_conector, self.destino_pos, 7, 2)

        # punta libre (la que se agarra)
        if not self.conectado:
            pygame.draw.circle(sup, BLANCO, (int(destino[0]), int(destino[1])), 7)
            pygame.draw.circle(sup, color, (int(destino[0]), int(destino[1])), 7, 2)


# ------------------------------------------------------------------
# JUEGO PRINCIPAL
# ------------------------------------------------------------------
class Game:
    ESTADOS = ("MENU", "JUGANDO", "ENCENDIENDO", "BIOS", "BENCHMARK", "FALLO", "EXPLOSION")

    def __init__(self):
        self.estado = "MENU"
        self.tiempo = 0.0
        self.particulas = []
        self.mensaje_error = ""
        self.puntaje_estetico = 0
        self.mensaje_flash = ""
        self.mensaje_flash_t = 0.0
        self.shake = 0.0
        self.timer_estado = 0.0
        self.fps_benchmark_mostrado = 0
        self.reiniciar_partida()

    # -------------------- SETUP --------------------
    def reiniciar_partida(self):
        self.tiempo = 0.0
        self.particulas = []
        self.puntaje_estetico = 0
        self.mensaje_error = ""
        self.timer_estado = 0.0
        self.lever_abierto = True

        # --- Gabinete / motherboard ---
        self.case_rect = pygame.Rect(190, 100, 860, 470)
        self.mb_rect = pygame.Rect(240, 130, 560, 380)
        self.panel_pos = (207, 500)  # mazo de cables del panel frontal (dentro del gabinete)
        self.power_btn = pygame.Rect(190, 420, 34, 34)

        # --- Slots (colliders) ---
        self.slots = {
            "cpu_socket": pygame.Rect(400, 170, 70, 70),
            "cooler_mount": pygame.Rect(385, 155, 100, 100),
            "ram_slot1": pygame.Rect(500, 150, 18, 110),
            "ram_slot2": pygame.Rect(525, 150, 18, 110),
            "m2_slot": pygame.Rect(260, 400, 80, 16),
            "pcie_slot": pygame.Rect(260, 440, 320, 60),
            "psu_bay": pygame.Rect(820, 390, 170, 140),
        }
        self.slot_acepta = {
            "cpu_socket": "cpu",
            "cooler_mount": "cooler",
            "ram_slot1": "ram",
            "ram_slot2": "ram",
            "m2_slot": "ssd",
            "pcie_slot": "gpu",
            "psu_bay": "psu",
        }

        # --- Componentes ---
        defs = [
            ("cpu", "CPU i7-14700K", "cpu", 125, (70, 70), (60, 600)),
            ("ram1", "RAM DDR5 #1", "ram", 10, (18, 110), (170, 590)),
            ("ram2", "RAM DDR5 #2", "ram", 10, (18, 110), (200, 590)),
            ("gpu", "RTX 4070", "gpu", 200, (320, 60), (260, 630)),
            ("ssd", "SSD NVMe", "ssd", 5, (80, 16), (620, 650)),
            ("psu", "Fuente 750W", "psu", 0, (170, 140), (760, 578)),
            ("cooler", "Cooler CPU", "cooler", 5, (100, 100), (980, 600)),
        ]
        self.componentes = {}
        for id_, nombre, tipo, watts, tam, pos in defs:
            self.componentes[id_] = Componente(id_, nombre, tipo, watts, tam, pos)

        # --- Cables ---
        cdefs = [
            ("atx24", "24-pin ATX", "psu", (10, 20), (790, 190), None, (30, 30, 200)),
            ("eps8", "8-pin CPU (EPS)", "psu", (10, 45), (405, 140), None, (200, 30, 30)),
            ("pcie1", "PCIe 8-pin #1", "psu", (10, 70), (290, 440), "gpu", (40, 40, 45)),
            ("pcie2", "PCIe 8-pin #2", "psu", (10, 95), (330, 440), "gpu", (40, 40, 45)),
            ("sata", "SATA / Power SSD", "psu", (10, 118), (300, 400), "ssd", (200, 170, 30)),
            ("pwr_sw", "Power SW (panel)", "panel", (0, 0), (270, 470), None, (100, 100, 105)),
            ("reset", "Reset SW (panel)", "panel", (0, 20), (300, 470), None, (100, 100, 105)),
            ("hdd_led", "HDD LED (panel)", "panel", (0, 40), (330, 470), None, (170, 60, 60)),
        ]
        self.cables = {}
        for id_, nombre, fte, off, dest, req, color in cdefs:
            self.cables[id_] = Cable(id_, nombre, fte, off, dest, req, color)

        self.cable_arrastrado = None
        self.componente_arrastrado = None

        # cables que realmente son OBLIGATORIOS para poder encender
        self.cables_obligatorios = ["atx24", "eps8", "pcie1", "pcie2", "sata", "pwr_sw"]
        self.componentes_obligatorios = ["cpu", "ram1", "ram2", "gpu", "ssd", "psu", "cooler"]

        self.watts_totales = sum(c.watts for c in self.componentes.values()) + 50  # 50W base motherboard
        self.psu_capacidad = 750

        self.estado = "JUGANDO"

    # -------------------- LÓGICA --------------------
    def progreso(self):
        total = len(self.componentes_obligatorios) + len(self.cables_obligatorios)
        hechos = sum(1 for k in self.componentes_obligatorios if self.componentes[k].colocado)
        hechos += sum(1 for k in self.cables_obligatorios if self.cables[k].conectado)
        return hechos / total

    def fase_actual(self):
        piezas_ok = all(self.componentes[k].colocado for k in self.componentes_obligatorios)
        if not piezas_ok:
            return "FASE 1: MONTAJE - arrastra las piezas a sus slots"
        cables_ok = all(self.cables[k].conectado for k in self.cables_obligatorios)
        if not cables_ok:
            return "FASE 2: CABLEADO - conecta todos los cables"
        return "FASE 3: ENCENDIDO - presiona el botón POWER del gabinete"

    def emitir_particulas_polvo(self, pos, color=(150, 130, 100)):
        for _ in range(14):
            self.particulas.append(Particula(pos[0], pos[1], color, vida=0.7, tipo="polvo"))

    def emitir_humo(self, pos):
        for _ in range(30):
            self.particulas.append(Particula(pos[0] + random.uniform(-20, 20),
                                        pos[1] + random.uniform(-10, 10),
                                        (60, 60, 65), vida=1.6, tipo="humo"))

    def flash(self, texto):
        self.mensaje_flash = texto
        self.mensaje_flash_t = 1.6

    # -------------------- EVENTOS --------------------
    def manejar_evento(self, ev):
        if ev.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            if ev.key == pygame.K_r:
                self.reiniciar_partida()
            return

        if self.estado != "JUGANDO":
            return

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            pos = ev.pos

            # 1) botón de power
            if self.power_btn.collidepoint(pos):
                self.intentar_encender()
                return

            # 2) puntas de cable (prioridad sobre componentes)
            for cable in reversed(list(self.cables.values())):
                if cable.cerca_de_punta(pos):
                    self.cable_arrastrado = cable
                    cable.arrastrando = True
                    sonar(SND_CLICK)
                    return

            # 3) componentes del estante / colocados no aplica (ya fijos)
            for comp in reversed(list(self.componentes.values())):
                if not comp.colocado and comp.contiene(pos):
                    comp.iniciar_arrastre(pos)
                    self.componente_arrastrado = comp
                    sonar(SND_CLICK)
                    return

        elif ev.type == pygame.MOUSEMOTION:
            if self.componente_arrastrado and self.componente_arrastrado.arrastrando:
                self.componente_arrastrado.mover(ev.pos)
            if self.cable_arrastrado and self.cable_arrastrado.arrastrando:
                self.cable_arrastrado.punta_libre = ev.pos

        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            if self.componente_arrastrado:
                self.soltar_componente(self.componente_arrastrado)
                self.componente_arrastrado.arrastrando = False
                self.componente_arrastrado = None
            if self.cable_arrastrado:
                self.soltar_cable(self.cable_arrastrado)
                self.cable_arrastrado.arrastrando = False
                self.cable_arrastrado = None

    def soltar_componente(self, comp):
        # ¿coincide con algún slot compatible?
        for slot_id, rect in self.slots.items():
            if self.slot_acepta[slot_id] != comp.tipo:
                continue
            if slot_id == "cooler_mount" and not self.componentes["cpu"].colocado:
                continue  # no se puede montar el cooler sin CPU
            if slot_id == "cpu_socket" and not self.lever_abierto:
                continue
            centro_comp = comp.rect.center
            if rect.collidepoint(centro_comp) or rect.colliderect(comp.rect):
                # snap exacto a la posición del slot
                comp.rect.topleft = rect.topleft
                comp.colocado = True
                self.emitir_particulas_polvo(rect.center)
                sonar(SND_SNAP)
                if slot_id == "cpu_socket":
                    self.lever_abierto = False
                    self.flash("CPU instalada. Palanca cerrada.")
                else:
                    self.flash(f"{comp.nombre} instalado correctamente")
                return
        # ningún slot válido -> rebote + sonido de error
        comp.soltar_en_estante()
        sonar(SND_ERROR)
        self.flash(f"¡Slot incorrecto para {comp.nombre}!")

    def soltar_cable(self, cable):
        exito, bonus = cable.intentar_conectar(self.componentes)
        if exito:
            sonar(SND_SNAP)
            self.emitir_particulas_polvo(cable.destino_pos, (90, 160, 220))
            if bonus:
                self.puntaje_estetico += 100
                self.flash(f"{cable.nombre} conectado (+100 estética: cable oculto)")
            else:
                self.flash(f"{cable.nombre} conectado correctamente")
        else:
            sonar(SND_ERROR)
            cable.punta_libre = None
            cable.inicializado = False
            self.flash(f"¡{cable.nombre} no encaja ahí!")

    # -------------------- ENCENDIDO --------------------
    def diagnosticar(self):
        """Devuelve None si todo está OK, o un string con el primer error."""
        c = self.componentes
        cab = self.cables
        if not c["cpu"].colocado:
            return "CPU no instalada en el socket LGA1700"
        if not (c["ram1"].colocado and c["ram2"].colocado):
            return "Falta instalar módulo(s) de RAM DDR5"
        if not c["cooler"].colocado:
            return "Cooler no instalado - riesgo de sobrecalentamiento"
        if not c["psu"].colocado:
            return "Fuente de poder no instalada en su bahía"
        if not cab["atx24"].conectado:
            return "Cable 24-pin ATX no conectado a la motherboard"
        if not cab["eps8"].conectado:
            return "CPU power (8-pin EPS) no conectado"
        if not c["gpu"].colocado:
            return "GPU no instalada en el slot PCIe x16"
        if not (cab["pcie1"].conectado and cab["pcie2"].conectado):
            return "Alimentación PCIe de la GPU incompleta"
        if not c["ssd"].colocado:
            return "SSD NVMe no instalado"
        if not cab["sata"].conectado:
            return "Cable de alimentación del SSD no conectado"
        if not cab["pwr_sw"].conectado:
            return "Cable Power SW no conectado al panel frontal"
        return None

    def intentar_encender(self):
        error = self.diagnosticar()
        if error:
            self.mensaje_error = error
            self.estado = "FALLO"
            self.timer_estado = 0.0
            sonar(SND_ERROR)
            return
        if self.watts_totales > self.psu_capacidad:
            self.mensaje_error = "¡La fuente de poder es insuficiente para la carga total!"
            self.estado = "EXPLOSION"
            self.timer_estado = 0.0
            self.emitir_humo(self.componentes["psu"].rect.center)
            sonar(SND_EXPLOSION)
            return
        # ¡todo correcto!
        self.estado = "ENCENDIENDO"
        self.timer_estado = 0.0
        sonar(SND_POWERON)

    # -------------------- UPDATE --------------------
    def actualizar(self, dt):
        self.tiempo += dt
        if self.mensaje_flash_t > 0:
            self.mensaje_flash_t -= dt

        self.particulas = [p for p in self.particulas if p.actualizar(dt)]

        if self.estado == "JUGANDO":
            for comp in self.componentes.values():
                comp.actualizar(dt)
            for cable in self.cables.values():
                cable.actualizar(self.componentes, self.panel_pos)

        elif self.estado == "ENCENDIENDO":
            self.timer_estado += dt
            if self.timer_estado > 0.4 and self.timer_estado < 0.42:
                sonar(SND_POST)
            if self.timer_estado >= 2.2:
                self.estado = "BIOS"
                self.timer_estado = 0.0

        elif self.estado == "BIOS":
            self.timer_estado += dt
            if self.timer_estado >= 2.6:
                self.estado = "BENCHMARK"
                self.timer_estado = 0.0

        elif self.estado == "BENCHMARK":
            self.timer_estado += dt
            objetivo = 144
            self.fps_benchmark_mostrado = min(objetivo, int(self.timer_estado * 90))

        elif self.estado == "EXPLOSION":
            self.timer_estado += dt
            self.shake = max(0, 14 - self.timer_estado * 10)

    # -------------------- DIBUJO --------------------
    def dibujar(self, sup):
        offset = (0, 0)
        if self.shake > 0:
            offset = (random.uniform(-self.shake, self.shake), random.uniform(-self.shake, self.shake))

        capa = pygame.Surface((ANCHO, ALTO))
        capa.fill((18, 18, 22))

        self.dibujar_gabinete(capa)
        self.dibujar_motherboard(capa)
        self.dibujar_slots(capa)

        # cables detrás de los componentes que van encima (se ven "por dentro")
        for cable in self.cables.values():
            cable.dibujar(capa, self.componentes, self.panel_pos)

        for comp in self.componentes.values():
            comp.dibujar(capa, self.tiempo, self.componentes["cpu"].colocado)

        for p in self.particulas:
            p.dibujar(capa)

        self.dibujar_panel_frontal(capa)
        self.dibujar_ui(capa)

        if self.estado in ("ENCENDIENDO", "BIOS", "BENCHMARK"):
            self.dibujar_rgb(capa)

        if self.estado == "BIOS":
            self.dibujar_bios(capa)
        elif self.estado == "BENCHMARK":
            self.dibujar_benchmark(capa)
        elif self.estado == "FALLO":
            self.dibujar_fallo(capa)
        elif self.estado == "EXPLOSION":
            self.dibujar_explosion(capa)

        sup.blit(capa, offset)

    def dibujar_gabinete(self, sup):
        pygame.draw.rect(sup, (25, 26, 30), self.case_rect, border_radius=10)
        pygame.draw.rect(sup, GRIS, self.case_rect, 4, border_radius=10)
        # canal de gestión de cables (zona de bonus estético)
        canal = pygame.Rect(190, 538, 860, 28)
        s = pygame.Surface((canal.width, canal.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (80, 200, 120, 40), (0, 0, canal.width, canal.height), border_radius=6)
        sup.blit(s, canal.topleft)
        dibujar_texto(sup, "Canal de gestión de cables (rutea aquí para +100 estética)",
                    fuente_chica, (110, 220, 150), (canal.x + 8, canal.y + 8))

    def dibujar_motherboard(self, sup):
        pygame.draw.rect(sup, VERDE_PCB, self.mb_rect, border_radius=6)
        pygame.draw.rect(sup, (10, 50, 30), self.mb_rect, 3, border_radius=6)
        dibujar_texto(sup, "MOTHERBOARD (atornillada)", fuente_chica, (150, 220, 180),
                    (self.mb_rect.x + 10, self.mb_rect.y + 8))
        # tornillos decorativos
        for tx, ty in [(self.mb_rect.x + 12, self.mb_rect.y + 12),
                    (self.mb_rect.right - 12, self.mb_rect.y + 12),
                    (self.mb_rect.x + 12, self.mb_rect.bottom - 12),
                    (self.mb_rect.right - 12, self.mb_rect.bottom - 12)]:
            pygame.draw.circle(sup, GRIS_CLARO, (tx, ty), 4)

    def dibujar_slots(self, sup):
        etiquetas = {
            "cpu_socket": "LGA1700",
            "ram_slot1": "RAM1",
            "ram_slot2": "RAM2",
            "m2_slot": "M.2",
            "pcie_slot": "PCIe x16",
            "psu_bay": "PSU BAY",
            "cooler_mount": "",
        }
        for slot_id, rect in self.slots.items():
            comp_tipo = self.slot_acepta[slot_id]
            ocupado = any(c.colocado and c.tipo == comp_tipo and c.rect.topleft == rect.topleft
                        for c in self.componentes.values())
            if slot_id == "cooler_mount" and ocupado:
                continue  # lo tapa el cooler
            if ocupado:
                continue
            color = (90, 95, 105)
            if slot_id == "cpu_socket":
                color = (200, 170, 60) if self.lever_abierto else (90, 60, 60)
            pygame.draw.rect(sup, (12, 14, 16), rect, border_radius=3)
            pygame.draw.rect(sup, color, rect, 2, border_radius=3)
            if etiquetas[slot_id]:
                dibujar_texto(sup, etiquetas[slot_id], fuente_chica, GRIS_CLARO,
                            (rect.centerx, rect.bottom + 8), centrado=True)
        # palanca del socket CPU
        lever_rect = pygame.Rect(400, 158, 70, 8)
        col = VERDE if self.lever_abierto else ROJO
        pygame.draw.rect(sup, col, lever_rect, border_radius=3)
        dibujar_texto(sup, "PALANCA " + ("ABIERTA" if self.lever_abierto else "CERRADA"),
                    fuente_chica, col, (lever_rect.centerx, lever_rect.y - 10), centrado=True)
        # conectores fijos de cables (24pin / 8pin / paneles) ya dibujados por Cable.dibujar()

    def dibujar_panel_frontal(self, sup):
        panel = pygame.Rect(self.case_rect.x, self.case_rect.y, 34, self.case_rect.height)
        pygame.draw.rect(sup, (45, 46, 50), panel)
        pygame.draw.rect(sup, GRIS, panel, 2)
        # botón power
        encendido = self.estado in ("ENCENDIENDO", "BIOS", "BENCHMARK")
        col = VERDE if encendido else (200, 60, 60)
        pygame.draw.circle(sup, (20, 20, 22), self.power_btn.center, 20)
        pygame.draw.circle(sup, col, self.power_btn.center, 15)
        dibujar_texto(sup, "PWR", fuente_chica, BLANCO, (self.power_btn.centerx, self.power_btn.centery + 32),
                    centrado=True)
        # mazo de cables del panel frontal (salida visual)
        pygame.draw.circle(sup, (90, 90, 95), self.panel_pos, 8)
        dibujar_texto(sup, "PANEL", fuente_chica, GRIS_CLARO, (self.panel_pos[0], self.panel_pos[1] + 14),
                    centrado=False)

    def dibujar_rgb(self, sup):
        """Iluminación RGB perimetral que cicla de color cuando la PC prende."""
        n = 40
        for i in range(n):
            t = i / n
            hue = (t + self.tiempo * 0.25) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 0.85, 1.0)
            color = (int(r * 255), int(g * 255), int(b * 255))
            perim = 2 * (self.case_rect.width + self.case_rect.height)
            d = t * perim
            x, y = self._punto_en_perimetro(self.case_rect, d)
            pygame.draw.circle(sup, color, (int(x), int(y)), 4)

    def _punto_en_perimetro(self, rect, d):
        w, h = rect.width, rect.height
        if d < w:
            return rect.x + d, rect.y
        d -= w
        if d < h:
            return rect.right, rect.y + d
        d -= h
        if d < w:
            return rect.right - d, rect.bottom
        d -= w
        return rect.x, rect.bottom - d

    def dibujar_ui(self, sup):
        barra = pygame.Rect(0, 0, ANCHO, 90)
        pygame.draw.rect(sup, (18, 19, 24), barra)
        pygame.draw.line(sup, GRIS, (0, 90), (ANCHO, 90), 2)

        dibujar_texto(sup, "PC BUILDER PRO 2D", fuente_grande, BLANCO, (16, 10))
        dibujar_texto(sup, self.fase_actual(), fuente_normal, AMARILLO, (16, 44))

        # barra de progreso
        prog = self.progreso()
        pb_rect = pygame.Rect(16, 68, 260, 14)
        pygame.draw.rect(sup, GRIS_OSCURO, pb_rect, border_radius=7)
        pygame.draw.rect(sup, VERDE, (pb_rect.x, pb_rect.y, int(pb_rect.width * prog), pb_rect.height),
                        border_radius=7)
        dibujar_texto(sup, f"Progreso {int(prog * 100)}%", fuente_chica, BLANCO, (pb_rect.right + 10, pb_rect.y - 1))

        # compatibilidad
        comp_ok = self.mensaje_flash_t <= 0 or "correctamente" in self.mensaje_flash or "instalado" in self.mensaje_flash \
            or "conectado" in self.mensaje_flash
        cx, cy = 420, 40
        pygame.draw.circle(sup, VERDE if comp_ok else ROJO, (cx, cy), 14)
        dibujar_texto(sup, "OK" if comp_ok else "X", fuente_chica, NEGRO, (cx, cy), centrado=True)
        dibujar_texto(sup, "Compatibilidad", fuente_chica, GRIS_CLARO, (cx - 55, cy + 18))

        # watts
        wx = 520
        pygame.draw.rect(sup, GRIS_OSCURO, (wx, 30, 220, 16), border_radius=8)
        frac = min(1.0, self.watts_totales / self.psu_capacidad)
        col_w = VERDE if frac < 0.85 else (AMARILLO if frac < 1.0 else ROJO)
        pygame.draw.rect(sup, col_w, (wx, 30, int(220 * frac), 16), border_radius=8)
        dibujar_texto(sup, f"{self.watts_totales}W / {self.psu_capacidad}W", fuente_chica, BLANCO, (wx, 50))

        # estética
        dibujar_texto(sup, f"Estética: {self.puntaje_estetico} pts", fuente_normal, VIOLETA, (800, 20))

        # lista de cables obligatorios pendientes
        pendientes = [self.cables[c].nombre for c in self.cables_obligatorios if not self.cables[c].conectado]
        if pendientes and self.estado == "JUGANDO":
            txt = "Cables pendientes: " + ", ".join(pendientes[:3]) + ("..." if len(pendientes) > 3 else "")
            dibujar_texto(sup, txt, fuente_chica, GRIS_CLARO, (800, 48))

        # mensaje flash inferior
        if self.mensaje_flash_t > 0:
            alpha = min(255, int(255 * min(1.0, self.mensaje_flash_t)))
            s = pygame.Surface((ANCHO, 34), pygame.SRCALPHA)
            s.fill((0, 0, 0, min(180, alpha)))
            sup.blit(s, (0, ALTO - 40))
            dibujar_texto(sup, self.mensaje_flash, fuente_normal, BLANCO, (ANCHO // 2, ALTO - 23), centrado=True)

        dibujar_texto(sup, "[R] Reiniciar   [ESC] Salir", fuente_chica, GRIS, (ANCHO - 190, 8))

    def dibujar_bios(self, sup):
        s = pygame.Surface((ANCHO, ALTO))
        s.fill((0, 0, 40))
        lineas = [
            "American MegaBuild BIOS (C) Pygame Corp.",
            "CPU: Intel Core i7-14700K  ................ OK",
            "Memoria: 2 x 16GB DDR5 detectada .......... OK",
            "GPU: NVIDIA GeForce RTX 4070 .............. OK",
            "Almacenamiento: NVMe SSD detectado ........ OK",
            "",
            "Presiona SUPR para entrar a Setup",
            "Arrancando desde SSD NVMe...",
        ]
        y = 220
        for linea in lineas:
            dibujar_texto(s, linea, fuente_mono, (180, 220, 255), (300, y))
            y += 30
        sup.blit(s, (0, 0))

    def dibujar_benchmark(self, sup):
        s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        s.fill((0, 0, 0, 210))
        dibujar_texto(s, "¡SISTEMA ENCENDIDO CON ÉXITO!", fuente_titulo, VERDE, (ANCHO // 2, 200), centrado=True)
        dibujar_texto(s, f"FPS del benchmark: {self.fps_benchmark_mostrado}", fuente_grande, BLANCO,
                      (ANCHO // 2, 280), centrado=True)
        puntaje = self.fps_benchmark_mostrado * 100 + self.puntaje_estetico
        dibujar_texto(s, f"Puntaje total: {puntaje} pts  (incluye {self.puntaje_estetico} de estética)",
                      fuente_normal, AMARILLO, (ANCHO // 2, 330), centrado=True)
        # barrita de FPS animada
        pygame.draw.rect(s, GRIS_OSCURO, (ANCHO // 2 - 200, 380, 400, 24), border_radius=12)
        frac = self.fps_benchmark_mostrado / 144
        pygame.draw.rect(s, VERDE, (ANCHO // 2 - 200, 380, int(400 * frac), 24), border_radius=12)
        dibujar_texto(s, "¡GANASTE! Presiona [R] para armar otra PC", fuente_normal, BLANCO,
                      (ANCHO // 2, 440), centrado=True)
        sup.blit(s, (0, 0))

    def dibujar_fallo(self, sup):
        s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        s.fill((0, 0, 0, 235))
        dibujar_texto(s, "LA PC NO ENCIENDE", fuente_titulo, ROJO, (ANCHO // 2, 260), centrado=True)
        dibujar_texto(s, f"Error: {self.mensaje_error}", fuente_normal, BLANCO, (ANCHO // 2, 330), centrado=True)
        dibujar_texto(s, "Revisa el cableado y vuelve a intentarlo (o presiona R para reiniciar)",
                      fuente_chica, GRIS_CLARO, (ANCHO // 2, 370), centrado=True)
        sup.blit(s, (0, 0))
        # click en cualquier lado / power vuelve a jugar
        if pygame.mouse.get_pressed()[0]:
            pass

    def dibujar_explosion(self, sup):
        s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        s.fill((30, 0, 0, 200))
        dibujar_texto(s, "¡LA FUENTE EXPLOTÓ!", fuente_titulo, NARANJA, (ANCHO // 2, 260), centrado=True)
        dibujar_texto(s, self.mensaje_error, fuente_normal, BLANCO, (ANCHO // 2, 320), centrado=True)
        dibujar_texto(s, "Presiona R para reiniciar", fuente_chica, GRIS_CLARO, (ANCHO // 2, 360), centrado=True)
        sup.blit(s, (0, 0))

    # permitir volver a intentar desde estados de fallo con click
    def click_estado_fallo(self):
        if self.estado in ("FALLO", "EXPLOSION"):
            self.estado = "JUGANDO"


# ------------------------------------------------------------------
# BUCLE PRINCIPAL
# ------------------------------------------------------------------
def main():
    juego = Game()
    ejecutando = True
    while ejecutando:
        dt = reloj.tick(FPS) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                ejecutando = False
            elif ev.type == pygame.MOUSEBUTTONDOWN and juego.estado in ("FALLO", "EXPLOSION"):
                juego.click_estado_fallo()
            else:
                juego.manejar_evento(ev)

        juego.actualizar(dt)
        juego.dibujar(pantalla)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
