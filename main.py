import pygame, math, sys, time, random

pygame.init()

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)  # Teljes képernyős mód
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
GREEN = (0, 255, 0)
#FOV = math.radians(60)  # Látómező sugara radiánban, végül nem használtuk

# Térkép
world_map = [
    "#########################################",
    "#     #     #    #  #  #    #     #     #",
    "#   # ##  # # #          ## ## #### #   #",
    "#   #         #     #    #     #    #   #",
    "#   #   ####  ####  # ##  ####   #  #   #",
    "#   #   #         #         #   #   #   #",
    "#   ### ### ###       ###  ### ##   ### #",
    "#                 #                 #   #",
    "#   ## ##  ####  #  ### ## #  # ##  #   #",
    "#   #       #  #         #          #   #",
    "#   #           #       #           #   #",
    "#   ####   ## ## ## ##   #### ### ##    #",
    "#        #                         #    #",
    "### ###  #   #####  ####   ###  ######  #",
    "#   #    #   #         #   #         #  #",
    "#   ### ###  #   ####  #   #  ####   #  #",
    "#           ##         #            #   #",
    "# #####  ######   ####   ##  ####   #   #",
    "#   #                                #  #",
    "#     ##  ###  ######  ## ###  ###      #",
    "#      #          #       #     #       #",
    "#   #    #   #         #   #      #  #  #",
    "#   ### ###  #   ## #  #   #  # ##      #",
    "#                      #             #  #",
    "########################################"
]

