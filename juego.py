# Importamos las librerías necesarias de Ursina
from ursina import * # Importa todas las funcionalidades del motor de juego Ursina
import math  # Importa el módulo math para operaciones matemáticas (aunque no se usa directamente en el código proporcionado)

# --- Configuración de Niveles ---
# Diccionario que almacena la configuración para cada nivel del juego.
LEVEL_CONFIG = {
    1: {'targets': 10, 'speed': (10, 15), 'scale': 2.8, 'accuracy_goal': 50},  # Configuración para el Nivel 1
    2: {'targets': 10, 'speed': (15, 22), 'scale': 2.0, 'accuracy_goal': 60},  # Configuración para el Nivel 2
    3: {'targets': 10, 'speed': (20, 28), 'scale': 1.8, 'accuracy_goal': 75}   # Configuración para el Nivel 3
}

# --- Clase para los Objetivos Esféricos (¡Ahora Patos!) ---
# Define la clase TargetSphere, que hereda de Entity de Ursina, representando un objetivo en el juego.
class TargetSphere(Entity):
    # Constructor de la clase TargetSphere.
    def __init__(self, speed_range, scale):
        side = random.choice([-1, 1])  # Elige aleatoriamente si el pato aparecerá desde la izquierda (-1) o la derecha (1).
        # Posición Y ajustada para que salgan más bajas
        start_pos = Vec3(22 * side, random.uniform(-8, -2), random.uniform(15, 25))  # Define la posición inicial del pato.
        direction = Vec3(-side, random.uniform(-.2, .2), random.uniform(-.1, .1))  # Define la dirección de movimiento del pato.

        super().__init__(  # Llama al constructor de la clase padre (Entity).
            model='quad',  # ¡CAMBIADO A 'quad' para usar una imagen 2D! Define la forma del modelo como un cuadrilátero.
            texture='assets/textures/mario.png', # ¡AQUÍ ES DONDE PONES LA RUTA A TU IMAGEN DE PATO! Asigna la textura al cuadrilátero.
            color=color.white, # Usa color.white para que la textura no se tiña. Establece el color de la entidad.
            scale=scale,  # Establece la escala del pato.
            position=start_pos,  # Establece la posición inicial del pato.
            collider='box', # Cambiamos a 'box' o 'quad' porque ya no es una esfera. 'box' es una buena opción general. Define el tipo de colisionador.
            shadow=True,  # Habilita las sombras para la entidad.
            billboard=True # ¡IMPORTANTE! Esto hace que el pato siempre mire a la cámara, sin importar la rotación. Hace que la entidad siempre mire hacia la cámara.
        )
        self.direction = direction  # Almacena la dirección de movimiento.
        self.speed = random.uniform(speed_range[0], speed_range[1])  # Asigna una velocidad aleatoria dentro del rango especificado.

    # Método update se llama automáticamente cada fotograma del juego.
    def update(self):
        # Mueve el objetivo
        self.position += self.direction * self.speed * time.dt  # Actualiza la posición del pato en función de su dirección y velocidad.
        # Destruye el objetivo si sale de la pantalla y spawnea el siguiente
        if abs(self.x) > 24:  # Si el pato sale de los límites horizontales de la pantalla.
            destroy(self)  # Destruye la instancia actual del pato.
            invoke(spawn_next_target, delay=0.5)  # Llama a la función spawn_next_target después de 0.5 segundos para generar un nuevo objetivo.

    # Método hit se llama cuando el pato es impactado.
    def hit(self):
        global hits, points  # Declara que se usarán las variables globales hits y points.
        hit_sound.play()  # Reproduce el sonido de impacto.
        hits += 1  # Incrementa el contador de aciertos.
        points += 100  # Suma puntos al marcador.
        # Crea un efecto visual de impacto (puedes ajustar este modelo/color si quieres un efecto diferente para los patos)
        # ESCALA DEL EFECTO DE IMPACTO REDUCIDA AQUÍ
        # Crea una entidad para el efecto visual del impacto.
        effect = Entity(model='quad', texture='assets/textures/hit_effect.png', color=color.white, scale=self.scale * 0.8, position=self.world_position, shadow=False, billboard=True)
        effect.animate_scale(self.scale * 1.2, duration=0.2, curve=curve.out_quad)  # Anima la escala del efecto.
        effect.fade_out(duration=0.2)  # Hace que el efecto se desvanezca.
        destroy(effect, delay=0.2)  # Destruye el efecto después de 0.2 segundos.

        # Destruye el objetivo y spawnea el siguiente
        destroy(self)  # Destruye la instancia del pato impactado.
        invoke(spawn_next_target, delay=0.5)  # Llama a la función spawn_next_target después de 0.5 segundos para generar un nuevo objetivo.

