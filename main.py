import tkinter as tk
from tkinter import ttk
import math
import time

class GameEngine:
    def __init__(self):
        # Initial position for reset (centered in viewport)
        self.initial_x = 640  # Half of 1280
        self.initial_y = 360  # Half of 720
        
        self.root = tk.Tk()
        self.root.title("PyCGE 2D Sample Engine")
        
        # Create main container with dark theme
        self.main_container = tk.Frame(self.root, bg='#1a1a1a')
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create game frame
        self.game_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        self.game_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas
        self.canvas = tk.Canvas(self.game_frame, width=1280, height=720, bg='black',
                              highlightthickness=0)  # Remove canvas border
        self.canvas.pack()
        
        # Create debug info frame at the top-left
        self.debug_frame = tk.Frame(self.canvas, bg='black')
        self.debug_frame.place(x=10, y=10)
        
        # Create horizontal debug info with Consolas font
        self.fps_label = tk.Label(self.debug_frame, text="FPS: 0", 
                                 bg='black', fg='white', 
                                 font=('Consolas', 12))
        self.fps_label.pack(side=tk.LEFT, padx=(0, 15))
        
        self.pos_label = tk.Label(self.debug_frame, text="Pos: (0, 0)", 
                                 bg='black', fg='white', 
                                 font=('Consolas', 12))
        self.pos_label.pack(side=tk.LEFT, padx=(0, 15))
        
        self.vel_label = tk.Label(self.debug_frame, text="Vel: (0, 0)", 
                                 bg='black', fg='white', 
                                 font=('Consolas', 12))
        self.vel_label.pack(side=tk.LEFT)
        
        # Physics properties (default values without sliders)
        self.gravity = 0.65
        self.jump_force = -14.5
        self.move_speed = 6.5
        self.friction = 0.8
        
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
          # Platforms (x, y, width, height)
        self.platforms = [
            (200, 600, 200, 20),
            (600, 500, 200, 20),
            (1000, 400, 200, 20),
            (0, 680, 1280, 20),  # Ground
        ]
        
        # Input handling
        self.keys = {'left': False, 'right': False, 'up': False}
        self.root.bind('<KeyPress>', self.key_press)
        self.root.bind('<KeyRelease>', self.key_release)
        
        # Start game loop
        self.update()
        self.root.mainloop()
        
    def update_camera(self):
        # Set camera target to center on player
        self.camera['target_x'] = self.player['x'] - 1280/2 + self.player['width']/2
        self.camera['target_y'] = self.player['y'] - 720/2 + self.player['height']/2
        
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
            if (x < platform[0] + platform[2] and
                x + player_rect[2] > platform[0] and
                y < platform[1] + platform[3] and
                y + player_rect[3] > platform[1]):
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
        
        # Draw platforms with camera offset
        for platform in self.platforms:
            screen_x, screen_y = self.world_to_screen(platform[0], platform[1])
            self.canvas.create_rectangle(
                screen_x, screen_y,
                screen_x + platform[2],
                screen_y + platform[3],
                fill='green'
            )
        
        # Draw player with camera offset
        player_screen_x, player_screen_y = self.world_to_screen(self.player['x'], self.player['y'])
        self.canvas.create_rectangle(
            player_screen_x,
            player_screen_y,
            player_screen_x + self.player['width'],
            player_screen_y + self.player['height'],
            fill='red'
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

if __name__ == "__main__":
    game = GameEngine()
