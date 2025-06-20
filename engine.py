import tkinter as tk
from tkinter import ttk
import math
import time

class GameEngine:
    def __init__(self, config=None, on_collision=None):
        self.config = config
        self.on_collision = on_collision
        # Initial position for reset
        self.initial_x = 400
        self.initial_y = 300
        
        self.root = tk.Tk()
        self.root.title("PyCGE 2D Sample Engine")
        
        # Configure style for dark theme
        style = ttk.Style()
        style.configure("Custom.Horizontal.TScale",
                       troughcolor='#2a2a2a',
                       slidercolor='#ffffff',
                       background='#1a1a1a')

        # Create main container with dark theme
        self.main_container = tk.Frame(self.root, bg='#1a1a1a')
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create game frame (left side)
        self.game_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        self.game_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Set background and player color from config or use defaults
        self.background_color = self.config.get('background_color', '#000000') if self.config else '#000000'
        self.player_color = (self.config.get('player', {}).get('color', '#FF0000') if self.config else '#FF0000')

        # Create canvas
        self.canvas = tk.Canvas(self.game_frame, width=800, height=600, bg=self.background_color,
                              highlightthickness=0)  # Remove canvas border
        self.canvas.pack(side=tk.LEFT)
        
        # Create debug info frame at the top-left
        self.debug_frame = tk.Frame(self.canvas, bg='black')
        self.debug_frame.place(x=10, y=10)
        
        # Create horizontal debug info with modern font
        self.fps_label = tk.Label(self.debug_frame, text="FPS: 0", 
                                 bg='black', fg='white', 
                                 font=('Helvetica', 12))
        self.fps_label.pack(side=tk.LEFT, padx=(0, 15))
        
        self.pos_label = tk.Label(self.debug_frame, text="Pos: (0, 0)", 
                                 bg='black', fg='white', 
                                 font=('Helvetica', 12))
        self.pos_label.pack(side=tk.LEFT, padx=(0, 15))
        
        self.vel_label = tk.Label(self.debug_frame, text="Vel: (0, 0)", 
                                 bg='black', fg='white', 
                                 font=('Helvetica', 12))
        self.vel_label.pack(side=tk.LEFT)
        
        # FPS tracking
        self.last_frame_time = time.time()
        self.fps = 0
        
        # Camera properties
        self.camera = {
            'x': 0,
            'y': 0,
            'target_x': 0,
            'target_y': 0,
            'smoothness': 0.1
        }
        
        # Player properties
        self.player = {
            'x': self.initial_x,
            'y': self.initial_y,
            'width': 30,
            'height': 30,
            'velocity_x': 0,
            'velocity_y': 0,
            'on_ground': False
        }
        # If config provides player size, override defaults
        if self.config and 'player' in self.config:
            self.player['width'] = self.config['player'].get('width', self.player['width'])
            self.player['height'] = self.config['player'].get('height', self.player['height'])
        
        # Platforms (x, y, width, height, id)
        self.platforms = []
        if self.config and 'platforms' in self.config:
            for plat in self.config['platforms']:
                self.platforms.append(tuple(plat))
        
        # Physics properties
        self.gravity = 0.5
        self.jump_force = -12
        self.move_speed = 5
        self.friction = 0.8
    
        # Input handling
        self.keys = {'left': False, 'right': False, 'up': False}
        self.root.bind('<KeyPress>', self.key_press)
        self.root.bind('<KeyRelease>', self.key_release)
        
        # Special platform ID
        self.special_pid = self.config.get('special_pid', 1) if self.config else 1
        
        # Start game loop
        self.update()
        self.root.mainloop()
    
    def create_slider(self, name, min_val, max_val, default, callback):
        frame = tk.Frame(self.controls_container, bg='#1a1a1a')
        frame.pack(fill=tk.X, pady=10)
        
        label = tk.Label(frame, text=name, bg='#1a1a1a', fg='white',
                        font=('Helvetica', 11))
        label.pack(anchor=tk.W)
        
        value_label = tk.Label(frame, text=f"{default:.2f}", bg='#1a1a1a', fg='#888888',
                              font=('Helvetica', 10))
        value_label.pack(anchor=tk.E)
        
        def update_callback(value):
            value_label.config(text=f"{float(value):.2f}")
            callback(value)
        
        slider = ttk.Scale(frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL,
                         value=default, command=update_callback, style="Custom.Horizontal.TScale")
        slider.pack(fill=tk.X, pady=(5, 0))
    
    def update_value(self, attribute, value):
        value = float(value)
        if attribute == 'gravity':
            self.gravity = value
        elif attribute == 'jump_force':
            self.jump_force = value
        elif attribute == 'move_speed':
            self.move_speed = value
        elif attribute == 'friction':
            self.friction = value
    
    def update_camera(self):
        # Set camera target to center on player
        self.camera['target_x'] = self.player['x'] - 800/2 + self.player['width']/2
        self.camera['target_y'] = self.player['y'] - 600/2 + self.player['height']/2
        
        # Smooth camera movement
        self.camera['x'] += (self.camera['target_x'] - self.camera['x']) * self.camera['smoothness']
        self.camera['y'] += (self.camera['target_y'] - self.camera['y']) * self.camera['smoothness']
    
    def world_to_screen(self, x, y):
        return x - self.camera['x'], y - self.camera['y']
    
    def update_debug_info(self):
        current_time = time.time()
        dt = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        if dt > 0:
            self.fps = 1.0 / dt
        
        self.fps_label.config(text=f"FPS: {self.fps:.1f}")
        self.pos_label.config(text=f"Pos: ({self.player['x']:.1f}, {self.player['y']:.1f})")
        self.vel_label.config(text=f"Vel: ({self.player['velocity_x']:.1f}, {self.player['velocity_y']:.1f})")
    
    def check_collision(self, x, y):
        player_rect = (x, y, self.player['width'], self.player['height'])
        for platform in self.platforms:
            px, py, pw, ph = platform[:4]
            pid = platform[4] if len(platform) > 4 else None
            if (x < px + pw and
                x + player_rect[2] > px and
                y < py + ph and
                y + player_rect[3] > py):
                if self.on_collision:
                    self.on_collision(pid)
                return True
        return False
    
    def reset_position(self):
        self.player['x'] = self.initial_x
        self.player['y'] = self.initial_y
        self.player['velocity_x'] = 0
        self.player['velocity_y'] = 0
        self.camera['x'] = 0
        self.camera['y'] = 0
        self.camera['target_x'] = 0
        self.camera['target_y'] = 0
    
    def add_platform(self, x, y, width, height, pid=None):
        if pid is not None:
            self.platforms.append((x, y, width, height, pid))
        else:
            self.platforms.append((x, y, width, height))
    
    def update(self):
        # Update camera position
        self.update_camera()
        
        # Handle horizontal movement (changed to WASD)
        if self.keys['left']:  # A key
            self.player['velocity_x'] = -self.move_speed
        elif self.keys['right']:  # D key
            self.player['velocity_x'] = self.move_speed
        else:
            self.player['velocity_x'] *= self.friction
        
        # Apply gravity
        if not self.player['on_ground']:
            self.player['velocity_y'] += self.gravity
        
        # Handle jumping (W key)
        if self.keys['up'] and self.player['on_ground']:
            self.player['velocity_y'] = self.jump_force
            self.player['on_ground'] = False
        
        # Update position
        new_x = self.player['x'] + self.player['velocity_x']
        new_y = self.player['y'] + self.player['velocity_y']
        
        # Check horizontal collision
        if not self.check_collision(new_x, self.player['y']):
            self.player['x'] = new_x
        else:
            self.player['velocity_x'] = 0
        
        # Check vertical collision
        if not self.check_collision(self.player['x'], new_y):
            self.player['y'] = new_y
            self.player['on_ground'] = False
        else:
            if self.player['velocity_y'] > 0:
                self.player['on_ground'] = True
            self.player['velocity_y'] = 0
        
        # Clear and redraw
        self.canvas.delete('all')
        self.canvas.config(bg=self.background_color)
        # Draw platforms with camera offset
        for platform in self.platforms:
            screen_x, screen_y = self.world_to_screen(platform[0], platform[1])
            self.canvas.create_rectangle(
                screen_x, screen_y,
                screen_x + platform[2],
                screen_y + platform[3],
                fill="#205D06", outline="#FFFFFF"
            )
        # Draw player with camera offset
        player_screen_x, player_screen_y = self.world_to_screen(self.player['x'], self.player['y'])
        self.canvas.create_rectangle(
            player_screen_x,
            player_screen_y,
            player_screen_x + self.player['width'],
            player_screen_y + self.player['height'],
            fill=self.player_color
        )
        
        # Update debug information
        self.update_debug_info()
        
        # Schedule next update
        self.root.after(16, self.update)  # ~60 FPS

    def key_press(self, event):
        if event.keysym.lower() == 'a':
            self.keys['left'] = True
        elif event.keysym.lower() == 'd':
            self.keys['right'] = True
        elif event.keysym == 'space' or event.keysym.lower() == 'w':  # Both space and W for jump
            self.keys['up'] = True
        elif event.keysym.lower() == 'r':  # Reset position when R is pressed
            self.reset_position()
            
    def key_release(self, event):
        if event.keysym.lower() == 'a':
            self.keys['left'] = False
        elif event.keysym.lower() == 'd':
            self.keys['right'] = False
        elif event.keysym == 'space' or event.keysym.lower() == 'w':  # Both space and W for jump
            self.keys['up'] = False
