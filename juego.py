# Importamos las librerías necesarias de Ursina
from ursina import *
import math

# ======================================================================================
# --- Configuración de Niveles ---
# ======================================================================================
# Diccionario que define las propiedades de cada nivel.
# 'targets': número de objetivos a aparecer
# 'speed': rango de velocidad de los objetivos (mínimo, máximo)
# 'scale': tamaño de los objetivos
# 'accuracy_goal': porcentaje de precisión requerido para completar el nivel
# 'batch_size': número de objetivos a generar a la vez para este nivel
LEVEL_CONFIG = {
    1: {'targets': 10, 'speed': (10, 15), 'scale': 2.8, 'accuracy_goal': 50, 'batch_size': 1},
    2: {'targets': 10, 'speed': (15, 22), 'scale': 2.0, 'accuracy_goal': 60, 'batch_size': 1},
    3: {'targets': 20, 'speed': (20, 28), 'scale': 1.8, 'accuracy_goal': 75, 'batch_size': 3} # Nivel 3 con 20 objetivos y aparecen de 3 en 3
}

# ======================================================================================
# --- Clase para los Objetivos (¡Ahora Marios en este juego!) ---
# ======================================================================================
class TargetSphere(Entity):
    def __init__(self, speed_range, scale):
        # Decide si el objetivo aparece por la izquierda (-1) o por la derecha (1)
        side = random.choice([-1, 1])
        # Posición inicial del objetivo fuera de la pantalla
        start_pos = Vec3(22 * side, random.uniform(-8, -2), random.uniform(15, 25))
        # Dirección en la que se moverá el objetivo
        direction = Vec3(-side, random.uniform(-.2, .2), random.uniform(-.1, .1))

        super().__init__(
            model='quad',  # Usamos un quad para la imagen de Mario
            texture='assets/textures/mario.png',  # Textura de Mario
            color=color.white,
            scale=scale,
            position=start_pos,
            collider='box',  # Colisionador para detectar disparos
            shadow=True,
            billboard=True  # Hace que la imagen siempre mire a la cámara
        )
        self.direction = direction
        self.speed = random.uniform(speed_range[0], speed_range[1])

    # Se llama cada frame para actualizar la posición del objetivo
    def update(self):
        self.position += self.direction * self.speed * time.dt
        # Si el objetivo se sale de los límites de la pantalla, se destruye
        if abs(self.x) > 24:
            destroy(self)
            # Invoca la creación del siguiente objetivo después de un pequeño retraso
            invoke(spawn_next_target, delay=0.5)

    # Se llama cuando el objetivo es golpeado por un disparo
    def hit(self):
        global hits, points
        hit_sound.play()  # Reproduce el sonido de impacto
        hits += 1         # Incrementa el contador de aciertos
        points += 100     # Suma puntos (aunque no se muestren actualmente en el HUD)
        
        # Crea un efecto visual de impacto
        effect = Entity(
            model='quad',
            texture='assets/textures/hit_effect.png',
            color=color.white,
            scale=self.scale * 0.8,
            position=self.world_position,
            shadow=False,
            billboard=True
        )
        # Anima el efecto para que crezca y se desvanezca
        effect.animate_scale(self.scale * 1.2, duration=0.2, curve=curve.out_quad)
        effect.fade_out(duration=0.2)
        destroy(effect, delay=0.2)

        destroy(self) # Destruye el objetivo golpeado
        # Invoca la creación del siguiente objetivo después de un pequeño retraso
        invoke(spawn_next_target, delay=0.5)

# ======================================================================================
# --- Variables Globales del Juego ---
# ======================================================================================
hits = 0            # Número de aciertos
points = 0          # Puntos del jugador (actualmente no usados en el HUD)
shots_fired = 0     # Número de disparos realizados
targets_spawned = 0 # Número de objetivos generados en el nivel actual
unlocked_level = 1  # El nivel más alto desbloqueado por el jugador
current_level = 1   # El nivel actual en juego
game_active = False # Booleano para saber si el juego está activo
last_shot_time = 0  # Tiempo del último disparo para controlar la cadencia
current_bg_music = None # Referencia a la música de fondo actual

# ======================================================================================
# --- Funciones del Juego ---
# ======================================================================================

