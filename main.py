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

def project(point, size, fov, distance=0.1):
    x,y,z = point
    if distance + z == 0:
        return None
    factor = size * fov / (distance + z)
    return (x*factor + CENTER_X, -y*factor + CENTER_Y)

class FPSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern FPS Engine")

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
        self.fps = 0.0

        self.cubes = [
            (0,0,0),(3,0,0),(-3,0,0),(5,5,5),
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

    def _update(self, dt):
        rs = self.rot_sens.get()
        ms = self.move_speed.get()
        g = self.gravity.get()
        j = self.jump_strength.get()
        vx = vz = 0

        if 'left' in self.keys: self.rot_y += rs
        if 'right' in self.keys: self.rot_y -= rs
        if 'up' in self.keys: self.rot_x = min(math.pi/2, self.rot_x+rs)
        if 'down' in self.keys: self.rot_x = max(-math.pi/2, self.rot_x-rs)

        sy, cy = math.sin(self.rot_y), math.cos(self.rot_y)
        if 'w' in self.keys: vx -= sy*ms; vz += cy*ms
        if 's' in self.keys: vx += sy*ms; vz -= cy*ms
        if 'a' in self.keys: vx -= cy*ms; vz -= sy*ms
        if 'd' in self.keys: vx += cy*ms; vz += sy*ms

        if 'space' in self.keys and self.pos[1] <= 0.001 and self.vel[1] == 0:
            self.vel[1] = j

        self.vel[1] -= g
        self.pos[1] += self.vel[1]
        if self.pos[1] < 0:
            self.pos[1] = 0
            self.vel[1] = 0

        self.pos[0] += vx
        self.pos[2] += vz

    def _to_camera(self, pt):
        dx,dy,dz = pt[0]-self.pos[0], pt[1]-self.pos[1], pt[2]-self.pos[2]
        sy, cy = math.sin(self.rot_y), math.cos(self.rot_y)
        x = cy*dx + sy*dz
        z = -sy*dx + cy*dz
        sx, cx = math.sin(self.rot_x), math.cos(self.rot_x)
        y = cx*dy - sx*z
        z = sx*dy + cx*z
        return (x,y,z)

    def _draw(self):
        self.canvas.delete("all")
        factor = 400
        for cube in self.cubes:
            pts = [self._to_camera((v[0]+cube[0], v[1]+cube[1], v[2]+cube[2])) for v in vertices]
            pts2 = [project(p, factor, self.fov.get()) if p[2]>0.05 else None for p in pts]
            for a,b in edges:
                p1,p2 = pts2[a], pts2[b]
                if p1 and p2:
                    self.canvas.create_line(p1[0],p1[1],p2[0],p2[1], fill=self.light_fg, width=2)

        info = (
            f"FPS: {self.fps:.1f}    "
            f"Pos: {self.pos[0]:.1f},{self.pos[1]:.1f},{self.pos[2]:.1f}    "
            f"Rot Y:{math.degrees(self.rot_y):.0f}° X:{math.degrees(self.rot_x):.0f}    "
            f"Keys:{''.join(sorted(self.keys))}    "
            f"FOV Zoom:{self.fov.get():.2f}    "
            f"Vel:{self.vel[0]:.2f},{self.vel[1]:.2f},{self.vel[2]:.2f}    "
        )
        self.canvas.create_text(10,10,anchor='nw',fill=self.light_fg,font=('Consolas',12),text=info)

    def _loop(self):
        now = time.time()
        dt = now - self.last
        self.last = now
        self.fps = 1/dt if dt>0 else self.fps

        self._update(dt)
        self._draw()
        self.root.after(16, self._loop)

if __name__ == '__main__':
    FPSApp(tk.Tk()).root.mainloop()