# --- Variables Globales del Juego ---
hits, points, shots_fired = 0, 0, 0  # Inicializa contadores de aciertos, puntos y disparos.
targets_spawned = 0  # Contador de objetivos generados.
unlocked_level = 1  # Nivel máximo desbloqueado por el jugador.
current_level = 1  # Nivel actual en el que se encuentra el jugador.
game_active = False  # Bandera para indicar si el juego está activo o en un menú.
last_shot_time = 0  # Almacena el tiempo del último disparo para controlar la cadencia.
current_bg_music = None  # Global variable to hold the current background music. Variable global para la música de fondo actual.

# --- Funciones del Juego ---
# Función para ir al menú de selección de nivel.
def go_to_level_select():
    main_menu.disable()  # Deshabilita el menú principal.
    level_select_menu.enable()  # Habilita el menú de selección de nivel.
    update_level_buttons()  # Actualiza el estado de los botones de nivel.

# Función para iniciar un nivel específico.
def start_level(level):
    global hits, points, shots_fired, game_active, current_level, targets_spawned, last_shot_time, current_bg_music # Declara que se usarán variables globales.
    current_level = level  # Establece el nivel actual.
    hits, points, shots_fired, targets_spawned = 0, 0, 0, 0  # Reinicia los contadores del juego.
    game_active = True  # Establece el estado del juego a activo.

    # --- Lógica de la música modificada para reiniciar ---
    if current_bg_music:  # Si hay música de fondo reproduciéndose.
        current_bg_music.stop()  # Detiene la música actual.
        current_bg_music = None  # Reinicia la referencia para que se cargue de nuevo.

    # Asigna la música correcta al nivel
    if current_level == 1:  # Si es el nivel 1.
        current_bg_music = start_sound  # Asigna la música del nivel 1.
    elif current_level == 2:  # Si es el nivel 2.
        current_bg_music = level2_music  # Asigna la música del nivel 2.
    elif current_level == 3:  # Si es el nivel 3.
        current_bg_music = level3_music  # Asigna la música del nivel 3.

    if current_bg_music:  # Si hay una música de fondo asignada.
        current_bg_music.play()  # Reproduce la música desde el principio.

    level_select_menu.disable()  # Deshabilita el menú de selección de nivel.
    game_hud.enable()  # Habilita el HUD del juego.
    crosshair.enable()  # Habilita la mira.
    mouse.locked = True  # Bloquea el cursor del ratón.

    last_shot_time = time.time()  # Reinicia el tiempo del último disparo.

    pistol.disable()  # Deshabilita la pistola.
    rifle.disable()  # Deshabilita el rifle.
    shotgun.disable()  # Deshabilita la escopeta.

    if current_level == 1:  # Si es el nivel 1.
        pistol.enable()  # Habilita la pistola.
    elif current_level == 2:  # Si es el nivel 2.
        rifle.enable()  # Habilita el rifle.
    elif current_level == 3:  # Si es el nivel 3.
        shotgun.enable()  # Habilita la escopeta.

    for t in scene.entities:  # Itera sobre todas las entidades en la escena.
        if isinstance(t, TargetSphere):  # Si la entidad es una instancia de TargetSphere.
            destroy(t)  # Destruye el objetivo.

    spawn_next_target()  # Genera el primer objetivo.

# Función para generar el siguiente objetivo.
def spawn_next_target():
    global targets_spawned  # Declara que se usará la variable global targets_spawned.
    if not game_active: return  # Si el juego no está activo, no hace nada.

    # Si aún no se han generado todos los objetivos para el nivel actual.
    if targets_spawned < LEVEL_CONFIG.get(current_level, {}).get('targets', 0):
        config = LEVEL_CONFIG.get(current_level, {})  # Obtiene la configuración del nivel actual.
        TargetSphere(config.get('speed', (10, 15)), config.get('scale', 1))  # Crea una nueva instancia de TargetSphere.
        targets_spawned += 1  # Incrementa el contador de objetivos generados.
        update_hud()  # Actualiza la información en el HUD.
    else:
        invoke(end_level, delay=1)  # Si todos los objetivos han sido generados, llama a end_level después de 1 segundo.