# Cambia a la pantalla de selección de nivel
def go_to_level_select():
    main_menu.disable()      # Deshabilita el menú principal
    level_select_menu.enable() # Habilita el menú de selección de nivel
    update_level_buttons()     # Actualiza el estado de los botones de nivel (desbloqueados/bloqueados)

# Inicia un nivel específico
def start_level(level):
    global hits, points, shots_fired, game_active, current_level, targets_spawned, last_shot_time, current_bg_music
    current_level = level        # Establece el nivel actual
    hits, points, shots_fired, targets_spawned = 0, 0, 0, 0 # Reinicia contadores
    game_active = True           # Activa el estado del juego

    # Detiene y DESTRUYE cualquier música de fondo previa para asegurar que reinicie
    if current_bg_music:
        current_bg_music.stop()
        destroy(current_bg_music) # Destruimos el objeto Audio
        current_bg_music = None

# ======================================================================================
    # Carga la música de fondo según el nivel
# ======================================================================================
    if current_level == 1:
        current_bg_music = Audio('assets/sounds/fondo.mp3', loop=True, autoplay=False, volume=0.8)
    elif current_level == 2:
        current_bg_music = Audio('assets/sounds/fondoNivel2.mp3', loop=True, autoplay=False, volume=0.8)
    elif current_level == 3:
        current_bg_music = Audio('assets/sounds/fondoNivel3.mp3', loop=True, autoplay=False, volume=0.4) # Volumen de fondo del Nivel 3

    if current_bg_music:
        current_bg_music.play() # Reproduce la música desde el inicio (ya que es un objeto nuevo)

    level_select_menu.disable() # Deshabilita el menú de selección
    game_hud.enable()           # Habilita el HUD del juego
    crosshair.enable()          # Habilita la mira
    mouse.locked = True         # Bloquea el ratón en el centro de la pantalla (para la cámara)

    last_shot_time = time.time() # Reinicia el temporizador del último disparo

# ======================================================================================
    # Deshabilita todas las armas y luego habilita la correcta para el nivel
# ======================================================================================
    pistol.disable()
    rifle.disable()
    shotgun.disable()

    if current_level == 1:
        pistol.enable()
    elif current_level == 2:
        rifle.enable()
    elif current_level == 3:
        shotgun.enable()

    # Destruye cualquier objetivo existente de un juego anterior
    for t in scene.entities:
        if isinstance(t, TargetSphere):
            destroy(t)

    # Llama a la función para generar el primer (o primeros) objetivo(s)
    # según la configuración del nivel (batch_size)
    spawn_next_target() 

# ======================================================================================
# Genera el siguiente objetivo (o batch de objetivos)
# ======================================================================================
def spawn_next_target():
    global targets_spawned
    if not game_active: return # No genera objetivos si el juego no está activo

    config = LEVEL_CONFIG.get(current_level, {})
    total_targets_for_level = config.get('targets', 0)
    batch_size = config.get('batch_size', 1) # Obtiene el tamaño del lote para el nivel actual

    # Calcula cuántos objetivos se deben generar en este momento (máx. batch_size, y no más del total del nivel)
    targets_to_spawn_now = min(batch_size, total_targets_for_level - targets_spawned)

    if targets_to_spawn_now > 0:
        for _ in range(targets_to_spawn_now):
            TargetSphere(config.get('speed', (10, 15)), config.get('scale', 1)) # Crea un nuevo objetivo
            targets_spawned += 1 # Incrementa el contador de objetivos generados
        update_hud() # Actualiza el HUD
    else:
        # Si ya se generaron todos los objetivos, finaliza el nivel después de un retraso
        invoke(end_level, delay=1)

# ======================================================================================
# Finaliza el nivel y muestra la pantalla de resultados
# ======================================================================================
def end_level():
    global game_active, unlocked_level, current_bg_music
    game_active = False # Desactiva el juego

    # Detiene y destruye cualquier música de fondo
    if current_bg_music:
        current_bg_music.stop()
        destroy(current_bg_music)
        current_bg_music = None

    # Deshabilita elementos del juego
    game_hud.disable()
    crosshair.disable()
    pistol.disable()
    rifle.disable()
    shotgun.disable()
    mouse.locked = False # Desbloquea el ratón para interactuar con la UI

    # Calcula la precisión
    accuracy = (hits / shots_fired) * 100 if shots_fired > 0 else 0
    goal = LEVEL_CONFIG.get(current_level, {}).get('accuracy_goal', 0)

