from engine import GameEngine, Server
import tkinter as tk
from tkinter import ttk, messagebox

def start_server():
    server = Server()
    print("Server started...")
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.stop()

def start_game(singleplayer=False):
    # Get server IP if multiplayer mode
    server_ip = "localhost"
    if not singleplayer:
        server_ip = tk.simpledialog.askstring("Connect", "Enter server IP:", initialvalue="localhost")
        if not server_ip:
            server_ip = "localhost"

    # Configure the game engine with custom settings
    config = {
        'window_title': "PyCGE" + (" - Singleplayer" if singleplayer else " - Multiplayer"),
        'window_width': 1280,
        'window_height': 720,
        'background_color': "#000000",
        'debug_enabled': True,
        'multiplayer_enabled': not singleplayer,  # Enable multiplayer only in multiplayer mode
        'server_ip': server_ip,      # Set the server IP
        'server_port': 5555,         # Make sure port matches server
        'physics': {
            'gravity': 0.65,
            'jump_force': -14.5,
            'move_speed': 6.5,
            'friction': 0.8
        },
        'player': {
            'width': 30,
            'height': 30,
            'color': 'blue',  # Color will be automatically set based on client ID
            'start_x': 640,
            'start_y': 360
        }
    }

    # Create game instance
    game = GameEngine(config)

    # Add platforms
    # Parameters: x, y, width, height, color(optional)
    game.add_platform(0, 680, 1280, 20)  # Ground
    game.add_platform(200, 600, 200, 20)  # Platform 1
    game.add_platform(600, 500, 200, 20)  # Platform 2
    game.add_platform(1000, 400, 200, 20)  # Platform 3
    game.add_platform(400, 300, 200, 20)

    # Start the game
    game.run()

class StartMenu:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PyCGE Launcher")
        self.root.geometry("400x500")
        self.root.configure(bg='#1a1a1a')
        
        # Center the window
        self.root.eval('tk::PlaceWindow . center')
        
        # Configure styles
        style = ttk.Style()
        style.configure('Modern.TButton',
            padding=10,
            background='#2a2a2a',
            foreground='white',
            font=('Segoe UI', 10)
        )
        style.configure('Title.TLabel',
            background='#1a1a1a',
            foreground='#ffffff',
            font=('Segoe UI', 24, 'bold')
        )
        style.configure('Subtitle.TLabel',
            background='#1a1a1a',
            foreground='#888888',
            font=('Segoe UI', 10)
        )
        
        # Create main frame
        main_frame = tk.Frame(self.root, bg='#1a1a1a', padx=40, pady=40)
        main_frame.pack(expand=True, fill='both')
        
        # Title and subtitle
        title = ttk.Label(
            main_frame,
            text="PyCGE",
            style='Title.TLabel'
        )
        title.pack(pady=(0, 5))
        
        subtitle = ttk.Label(
            main_frame,
            text="Python Custom Game Engine",
            style='Subtitle.TLabel'
        )
        subtitle.pack(pady=(0, 40))
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg='#1a1a1a')
        button_frame.pack(expand=True)
        
        # Create custom button style
        def on_enter(e):
            e.widget.configure(bg='#3a3a3a')
        def on_leave(e):
            e.widget.configure(bg='#2a2a2a')
        
        # Buttons
        button_configs = [
            ("Play Singleplayer", self.start_singleplayer),
            ("Play Multiplayer", self.start_multiplayer),
            ("Host Server", self.start_server)
        ]
        
        for text, command in button_configs:
            btn = tk.Button(
                button_frame,
                text=text,
                command=command,
                width=20,
                height=2,
                bg='#2a2a2a',
                fg='white',
                font=('Segoe UI', 11),
                relief='flat',
                activebackground='#3a3a3a',
                activeforeground='white',
                cursor='hand2'
            )
            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)
            btn.pack(pady=10)
        
        # Version info
        version = ttk.Label(
            main_frame,
            text="v1.0.0",
            style='Subtitle.TLabel'
        )
        version.pack(side='bottom', pady=20)
        
        self.root.mainloop()
    
    def start_singleplayer(self):
        self.root.destroy()
        start_game(singleplayer=True)
    
    def start_multiplayer(self):
        self.root.destroy()
        start_game(singleplayer=False)
    
    def start_server(self):
        self.root.destroy()
        start_server()

if __name__ == "__main__":
    StartMenu()