# Función para finalizar el nivel.
def end_level():
    global game_active, unlocked_level, current_bg_music  # Declara que se usarán variables globales.
    game_active = False  # Establece el estado del juego a inactivo.

    # Stop background music when level ends
    if current_bg_music:  # Si hay música de fondo reproduciéndose.
        current_bg_music.stop()  # Detiene la música actual.

    game_hud.disable()  # Deshabilita el HUD del juego.
    crosshair.disable()  # Deshabilita la mira.
    pistol.disable()  # Deshabilita la pistola.
    rifle.disable()  # Deshabilita el rifle.
    shotgun.disable()  # Deshabilita la escopeta.
    mouse.locked = False  # Desbloquea el cursor del ratón.

    accuracy = (hits / shots_fired) * 100 if shots_fired > 0 else 0  # Calcula la precisión.
    goal = LEVEL_CONFIG.get(current_level, {}).get('accuracy_goal', 0)  # Obtiene el objetivo de precisión para el nivel.

    # Crea un panel para mostrar los resultados del nivel.
    end_panel = Entity(parent=camera.ui, model='quad', scale=(.8, .5), color=color.dark_gray.tint(.2), z=1)
    # Muestra la precisión y el objetivo de precisión.
    Text(parent=end_panel, text=f"Precisión: {accuracy:.1f}% (Objetivo: {goal}%)", origin=(0,0), y=0, scale=1.5)
    # Muestra los aciertos y disparos realizados.
    Text(parent=end_panel, text=f"Aciertos: {hits} / {shots_fired}", origin=(0,0), y=-.1, scale=1.5)

    if accuracy >= goal:  # Si la precisión es mayor o igual al objetivo.
        message = f"¡NIVEL {current_level} COMPLETADO!"  # Mensaje de nivel completado.
        if current_level < 3:  # Si no es el último nivel.
            unlocked_level = max(unlocked_level, current_level + 1)  # Desbloquea el siguiente nivel.

        Text(parent=end_panel, text=message, origin=(0,0), y=.2, scale=2)  # Muestra el mensaje de nivel completado.
        # Botón para volver al menú de niveles.
        Button(parent=end_panel, text="Menú de Niveles", color=color.azure, scale=(0.25, 0.08), y=-.3, on_click=Func(lambda: (destroy(end_panel), show_level_select_menu())))
    else:
        message = "INTÉNTALO DE NUEVO"  # Mensaje para intentar de nuevo.

        Text(parent=end_panel, text=message, origin=(0,0), y=.2, scale=2)  # Muestra el mensaje de intentar de nuevo.
        # Simplificamos la llamada aquí para que start_level se encargue de la música
        # Botón para reintentar el nivel.
        Button(parent=end_panel, text="Reintentar", color=color.azure, scale=(0.25, 0.08), y=-.25, on_click=Func(lambda: (destroy(end_panel), start_level(current_level))))
        # Botón para volver al menú de niveles.
        Button(parent=end_panel, text="Menú de Niveles", color=color.red, scale=(0.25, 0.08), y=-.4, on_click=Func(lambda: (destroy(end_panel), show_level_select_menu())))

# Función para mostrar el menú de selección de nivel.
def show_level_select_menu():
    global current_bg_music  # Declara que se usará la variable global current_bg_music.
    game_hud.disable()  # Deshabilita el HUD del juego.
    pistol.disable()  # Deshabilita la pistola.
    rifle.disable()  # Deshabilita el rifle.
    shotgun.disable()  # Deshabilita la escopeta.
    crosshair.disable()  # Deshabilita la mira.
    for t in scene.entities:  # Itera sobre todas las entidades en la escena.
        if isinstance(t, TargetSphere):  # Si la entidad es una instancia de TargetSphere.
            destroy(t)  # Destruye el objetivo.
    level_select_menu.enable()  # Habilita el menú de selección de nivel.
    update_level_buttons()  # Actualiza el estado de los botones de nivel.
    mouse.locked = False  # Desbloquea el cursor del ratón.
    # Stop background music when going to level select
    if current_bg_music:  # Si hay música de fondo reproduciéndose.
        current_bg_music.stop()  # Detiene la música actual.

