from engine import GameEngine
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from network import HostConnection, ClientConnection

def start_game(multiplayer=False):
    net = None
    player_id = "You"
    remote_id = "Peer"
    if multiplayer:
        root = tk.Tk()
        root.withdraw()
        player_id = simpledialog.askstring("Multiplayer", "Enter your player name:", initialvalue="Player")
        role = simpledialog.askstring("Multiplayer", "Host or Join? (h/j)", initialvalue="h")
        if role and role.lower().startswith('h'):
            host_port = simpledialog.askinteger("Host", "Enter port to host on (e.g. 5000):", initialvalue=5000)
            net = HostConnection(host_port)
            remote_id = "Peer"
        else:
            host_ip = simpledialog.askstring("Join", "Enter host IP:", initialvalue="127.0.0.1")
            host_port = simpledialog.askinteger("Join", "Enter host port (e.g. 5000):", initialvalue=5000)
            net = ClientConnection(host_ip, host_port)
            remote_id = "Host"
        root.destroy()

    config = {
        'window_title': "PyCGE - Multiplayer" if multiplayer else "PyCGE - Singleplayer",
        'window_width': 1000,
        'window_height': 800,
        'background_color': "#000000",
        'debug_enabled': True,
        'player': {
            'width': 30,
            'height': 30,
            'color': "#FF0606",
            'start_x': 640,
            'start_y': 360
        },
        'platforms': [
            (100, 500, 5000, 200, 0),
            (400, 400, 200, 20, 1),
            (700, 300, 200, 20, 2),
            (200, 200, 200, 20, 3),
            (600, 100, 200, 20, 4)
        ],
        'net': net,
        'player_id': player_id,
        'remote_id': remote_id
    }

    def on_collision(pid):
        if pid == 2:
            print("works")

    game = GameEngine(config, on_collision=on_collision)
    for plat in config['platforms']:
        game.add_platform(*plat)

if __name__ == "__main__":
    from launcher import StartMenu
    StartMenu()