# ======================================================================================
    # Crea el panel de fin de nivel con la imagen de fondo
# ======================================================================================
    end_panel = Entity(
        parent=camera.ui,
        model='quad',
        scale_x=camera.aspect_ratio, # Ajusta el ancho al ratio de aspecto de la cámara
        scale_y=1,                   # Ajusta la altura para que ocupe toda la pantalla
        texture='assets/textures/fondoSalida.png',  
        color=color.white,  # Asegura que el color base no interfiera con la textura
        z=1
    )
    
# ======================================================================================
# Muestra la precisión y aciertos por nivel 
# ======================================================================================
    Text(parent=end_panel, text=f"Precisión: {accuracy:.1f}% (Objetivo: {goal}%)", origin=(0,0), y=0.1, scale=1.5)
    Text(parent=end_panel, text=f"Aciertos: {hits} / {targets_spawned}", origin=(0,0), y=-.05, scale=1.5) # Mostrar aciertos/objetivos_generados

    # Lógica para nivel completado o fallido
    if accuracy >= goal:
        message = f"¡NIVEL {current_level} COMPLETADO!"
        if current_level < 3: # Si no es el último nivel, desbloquea el siguiente
            unlocked_level = max(unlocked_level, current_level + 1)
        
        Text(parent=end_panel, text=message, origin=(0,0), y=.3, scale=2)

        # Botón para ir al siguiente nivel (aparece si no es el último nivel)
        if current_level < len(LEVEL_CONFIG): # Comprueba si hay un siguiente nivel
            Button(parent=end_panel, text="Siguiente Nivel", color=color.green, scale=(0.25, 0.08), y=-.2, on_click=Func(lambda: (destroy(end_panel), start_level(current_level + 1))))
        
        # Botón para volver al menú de niveles
        Button(parent=end_panel, text="Menú de Niveles", color=color.azure, scale=(0.25, 0.08), y=-.35, on_click=Func(lambda: (destroy(end_panel), show_level_select_menu())))
    else:
        message = "INTÉNTALO DE NUEVO"

        Text(parent=end_panel, text=message, origin=(0,0), y=.3, scale=2)
        # Botón para reintentar el nivel
        Button(parent=end_panel, text="Reintentar", color=color.azure, scale=(0.25, 0.08), y=-.2, on_click=Func(lambda: (destroy(end_panel), start_level(current_level))))
        # Botón para volver al menú de niveles
        Button(parent=end_panel, text="Menú de Niveles", color=color.red, scale=(0.25, 0.08), y=-.35, on_click=Func(lambda: (destroy(end_panel), show_level_select_menu())))
# ======================================================================================
# Muestra el menú de selección de nivel
# ======================================================================================
def show_level_select_menu():
    global current_bg_music
    game_hud.disable()
    pistol.disable()
    rifle.disable()
    shotgun.disable()
    crosshair.disable()
    # Destruye todos los objetivos existentes
    for t in scene.entities:
        if isinstance(t, TargetSphere):
            destroy(t)
    level_select_menu.enable() # Habilita el menú de selección
    update_level_buttons()     # Actualiza el estado de los botones
    mouse.locked = False       # Desbloquea el ratón
    # Detiene cualquier música de fondo si la hay
    if current_bg_music:
        current_bg_music.stop()
        destroy(current_bg_music)
        current_bg_music = None

# ======================================================================================
# Muestra el menú principal
# ======================================================================================
def show_main_menu():
    global current_bg_music
    level_select_menu.disable()
    game_hud.disable()
    pistol.disable()
    rifle.disable()
    shotgun.disable()
    crosshair.disable()
    # Destruye todos los objetivos existentes
    for t in scene.entities:
        if isinstance(t, TargetSphere):
            destroy(t)
    main_menu.enable() # Habilita el menú principal
    mouse.locked = False # Desbloquea el ratón
    # Detiene cualquier música de fondo si la hay
    if current_bg_music:
        current_bg_music.stop()
        destroy(current_bg_music)
        current_bg_music = None

