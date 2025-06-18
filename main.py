import tkinter as tk
from tkinter import ttk
import math, time
from collections import defaultdict

# — Window & projection setup —
WIDTH, HEIGHT = 1280, 960
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2

# Cube geometry (moved to class level to avoid global variables)
class CubeGeometry:
    vertices = [
        (-0.5, -0.5, -0.5), (-0.5, -0.5,  0.5),
        (-0.5,  0.5, -0.5), (-0.5,  0.5,  0.5),
        ( 0.5, -0.5, -0.5), ( 0.5, -0.5,  0.5),
        ( 0.5,  0.5, -0.5), ( 0.5,  0.5,  0.5),
    ]
    faces = [
        (0,1,3,2), (4,5,7,6), (0,1,5,4), (2,3,7,6), (0,2,6,4), (1,3,7,5)
    ]
    face_normals = [
        (-1,0,0), (1,0,0), (0,-1,0), (0,1,0), (0,0,-1), (0,0,1)
    ]

def project(point, size, fov, distance=0.001):
    x,y,z = point
    if distance + z <= 0.001:  # Avoid division by near-zero
        return None
    factor = size * fov / (distance + z)
    return (x*factor + CENTER_X, -y*factor + CENTER_Y)

class FPSApp:
    PLAYER_HEIGHT = 1.5
    PLAYER_WIDTH = 0.6
    EYE_HEIGHT = 1.3
    TICK_RATE = 12  # Physics updates per second
    MAX_FPS = 60    # Maximum render FPS
    FRAME_TIME = 1.0 / MAX_FPS
    DEFAULT_RENDER_DISTANCE = 20.0  # Default render distance in game units

    def __init__(self, root):
        self.root = root
        self.root.title("PyCGE | Sample 3D Engine")

        # Variables
        self.light_fg = "#eee"
        self.rot_sens = tk.DoubleVar(value=0.075)
        self.move_speed = tk.DoubleVar(value=0.1)
        self.gravity = tk.DoubleVar(value=0.007)
        self.jump_strength = tk.DoubleVar(value=0.15)
        self.fov = tk.DoubleVar(value=1.0)
        self.render_distance = tk.DoubleVar(value=self.DEFAULT_RENDER_DISTANCE)

        # Layout setup
        container = ttk.Frame(root)
        container.pack(fill="both", expand=True)
        
        # Setup canvas with fixed dark background
        self.canvas = tk.Canvas(container, width=WIDTH, height=HEIGHT, 
                              bg="#080808", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Setup control panel
        self.panel = ttk.Frame(container, width=220)
        self.panel.grid(row=0, column=1, sticky="ns", padx=10, pady=10)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        
        # Setup dark theme
        style = ttk.Style(root)
        style.theme_use('alt')
        for cls in ('TFrame','TLabel','TScale'):
            style.configure(cls, background="#080808", foreground=self.light_fg)
        
        self._build_panel()

        # Game state
        self.pos = [5,5,5]
        self.vel = [0,0,0]
        self.rot_y = math.pi
        self.rot_x = 0
        self.keys = set()
        
        # Performance tracking
        self.last_tick = self.last_frame = time.time()
        self.fps = 0
        self.accumulated_time = 0
        self.tick_delta = 1.0 / self.TICK_RATE

        # Cache for sin/cos calculations
        self.sin_y = math.sin(self.rot_y)
        self.cos_y = math.cos(self.rot_y)
        self.sin_x = math.sin(self.rot_x)
        self.cos_x = math.cos(self.rot_x)

        # World setup
        self.cubes = [(0,0,0),(3,0,0),(-3,0,0),(2,1.5,2)]
        self.cube_grid = defaultdict(list)
        self._update_spatial_grid()

        # Bind events
        root.bind("<KeyPress>", self._on_key)
        root.bind("<KeyRelease>", self._on_key_release)
        self._game_loop()

    def _build_panel(self):
        def add_slider(label, var, frm, to, resolution=0.001):
            ttk.Label(self.panel, text=label).pack(anchor='w', pady=(10,0))
            ttk.Scale(self.panel, from_=frm, to=to, variable=var, orient='horizontal').pack(fill='x')

        add_slider("Rotation Sensitivity", self.rot_sens, 0.01, 0.2)
        add_slider("Move Speed", self.move_speed, 0.01, 0.5)
        add_slider("Gravity", self.gravity, 0.001, 0.02)
        add_slider("Jump Strength", self.jump_strength, 0.05, 1.0)
        add_slider("FOV Zoom Scale", self.fov, 0.5, 2.0)
        add_slider("Render Distance", self.render_distance, 5.0, 50.0, 1.0)

    def _update_spatial_grid(self):
        self.cube_grid.clear()
        for cube in self.cubes:
            grid_x = int(cube[0] // 2)
            grid_z = int(cube[2] // 2)
            self.cube_grid[(grid_x, grid_z)].append(cube)

    def _get_nearby_cubes(self, for_rendering=False):
        grid_x = int(self.pos[0] // 2)
        grid_z = int(self.pos[2] // 2)
        nearby = []
        render_dist = self.render_distance.get() if for_rendering else 4  # Use smaller radius for physics
        grid_radius = int(render_dist // 2)
        
        for dx in range(-grid_radius, grid_radius + 1):
            for dz in range(-grid_radius, grid_radius + 1):
                cubes = self.cube_grid.get((grid_x + dx, grid_z + dz), [])
                if for_rendering:
                    # Filter by actual distance for rendering
                    for cube in cubes:
                        dist = math.sqrt((cube[0]-self.pos[0])**2 + (cube[2]-self.pos[2])**2)
                        if dist <= render_dist:
                            nearby.append(cube)
                else:
                    nearby.extend(cubes)
        return nearby

    def _on_key(self, e): self.keys.add(e.keysym.lower())
    def _on_key_release(self, e): self.keys.discard(e.keysym.lower())

    def _collides(self, pos):
        px, py, pz = pos
        hw = self.PLAYER_WIDTH / 2
        feet_y = py - self.EYE_HEIGHT
        head_y = feet_y + self.PLAYER_HEIGHT

        # Only check nearby cubes using spatial partitioning
        for cx, cy, cz in self._get_nearby_cubes():
            if (abs(px - cx) <= (0.5 + hw) and
                feet_y < cy + 0.5 and head_y > cy - 0.5 and
                abs(pz - cz) <= (0.5 + hw)):
                return True
        return False

    def _check_ground(self):
        feet_y = self.pos[1] - self.EYE_HEIGHT
        if feet_y <= 0:
            return True

        for cx, cy, cz in self._get_nearby_cubes():
            if (abs(self.pos[0] - cx) <= 0.5 + self.PLAYER_WIDTH/2 and
                abs(self.pos[2] - cz) <= 0.5 + self.PLAYER_WIDTH/2 and
                abs(feet_y - (cy + 0.5)) < 0.1):
                return True
        return False

    def _update_rotation_cache(self):
        self.sin_y = math.sin(self.rot_y)
        self.cos_y = math.cos(self.rot_y)
        self.sin_x = math.sin(self.rot_x)
        self.cos_x = math.cos(self.rot_x)

    def _update(self):
        rs = self.rot_sens.get()
        ms = self.move_speed.get()
        g = self.gravity.get()
        j = self.jump_strength.get()
        vx = vz = 0

        if 'left' in self.keys: self.rot_y += rs
        if 'right' in self.keys: self.rot_y -= rs
        if 'up' in self.keys: self.rot_x = min(math.pi/2, self.rot_x+rs)
        if 'down' in self.keys: self.rot_x = max(-math.pi/2, self.rot_x-rs)

        self._update_rotation_cache()

        if 'w' in self.keys: vx -= self.sin_y*ms; vz += self.cos_y*ms
        if 's' in self.keys: vx += self.sin_y*ms; vz -= self.cos_y*ms
        if 'a' in self.keys: vx -= self.cos_y*ms; vz -= self.sin_y*ms
        if 'd' in self.keys: vx += self.cos_y*ms; vz += self.sin_y*ms

        if not self._collides([self.pos[0]+vx, self.pos[1], self.pos[2]]):
            self.pos[0] += vx
        if not self._collides([self.pos[0], self.pos[1], self.pos[2]+vz]):
            self.pos[2] += vz

        on_ground = self._check_ground()
        if 'space' in self.keys and on_ground:
            self.vel[1] = j

        self.vel[1] -= g
        new_pos = [self.pos[0], self.pos[1]+self.vel[1], self.pos[2]]
        
        if not self._collides(new_pos):
            self.pos[1] += self.vel[1]
        else:
            self.vel[1] = 0
            if self.vel[1] < 0:
                max_y = -float('inf')
                for cx, cy, cz in self._get_nearby_cubes():
                    if (abs(self.pos[0] - cx) <= 0.5 + self.PLAYER_WIDTH/2 and
                        abs(self.pos[2] - cz) <= 0.5 + self.PLAYER_WIDTH/2):
                        cube_top = cy + 0.5
                        if cube_top > max_y:
                            max_y = cube_top
                if max_y > -float('inf'):
                    self.pos[1] = max_y + self.EYE_HEIGHT

        feet_y = self.pos[1] - self.EYE_HEIGHT
        if feet_y < 0:
            self.pos[1] = self.EYE_HEIGHT
            self.vel[1] = 0

    def _to_camera(self, pt):
        dx,dy,dz = pt[0]-self.pos[0], pt[1]-self.pos[1], pt[2]-self.pos[2]
        x = self.cos_y*dx + self.sin_y*dz
        z = -self.sin_y*dx + self.cos_y*dz
        y = self.cos_x*dy - self.sin_x*z
        z = self.sin_x*dy + self.cos_x*z
        return (x,y,z)

    def _is_face_visible(self, cube_pos, face_idx):
        # Check if face normal points towards camera
        normal = CubeGeometry.face_normals[face_idx]
        dx = self.pos[0] - (cube_pos[0] + normal[0] * 0.5)
        dy = self.pos[1] - (cube_pos[1] + normal[1] * 0.5)
        dz = self.pos[2] - (cube_pos[2] + normal[2] * 0.5)
        return dx*normal[0] + dy*normal[1] + dz*normal[2] > 0

    def _draw(self):
        self.canvas.delete("all")
        factor = 400
        fov = self.fov.get()
        
        # Sort cubes by distance for proper occlusion
        visible_cubes = [(cube, sum((x-p)**2 for x,p in zip(cube, self.pos))) 
                        for cube in self._get_nearby_cubes(for_rendering=True)]
        visible_cubes.sort(key=lambda x: -x[1])  # Sort back to front

        for cube, _ in visible_cubes:
            pts = [self._to_camera((v[0]+cube[0], v[1]+cube[1], v[2]+cube[2])) 
                  for v in CubeGeometry.vertices]
            pts2 = [project(p, factor, fov) if p[2]>0.05 else None for p in pts]
            
            # Only draw visible faces (occlusion culling)
            for face_idx, face in enumerate(CubeGeometry.faces):
                if self._is_face_visible(cube, face_idx):
                    face_pts = [pts2[i] for i in face]
                    if all(p is not None for p in face_pts):
                        flat = [coord for p in face_pts for coord in p]
                        self.canvas.create_polygon(flat, fill='white', outline=self.light_fg, width=2)

        # Display performance metrics
        info = (
            f"FPS: {self.fps:.1f}      "
            f"Pos: {self.pos[0]:.1f},{self.pos[1]:.1f},{self.pos[2]:.1f}      "
            f"Rot Y:{math.degrees(self.rot_y):.0f}° X:{math.degrees(self.rot_x):.0f}°      "
            f"Render Dist: {self.render_distance.get():.1f}    "
            f"FOV: {self.fov.get():.2f}      "
            f"Gravity: {self.gravity.get():.3f}      "
            f"Jump: {self.jump_strength.get():.2f}      "
            f"Move Speed: {self.move_speed.get():.2f}      "
            f"Rot Sens: {self.rot_sens.get():.3f}      "
        )
        self.canvas.create_text(10,10,anchor='nw',fill=self.light_fg,font=('Consolas',12),text=info)

    def _game_loop(self):
        current_time = time.time()
        frame_time = current_time - self.last_frame
        
        # Update game state at fixed time steps
        self.accumulated_time += frame_time
        while self.accumulated_time >= self.tick_delta:
            self._update()
            self.accumulated_time -= self.tick_delta

        # Limit frame rate
        if frame_time >= self.FRAME_TIME:
            self._draw()
            self.fps = 1.0 / frame_time
            self.last_frame = current_time

        self.root.after(1, self._game_loop)

if __name__ == '__main__':
    root = tk.Tk()
    app = FPSApp(root)
    root.mainloop()
