from game import Game
import pyray as rl
from enum import Enum
import random
import os
import time
from game import bfs
from game import dfs
from game import ids
from game import a_star_1
from game import a_star_2
from game import weighted_a_star

MENU_WIDTH = 600
MENU_HEIGHT = 400
DEFAULT_SCREEN_WIDTH = 1800
DEFAULT_SCREEN_HEIGHT = 1000
CELL_SIZE = 128
WIDTH_MARGIN = 120
HEIGHT_MARGIN = 100
N_ASSET = 8

# You can add your algorithms here
SOLVERS = {
    "BFS": bfs,
    "DFS": dfs,
    "IDS": ids,
    "A*_1": a_star_1,
    "A*_2": a_star_2,
    "WEIGHTED_A*": weighted_a_star
}

def generate_color(box_id):
    random.seed(box_id)
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return rl.Color(r, g, b, 255)

class Direction(Enum):
    UP = 'U'
    DOWN = 'D'
    LEFT = 'L'
    RIGHT = 'R'

def load_game_from_file(filename):
    try:
        with open(filename) as f:
            return Game(f.read())
    except FileNotFoundError:
        print(f"Error: Could not find file {filename}")
        return None

def adjust_window_size(game: Game):
    global CELL_SIZE, WIDTH_MARGIN, HEIGHT_MARGIN, SCREEN_WIDTH, SCREEN_HEIGHT, DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT, BACK
    CELL_SIZE = min((DEFAULT_SCREEN_WIDTH - WIDTH_MARGIN) // game.width, (DEFAULT_SCREEN_HEIGHT - HEIGHT_MARGIN) // game.height)
    SCREEN_WIDTH = CELL_SIZE * game.width + WIDTH_MARGIN
    SCREEN_HEIGHT = CELL_SIZE * game.height + HEIGHT_MARGIN
    BACK = {
        'x': SCREEN_WIDTH - WIDTH_MARGIN + 10,
        'y': 20,
        'w': 100,
        'h': 30,
        'text_x': SCREEN_WIDTH - WIDTH_MARGIN + 28,
        'text_y': 28
    }

def load_and_resize_texture(filename, target_size):
    image = rl.load_image(filename)
    if image.width == 0 or image.height == 0:
        print(f"Failed to load image: {filename}")
        return None
    if image.width != target_size or image.height != target_size:
        rl.image_resize(image, target_size, target_size)
    texture = rl.load_texture_from_image(image)
    rl.unload_image(image)
    return texture

def get_map_files():
    maps_dir = './assets/maps'
    # Only include files that start with "map"
    return [f for f in os.listdir(maps_dir) if f.startswith('map') and f.endswith('.txt')]

def draw_map_menu(maps, selected_map, scroll_offset):
    rl.clear_background(rl.RAYWHITE)
    rl.draw_text("Select Map:", 50, 50, 20, rl.BLACK)
    
    # Limit to maximum 5 visible items
    visible_items = min(5, len(maps))  # Maximum 5 items visible
    start_y = 80
    menu_width = 300  # Width for the menu text
    scrollbar_x = 50 + menu_width + 10  # Position scrollbar 10 pixels to the right of menu
    
    # Draw visible maps
    for i in range(len(maps)):
        adjusted_y = start_y + (i - scroll_offset) * 30
        # Only draw if within visible area (5 items max)
        if 80 <= adjusted_y < 80 + visible_items * 30:  # Changed <= to < to keep it above bottom
            color = rl.RED if i == selected_map else rl.BLACK
            rl.draw_text(maps[i], 50, adjusted_y, 20, color)
    
    # Draw scrollbar if needed
    if len(maps) > visible_items:
        scrollbar_height = int((visible_items / len(maps)) * (visible_items * 30))  # Height based on visible area
        scrollbar_y = int(80 + (scroll_offset / len(maps)) * (visible_items * 30))  # Position based on scroll
        scrollbar_height = max(10, scrollbar_height)  # Minimum height of 10 pixels
        rl.draw_rectangle(scrollbar_x, scrollbar_y, 10, scrollbar_height, rl.GRAY)
    
    rl.draw_text("Press ENTER to select map", 50, 350, 20, rl.BLACK)

def draw_mode_menu(selected_mode):
    rl.clear_background(rl.RAYWHITE)
    rl.draw_text("Select Mode:", 50, 50, 20, rl.BLACK)
    modes = ["Player"] + list(SOLVERS.keys())
    for i, mode in enumerate(modes):
        color = rl.BLUE if i == selected_mode else rl.BLACK
        rl.draw_text(mode, 50, 80 + i * 30, 20, color)
    rl.draw_text("Press ENTER to start game", 50, 300, 20, rl.BLACK)

def draw_no_solution_screen():
    rl.clear_background(rl.RAYWHITE)
    rl.draw_text("AI didn't find solution", 
                 rl.get_screen_width()//2 - 140, 
                 rl.get_screen_height()//2 - 10, 
                 30, rl.RED)


def play_game(game: Game, solver_func=None):

    wall_texture = load_and_resize_texture("./assets/sprites/environment/wall.png", CELL_SIZE)
    portal_texture = [load_and_resize_texture(f"./assets/sprites/portal/portal{i}.png", CELL_SIZE) for i in range(2)]
    box_texture = [load_and_resize_texture(f"./assets/sprites/box/box{i}.png", CELL_SIZE) for i in range(N_ASSET)]
    goal_texture = [load_and_resize_texture(f"./assets/sprites/goal/goal{i}.png", CELL_SIZE) for i in range(N_ASSET)]
    player_texture = {
        d.value: load_and_resize_texture(f"./assets/sprites/player/player_{d.value}.png", CELL_SIZE)
        for d in Direction
    }

    move_sound_effect = rl.load_sound("./assets/sounds/move.wav")
    
    if (wall_texture is None or wall_texture.id == 0 or 
        not all(portal_texture) or any([t.id == 0 for t in portal_texture]) or
        not all(box_texture) or any([t.id == 0 for t in box_texture]) or
        not all(goal_texture) or any([t.id == 0 for t in goal_texture]) or
        not all(player_texture.values()) or any([t.id == 0 for t in player_texture.values()])):
        print("Error loading textures")
        return False
    
    ai_moves = None
    move_index = 0
    move_delay = 0.5
    last_move_time = rl.get_time()
    game_won_time = None
    no_solution_time = None
    last_dir = 'D'
    
    if solver_func:
        ai_moves = solver_func(game.get_map())
        if ai_moves == 'No solution':
            no_solution_time = rl.get_time()
            ai_moves = None
    
    while not rl.window_should_close():
        global MUSIC
        rl.update_music_stream(MUSIC)
        
        if no_solution_time:
            rl.begin_drawing()
            draw_no_solution_screen()
            rl.end_drawing()
            if rl.get_time() - no_solution_time >= 3.0:
                rl.unload_texture(wall_texture)
                rl.unload_texture(player_texture)
                [rl.unload_texture(t) for t in portal_texture]
                [rl.unload_texture(t) for t in box_texture]
                [rl.unload_texture(t) for t in goal_texture]
                [rl.unload_texture(t) for t in player_texture.values()]

                return True
            continue
        
        direction = None
        if not solver_func:
            if rl.is_key_pressed(rl.KEY_UP) or rl.is_key_pressed(rl.KEY_W):
                direction = Direction.UP.value
            elif rl.is_key_pressed(rl.KEY_DOWN) or rl.is_key_pressed(rl.KEY_S):
                direction = Direction.DOWN.value
            elif rl.is_key_pressed(rl.KEY_LEFT) or rl.is_key_pressed(rl.KEY_A):
                direction = Direction.LEFT.value
            elif rl.is_key_pressed(rl.KEY_RIGHT) or rl.is_key_pressed(rl.KEY_D):
                direction = Direction.RIGHT.value
        elif ai_moves and move_index < len(ai_moves) and rl.get_time() - last_move_time >= move_delay:
            direction = ai_moves[move_index]
            move_index += 1
            last_move_time = rl.get_time()
        if direction:
            last_dir = direction
            rl.play_sound(move_sound_effect)
            try:
                game.apply_move(direction)
                if game.is_game_won() and game_won_time is None:
                    game_won_time = rl.get_time()
            except ValueError:
                pass
        
        rl.begin_drawing()
        rl.clear_background(rl.RAYWHITE)
        
        for y in range(game.height):
            for x in range(game.width):
                cell_x = x * CELL_SIZE
                cell_y = y * CELL_SIZE
                elements = game.get_elements_in_position((y, x))
                
                has_goal = any(e.startswith('G') for e in elements)
                if has_goal:
                    goal_num = int([e[1:] for e in elements if e.startswith('G')][0])
                    rl.draw_texture(goal_texture[goal_num % N_ASSET], cell_x, cell_y, rl.WHITE)
                    # color = generate_color(goal_num)
                    # rl.draw_rectangle(cell_x, cell_y, CELL_SIZE, CELL_SIZE, 
                    #                 rl.fade(color, 0.3))
                    rl.draw_text(str(goal_num), 
                               cell_x + CELL_SIZE//2 - 5, 
                               cell_y + CELL_SIZE//2 - 10, 
                               20, rl.BLACK)
                
                if 'W' in elements:
                    rl.draw_texture(wall_texture, cell_x, cell_y, rl.WHITE)
                
                box = [e for e in elements if e.startswith('B')]
                if box:
                    box_num = int(box[0][1:])
                    rl.draw_texture(box_texture[box_num % N_ASSET], cell_x, cell_y, rl.WHITE)
                    # color = generate_color(box_num)
                    # rl.draw_rectangle(cell_x + 8, cell_y + 8, CELL_SIZE - 16, CELL_SIZE - 16, 
                    #                 color)
                    rl.draw_text(str(box_num), 
                               cell_x + CELL_SIZE//2 - 5, 
                               cell_y + CELL_SIZE//2 - 10, 
                               20, rl.WHITE)
                
                portal = [e for e in elements if e.startswith('P')]
                if portal:
                    portal_num = int(portal[0][1:]) - 1
                    rl.draw_texture(portal_texture[portal_num], cell_x, cell_y, rl.WHITE)
                if 'H' in elements:
                    rl.draw_texture(player_texture[last_dir], cell_x, cell_y, rl.WHITE)
                rl.draw_rectangle_lines(cell_x, cell_y, CELL_SIZE, CELL_SIZE, rl.LIGHTGRAY)
        
        rl.draw_rectangle(BACK['x'], BACK['y'], BACK['w'], BACK['h'], rl.RED)
        rl.draw_text("Back", BACK['text_x'], BACK['text_y'], 20, rl.WHITE)
        
        if game.is_game_won():
            rl.draw_text("You Won!", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - HEIGHT_MARGIN + 25, 
                        50, rl.GREEN)
            if rl.get_time() - game_won_time >= 2.0:
                rl.unload_texture(wall_texture)
                [rl.unload_texture(t) for t in portal_texture]
                [rl.unload_texture(t) for t in box_texture]
                [rl.unload_texture(t) for t in goal_texture]
                [rl.unload_texture(t) for t in player_texture.values()]
                rl.unload_sound(move_sound_effect)
                return True
        
        rl.end_drawing()
        
        if rl.is_mouse_button_pressed(rl.MOUSE_LEFT_BUTTON):
            mouse_x, mouse_y = rl.get_mouse_x(), rl.get_mouse_y()
            if (BACK['x'] <= mouse_x <= BACK['x'] + BACK['w'] and 
                BACK['y'] <= mouse_y <= BACK['y'] + BACK['h']):
                rl.unload_texture(wall_texture)
                [rl.unload_texture(t) for t in portal_texture]
                [rl.unload_texture(t) for t in box_texture]
                [rl.unload_texture(t) for t in goal_texture]
                [rl.unload_texture(t) for t in player_texture.values()]
                rl.unload_sound(move_sound_effect)
                return True
        
        if rl.is_key_pressed(rl.KEY_ESCAPE):
            rl.unload_texture(wall_texture)
            [rl.unload_texture(t) for t in portal_texture]
            [rl.unload_texture(t) for t in box_texture]
            [rl.unload_texture(t) for t in goal_texture]
            [rl.unload_texture(t) for t in player_texture.values()]
            rl.unload_sound(move_sound_effect)
            return True
    
    rl.unload_texture(wall_texture)
    rl.unload_texture(portal_texture)
    [rl.unload_texture(t) for t in portal_texture]
    [rl.unload_texture(t) for t in box_texture]
    [rl.unload_texture(t) for t in goal_texture]
    [rl.unload_texture(t) for t in player_texture.values()]
    rl.unload_sound(move_sound_effect)
    return False

def main():
    rl.init_window(MENU_WIDTH, MENU_HEIGHT, "Game Menu")
    rl.init_audio_device()
    rl.set_target_fps(60)

    global MUSIC
    MUSIC = rl.load_music_stream('./assets/sounds/music.mp3')
    rl.play_music_stream(MUSIC)

    maps = get_map_files()
    selected_map = 0
    selected_mode = 0
    in_map_selection = True
    scroll_offset = 0
    visible_items = 5  # Maximum 5 visible items
    
    while not rl.window_should_close():
        rl.update_music_stream(MUSIC)
        if in_map_selection:
            if rl.is_key_pressed(rl.KEY_DOWN):
                selected_map = min(len(maps) - 1, selected_map + 1)
                # Adjust scroll if selection goes beyond visible area
                if selected_map - scroll_offset >= visible_items:
                    scroll_offset += 1
            if rl.is_key_pressed(rl.KEY_UP):
                selected_map = max(0, selected_map - 1)
                # Adjust scroll if selection goes above visible area
                if selected_map < scroll_offset:
                    scroll_offset -= 1
            if rl.is_key_pressed(rl.KEY_ENTER):
                in_map_selection = False
                selected_mode = 0
            
            rl.begin_drawing()
            draw_map_menu(maps, selected_map, scroll_offset)
            rl.end_drawing()
        
        else:
            if rl.is_key_pressed(rl.KEY_DOWN):
                selected_mode = min(len(SOLVERS) + 1 - 1, selected_mode + 1)
            if rl.is_key_pressed(rl.KEY_UP):
                selected_mode = max(0, selected_mode - 1)
            if rl.is_key_pressed(rl.KEY_ENTER):
                game = load_game_from_file(f'./assets/maps/{maps[selected_map]}')
                adjust_window_size(game)
                if game:
                    rl.close_window()
                    rl.init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Game")
                    solver_func = SOLVERS[list(SOLVERS.keys())[selected_mode - 1]] if selected_mode > 0 else None
                    play_game(game, solver_func)
                    rl.close_window()
                    rl.init_window(MENU_WIDTH, MENU_HEIGHT, "Game Menu")
                    in_map_selection = True
            
            rl.begin_drawing()
            draw_mode_menu(selected_mode)
            rl.end_drawing()

    rl.stop_music_stream(MUSIC)
    rl.unload_music_stream(MUSIC)
    rl.close_audio_device()
    rl.close_window()
    
if __name__ == "__main__":
    main()