# Función para mostrar el menú principal.
def show_main_menu():
    global current_bg_music  # Declara que se usará la variable global current_bg_music.
    level_select_menu.disable()  # Deshabilita el menú de selección de nivel.
    game_hud.disable()  # Deshabilita el HUD del juego.
    pistol.disable()  # Deshabilita la pistola.
    rifle.disable()  # Deshabilita el rifle.
    shotgun.disable()  # Deshabilita la escopeta.
    crosshair.disable()  # Deshabilita la mira.
    for t in scene.entities:  # Itera sobre todas las entidades en la escena.
        if isinstance(t, TargetSphere):  # Si la entidad es una instancia de TargetSphere.
            destroy(t)  # Destruye el objetivo.
    main_menu.enable()  # Habilita el menú principal.
    mouse.locked = False  # Desbloquea el cursor del ratón.
    # Stop background music when going to main menu
    if current_bg_music:  # Si hay música de fondo reproduciéndose.
        current_bg_music.stop()  # Detiene la música actual.

# Función para actualizar el HUD del juego.
def update_hud():
    accuracy = (hits / shots_fired) * 100 if shots_fired > 0 else 0  # Calcula la precisión.
    # Actualiza el texto del HUD con la información del nivel, objetivos, aciertos y precisión.
    hud_text.text = (
        f"NIVEL {current_level}\n"
        f"Objetivo: {targets_spawned}/{LEVEL_CONFIG.get(current_level, {}).get('targets', 0)}\n"
        f"Aciertos: {hits}\n"
        f"Precisión: {accuracy:.1f}%"
    )

# Función para actualizar el estado de los botones de selección de nivel.
def update_level_buttons():
    for i, button in enumerate(level_buttons):  # Itera sobre los botones de nivel.
        button.disabled = (i + 1 > unlocked_level)  # Deshabilita el botón si el nivel no está desbloqueado.
        # Cambia el color del texto del botón según si está habilitado o deshabilitado.
        button.text_entity.color = color.white if not button.disabled else color.gray

# Función para reanudar el juego desde el menú de pausa.
def resume_game():
    global current_bg_music  # Declara que se usará la variable global current_bg_music.
    pause_menu.disable()  # Deshabilita el menú de pausa.
    mouse.locked = True  # Bloquea el cursor del ratón.
    application.resume()  # Reanuda la aplicación Ursina.
    # Resume background music if it was playing
    if current_bg_music:  # Si hay música de fondo.
        current_bg_music.play()  # Usa play() para reanudar desde donde se detuvo.

# --- Inicialización de la Aplicación Ursina ---
# Set fullscreen=True to make the window maximize to the full screen
app = Ursina(title='AIM PRESICION DDC', borderless=False, fullscreen=True)  # Inicializa la aplicación Ursina.

# --- Sonidos ---
gunshot_sound = Audio('assets/sounds/hit.mp3', loop=False, autoplay=False, volume=0.3)  # Carga el sonido de disparo.
hit_sound = Audio('assets/sounds/hit.mp3', loop=False, autoplay=False, volume=0.5)  # Carga el sonido de impacto.
# Main background music (for level 1)
start_sound = Audio('assets/sounds/fondo.mp3', loop=True, autoplay=False, volume=0.8) # Increased volume. Carga la música de fondo para el nivel 1.
# New background music for Level 2
level2_music = Audio('assets/sounds/fondoNivel2.mp3', loop=True, autoplay=False, volume=0.8) # Increased volume. Carga la música de fondo para el nivel 2.
# New background music for Level 3
level3_music = Audio('assets/sounds/fondoNivel3.mp3', loop=True, autoplay=False, volume=0.8) # Increased volume. Carga la música de fondo para el nivel 3.

# --- Creación del Entorno (Cabina de Disparo con estilo oscuro) ---
# Entidad para el fondo del campo de tiro (deshabilitado inicialmente).
shooting_range_background = Entity(
    model='quad',
    texture='assets/textures/mapa.png',
    scale=(100, 50),
    position=(0, 0, 50),
    rotation_y=180,
    double_sided=True
).disable()

# **CABINA DE DISPARO - ESTILO OSCURO**
back_wall = Entity(    # Crea una nueva entidad (un objeto en la escena) y la asigna a la variable 'back_wall'.
    model='cube',      # Define la forma de la entidad. En este caso, es un cubo.
    scale=(40, 30, 1), # Ancho: 10 unidades (de X=-5 a X=5), Alto: 30, Profundidad: 1. (Esta es la nueva anchura de referencia). Establece la escala de la pared trasera.
    position=(0, 5, 30), # Ubicación central: X=0, Y=5, Z=30 (esta es la pared trasera). Establece la posición de la pared trasera.
    texture='assets/textures/mapa.png', # Cambiado a madera.png. Asigna la textura a la pared trasera.
    color=color.white, # Cambiado a blanco para que la textura se vea. Establece el color de la pared trasera.
    collider='box'     # Asigna un colisionador de tipo caja.
)

