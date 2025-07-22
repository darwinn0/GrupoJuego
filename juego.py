# Importamos las librerías necesarias de Ursina
from ursina import *
import math

# --- Configuración de Niveles ---
LEVEL_CONFIG = {
    1: {'targets': 10, 'speed': (10, 15), 'scale': 2.8, 'accuracy_goal': 50},
    2: {'targets': 10, 'speed': (15, 22), 'scale': 2.0, 'accuracy_goal': 60},
    3: {'targets': 10, 'speed': (20, 28), 'scale': 1.8, 'accuracy_goal': 75}
}

# --- Clase para los Objetivos Esféricos (¡Ahora Patos!) ---
class TargetSphere(Entity):
    def __init__(self, speed_range, scale):
        side = random.choice([-1, 1])
        start_pos = Vec3(22 * side, random.uniform(-8, -2), random.uniform(15, 25))
        direction = Vec3(-side, random.uniform(-.2, .2), random.uniform(-.1, .1))

        super().__init__(
            model='quad',
            texture='assets/textures/mario.png',
            color=color.white,
            scale=scale,
            position=start_pos,
            collider='box',
            shadow=True,
            billboard=True
        )
        self.direction = direction
        self.speed = random.uniform(speed_range[0], speed_range[1])

    def update(self):
        self.position += self.direction * self.speed * time.dt
        if abs(self.x) > 24:
            destroy(self)
            invoke(spawn_next_target, delay=0.5)

    def hit(self):
        global hits, points
        hit_sound.play()
        hits += 1
        points += 100
        effect = Entity(
            model='quad',
            texture='assets/textures/hit_effect.png',
            color=color.white,
            scale=self.scale * 0.8,
            position=self.world_position,
            shadow=False,
            billboard=True
        )
        effect.animate_scale(self.scale * 1.2, duration=0.2, curve=curve.out_quad)
        effect.fade_out(duration=0.2)
        destroy(effect, delay=0.2)

        destroy(self)
        invoke(spawn_next_target, delay=0.5)

# --- Variables Globales del Juego ---
hits, points, shots_fired = 0, 0, 0
targets_spawned = 0
unlocked_level = 1
current_level = 1
game_active = False
last_shot_time = 0
current_bg_music = None

# --- Funciones del Juego ---
def go_to_level_select():
    main_menu.disable()
    level_select_menu.enable()
    update_level_buttons()

def start_level(level):
    global hits, points, shots_fired, game_active, current_level, targets_spawned, last_shot_time, current_bg_music
    current_level = level
    hits, points, shots_fired, targets_spawned = 0, 0, 0, 0
    game_active = True

    if current_bg_music:
        current_bg_music.stop()
        destroy(current_bg_music)
        current_bg_music = None

    if current_level == 1:
        current_bg_music = Audio('assets/sounds/fondo.mp3', loop=True, autoplay=False, volume=0.8)
    elif current_level == 2:
        current_bg_music = Audio('assets/sounds/fondoNivel2.mp3', loop=True, autoplay=False, volume=0.8)
    elif current_level == 3:
        current_bg_music = Audio('assets/sounds/fondoNivel3.mp3', loop=True, autoplay=False, volume=0.8)

    if current_bg_music:
        current_bg_music.play()

    level_select_menu.disable()
    game_hud.enable()
    crosshair.enable()
    mouse.locked = True

    last_shot_time = time.time()

    pistol.disable()
    rifle.disable()
    shotgun.disable()

    if current_level == 1:
        pistol.enable()
    elif current_level == 2:
        rifle.enable()
    elif current_level == 3:
        shotgun.enable()

    for t in scene.entities:
        if isinstance(t, TargetSphere):
            destroy(t)

    spawn_next_target()

def spawn_next_target():
    global targets_spawned
    if not game_active: return

    if targets_spawned < LEVEL_CONFIG.get(current_level, {}).get('targets', 0):
        config = LEVEL_CONFIG.get(current_level, {})
        TargetSphere(config.get('speed', (10, 15)), config.get('scale', 1))
        targets_spawned += 1
        update_hud()
    else:
        invoke(end_level, delay=1)

