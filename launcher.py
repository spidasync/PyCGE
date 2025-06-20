import tkinter as tk
from tkinter import ttk, messagebox
from main import start_game, start_server

class StartMenu:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PyCGE Launcher")
        self.root.geometry("400x500")
        self.root.configure(bg="#000000")
        
        # Center the window
        self.root.eval('tk::PlaceWindow . center')
        
        # Configure styles
        style = ttk.Style()
        style.configure('Modern.TButton',
            padding=10,
            background="#000000",
            foreground='white',
            font=('Segoe UI', 10)
        )
        style.configure('Title.TLabel',
            background="#000000",
            foreground="#000000",
            font=('Segoe UI', 24, 'bold')
        )
        style.configure('Subtitle.TLabel',
            background="#000000",
            foreground="#000000",
            font=('Segoe UI', 10)
        )
        
        # Create main frame
        main_frame = tk.Frame(self.root, bg="#000000", padx=40, pady=40)
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
        button_frame = tk.Frame(main_frame, bg="#000000")
        button_frame.pack(expand=True)
        
        # Create custom button style
        def on_enter(e):
            e.widget.configure(bg="#000000")
        def on_leave(e):
            e.widget.configure(bg="#000000")
        
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
                bg="#000000",
                fg='white',
                font=('Segoe UI', 11),
                relief='flat',
                activebackground="#000000",
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