left_wall = Entity(
    model='cube',
    scale=(1, 30, 60), # Ancho: 1, Alto: 30, Profundidad: 45. (Cubre desde Z=-15 hasta Z=30). Establece la escala de la pared izquierda.
    position=(-20, 5, 7.5), # Posición X ajustada a -20. Establece la posición de la pared izquierda.
    texture='assets/textures/mapa.png', # Cambiado a madera.png. Asigna la textura a la pared izquierda.
    color=color.white, # Cambiado a blanco para que la textura se vea. Establece el color de la pared izquierda.
    collider='box' # Asigna un colisionador de tipo caja.
)

right_wall = Entity(
    model='cube',
    scale=(1, 30, 60), # Ancho: 1, Alto: 30, Profundidad: 45. Establece la escala de la pared derecha.
    position=(20, 5, 7.5), # Posición X ajustada a 20. Establece la posición de la pared derecha.
    texture='assets/textures/mapa.png', # Textura de la pared. Asigna la textura a la pared derecha.
    color=color.white, # ¡CAMBIADO A BLANCO! Establece el color de la pared derecha.
    collider='box' # Asigna un colisionador de tipo caja.
)

ceiling = Entity(
    model='cube',
    scale=(42, 1, 45), # ANCHO AJUSTADO: Ahora es 42 para cubrir el espacio de 40 de la pared trasera y un poco más. Establece la escala del techo.
    position=(0, 20, 7.5), # Posición X=0 (centrado), Y=20 (altura del techo), Z=7.5 (posición Z central, igual que paredes laterales). Establece la posición del techo.
    texture='assets/textures/cieloo.png', # Textura del cielo (asumiendo que 'cieloo.png' es la versión oscura). Asigna la textura al techo.
    color=color.white, # Asegurarse de que el color sea blanco si hay textura. Establece el color del techo.
    collider='box' # Asigna un colisionador de tipo caja.
)

# Suelo (con textura de cesped oscuro)
ground_plane = Entity(
    model='plane', # Define la forma del modelo como un plano.
    scale=(150, 1, 150), # Un tamaño muy grande para asegurar que siempre haya suelo visible. Establece la escala del suelo.
    position=(0, -10, 5), # Posición Y ajustada para estar más cerca. Establece la posición del suelo.
    texture='assets/textures/piso.jpg', # Cambiado a una textura de cesped oscuro. Asigna la textura al suelo.
    texture_scale=(2, 2), # Escala de la textura para que se vea más grande y cercano. Establece la escala de la textura del suelo.
    collider='box' # Asigna un colisionador de tipo caja.
)

# Cielo (completamente negro, sin textura si cieloo.png es el fondo oscuro)
sky_color = Sky(color=color.black) # Establece el color del cielo a negro.

# Luz direccional - ¡AUMENTAMOS SU INTENSIDAD!
sun = DirectionalLight(y=10, x=20, shadows=True, color=color.white) # Cambiado de color.white33 a color.white. Crea una luz direccional.

# ¡AÑADIMOS LUZ AMBIENTAL para iluminar las áreas en sombra!
ambient_light = AmbientLight(color=color.rgba(100, 100, 100, 255)) # Una luz ambiental gris suave. Crea una luz ambiental.

# --- Configuración del Jugador (Cámara estática) ---
camera.position = (0, 0, -15) # Establece la posición de la cámara.
camera.fov = 80 # Establece el campo de visión de la cámara.

# --- Arma y Mira (DISEÑOS MEJORADOS) ---