def end_level():
    global game_active, unlocked_level, current_bg_music
    game_active = False

    if current_bg_music:
        current_bg_music.stop()
        destroy(current_bg_music)
        current_bg_music = None

    game_hud.disable()
    crosshair.disable()
    pistol.disable()
    rifle.disable()
    shotgun.disable()
    mouse.locked = False

    accuracy = (hits / shots_fired) * 100 if shots_fired > 0 else 0
    goal = LEVEL_CONFIG.get(current_level, {}).get('accuracy_goal', 0)

    end_panel = Entity(parent=camera.ui, model='quad', scale=(.8, .5), color=color.dark_gray.tint(.2), z=1)
    Text(parent=end_panel, text=f"Precisión: {accuracy:.1f}% (Objetivo: {goal}%)", origin=(0,0), y=0, scale=1.5)
    Text(parent=end_panel, text=f"Aciertos: {hits} / {shots_fired}", origin=(0,0), y=-.1, scale=1.5)

    if accuracy >= goal:
        message = f"¡NIVEL {current_level} COMPLETADO!"
        if current_level < 3:
            unlocked_level = max(unlocked_level, current_level + 1)

        Text(parent=end_panel, text=message, origin=(0,0), y=.2, scale=2)
        Button(parent=end_panel, text="Menú de Niveles", color=color.azure, scale=(0.25, 0.08), y=-.3, on_click=Func(lambda: (destroy(end_panel), show_level_select_menu())))
    else:
        message = "INTÉNTALO DE NUEVO"

        Text(parent=end_panel, text=message, origin=(0,0), y=.2, scale=2)
        Button(parent=end_panel, text="Reintentar", color=color.azure, scale=(0.25, 0.08), y=-.25, on_click=Func(lambda: (destroy(end_panel), start_level(current_level))))
        Button(parent=end_panel, text="Menú de Niveles", color=color.red, scale=(0.25, 0.08), y=-.4, on_click=Func(lambda: (destroy(end_panel), show_level_select_menu())))

def show_level_select_menu():
    global current_bg_music
    game_hud.disable()
    pistol.disable()
    rifle.disable()
    shotgun.disable()
    crosshair.disable()
    for t in scene.entities:
        if isinstance(t, TargetSphere):
            destroy(t)
    level_select_menu.enable()
    update_level_buttons()
    mouse.locked = False
    if current_bg_music:
        current_bg_music.stop()
        destroy(current_bg_music)
        current_bg_music = None

def show_main_menu():
    global current_bg_music
    level_select_menu.disable()
    game_hud.disable()
    pistol.disable()
    rifle.disable()
    shotgun.disable()
    crosshair.disable()
    for t in scene.entities:
        if isinstance(t, TargetSphere):
            destroy(t)
    main_menu.enable()
    mouse.locked = False
    if current_bg_music:
        current_bg_music.stop()
        destroy(current_bg_music)
        current_bg_music = None

def update_hud():
    accuracy = (hits / shots_fired) * 100 if shots_fired > 0 else 0
    hud_text.text = (
        f"NIVEL {current_level}\n"
        f"Objetivo: {targets_spawned}/{LEVEL_CONFIG.get(current_level, {}).get('targets', 0)}\n"
        f"Aciertos: {hits}\n"
        f"Precisión: {accuracy:.1f}%"
    )

def update_level_buttons():
    for i, button in enumerate(level_buttons):
        button.disabled = (i + 1 > unlocked_level)
        button.text_entity.color = color.white if not button.disabled else color.gray

def resume_game():
    global current_bg_music
    pause_menu.disable()
    mouse.locked = True
    application.resume()
    if current_bg_music:
        current_bg_music.play()

# --- Inicialización de la Aplicación Ursina ---
app = Ursina(title='AIM PRESICION DDC', borderless=False, fullscreen=True)

# --- Sonidos ---
gunshot_sound = Audio('assets/sounds/hit.mp3', loop=False, autoplay=False, volume=0.3)
hit_sound = Audio('assets/sounds/hit.mp3', loop=False, autoplay=False, volume=0.5)

# --- Creación del Entorno (Cabina de Disparo con estilo oscuro) ---
shooting_range_background = Entity(
    model='quad',
    texture='assets/textures/mapa.png',
    scale=(100, 50),
    position=(0, 0, 50),
    rotation_y=180,
    double_sided=True
).disable()