# Actualiza el texto en el HUD
def update_hud():
    accuracy = (hits / shots_fired) * 100 if shots_fired > 0 else 0
    hud_text.text = (
        f"NIVEL {current_level}\n"
        f"Objetivo: {targets_spawned}/{LEVEL_CONFIG.get(current_level, {}).get('targets', 0)}\n"
        f"Aciertos: {hits}\n"
        f"Precisión: {accuracy:.1f}%"
    )

# Actualiza el estado de los botones de nivel (habilitados/deshabilitados)
def update_level_buttons():
    for i, button in enumerate(level_buttons):
        button.disabled = (i + 1 > unlocked_level) # Deshabilita si el nivel no está desbloqueado
        button.text_entity.color = color.white if not button.disabled else color.gray # Cambia color del texto

# ======================================================================================
# Reanuda el juego cuando se sale 
# ======================================================================================
def resume_game():
    global current_bg_music
    pause_menu.disable() # Deshabilita el menú de pausa
    mouse.locked = True  # Bloquea el ratón
    application.resume() # Reanuda la aplicación (actualizaciones, etc.)
    if current_bg_music:
        current_bg_music.stop() # Detiene la música para reiniciar
        current_bg_music.play() # Reanuda la música de fondo al reanudar el juego

# Inicialización de la Aplicación Ursina 
app = Ursina(title='AIM PRESICION DDC', borderless=False, fullscreen=True, info=False)

# ======================================================================================
# Sonidos de cada arma y de efecto de disaparo
# ======================================================================================
gunshot_pistol_sound = Audio('assets/sounds/hit.mp3', loop=False, autoplay=False, volume=0.3)
gunshot_rifle_sound = Audio('assets/sounds/sonidoRifle.mp3', loop=False, autoplay=False, volume=0.5)
gunshot_shotgun_sound = Audio('assets/sounds/sonidoEscopeta.mp3', loop=False, autoplay=False, volume=3.0) 
hit_sound = Audio('assets/sounds/hit.mp3', loop=False, autoplay=False, volume=0.5)

# ======================================================================================
# Creación del Entorno de la cabina de disparo
# ======================================================================================
shooting_range_background = Entity(
    model='quad',
    texture='assets/textures/mapa.png',
    scale=(100, 50),
    position=(0, 0, 50),
    rotation_y=180,
    double_sided=True
).disable()

# Pared trasera
back_wall = Entity(
    model='cube',
    scale=(40, 30, 1),
    position=(0, 5, 30),
    texture='assets/textures/fondoMario.jpg',
    color=color.white,
    collider='box'
)

# Pared izquierda
left_wall = Entity(
    model='cube',
    scale=(1, 30, 85),
    position=(-20, 5, 7.5),
    texture='assets/textures/fondoMario.jpg',
    color=color.white,
    collider='box'
)

# Pared derecha
right_wall = Entity(
    model='cube',
    scale=(1, 30, 85),
    position=(20, 5, 7.5),
    texture='assets/textures/fondoMario.jpg',
    color=color.white,
    collider='box'
)

# Techo
ceiling = Entity(
    model='cube',
    scale=(49, 1, 85),
    position=(0, 20, 9.5),
    texture='assets/textures/cieloMario.jpg',
    color=color.white,
    collider='box'
)

# Suelo
ground_plane = Entity(
    model='plane',
    scale=(150, 1, 150),
    position=(0, -10, 5),
    texture='assets/textures/sueloMario.jpg',
    texture_scale=(2, 2),
    collider='box'
)

# Cielo (color)
sky_color = Sky(color=color.black66)

# Iluminación direccional (simula un sol)
sun = DirectionalLight(y=10, x=20, shadows=True, color=color.white)

# Luz ambiental
ambient_light = AmbientLight(color=color.rgba(100, 100, 100, 255))

# --- Configuración del Jugador (Cámara estática) ---
camera.position = (0, 0, -15) # Posición de la cámara
camera.fov = 80              # Campo de visión de la cámara

# ======================================================================================
# diseños de las armas con texturas y modelos
# ======================================================================================
# Pistola (Nivel 1)
pistol = Entity(parent=camera,
                model='assets/models/modeloArma1.obj',
                texture='assets/textures/arma1.png',
                position=(0.5, -0.4, 1.2),
                rotation=(0, -90, 0), # Ajustada para que apunte hacia adelante
                scale=0.15
               )
pistol.disable() # Deshabilitada al inicio.

