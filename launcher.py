import tkinter as tk
from tkinter import ttk, messagebox
from main import start_game

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
            font=('Consolas', 10)
        )
        style.configure('Title.TLabel',
            background="#000000",
            foreground="#FFFFFF",
            font=('Consolas', 24, 'bold')
        )
        style.configure('Subtitle.TLabel',
            background="#000000",
            foreground="#FFFFFF",
            font=('Consolas', 10)
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
            text="PyCGE Launcher",
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
        
        # Buttons for singleplayer and multiplayer
        btn_sp = tk.Button(
            button_frame,
            text="Play Singleplayer",
            command=self.start_singleplayer,
            width=20,
            height=2,
            bg="#000000",
            fg='white',
            font=('Consolas', 11),
            relief='flat',
            activebackground="#000000",
            activeforeground='white',
            cursor='hand2'
        )
        btn_sp.bind('<Enter>', on_enter)
        btn_sp.bind('<Leave>', on_leave)
        btn_sp.pack(pady=10)

        btn_mp = tk.Button(
            button_frame,
            text="Play Multiplayer",
            command=self.start_multiplayer,
            width=20,
            height=2,
            bg="#000000",
            fg='white',
            font=('Consolas', 11),
            relief='flat',
            activebackground="#000000",
            activeforeground='white',
            cursor='hand2'
        )
        btn_mp.bind('<Enter>', on_enter)
        btn_mp.bind('<Leave>', on_leave)
        btn_mp.pack(pady=10)
        
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
        start_game()

    def start_multiplayer(self):
        self.root.destroy()
        start_game(multiplayer=True)