# Pistola mejorada
# La entidad 'pistol' ahora solo actúa como un contenedor para sus partes.
pistol = Entity(parent=camera, position=(0.4, -0.45, 1.2), rotation=(0, 0, 0)) # Crea una entidad vacía para agrupar las partes de la pistola.
# Cuerpo principal
Entity(parent=pistol, model='cube', scale=(0.12, 0.2, 0.6), color=color.dark_gray.tint(-0.1)) # Parte del cuerpo de la pistola.
# Empuñadura
Entity(parent=pistol, model='cube', scale=(0.12, 0.3, 0.2), position=(0, -0.2, -0.2), color=color.black, texture='brick') # Parte de la empuñadura.
# Corredera
Entity(parent=pistol, model='cube', scale=(0.1, 0.15, 0.55), position=(0, 0.07, 0), color=color.gray) # Parte de la corredera.
# Cañón asomando
Entity(parent=pistol, model='cube', scale=(0.05, 0.05, 0.1), position=(0, 0.07, 0.3), color=color.black) # Parte del cañón.
# Gatillo
Entity(parent=pistol, model='cube', scale=(0.04, 0.08, 0.05), position=(0, -0.07, -0.1), color=color.gray) # Parte del gatillo.
# Miras
Entity(parent=pistol, model='cube', scale=(0.02, 0.02, 0.05), position=(0, 0.15, 0.25), color=color.black) # Mira delantera.
Entity(parent=pistol, model='cube', scale=(0.05, 0.02, 0.05), position=(0, 0.15, -0.25), color=color.black) # Mira trasera.
pistol.disable() # Deshabilita la pistola inicialmente.

# Rifle mejorado
# La entidad 'rifle' ahora solo actúa como un contenedor.
rifle = Entity(parent=camera, position=(0.6, -0.55, 1.8), rotation=(0,0,0)) # Crea una entidad vacía para agrupar las partes del rifle.
# Cuerpo principal / Receptor
Entity(parent=rifle, model='cube', scale=(0.1, 0.1, 1.2), color=color.dark_gray.tint(-0.1)) # Parte del cuerpo del rifle.
# Cañón
Entity(parent=rifle, model='cylinder', scale=(0.05, 0.05, 0.8), position=(0, 0, 0.6), rotation_x=90, color=color.gray) # Parte del cañón.
# Culata
Entity(parent=rifle, model='cube', scale=(0.1, 0.25, 0.3), position=(0, -0.1, -0.6), color=color.black) # Parte de la culata.
# Empuñadura de pistola
Entity(parent=rifle, model='cube', scale=(0.08, 0.2, 0.1), position=(0, -0.15, -0.3), color=color.black) # Parte de la empuñadura.
# Mira telescópica
Entity(parent=rifle, model='cylinder', scale=(0.05, 0.05, 0.3), position=(0, 0.08, 0.2), rotation_x=90, color=color.black) # Parte de la mira telescópica.
# Lente de mira
Entity(parent=rifle, model='circle', scale=0.04, position=(0, 0.08, 0.35), rotation_x=90, color=color.light_gray) # Parte de la lente de la mira.
# Bípode
Entity(parent=rifle, model='cube', scale=(0.02, 0.1, 0.02), position=(-0.05, -0.08, 0.3), color=color.gray) # Parte del bípode.
Entity(parent=rifle, model='cube', scale=(0.02, 0.1, 0.02), position=(0.05, -0.08, 0.3), color=color.gray) # Otra parte del bípode.
# Cargador
Entity(parent=rifle, model='cube', scale=(0.06, 0.2, 0.1), position=(0, -0.1, -0.1), color=color.dark_gray) # Parte del cargador.
# Riel Picatinny en la parte superior
Entity(parent=rifle, model='cube', scale=(0.08, 0.01, 0.8), position=(0, 0.06, 0), color=color.dark_gray) # Parte del riel.
rifle.disable() # Deshabilita el rifle inicialmente.

# Escopeta mejorada
# La entidad 'shotgun' ahora solo actúa como un contenedor.
shotgun = Entity(parent=camera, position=(0.5, -0.65, 1.5), rotation=(0,0,0)) # Crea una entidad vacía para agrupar las partes de la escopeta.
# Cuerpo principal
Entity(parent=shotgun, model='cube', scale=(0.18, 0.15, 1.0), color=color.dark_gray.tint(-0.1)) # Parte del cuerpo de la escopeta.
# Cañón
Entity(parent=shotgun, model='cylinder', scale=(0.08, 0.08, 0.8), position=(0, 0, 0.5), rotation_x=90, color=color.gray) # Parte del cañón.
# Guardamanos/Bomba
Entity(parent=shotgun, model='cube', scale=(0.12, 0.1, 0.25), position=(0, -0.05, 0.2), color=color.black) # Parte del guardamanos.
# Empuñadura de pistola (o parte de la culata)
Entity(parent=shotgun, model='cube', scale=(0.18, 0.3, 0.15), position=(0, -0.2, -0.4), color=color.black, texture='wood') # Parte de la empuñadura/culata.
# Recámara o parte superior del cuerpo
Entity(parent=shotgun, model='cube', scale=(0.18, 0.05, 0.3), position=(0, 0.1, -0.1), color=color.dark_gray) # Parte de la recámara.
# Cargador tubular bajo el cañón
Entity(parent=shotgun, model='cylinder', scale=(0.05, 0.05, 0.7), position=(0, -0.08, 0.3), rotation_x=90, color=color.dark_gray) # Parte del cargador tubular.
# Alza y mira delantera
Entity(parent=shotgun, model='cube', scale=(0.02, 0.03, 0.05), position=(0, 0.08, 0.45), color=color.black) # Mira delantera.
Entity(parent=shotgun, model='cube', scale=(0.05, 0.02, 0.05), position=(0, 0.08, -0.2), color=color.black) # Alza trasera.
shotgun.disable() # Deshabilita la escopeta inicialmente.