# Rifle (Nivel 2)
rifle = Entity(parent=camera, 
               model='assets/models/xm177.obj', 
               color=color.black, rotation=(0, 100, -5), 
               position=(0.6, -0.5, 1.5), 
               scale=0.03)
rifle.disable() # Deshabilitada al inicio

# Escopeta (Nivel 3)
shotgun = Entity(parent=camera,
                 model='assets/models/Shotgun.obj',
                 texture='assets/textures/Gun_nivel3.jpg',
                 position=(0.5, -0.65, 1.5),
                 rotation=(0, 90, 0),
                 scale=0.15
                )
shotgun.disable() # Deshabilitada al inicio

# Mira del juego
crosshair = Entity(parent=camera.ui, model='circle', scale=0.008, color=color.red)

# --- Interfaz de Usuario (UI) Mejorada ---
game_hud = Entity(parent=camera.ui, enabled=False) # Contenedor para el HUD, inicialmente deshabilitado
hud_background = Entity(
    parent=game_hud,
    model='quad',
    scale=(0.25, 0.15),
    position=window.bottom_left + Vec2(0.1, 0.1),
    color=color.black66,
    origin=(-0.5, -0.5)
).disable() # Fondo del HUD, inicialmente deshabilitado
hud_text = Text(
    parent=hud_background,
    text="",
    origin=(-0.5, -0.5),
    position=(0.05, 0.05),
    scale=3.0,
    color=color.white
)


# ======================================================================================
# Botones iniciales del inicio del juego
# ======================================================================================

# --- Menú Principal ---
main_menu = Entity(
    parent=camera.ui,
    model='quad',
    texture='assets/textures/fondoLogo.jpg', # Fondo del menú principal
    scale_x=camera.aspect_ratio,
    scale_y=1,
    enabled=True,
    z=0.1,
    color=color.white
)

button_container = Entity(parent=main_menu, y=-0.4) # Contenedor para los botones del menú principal

start_button = Button(
    parent=button_container,
    text="INICIAR",
    color=color.blue,
    scale=(0.35, 0.1),
    x=-0.2,
    on_click=go_to_level_select # Llama a la función para ir al menú de selección de nivel
)
quit_button = Button(
    parent=button_container,
    text="SALIR",
    color=color.red,
    scale=(0.35, 0.1),
    x=0.2,
    on_click=application.quit # Sale de la aplicación
)

# ======================================================================================
# Fondo para el Menú de la Selección de Nivel
# ======================================================================================
level_select_menu = Entity(parent=camera.ui, enabled=False) # Contenedor para el menú de selección de nivel, inicialmente deshabilitado

level_select_background = Entity(
    parent=level_select_menu,
    model='quad',
    texture='assets/textures/MenuNiveles.jpg', # Fondo del menú de selección de nivel
    scale_x=camera.aspect_ratio,
    scale_y=1,
    z=0.1,
    color=color.white
)

level_title = Text(parent=level_select_menu, text="Seleccionar Nivel", scale=3, origin=(0,0), y=0.4)

# ======================================================================================
# Botones para escoger el nivle en el menu de seleccion de niveles
# ======================================================================================
level_buttons_container = Entity(parent=level_select_menu, y=-0.4) # Ajusta la 'y' para mover el grupo de botones hacia abajo
# Botones para seleccionar cada nivel, ahora dentro del contenedor y con posiciones X ajustadas
level_1_button = Button(parent=level_buttons_container, text="Nivel 1", scale=(0.25, 0.08), x=-0.35, y=0.1, on_click=lambda: start_level(1))
level_2_button = Button(parent=level_buttons_container, text="Nivel 2", scale=(0.25, 0.08), x=0, y=0.1, on_click=lambda: start_level(2))
level_3_button = Button(parent=level_buttons_container, text="Nivel 3", scale=(0.25, 0.08), x=0.35, y=0.1, on_click=lambda: start_level(3))
level_buttons = [level_1_button, level_2_button, level_3_button] # Lista de botones de nivel
back_to_main_menu_button = Button( parent=level_buttons_container,text="Regresar al Inicio",color=color.red,scale=(0.3, 0.08),y=-0.02,on_click=show_main_menu) # Llama a la función para mostrar el menú principal


