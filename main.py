from engine import GameEngine
from server import GameServer
import tkinter as tk
from tkinter import ttk, messagebox

def start_server():
    server = GameServer()
    print("Server started...")
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.stop()

def start_game(singleplayer=False):
    server_ip = "localhost"
    if not singleplayer:
        server_ip = tk.simpledialog.askstring("Connect", "Enter server IP:", initialvalue="localhost")
        if not server_ip:
            server_ip = "localhost"

    # Configure the game engine with custom settings
    config = {
        'window_title': "PyCGE" + (" - Singleplayer" if singleplayer else " - Multiplayer"),
        'window_width': 1000,
        'window_height': 800,
        'background_color': "#000000",
        'debug_enabled': True,
        'multiplayer_enabled': not singleplayer,
        'server_ip': server_ip,
        'server_port': 5555,
        'physics': {
            'gravity': 0.65,
            'jump_force': -14.5,
            'move_speed': 6.5,
            'friction': 0.8
        },
        'player': {
            'width': 30,
            'height': 30,
            'color': "#FF0606",
            'start_x': 640,
            'start_y': 360
        },

        # X, Y, Width, Height, Platform ID
        'platforms': [
            (100, 500, 5000, 200, 0),
            (400, 400, 200, 20, 1),
            (700, 300, 200, 20, 2),
            (200, 200, 200, 20, 3),
            (600, 100, 200, 20, 4)
        ]
    }

    # Simple Game Variables
    level = 1
    score = 0
    upgraded = False

    # Create game instance with collision callback
    def on_collision(pid):
        nonlocal level
        if pid == 2:
            print("Collision with platform 2 detected!")

    game = GameEngine(config, on_collision=on_collision)

    # Create Environment
    for plat in config['platforms']:
        game.add_platform(*plat)

if __name__ == "__main__":
    from launcher import StartMenu
    StartMenu()
