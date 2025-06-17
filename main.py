import tkinter as tk
from tkinter import ttk, colorchooser
import math, time

# — Window & projection setup —
WIDTH, HEIGHT = 1280, 960
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2

# Cube geometry
vertices = [
    (-0.5, -0.5, -0.5), (-0.5, -0.5,  0.5),
    (-0.5,  0.5, -0.5), (-0.5,  0.5,  0.5),
    ( 0.5, -0.5, -0.5), ( 0.5, -0.5,  0.5),
    ( 0.5,  0.5, -0.5), ( 0.5,  0.5,  0.5),
]
edges = [
    (0,1),(1,3),(3,2),(2,0),
    (4,5),(5,7),(7,6),(6,4),
    (0,4),(1,5),(2,6),(3,7),
]
faces = [
    (0,1,3,2), (4,5,7,6), (0,1,5,4), (2,3,7,6), (0,2,6,4), (1,3,7,5)
]

def project(point, size, fov, distance=0.008):
    x,y,z = point
    if distance + z == 0:
        return None
    factor = size * fov / (distance + z)
    return (x*factor + CENTER_X, -y*factor + CENTER_Y)

class FPSApp:
    # Minecraft-like player dimensions
    PLAYER_HEIGHT = 1.5  # Total height (like Minecraft)
    PLAYER_WIDTH = 0.6   # Width (like Minecraft)
    EYE_HEIGHT = 1.3     # Camera/eye position (like Minecraft)

    def __init__(self, root):
        self.root = root
        self.root.title("Untitled Game Engine")

        # Enable double buffering
        self.root.update_idletasks()
        self.root.attributes('-alpha', 1.0)

        # Dark style
        self.dark_bg = "#000000"
        self.light_fg = "#eee"
        style = ttk.Style(root)
        root.configure(bg=self.dark_bg)
        style.theme_use('alt')
        for cls in ('TFrame','TLabel','TScale','TButton'):
            style.configure(cls, background=self.dark_bg, foreground=self.light_fg)
        style.map('TButton', background=[('active', self.dark_bg)])
        
        # Settings variables
        self.rot_sens = tk.DoubleVar(value=0.04)
        self.move_speed = tk.DoubleVar(value=0.1)
        self.gravity = tk.DoubleVar(value=0.007)
        self.jump_strength = tk.DoubleVar(value=0.15)
        self.fov = tk.DoubleVar(value=1.0)
        self.bg_color = self.dark_bg
        
        # Performance settings
        self.target_fps = 60
        self.frame_time = 1.0 / self.target_fps
        self.last_frame = 0
        self.frame_count = 0
        self.last_fps_update = 0
        self.current_fps = 0
        
        # Pre-calculate cube vertices for each cube
        self.cube_cache = {}

        # Layout: canvas + control panel
        container = ttk.Frame(root)
        container.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(container, width=WIDTH, height=HEIGHT, bg=self.bg_color, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.panel = ttk.Frame(container, width=220)
        self.panel.grid(row=0, column=1, sticky="ns", padx=10, pady=10)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        self._build_panel()

        # Player state
        self.pos = [5,5,5]
        self.vel = [0,0,0]
        self.rot_y = math.pi
        self.rot_x = 0
        self.keys = set()
        self.last = time.time()
        self.fps = 0

        self.cubes = [
            (0,0,0),(3,0,0),(-3,0,0),(2,1.5,2),
        ]

        root.bind("<KeyPress>", self._on_key)
        root.bind("<KeyRelease>", self._on_key_release)
        self._loop()

    def _build_panel(self):
        def add_slider(label, var, frm, to, resolution=0.001):
            ttk.Label(self.panel, text=label).pack(anchor='w', pady=(10,0))
            ttk.Scale(self.panel, from_=frm, to=to, variable=var, orient='horizontal').pack(fill='x')

        add_slider("Rotation Sensitivity", self.rot_sens, 0.01, 0.2)
        add_slider("Move Speed", self.move_speed, 0.01, 0.5)
        add_slider("Gravity", self.gravity, 0.001, 0.02)
        add_slider("Jump Strength", self.jump_strength, 0.05, 1.0)
        add_slider("FOV Zoom Scale", self.fov, 0.5, 2.0)
        ttk.Button(self.panel, text="Skybox Color", command=self._choose_color, takefocus=False).pack(fill='x', pady=(20,0))

    def _choose_color(self):
        c = colorchooser.askcolor(title="Sky Color")[1]
        if c:
            self.bg_color = c
            self.canvas.config(bg=c)

    def _on_key(self, e): self.keys.add(e.keysym.lower())
    def _on_key_release(self, e): self.keys.discard(e.keysym.lower())

    def _collides(self, pos):
        px, py, pz = pos
        hw = self.PLAYER_WIDTH / 2  # Half width
        
        # Note: py is at eye level, so we need to check the full body below it
        feet_y = py - self.EYE_HEIGHT  # Convert eye level to feet position
        head_y = feet_y + self.PLAYER_HEIGHT

        # Check collision with each cube
        for cx, cy, cz in self.cubes:
            # Check X overlap
            if abs(px - cx) > (0.5 + hw): continue
            # Check Y overlap (from feet to head)
            if feet_y >= cy + 0.5 or head_y <= cy - 0.5: continue
            # Check Z overlap
            if abs(pz - cz) > (0.5 + hw): continue
            
            return True
        return False

    def _check_ground(self):
        # Convert eye position to feet position
        feet_y = self.pos[1] - self.EYE_HEIGHT
        
        if feet_y <= 0:  # Check world floor
            return True

        # Check for cubes below feet
        for cx, cy, cz in self.cubes:
            if (abs(self.pos[0] - cx) <= 0.5 + self.PLAYER_WIDTH/2 and
                abs(self.pos[2] - cz) <= 0.5 + self.PLAYER_WIDTH/2 and
                abs(feet_y - (cy + 0.5)) < 0.1):  # Small threshold for ground detection
                return True
        return False

    def _update(self, dt):
        rs = self.rot_sens.get()
        ms = self.move_speed.get()
        g = self.gravity.get()
        j = self.jump_strength.get()
        vx = vz = 0

        # Movement and rotation
        if 'left' in self.keys: self.rot_y += rs
        if 'right' in self.keys: self.rot_y -= rs
        if 'up' in self.keys: self.rot_x = min(math.pi/2, self.rot_x+rs)
        if 'down' in self.keys: self.rot_x = max(-math.pi/2, self.rot_x-rs)

        sy, cy = math.sin(self.rot_y), math.cos(self.rot_y)
        if 'w' in self.keys: vx -= sy*ms; vz += cy*ms
        if 's' in self.keys: vx += sy*ms; vz -= cy*ms
        if 'a' in self.keys: vx -= cy*ms; vz -= sy*ms
        if 'd' in self.keys: vx += cy*ms; vz += sy*ms

        # Try X movement
        if not self._collides([self.pos[0]+vx, self.pos[1], self.pos[2]]):
            self.pos[0] += vx
            
        # Try Z movement
        if not self._collides([self.pos[0], self.pos[1], self.pos[2]+vz]):
            self.pos[2] += vz

        # Ground check
        on_ground = self._check_ground()

        # Jump only when on ground
        if 'space' in self.keys and on_ground:
            self.vel[1] = j

        # Apply gravity
        self.vel[1] -= g

        # Try vertical movement
        new_pos = [self.pos[0], self.pos[1]+self.vel[1], self.pos[2]]
        if not self._collides(new_pos):
            self.pos[1] += self.vel[1]
        else:
            # If we hit something, stop vertical movement
            self.vel[1] = 0
            
            # If we're falling, place us on top of the block
            if self.vel[1] < 0:
                # Find the highest cube we're colliding with
                max_y = -float('inf')
                for cx, cy, cz in self.cubes:
                    if (abs(self.pos[0] - cx) <= 0.5 + self.PLAYER_WIDTH/2 and
                        abs(self.pos[2] - cz) <= 0.5 + self.PLAYER_WIDTH/2):
                        cube_top = cy + 0.5
                        if cube_top > max_y:
                            max_y = cube_top
                
                if max_y > -float('inf'):
                    # Position the eyes at the correct height above the surface
                    self.pos[1] = max_y + self.EYE_HEIGHT

        # World floor collision
        feet_y = self.pos[1] - self.EYE_HEIGHT
        if feet_y < 0:
            self.pos[1] = self.EYE_HEIGHT  # Place eyes at correct height above ground
            self.vel[1] = 0

    def _to_camera(self, pt):
        dx,dy,dz = pt[0]-self.pos[0], pt[1]-self.pos[1], pt[2]-self.pos[2]
        sy, cy = math.sin(self.rot_y), math.cos(self.rot_y)
        x = cy*dx + sy*dz
        z = -sy*dx + cy*dz
        sx, cx = math.sin(self.rot_x), math.cos(self.rot_x)
        y = cx*dy - sx*z
        z = sx*dy + cx*z
        return (x,y,z)

    def _update_cube_cache(self):
        # Update cached projections if FOV changed
        current_fov = self.fov.get()
        if not hasattr(self, '_last_fov') or self._last_fov != current_fov:
            self.cube_cache.clear()
            self._last_fov = current_fov

    def _draw(self):
        now = time.time()
        
        # Control frame rate
        if now - self.last_frame < self.frame_time:
            return
        
        # Update FPS counter
        self.frame_count += 1
        if now - self.last_fps_update >= 1.0:
            self.current_fps = self.frame_count / (now - self.last_fps_update)
            self.frame_count = 0
            self.last_fps_update = now
        
        self.last_frame = now
        
        # Clear canvas efficiently
        self.canvas.delete("all")
        
        # Update cube cache if needed
        self._update_cube_cache()
        
        factor = 400
        fov = self.fov.get()
        
        # Sort cubes by distance for proper rendering order
        sorted_cubes = sorted(
            [(cube, sum((c-p)**2 for c, p in zip(cube, self.pos))) 
             for cube in self.cubes],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Render cubes
        for cube, _ in sorted_cubes:
            cache_key = (cube[0], cube[1], cube[2], self.pos[0], self.pos[1], self.pos[2])
            
            if cache_key not in self.cube_cache:
                # Calculate new projections
                pts = [self._to_camera((v[0]+cube[0], v[1]+cube[1], v[2]+cube[2])) for v in vertices]
                pts2 = [project(p, factor, fov) if p[2]>0.05 else None for p in pts]
                self.cube_cache[cache_key] = pts2
            else:
                pts2 = self.cube_cache[cache_key]
            
            # Draw faces
            for face in faces:
                face_pts = [pts2[i] for i in face]
                if all(p is not None for p in face_pts):
                    flat = [coord for p in face_pts for coord in p]
                    self.canvas.create_polygon(flat, fill='white', outline=self.light_fg, width=2, stipple='')

        # Display info
        info = (
            f"FPS: {self.current_fps:.1f}    "
            f"Pos: {self.pos[0]:.1f},{self.pos[1]:.1f},{self.pos[2]:.1f}    "
            f"Rot Y:{math.degrees(self.rot_y):.0f}° X:{math.degrees(self.rot_x):.0f}°"
        )
        self.canvas.create_text(10,10,anchor='nw',fill=self.light_fg,font=('Consolas',12),text=info)

    def _loop(self):
        current_time = time.time()
        dt = current_time - self.last
        self.last = current_time

        self._update(dt)
        self._draw()
        
        # Schedule next frame
        delay = int(max(1, (self.frame_time - (time.time() - current_time)) * 1000))
        self.root.after(delay, self._loop)

if __name__ == '__main__':
    FPSApp(tk.Tk()).root.mainloop()