# ======================================================================================
# --- Menú de cuando se le da al scape
# ======================================================================================
pause_menu = Entity(parent=camera.ui, enabled=False, model='quad', scale=(0.5, 0.5), color=color.black90) # Menú de pausa
Text(parent=pause_menu, text="Juego en Pausa", origin=(0,0), y=0.4, scale=2)

Button(parent=pause_menu, text="Reanudar Juego", color=color.azure, scale=(0.8, 0.2), y=0.15, on_click=resume_game)
Button(parent=pause_menu, text="Menú de Niveles", color=color.blue, scale=(0.8, 0.2), y=-0.1, on_click=Func(lambda: (application.resume(), pause_menu.disable(), show_level_select_menu())))
Button(parent=pause_menu, text="Salir al Menú Principal", color=color.red, scale=(0.8, 0.2), y=-0.35, on_click=Func(lambda: (application.resume(), pause_menu.disable(), show_main_menu())))

# ======================================================================================
# --- Lógica Principal del Juego ---
# ======================================================================================
def update():
    global current_bg_music
    # Si el juego no está pausado y está activo
    if not application.paused and game_active:
        update_hud() # Actualiza el HUD
        # Controla la rotación de la cámara con el ratón
        camera.rotation_y += mouse.velocity.x * 60
        camera.rotation_x -= mouse.velocity.y * 60
        # Limita la rotación de la cámara para que no gire completamente
        camera.rotation_x = clamp(camera.rotation_x, -50, 50)
        camera.rotation_y = clamp(camera.rotation_y, -80, 80)
    # Si el juego está pausado y hay música de fondo sonando, pausar la música
    elif application.paused and current_bg_music and current_bg_music.playing:
        current_bg_music.pause()

# ======================================================================================
# Función que maneja la entrada del usuario (teclado y ratón)
# ======================================================================================
def input(key):
    global shots_fired, last_shot_time, current_bg_music
    # Si se presiona 'escape' y el juego está activo, se alterna la pausa
    if key == 'escape' and game_active:
        application.paused = not application.paused # Alterna el estado de pausa de la aplicación
        pause_menu.enabled = application.paused      # Habilita/deshabilita el menú de pausa
        mouse.locked = not pause_menu.enabled        # Bloquea/desbloquea el ratón
        if application.paused:
            if current_bg_music:
                current_bg_music.pause() # Pausa la música de fondo
        else:
            if current_bg_music:
                current_bg_music.stop() # Detiene la música para reiniciarla
                current_bg_music.play() # Reanuda la música de fondo
    
    if application.paused: # Si el juego está pausado, no procesar más entradas de juego
        return

# ======================================================================================
    # desactiva el clic izquierdo para que no haga ni una funcion
# ======================================================================================
    if game_active and key == 'left mouse down':
        # Controla la cadencia de disparo (0.5 segundos entre disparos)
        if time.time() - last_shot_time < 0.5:
            return
        last_shot_time = time.time() # Actualiza el tiempo del último disparo
        shots_fired += 1 # Incrementa el contador de disparos
        ignore_list = [] # Lista de entidades a ignorar en el raycast

# ======================================================================================
    # Reproducir el sonido de disparo y animar el arma correcta según el nivel
# ======================================================================================
        if current_level == 1:
            gunshot_pistol_sound.play()
            pistol.rotation_x = -10
            pistol.animate_rotation_x(0, duration=0.1)
            ignore_list = [pistol]
        elif current_level == 2:
            gunshot_rifle_sound.play()
            rifle.rotation_x = -5
            rifle.animate_rotation_x(0, duration=0.1)
            ignore_list = [rifle]
        elif current_level == 3:
            gunshot_shotgun_sound.play()
            shotgun.rotation_x = -15
            shotgun.animate_rotation_x(0, duration=0.1)
            ignore_list = [shotgun]
        
        # Realiza un raycast desde la cámara para detectar si se golpeó un objetivo
        hit_info = raycast(camera.world_position, camera.forward, distance=200, ignore=ignore_list)
        if hit_info.hit and hasattr(hit_info.entity, 'hit'):
            hit_info.entity.hit() # Si se golpeó una entidad con el método 'hit', lo llama
# ======================================================================================
# --- Iniciar el Juego ---
# ======================================================================================
game_hud.disable()
pistol.disable()
rifle.disable()
shotgun.disable()
crosshair.disable()
mouse.locked = False # Asegura que el ratón no esté bloqueado al inicio
app.run()