# Csempék beállítása a world_maphoz arányosítva
TILE_SIZE = min(HEIGHT // len(world_map), WIDTH // len(world_map[0]))

player_x, player_y = TILE_SIZE * 1.5, TILE_SIZE * 2.5
score = 0 
#player_angle = math.pi / 4  # Kezdeti nézőszög, végül nem használtuk

# O betű pozíció
o_positions = []
last_remove_time = time.time() # Utolsó eltávolítás idő

# Változók a radar megjelenítéséhez
radar_type = None
radar_timer = time.time()
radar_display_time = 1  
radar_position = None

# Változók a riasztási esemény kezeléséhez
alert_triggered = False
alert_square_timer = None
alert_screen_timer = None

# Raycasting függvény
def cast_ray(x, y, angle):
    sin_a = math.sin(angle)
    cos_a = math.cos(angle)

    for depth in range(0, 1000, 5):
        target_x = x + depth * cos_a
        target_y = y + depth * sin_a
        tile_x, tile_y = int(target_x / TILE_SIZE), int(target_y / TILE_SIZE)

        # Ha a sugár falat talál, visszatérünk a távolsággal
        if world_map[tile_y][tile_x] == '#':
            return depth
    return 1000  # Maximális távolság, ha nem talál falat

# 2D nézet kirajzolása homályos fényhatással
def draw_2d_with_fade_effect():
    # Térkép kirajzolása
    for y, row in enumerate(world_map):
        for x, cell in enumerate(row):
            if cell == '#':
                pygame.draw.rect(screen, (200, 200, 200), (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
    
    # Játékos pozíciójának kirajzolása
    pygame.draw.circle(screen, BLUE, (int(player_x), int(player_y)), 10)

    # Teljesen fekete sötét réteg létrehozása
    darkness_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    darkness_surface.fill((0, 0, 0))  # Teljesen fekete kitöltés

    # Fényhatás maszk létrehozása
    light_radius = 100  # A fénykör sugara
    light_surface = pygame.Surface((light_radius * 2, light_radius * 2), pygame.SRCALPHA)
    
    for i in range(light_radius, 0, -1):
        # Az áttetszőség változtatása a sugár alapján
        alpha = int(255 * (1 - i / light_radius))
        pygame.draw.circle(light_surface, (0, 0, 0, alpha), (light_radius, light_radius), i)

    # A fényhatás középpontjának kiszámítása a játékos pozíciójában
    light_pos = (int(player_x - light_radius), int(player_y - light_radius))
    
    # Maszk alkalmazása a sötét rétegre (kivonó keverési mód nélkül, így ahol a lámpa világít, ott lesz áttetsző)
    darkness_surface.blit(light_surface, light_pos, special_flags=pygame.BLEND_RGBA_SUB)

    # Sötét réteg alkalmazása a képernyőre
    screen.blit(darkness_surface, (0, 0))

# Függvény az O betű elhelyezésére
def place_o():
    global o_positions
    width = len(world_map[0])
    height = len(world_map)

    # Véletlenszerű koordináták generálása
    while True:
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)

        # Ellenőrizzük, hogy az adott hely üres-e
        if world_map[y][x] == ' ' and (x, y) not in o_positions:
            o_positions.append((x, y))  # Hozzáadjuk az O pozíciót
            return  # Csak egy O betűt helyezünk el

# O betűk kirajzolása
def draw_o():
    for (x, y) in o_positions:
        pygame.draw.rect(screen, GREEN, (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

#Ütközés a zöld pontokkal
def check_collision():
    global score
    player_tile_x = player_x // TILE_SIZE
    player_tile_y = player_y // TILE_SIZE

    for o in o_positions:
        if o == (player_tile_x, player_tile_y):
            o_positions.remove(o) 
            score += 1  

# Függvény a régi O betűk eltávolítására
def remove_old_o():
    global last_remove_time
    current_time = time.time()

    # Ha eltelt 5 másodperc és van legalább 2 o betű
    if current_time - last_remove_time >= 5 and len(o_positions) >= 2:
        random_index = random.randint(0, len(o_positions) - 1)
        o_positions.pop(random_index)  
        last_remove_time = current_time  

# Függvény a pontszám kirajzolására
def draw_score(score):
    score_text = font.render(f'Score: {score}', True, (255, 255, 255))  # Fehér színű szöveg
    screen.blit(score_text, (WIDTH - score_text.get_width() - 10, HEIGHT - score_text.get_height() - 10))  # Kirajzolás a jobb alsó sarokba

# Függvény a véletlen radar megjelenítésére
def show_radar():
    global radar_type, radar_position, radar_timer
    options = ['A', 'B', 'C', 'D']
    if player_x < WIDTH / 4:
        options.remove('D')
    if player_x > WIDTH / 4 * 3:
        options.remove('C')
    if player_y < HEIGHT / 4:
        options.remove('A')
    if player_y > HEIGHT / 4 * 3:
        options.remove('B')
    radar_type = random.choice(options)  
    radar_timer = time.time() 

    # Pozíció beállítása az A, B, C, D szerint
    if radar_type == 'A':
        radar_position = (0, 0)  # Képernyő tetején
    elif radar_type == 'B':
        radar_position = (0, HEIGHT - 30)  # Képernyő alján
    elif radar_type == 'C':
        radar_position = (WIDTH - 30, 0)  # Képernyő jobb szélén
    elif radar_type == 'D':
        radar_position = (0, 0)  # Képernyő bal szélén

# Függvény a radar kirajzolására
def draw_radar():
    if radar_type is not None and radar_position is not None:
        if radar_type in ['A', 'B']:
            # Vízszintes csík (A: fent, B: lent)
            pygame.draw.rect(screen, (255, 0, 0), (radar_position[0], radar_position[1], WIDTH, 30))
        elif radar_type in ['C', 'D']:
            # Függőleges csík (C: jobbra, D: balra)
            pygame.draw.rect(screen, (255, 0, 0), (radar_position[0], radar_position[1], 30, HEIGHT))

#Radar iránytű
def draw_compass():
    bottom_left_x, bottom_left_y = 80, HEIGHT - 80  # A bal alsó sarokban
    size = 50  # A háromszögek mérete

    # Szín beállítása a radar típusának megfelelően
    color = WHITE  # Alapértelmezett szín
    if radar_type == 'A':
        color = (255, 0, 0)  # Piros Észak
    elif radar_type == 'B':
        color = (255, 0, 0)  # Piros Dél
    elif radar_type == 'C':
        color = (255, 0, 0)  # Piros Kelet
    elif radar_type == 'D':
        color = (255, 0, 0)  # Piros Nyugat

    # Észak
    north_points = [(bottom_left_x, bottom_left_y - size), 
                    (bottom_left_x - size // 2, bottom_left_y), 
                    (bottom_left_x + size // 2, bottom_left_y)]
    pygame.draw.polygon(screen, color if radar_type == 'A' else WHITE, north_points)

    # Dél
    south_points = [(bottom_left_x, bottom_left_y + size), 
                    (bottom_left_x - size // 2, bottom_left_y), 
                    (bottom_left_x + size // 2, bottom_left_y)]
    pygame.draw.polygon(screen, color if radar_type == 'B' else WHITE, south_points)

    # Nyugat
    west_points = [(bottom_left_x - size, bottom_left_y), 
                   (bottom_left_x, bottom_left_y - size // 2), 
                   (bottom_left_x, bottom_left_y + size // 2)]
    pygame.draw.polygon(screen, color if radar_type == 'D' else WHITE, west_points)

    # Kelet
    east_points = [(bottom_left_x + size, bottom_left_y), 
                   (bottom_left_x, bottom_left_y - size // 2), 
                   (bottom_left_x, bottom_left_y + size // 2)]
    pygame.draw.polygon(screen, color if radar_type == 'C' else WHITE, east_points)

# Függvény az eltelt idő megjelenítésére
def draw_elapsed_time(start_time):
    current_time = time.time()
    elapsed_time = current_time - start_time  # Eltelt idő másodpercekben

    # Perc és másodperc kiszámítása
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)

    time_text = f'Survived: {minutes:02}:{seconds:02}'
    text_surface = font.render(time_text, True, WHITE)  # Fehér színű szöveg
    text_rect = text_surface.get_rect(center=(WIDTH // 2, 35))  
    screen.blit(text_surface, text_rect)  

# Fő ciklus
def main():
    global player_x, player_y, radar_type, alert_triggered, alert_square_timer, alert_screen_timer
    running = True
    radar_interval = 5  # Alapértelmezett radar megjelenítési idő
    alert = random.randint(20, 40)  # Riasztási idő
    start_time = time.time()  # Játék indításának ideje
    last_o_time = time.time()  # Utolsó O betű elhelyezési idő
    radar_timer = time.time()  # Az utolsó radar megjelenítési idő

    while running:
        current_time = time.time()  # Jelenlegi idő
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Játékos mozgás kezelése
        keys = pygame.key.get_pressed()
        ''' SZÖG ALAPÚ MOZGÁS
        if keys[pygame.K_LEFT]:
            player_angle -= 0.12  # Forgás balra
        if keys[pygame.K_RIGHT]:
            player_angle += 0.12  # Forgás jobbra

        # Játékos pozíciójának előrelépése az új irányba
        move_x, move_y = 0, 0
        if keys[pygame.K_UP]:
            move_x = 5 * math.cos(player_angle)
            move_y = 5 * math.sin(player_angle)
        if keys[pygame.K_DOWN]:
            move_x = -5 * math.cos(player_angle)
            move_y = -5 * math.sin(player_angle)
        '''
        # Koordináta-alapú mozgás
        move_x, move_y = 0, 0
        if keys[pygame.K_UP]:      # Fel mozgás
            move_y -= 3
        if keys[pygame.K_DOWN]:    # Le mozgás
            move_y += 3
        if keys[pygame.K_LEFT]:    # Balra mozgás
            move_x -= 3
        if keys[pygame.K_RIGHT]:   # Jobbra mozgás
            move_x += 3

        # Kilépés a játékból
        if keys[pygame.K_ESCAPE]:  # ESC megnyomása kilépéshez
            running = False

        # Ütközés falakkal
        new_x = player_x + move_x
        new_y = player_y + move_y
        if world_map[int(new_y // TILE_SIZE)][int(new_x // TILE_SIZE)] != '#':
            player_x = max(0, min(WIDTH - TILE_SIZE, new_x))
            player_y = max(0, min(HEIGHT - TILE_SIZE, new_y))

        # új O betű elhelyezése X másodpercenként
        current_time = time.time()
        if current_time - last_o_time >= 4:  
            place_o() 
            last_o_time = current_time 

        #RADAR
        elapsed_time = current_time - start_time
        if elapsed_time >= alert / 4 * 3:
            radar_interval = 2 
        elif elapsed_time >= alert / 2:
            radar_interval = 3  
        elif elapsed_time >= alert / 4:
            radar_interval = 4  

        if current_time - radar_timer >= radar_interval:
            show_radar() 
            radar_timer = current_time
        # Ellenőrizze, hogy a csík megjelenítési ideje eltelt-e
        if current_time - radar_timer >= radar_display_time:
            radar_type = None  # Törölje a csíkot

        # Ellenőrzés, ha elérte az alert időt
        elapsed_time = current_time - start_time
        if not alert_triggered and elapsed_time >= alert:
            alert_triggered = True
            alert_square_timer = time.time() 

            # Véletlenszerű üres mező keresése a játékos közelében
            found_empty_spot = False
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                test_x = player_x + dx * TILE_SIZE
                test_y = player_y + dy * TILE_SIZE
                tile_x, tile_y = int(test_x // TILE_SIZE), int(test_y // TILE_SIZE)
                if world_map[tile_y][tile_x] == ' ':
                    alert_square_position = (test_x, test_y)
                    found_empty_spot = True
                    break
            
            if not found_empty_spot:
                alert_square_position = (player_x, player_y)  # Ha nincs közeli üres mező, akkor játékos pozíció

            alert_screen_timer = alert_square_timer + 0.5  # teljes képernyőre váltás

        screen.fill(GRAY) #képernyő alapszíne
        check_collision() # Ütközés ellenőrzése a játékos és az O betűk között    
        remove_old_o() # Régi O betűk eltávolítása
        draw_2d_with_fade_effect() # 2D rajzolás homályos fényhatással
        draw_o()  # O betűk rajzolása
        draw_radar()  # radar kirajzolása
        draw_compass() #iránytű kirajzolása
        draw_score(score)  # Pontszám kiírása
        draw_elapsed_time(start_time) # Eltelt idő kiírása

        # Piros négyzet kirajzolása
        if alert_triggered and alert_square_timer and current_time - alert_square_timer < 1:
            pygame.draw.circle(screen, (255, 0, 0), alert_square_position, TILE_SIZE // 2)

        # Egész képernyő vörösre állítása 1 másodperc után
        if alert_triggered and alert_screen_timer and current_time >= alert_screen_timer:
            screen.fill((255, 0, 0))  # Teljes vörös képernyő

        # Képernyő frissítése
        pygame.display.flip()
        clock.tick(60)  # FPS limit

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
