from engine import GameEngine
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from network import HostConnection, ClientConnection
import json

def start_game(multiplayer=False, level_path="level.json"):
    net = None
    player_id = "You"
    host_info = ""
    if multiplayer:
        root = tk.Tk()
        root.withdraw()
        player_id = simpledialog.askstring("Multiplayer", "Enter your player name:", initialvalue="Client")
        role = simpledialog.askstring("Multiplayer", "Host or Join? (host/join)", initialvalue="host")
        if role and role.lower().startswith('host'):
            host_port = simpledialog.askinteger("Host", "Enter port to host on (e.g. 5000):", initialvalue=5000)
            net = HostConnection(host_port)
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            host_info = f"IP: {local_ip} Port: {host_port}"
            print(f"Hosting on {host_info}")
        else:
            host_ip = simpledialog.askstring("Join", "Enter host IP:", initialvalue="127.0.0.1")
            host_port = simpledialog.askinteger("Join", "Enter host port (e.g. 5000):", initialvalue=5000)
            net = ClientConnection(host_ip, host_port)
        root.destroy()

    # Load level from JSON file
    try:
        with open(level_path, "r") as f:
            level = json.load(f)
    except Exception as e:
        print(f"Failed to load level file: {e}")
        return

    player = level.get('player', {
        'width': 30,
        'height': 30,
        'color': "#FF0000",
        'start_x': 640,
        'start_y': 360
    })
    player['start_x'] = int(player['start_x'])
    player['start_y'] = int(player['start_y'])

    config = {
        'window_title': "PyCGE - Platformer Demo",
        'window_width': 1280,
        'window_height': 720,
        'background_color': level.get('background_color', "#000000"),
        'debug_enabled': True,
        'player': player,
        'platforms': [
            (plat['x'], plat['y'], plat['width'], plat['height'], idx, plat.get('color', '#205D06'))
            for idx, plat in enumerate(level.get('platforms', []))
        ],
        'objects': level.get('objects', []),
        'net': net,
        'player_id': player_id
    }

    def on_collision(pid):
        if pid == 2:
            print("Collision detected with platform 2")

    game = GameEngine(config, on_collision=on_collision)
    for plat in config['platforms']:
        if len(plat) == 6:
            game.add_platform(*plat[:5], color=plat[5])
        else:
            game.add_platform(*plat)
    if hasattr(game, 'add_object'):
        for obj in config['objects']:
            game.add_object(obj)
    elif hasattr(game, 'canvas'):
        try:
            if game.canvas.winfo_exists():
                for obj in config['objects']:
                    t = obj.get('type', 'object')
                    if t in ("object", "crate", "coin", "enemy", "checkpoint", "trigger"):
                        x, y, w, h = obj['x'], obj['y'], obj['width'], obj['height']
                        outline = "#FFD700" if t in ("object", "crate", "coin") else ""
                        game.canvas.create_rectangle(x-w//2, y-h//2, x+w//2, y+h//2, fill=obj['color'], outline=outline, width=2)
                    elif t == 'oval':
                        x, y, w, h = obj['x'], obj['y'], obj['width'], obj['height']
                        game.canvas.create_oval(x, y, x+w, y+h, fill=obj['color'], outline="")
                    elif t == 'line':
                        game.canvas.create_line(obj['x0'], obj['y0'], obj['x1'], obj['y1'], fill=obj['color'], width=2)
        except tk.TclError:
            pass

if __name__ == "__main__":
    from launcher import StartMenu
    StartMenu()