back_wall = Entity(
    model='cube',
    scale=(40, 30, 1),
    position=(0, 5, 30),
    texture='assets/textures/mapa.png',
    color=color.white,
    collider='box'
)

left_wall = Entity(
    model='cube',
    scale=(1, 30, 85),
    position=(-20, 5, 7.5),
    texture='assets/textures/mapa.png',
    color=color.white,
    collider='box'
)

right_wall = Entity(
    model='cube',
    scale=(1, 30, 85),
    position=(20, 5, 7.5),
    texture='assets/textures/mapa.png',
    color=color.white,
    collider='box'
)

ceiling = Entity(
    model='cube',
    scale=(49, 1, 85),
    position=(0, 20, 9.5),
    texture='assets/textures/cieloo.png',
    color=color.white,
    collider='box'
)

ground_plane = Entity(
    model='plane',
    scale=(150, 1, 150),
    position=(0, -10, 5),
    texture='assets/textures/piso.jpg',
    texture_scale=(2, 2),
    collider='box'
)

sky_color = Sky(color=color.black66)

sun = DirectionalLight(y=10, x=20, shadows=True, color=color.white)

ambient_light = AmbientLight(color=color.rgba(100, 100, 100, 255))

# --- Configuración del Jugador (Cámara estática) ---
camera.position = (0, 0, -15)
camera.fov = 80

# --- Arma y Mira (DISEÑOS MEJORADOS) ---
# para el nivel 1
pistol = Entity(parent=camera,
                model='assets/models/GUN.obj',
                texture='assets/textures/GUN_Material.003_BaseColor.jpg',
                position=(0.5, -0.4, 1.2),
                rotation=(0, 180, 0),
                scale=0.15
               )
pistol.disable()


# para el nivel 2
rifle = Entity(parent=camera, model='assets/models/xm177.obj', color=color.black, rotation=(0, 100, -5), position=(0.6, -0.5, 1.5), scale=0.03)

# para el nivel 3
shotgun = Entity(parent=camera,
                 model='assets/models/Shotgun.obj',
                 texture='assets/textures/Gun_nivel3.jpg',
                 position=(0.5, -0.65, 1.5),
                 rotation=(0, 90, 0),
                 scale=0.15
                )
shotgun.disable()

crosshair = Entity(parent=camera.ui, model='circle', scale=0.008, color=color.red)

# --- Interfaz de Usuario (UI) Mejorada ---
game_hud = Entity(parent=camera.ui, enabled=False)
hud_background = Entity(
    parent=game_hud,
    model='quad',
    scale=(0.25, 0.15),
    position=window.bottom_left + Vec2(0.1, 0.1),
    color=color.black66,
    origin=(-0.5, -0.5)
).disable()
hud_text = Text(
    parent=hud_background,
    text="",
    origin=(-0.5, -0.5),
    position=(0.05, 0.05),
    scale=3.0,
    color=color.white
)

# --- Menú Principal ---
main_menu = Entity(
    parent=camera.ui,
    model='quad',
    texture='assets/textures/fondoLogo.jpg',
    scale_x=camera.aspect_ratio,
    scale_y=1,
    enabled=True,
    z=0.1,
    color=color.white
)

button_container = Entity(parent=main_menu, y=-0.4)

start_button = Button(
    parent=button_container,
    text="INICIAR",
    color=color.blue,
    scale=(0.35, 0.1),
    x=-0.2,
    on_click=go_to_level_select
)
quit_button = Button(
    parent=button_container,
    text="SALIR",
    color=color.red,
    scale=(0.35, 0.1),
    x=0.2,
    on_click=application.quit
)

# --- Menú de Selección de Nivel ---
level_select_menu = Entity(parent=camera.ui, enabled=False)

# --- Nuevo Fondo para el Menú de Selección de Nivel ---
level_select_background = Entity(
    parent=level_select_menu,
    model='quad',
    texture='assets/textures/MenuNiveles.jpg',
    scale_x=camera.aspect_ratio,
    scale_y=1,
    z=0.1,
    color=color.white
)

level_title = Text(parent=level_select_menu, text="Seleccionar Nivel", scale=3, origin=(0,0), y=0.4)