crosshair = Entity(parent=camera.ui, model='circle', scale=0.008, color=color.red) # Crea una mira en la interfaz de usuario.

# --- Interfaz de Usuario (UI) Mejorada ---
game_hud = Entity(parent=camera.ui, enabled=False) # Entidad para el HUD del juego (deshabilitado inicialmente).
hud_background = Entity(
    parent=game_hud,
    model='quad',
    scale=(0.25, 0.15),
    position=window.bottom_left + Vec2(0.15, 0.1),
    color=color.black66,
    origin=(-0.5, -0.5)
) # Fondo para el HUD.
hud_text = Text(
    parent=hud_background,
    text="",
    origin=(-0.5, -0.5),
    position=(0.05, 0.05),
    scale=1.0,
    color=color.white
) # Texto dentro del HUD.

# --- Menú Principal ---
main_menu = Entity(
    parent=camera.ui,
    model='quad',
    texture='assets/textures/logo.png',
    scale_x=camera.aspect_ratio,
    scale_y=1,
    enabled=True,
    z=0.1,
    color=color.white
) # Entidad para el menú principal.

start_button = Button(parent=main_menu, text="INICIAR", color=color.azure, scale=(0.4, 0.1), y=-0.1, on_click=go_to_level_select) # Botón de iniciar juego.
quit_button = Button(parent=main_menu, text="SALIR", color=color.azure, scale=(0.4, 0.1), y=-0.25, on_click=application.quit) # Botón de salir del juego.

# --- Menú de Selección de Nivel ---
level_select_menu = Entity(parent=camera.ui, enabled=False) # Entidad para el menú de selección de nivel (deshabilitado inicialmente).
level_title = Text(parent=level_select_menu, text="Seleccionar Nivel", scale=3, origin=(0,0), y=0.4) # Título del menú de selección de nivel.
level_1_button = Button(parent=level_select_menu, text="Nivel 1", scale=(0.3, 0.1), y=0.1, on_click=lambda: start_level(1)) # Botón para el Nivel 1.
level_2_button = Button(parent=level_select_menu, text="Nivel 2", scale=(0.3, 0.1), y=0, on_click=lambda: start_level(2)) # Botón para el Nivel 2.
level_3_button = Button(parent=level_select_menu, text="Nivel 3", scale=(0.3, 0.1), y=-0.1, on_click=lambda: start_level(3)) # Botón para el Nivel 3.
level_buttons = [level_1_button, level_2_button, level_3_button] # Lista de botones de nivel.

# --- Menú de Pausa ---
pause_menu = Entity(parent=camera.ui, enabled=False, model='quad', scale=(0.5, 0.5), color=color.black90) # Entidad para el menú de pausa (deshabilitado inicialmente).
Text(parent=pause_menu, text="Juego en Pausa", origin=(0,0), y=0.4, scale=2) # Texto de "Juego en Pausa".

Button(parent=pause_menu, text="Reanudar Juego", color=color.azure, scale=(0.8, 0.2), y=0.15, on_click=resume_game) # Botón para reanudar el juego.
Button(parent=pause_menu, text="Menú de Niveles", color=color.blue, scale=(0.8, 0.2), y=-0.1, on_click=Func(lambda: (application.resume(), pause_menu.disable(), show_level_select_menu()))) # Botón para ir al menú de niveles.
Button(parent=pause_menu, text="Salir al Menú Principal", color=color.red, scale=(0.8, 0.2), y=-0.35, on_click=Func(lambda: (application.resume(), pause_menu.disable(), show_main_menu()))) # Botón para salir al menú principal.

