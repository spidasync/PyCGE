
import tkinter as tk
import math
import time

# Window and center setup
WIDTH, HEIGHT = 1280, 720
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2

# Cube geometry
vertices = [
    [-0.5, -0.5, -0.5],
    [-0.5, -0.5,  0.5],
    [-0.5,  0.5, -0.5],
    [-0.5,  0.5,  0.5],
    [ 0.5, -0.5, -0.5],
    [ 0.5, -0.5,  0.5],
    [ 0.5,  0.5, -0.5],
    [ 0.5,  0.5,  0.5],
]

edges = [
    (0,1), (1,3), (3,2), (2,0),
    (4,5), (5,7), (7,6), (6,4),
    (0,4), (1,5), (2,6), (3,7)
]

def project(point, size=400, distance=3):
    x, y, z = point
    if distance + z == 0:
        return None
    factor = size / (distance + z)
    x_proj = x * factor + CENTER_X
    y_proj = -y * factor + CENTER_Y
    return (x_proj, y_proj)

class FPSApp:
    def __init__(self, master):
        self.master = master
        self.canvas = tk.Canvas(master, width=WIDTH, height=HEIGHT, bg="black")
        self.canvas.pack()

        self.pos = [0, 0, 5]        # Player start position
        self.vel = [0, 0, 0]        # Velocity
        self.rot_y = math.pi        # Face the cubes (180°)
        self.rot_x = 0              # Pitch
        self.keys = set()

        self.last_time = time.time()
        self.fps = 0

        self.cubes = [
            [0, 0, 0],
            [3, 0, 0],
            [-3, 0, 0],
            [0, 0, 3],
            [0, 0, -3],
            [3, 0, 3],
            [-3, 0, -3]
        ]

        master.bind("<KeyPress>", self.on_key_press)
        master.bind("<KeyRelease>", self.on_key_release)

        self.animate()

    def on_key_press(self, event):
        self.keys.add(event.keysym.lower())

    def on_key_release(self, event):
        self.keys.discard(event.keysym.lower())

    def update(self):
        rot_speed = 0.04
        move_speed = 0.1
        gravity = 0.007
        jump_strength = 0.15

        vx = vz = 0

        # Handle rotation
        if 'left' in self.keys:
            self.rot_y += rot_speed
        if 'right' in self.keys:
            self.rot_y -= rot_speed
        if 'up' in self.keys:
            self.rot_x = min(math.pi/2, self.rot_x + rot_speed)
        if 'down' in self.keys:
            self.rot_x = max(-math.pi/2, self.rot_x - rot_speed)

        sin_y = math.sin(self.rot_y)
        cos_y = math.cos(self.rot_y)

        # Horizontal movement
        if 'w' in self.keys:
            vx -= sin_y * move_speed
            vz += cos_y * move_speed
        if 's' in self.keys:
            vx += sin_y * move_speed
            vz -= cos_y * move_speed
        if 'a' in self.keys:
            vx -= cos_y * move_speed
            vz -= sin_y * move_speed
        if 'd' in self.keys:
            vx += cos_y * move_speed
            vz += sin_y * move_speed

        # Jump (only if grounded)
        if 'space' in self.keys and self.pos[1] <= 0.001 and self.vel[1] == 0:
            self.vel[1] = jump_strength

        # Gravity and vertical velocity
        self.vel[1] -= gravity
        self.pos[1] += self.vel[1]
        if self.pos[1] < 0:
            self.pos[1] = 0
            self.vel[1] = 0

        # Apply horizontal velocity
        self.vel[0] = vx
        self.vel[2] = vz
        self.pos[0] += vx
        self.pos[2] += vz

    def world_to_camera(self, point):
        dx = point[0] - self.pos[0]
        dy = point[1] - self.pos[1]
        dz = point[2] - self.pos[2]

        sin_y = math.sin(self.rot_y)
        cos_y = math.cos(self.rot_y)
        xz_x = cos_y * dx + sin_y * dz
        xz_z = -sin_y * dx + cos_y * dz

        sin_x = math.sin(self.rot_x)
        cos_x = math.cos(self.rot_x)
        yz_y = cos_x * dy - sin_x * xz_z
        yz_z = sin_x * dy + cos_x * xz_z

        return [xz_x, yz_y, yz_z]

    def draw_debug_text(self):
        text = f"FPS: {self.fps:.1f}\n"
        text += f"Pos: {self.pos[0]:.2f}, {self.pos[1]:.2f}, {self.pos[2]:.2f}\n"
        text += f"Vel: {self.vel[0]:.2f}, {self.vel[1]:.2f}, {self.vel[2]:.2f}"
        self.canvas.create_text(10, 10, anchor='nw', fill='white', font=('Courier', 12), text=text)

    def animate(self):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        if dt > 0:
            self.fps = 1 / dt

        self.canvas.delete("all")
        self.update()

        for cube_pos in self.cubes:
            transformed = []
            for v in vertices:
                cam_coords = self.world_to_camera([
                    v[0] + cube_pos[0],
                    v[1] + cube_pos[1],
                    v[2] + cube_pos[2]
                ])
                transformed.append(cam_coords)

            points_2d = []
            for p in transformed:
                if p[2] <= 0.05:
                    points_2d.append(None)
                else:
                    points_2d.append(project(p))

            for edge in edges:
                p1 = points_2d[edge[0]]
                p2 = points_2d[edge[1]]
                if p1 and p2:
                    self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="white", width=2)

        self.draw_debug_text()
        self.master.after(16, self.animate)

# Run the app
root = tk.Tk()
root.title("Untitled Game Engine")
app = FPSApp(root)
root.mainloop()