# Contenedor para los botones de nivel para organizarlos horizontalmente
level_buttons_container = Entity(parent=level_select_menu, y=-0.4) # Ajusta la 'y' para mover el grupo de botones hacia abajo
# Botones para seleccionar cada nivel, ahora dentro del contenedor y con posiciones X ajustadas
level_1_button = Button(parent=level_buttons_container, text="Nivel 1", scale=(0.25, 0.08), x=-0.35, y=0.1, on_click=lambda: start_level(1))
level_2_button = Button(parent=level_buttons_container, text="Nivel 2", scale=(0.25, 0.08), x=0, y=0.1, on_click=lambda: start_level(2))
level_3_button = Button(parent=level_buttons_container, text="Nivel 3", scale=(0.25, 0.08), x=0.35, y=0.1, on_click=lambda: start_level(3))
level_buttons = [level_1_button, level_2_button, level_3_button]

# Nuevo botón para regresar al inicio
back_to_main_menu_button = Button(
    parent=level_buttons_container,
    text="Regresar al Inicio",
    color=color.red,    # Puedes elegir el color que prefieras
    scale=(0.3, 0.08),  # Ajusta el tamaño si es necesario
    y=-0.02,            # CAMBIADO: Posiciona este botón más arriba (menos negativo)
    on_click=show_main_menu # Llama a la función para mostrar el menú principal
)
# --- Menú de Pausa ---
pause_menu = Entity(parent=camera.ui, enabled=False, model='quad', scale=(0.5, 0.5), color=color.black90)
Text(parent=pause_menu, text="Juego en Pausa", origin=(0,0), y=0.4, scale=2)

Button(parent=pause_menu, text="Reanudar Juego", color=color.azure, scale=(0.8, 0.2), y=0.15, on_click=resume_game)
Button(parent=pause_menu, text="Menú de Niveles", color=color.blue, scale=(0.8, 0.2), y=-0.1, on_click=Func(lambda: (application.resume(), pause_menu.disable(), show_level_select_menu())))
Button(parent=pause_menu, text="Salir al Menú Principal", color=color.red, scale=(0.8, 0.2), y=-0.35, on_click=Func(lambda: (application.resume(), pause_menu.disable(), show_main_menu())))

# --- Lógica Principal ---
def update():
    global current_bg_music
    if not application.paused and game_active:
        update_hud()
        camera.rotation_y += mouse.velocity.x * 60
        camera.rotation_x -= mouse.velocity.y * 60
        camera.rotation_x = clamp(camera.rotation_x, -50, 50)
        camera.rotation_y = clamp(camera.rotation_y, -80, 80)
    elif application.paused and current_bg_music and current_bg_music.playing:
        current_bg_music.pause()

def input(key):
    global shots_fired, last_shot_time, current_bg_music
    if key == 'escape' and game_active:
        application.paused = not application.paused
        pause_menu.enabled = application.paused
        mouse.locked = not pause_menu.enabled
        if application.paused:
            if current_bg_music:
                current_bg_music.pause()
        else:
            if current_bg_music:
                current_bg_music.play()

    if application.paused:
        return

    if game_active and key == 'left mouse down':
        if time.time() - last_shot_time < 0.5:
            return
        last_shot_time = time.time()

        shots_fired += 1
        gunshot_sound.play()

        if current_level == 1:
            pistol.rotation_x = -10
            pistol.animate_rotation_x(0, duration=0.1)
            ignore_list = [pistol]
        elif current_level == 2:
            rifle.rotation_x = -5
            rifle.animate_rotation_x(0, duration=0.1)
            ignore_list = [rifle]
        elif current_level == 3:
            shotgun.rotation_x = -15
            shotgun.animate_rotation_x(0, duration=0.1)
            ignore_list = [shotgun]
        else:
            ignore_list = []

        hit_info = raycast(camera.world_position, camera.forward, distance=200, ignore=ignore_list)
        if hit_info.hit and hasattr(hit_info.entity, 'hit'):
            hit_info.entity.hit()

# --- Iniciar el Juego ---
game_hud.disable()
pistol.disable()
rifle.disable()
shotgun.disable()
crosshair.disable()
mouse.locked = False
app.run()