# --- Lógica Principal ---
# Función update se llama automáticamente cada fotograma.
def update():
    global current_bg_music # Declara que se usará la variable global current_bg_music.
    if not application.paused and game_active: # Si la aplicación no está pausada y el juego está activo.
        update_hud() # Actualiza el HUD.
        camera.rotation_y += mouse.velocity.x * 60 # Controla la rotación horizontal de la cámara con el movimiento del ratón.
        camera.rotation_x -= mouse.velocity.y * 60 # Controla la rotación vertical de la cámara con el movimiento del ratón.
        camera.rotation_x = clamp(camera.rotation_x, -50, 50) # Limita la rotación vertical de la cámara.
        camera.rotation_y = clamp(camera.rotation_y, -80, 80) # Limita la rotación horizontal de la cámara.
    elif application.paused and current_bg_music and current_bg_music.playing: # Si la aplicación está pausada y la música de fondo está reproduciéndose.
        current_bg_music.pause() # Pause music when game is paused. Pausa la música.

# Función input se llama cuando se presiona una tecla o botón del ratón.
def input(key):
    global shots_fired, last_shot_time, current_bg_music # Declara que se usarán variables globales.
    if key == 'escape' and game_active: # Si se presiona la tecla 'escape' y el juego está activo.
        application.paused = not application.paused # Alterna el estado de pausa de la aplicación.
        pause_menu.enabled = application.paused # Habilita o deshabilita el menú de pausa.
        mouse.locked = not pause_menu.enabled # Bloquea o desbloquea el cursor del ratón.
        # Pause or resume music based on game pause state
        if application.paused: # Si el juego está pausado.
            if current_bg_music: # Si hay música de fondo.
                current_bg_music.pause() # Pausa la música.
        else: # Si el juego se reanuda.
            if current_bg_music: # Si hay música de fondo.
                current_bg_music.play() # Reproduce la música.

    if application.paused: # Si la aplicación está pausada.
        return # Sale de la función para no procesar otros inputs.

    if game_active and key == 'left mouse down': # Si el juego está activo y se presiona el botón izquierdo del ratón.
        # Control de cadencia de fuego para todas las armas
        if time.time() - last_shot_time < 0.5: # Disparo cada 0.5 segundos. Si ha pasado menos de 0.5 segundos desde el último disparo.
            return # No permite disparar.
        last_shot_time = time.time() # Actualiza el tiempo del último disparo.

        shots_fired += 1 # Incrementa el contador de disparos.
        gunshot_sound.play() # Reproduce el sonido de disparo.

        if current_level == 1: # Si es el nivel 1.
            pistol.rotation_x = -10 # Anima la rotación de la pistola para simular el retroceso.
            pistol.animate_rotation_x(0, duration=0.1) # Anima el regreso de la pistola a su posición original.
            ignore_list = [pistol] # Ignora la pistola en el raycast.
        elif current_level == 2: # Si es el nivel 2.
            rifle.rotation_x = -5 # Anima la rotación del rifle.
            rifle.animate_rotation_x(0, duration=0.1) # Anima el regreso del rifle.
            ignore_list = [rifle] # Ignora el rifle en el raycast.
        elif current_level == 3: # Si es el nivel 3.
            shotgun.rotation_x = -15 # Anima la rotación de la escopeta.
            shotgun.animate_rotation_x(0, duration=0.1) # Anima el regreso de la escopeta.
            ignore_list = [shotgun] # Ignora la escopeta en el raycast.
        else:
            ignore_list = [] # Lista vacía si no hay arma activa.

        # Realiza un raycast desde la posición de la cámara hacia adelante para detectar impactos.
        hit_info = raycast(camera.world_position, camera.forward, distance=200, ignore=ignore_list)
        if hit_info.hit and hasattr(hit_info.entity, 'hit'): # Si el raycast impacta en algo y esa entidad tiene un método 'hit'.
            hit_info.entity.hit() # Llama al método 'hit' de la entidad impactada.

# --- Iniciar el Juego ---
game_hud.disable() # Deshabilita el HUD al inicio.
pistol.disable() # Deshabilita la pistola al inicio.
rifle.disable() # Deshabilita el rifle al inicio.
shotgun.disable() # Deshabilita la escopeta al inicio.
crosshair.disable() # Deshabilita la mira al inicio.
mouse.locked = False # Desbloquea el cursor del ratón al inicio (para interactuar con los menús).
app.run() # Inicia la aplicación Ursina.