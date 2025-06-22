import tkinter as tk
from tkinter import colorchooser, messagebox
import json

class LevelEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PyCGE Level Editor")
        self.geometry("1500x900")
        self.configure(bg="#181818")
        self.bg_color = "#222222"
        self.snap_value = 10
        self.current_shape = tk.StringVar(value="platform")
        self.current_color = "#FF0000"
        self.platforms = []
        self.objects = []
        self.player_spawn = None
        self.selected_index = None
        self.rect_start = None
        self.temp_rect = None
        self.temp_oval = None
        self.temp_line = None
        self.collider_enabled = tk.BooleanVar(value=True)
        self.selected_item = None  # Will store (index, kind) of selected item
        self._build_ui()
        self._bind_events()

    def _build_ui(self):
        # Toolbar
        toolbar = tk.Frame(self, bg="#181818", height=50, highlightbackground="#cccccc", highlightthickness=1)
        toolbar.pack(fill=tk.X, side=tk.TOP)
        font = ("Consolas", 12)
        tk.Label(toolbar, text="Shape:", bg="#181818", fg="#fff", font=font).pack(side=tk.LEFT, padx=5)
        for shape in ["platform", "player", "oval", "line", "object", "select"]:
            tk.Radiobutton(toolbar, text=shape.capitalize(), variable=self.current_shape, value=shape, bg="#181818", fg="#fff", selectcolor="#444", font=font, activebackground="#181818").pack(side=tk.LEFT)
        # Object Prefab Dropdown
        tk.Label(toolbar, text="Object Prefab:", bg="#181818", fg="#fff", font=font).pack(side=tk.LEFT, padx=(20, 2))
        self.object_prefab = tk.StringVar(value="crate")
        object_options = ["crate", "coin", "enemy", "custom"]
        object_menu = tk.OptionMenu(toolbar, self.object_prefab, *object_options)
        object_menu.config(bg="#222", fg="#fff", font=font, activebackground="#333")
        object_menu['menu'].config(bg="#222", fg="#fff", font=font)
        object_menu.pack(side=tk.LEFT, padx=2)
        # Event Prefab Dropdown
        tk.Label(toolbar, text="Event Prefab:", bg="#181818", fg="#fff", font=font).pack(side=tk.LEFT, padx=(20, 2))
        self.event_prefab = tk.StringVar(value="player_spawn")
        event_options = ["player_spawn", "checkpoint", "trigger"]
        event_menu = tk.OptionMenu(toolbar, self.event_prefab, *event_options)
        event_menu.config(bg="#222", fg="#fff", font=font, activebackground="#333")
        event_menu['menu'].config(bg="#222", fg="#fff", font=font)
        event_menu.pack(side=tk.LEFT, padx=2)
        # Color button
        tk.Button(toolbar, text="Color", command=self.choose_color, bg="#222", fg="#fff", font=font, activebackground="#333").pack(side=tk.LEFT, padx=5)
        tk.Label(toolbar, text="Snap:", bg="#181818", fg="#fff", font=font).pack(side=tk.LEFT, padx=5)
        self.snap_entry = tk.Entry(toolbar, width=4, font=font, bg="#222", fg="#fff", insertbackground="#fff")
        self.snap_entry.insert(0, str(self.snap_value))
        self.snap_entry.pack(side=tk.LEFT)
        tk.Button(toolbar, text="Set Snap", command=self.set_snap, bg="#222", fg="#fff", font=font, activebackground="#333").pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="BG Color", command=self.choose_bg_color, bg="#222", fg="#fff", font=font, activebackground="#333").pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Save", command=self.save_level, bg="#228B22", fg="#fff", font=font, activebackground="#2ecc71").pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Load", command=self.load_level, bg="#1E90FF", fg="#fff", font=font, activebackground="#3498db").pack(side=tk.LEFT, padx=5)
        self.color_preview = tk.Label(toolbar, bg=self.current_color, width=4)
        self.color_preview.pack(side=tk.LEFT, padx=5)
        self.bg_preview = tk.Label(toolbar, bg=self.bg_color, width=4)
        self.bg_preview.pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(toolbar, text="Collider", variable=self.collider_enabled, bg="#181818", fg="#fff", font=font, selectcolor="#444").pack(side=tk.LEFT, padx=10)

        # Main layout
        main_frame = tk.Frame(self, bg="#0f0f0f")
        main_frame.pack(fill=tk.BOTH, expand=True)
        # Hierarchy panel
        hierarchy_frame = tk.Frame(main_frame, bg="#181818", width=250, highlightbackground="#cccccc", highlightthickness=1)
        hierarchy_frame.pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(hierarchy_frame, text="Hierarchy", bg="#181818", fg="#fff", font=("Consolas", 14, "bold")).pack(pady=10)
        self.hierarchy_list = tk.Listbox(hierarchy_frame, bg="#0f0f0f", fg="#fff", font=font, selectbackground="#444", activestyle='none', highlightthickness=0, borderwidth=0)
        self.hierarchy_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.hierarchy_list.bind('<<ListboxSelect>>', self.on_hierarchy_select)
        self.hierarchy_list.bind('<Delete>', self.on_hierarchy_delete)
        self.hierarchy_list.bind('<BackSpace>', self.on_hierarchy_delete)
        self.hierarchy_list.focus_set()
        # Canvas with border
        canvas_frame = tk.Frame(main_frame, bg="#0f0f0f", highlightbackground="#cccccc", highlightthickness=1)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.canvas = tk.Canvas(canvas_frame, bg=self.bg_color, width=1200, height=800, highlightthickness=0, borderwidth=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add properties panel
        properties_frame = tk.Frame(main_frame, bg="#181818", width=250, highlightbackground="#cccccc", highlightthickness=1)
        properties_frame.pack(side=tk.RIGHT, fill=tk.Y)
        tk.Label(properties_frame, text="Properties", bg="#181818", fg="#fff", font=("Consolas", 14, "bold")).pack(pady=10)
        
        # Properties content
        self.properties_content = tk.Frame(properties_frame, bg="#181818")
        self.properties_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initially hide properties
        self.clear_properties()

    def clear_properties(self):
        for widget in self.properties_content.winfo_children():
            widget.destroy()
        tk.Label(self.properties_content, text="No object selected", bg="#181818", fg="#888", font=("Consolas", 12)).pack(pady=20)

    def show_properties(self, item_index, kind):
        for widget in self.properties_content.winfo_children():
            widget.destroy()
        
        font = ("Consolas", 12)
        item = None
        if kind == 'platform':
            item = self.platforms[item_index]
        elif kind == 'object':
            item = self.objects[item_index]
        
        if not item:
            return
        
        # Color picker
        color_frame = tk.Frame(self.properties_content, bg="#181818")
        color_frame.pack(fill=tk.X, pady=5)
        tk.Label(color_frame, text="Color:", bg="#181818", fg="#fff", font=font).pack(side=tk.LEFT, padx=5)
        color_preview = tk.Label(color_frame, bg=item.get('color', '#FF0000'), width=4)
        color_preview.pack(side=tk.LEFT, padx=5)
        
        def update_color():
            color = colorchooser.askcolor(title="Choose color", initialcolor=item.get('color', '#FF0000'))[1]
            if color:
                item['color'] = color
                color_preview.config(bg=color)
                self.redraw_canvas()
        
        tk.Button(color_frame, text="Change", command=update_color, bg="#222", fg="#fff", 
                 font=font, activebackground="#333").pack(side=tk.LEFT, padx=5)
        
        # Collider toggle
        if 'collider' in item:
            collider_var = tk.BooleanVar(value=item.get('collider', True))
            
            def update_collider():
                item['collider'] = collider_var.get()
            
            tk.Checkbutton(self.properties_content, text="Collider", variable=collider_var,
                          command=update_collider, bg="#181818", fg="#fff", font=font,
                          selectcolor="#444").pack(pady=5, anchor=tk.W)
        
        # Delete button
        def delete_item():
            if kind == 'platform':
                self.platforms.pop(item_index)
            elif kind == 'object':
                self.objects.pop(item_index)
            self.selected_item = None
            self.clear_properties()
            self.update_hierarchy()
            self.redraw_canvas()
        
        tk.Button(self.properties_content, text="Delete", command=delete_item,
                 bg="#FF4444", fg="#fff", font=font, activebackground="#CC3333").pack(pady=20)

    def choose_color(self):
        color = colorchooser.askcolor(title="Choose color", initialcolor=self.current_color)[1]
        if color:
            self.current_color = color
            self.color_preview.config(bg=color)

    def choose_bg_color(self):
        color = colorchooser.askcolor(title="Choose background color", initialcolor=self.bg_color)[1]
        if color:
            self.bg_color = color
            self.canvas.config(bg=color)
            self.bg_preview.config(bg=color)

    def set_snap(self):
        try:
            self.snap_value = int(self.snap_entry.get())
        except ValueError:
            self.snap_value = 10
            self.snap_entry.delete(0, tk.END)
            self.snap_entry.insert(0, "10")

    def snap(self, x, y):
        s = self.snap_value
        return (round(x / s) * s, round(y / s) * s)

    def update_hierarchy(self):
        self.hierarchy_list.delete(0, tk.END)
        for i, plat in enumerate(self.platforms):
            self.hierarchy_list.insert(tk.END, f"Platform {i+1}")
        for i, obj in enumerate(self.objects):
            self.hierarchy_list.insert(tk.END, f"{obj['type'].capitalize()} {i+1}")
        if self.player_spawn:
            self.hierarchy_list.insert(tk.END, "Player Spawn")

    def on_hierarchy_select(self, event):
        selection = self.hierarchy_list.curselection()
        if not selection:
            self.selected_item = None
            self.clear_properties()
            self.redraw_canvas()
            return
            
        idx = selection[0]
        plat_count = len(self.platforms)
        obj_count = len(self.objects)
        
        if idx < plat_count:
            self.select_item(idx, 'platform')
        elif idx < plat_count + obj_count:
            self.select_item(idx - plat_count, 'object')
        elif idx == plat_count + obj_count and self.player_spawn:
            self.select_item(idx, 'player')

    def on_hierarchy_delete(self, event):
        if self.selected_item:
            idx, kind = self.selected_item
            if kind == 'platform':
                self.platforms.pop(idx)
            elif kind == 'object':
                self.objects.pop(idx)
            self.selected_item = None
            self.clear_properties()
            self.update_hierarchy()
            self.redraw_canvas()

    def on_canvas_click(self, event):
        # Convert screen (canvas) coordinates to world coordinates
        zoom = getattr(self, 'zoom', 1.0)
        ox, oy = self.camera_offset
        x = (event.x - ox) / zoom
        y = (event.y - oy) / zoom
        x, y = self.snap(x, y)
        shape = self.current_shape.get()
        collider = self.collider_enabled.get()
        # Use event prefab if selected and shape is player
        if shape == "player":
            prefab = self.event_prefab.get()
            if prefab == "player_spawn":
                if self.player_spawn:
                    self.canvas.delete(self.player_spawn[2])
                size = 30
                rect = self.canvas.create_rectangle(event.x-size//2, event.y-size//2, event.x+size//2, event.y+size//2, outline="#00FF00", width=2)
                self.player_spawn = (x, y, rect)
            elif prefab == "checkpoint":
                size = 30
                self.objects.append({"type": "checkpoint", "x": x, "y": y, "width": size, "height": size, "color": "#00BFFF", "collider": False})
            elif prefab == "trigger":
                size = 30
                self.objects.append({"type": "trigger", "x": x, "y": y, "width": size, "height": size, "color": "#FFD700", "collider": False})
            self.update_hierarchy()
            return
        elif shape == "object":
            prefab = self.object_prefab.get()
            size = 40
            color = self.current_color
            obj_type = "object"
            if prefab == "crate":
                color = "#8B4513"
                obj_type = "crate"
            elif prefab == "coin":
                color = "#FFD700"
                obj_type = "coin"
            elif prefab == "enemy":
                color = "#FF2222"
                obj_type = "enemy"
            elif prefab == "custom":
                obj_type = "object"
            obj = self.canvas.create_rectangle(event.x-size//2, event.y-size//2, event.x+size//2, event.y+size//2, fill=color, outline="#FFD700", width=2)
            self.objects.append({"type": obj_type, "x": x, "y": y, "width": size, "height": size, "color": color, "collider": collider})
            self.update_hierarchy()
            return
        if shape == "select":
            idx, kind = self.find_item_at(x, y)
            if idx is not None:
                self.select_item(idx, kind)
                self.selected_drag = (kind, idx, x, y)
            else:
                self.selected_item = None
                self.selected_drag = None
                self.clear_properties()
                self.hierarchy_list.selection_clear(0, tk.END)
                self.redraw_canvas()
        elif shape == "platform":
            self.rect_start = (x, y)
            self.temp_rect = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline=self.current_color, width=2)
        elif shape == "player":
            if self.player_spawn:
                self.canvas.delete(self.player_spawn[2])
            size = 30
            rect = self.canvas.create_rectangle(event.x-size//2, event.y-size//2, event.x+size//2, event.y+size//2, outline="#00FF00", width=2)
            self.player_spawn = (x, y, rect)
        elif shape == "oval":
            self.rect_start = (x, y)
            self.temp_oval = self.canvas.create_oval(event.x, event.y, event.x, event.y, outline=self.current_color, width=2)
        elif shape == "line":
            self.rect_start = (x, y)
            self.temp_line = self.canvas.create_line(event.x, event.y, event.x, event.y, fill=self.current_color, width=2)
        elif shape == "object":
            prefab = self.selected_object_prefab.get()
            size = 40
            if prefab == "crate":
                obj = self.canvas.create_rectangle(event.x-size//2, event.y-size//2, event.x+size//2, event.y+size//2, fill=self.current_color, outline="#FFD700", width=2)
                self.objects.append({"type": "object", "x": x, "y": y, "width": size, "height": size, "color": self.current_color, "collider": collider})
            elif prefab == "coin":
                obj = self.canvas.create_oval(event.x-size//2, event.y-size//2, event.x+size//2, event.y+size//2, fill=self.current_color, outline="#FFD700", width=2)
                self.objects.append({"type": "oval", "x": x, "y": y, "width": size, "height": size, "color": self.current_color, "collider": collider})
            elif prefab == "enemy":
                obj = self.canvas.create_polygon(event.x, event.y-size, event.x-size, event.y+size, event.x+size, event.y+size, fill=self.current_color, outline="#FFD700", width=2)
                self.objects.append({"type": "enemy", "x": x, "y": y, "width": size, "height": size, "color": self.current_color, "collider": collider})
            self.update_hierarchy()

    def on_canvas_drag(self, event):
        x, y = self.snap(event.x - self.camera_offset[0], event.y - self.camera_offset[1])
        shape = self.current_shape.get()
        if shape == "select" and hasattr(self, 'selected_drag') and self.selected_drag:
            kind, idx, last_x, last_y = self.selected_drag
            dx, dy = x - last_x, y - last_y
            if kind == 'platform' and idx is not None:
                plat = self.platforms[idx]
                plat['x'] += dx
                plat['y'] += dy
                self.selected_drag = (kind, idx, x, y)
                self.select_item(idx, kind)
            elif kind == 'object' and idx is not None:
                obj = self.objects[idx]
                obj['x'] += dx
                obj['y'] += dy
                self.selected_drag = (kind, idx, x, y)
                self.select_item(idx, kind)
            elif kind == 'player' and self.player_spawn:
                self.player_spawn = (self.player_spawn[0] + dx, self.player_spawn[1] + dy, self.player_spawn[2])
                self.selected_drag = (kind, idx, x, y)
                self.select_item(idx, kind)
            self.redraw_canvas()
            return
        # ...existing code for other tools...
        if shape == "platform" and self.temp_rect:
            x0, y0 = self.rect_start
            self.canvas.coords(self.temp_rect, x0, y0, x, y)
        elif shape == "oval" and self.temp_oval:
            x0, y0 = self.rect_start
            self.canvas.coords(self.temp_oval, x0, y0, x, y)
        elif shape == "line" and self.temp_line:
            x0, y0 = self.rect_start
            self.canvas.coords(self.temp_line, x0, y0, x, y)

    def on_canvas_release(self, event):
        self.selected_drag = None
        x, y = self.snap(event.x, event.y)
        collider = self.collider_enabled.get()
        if self.current_shape.get() == "platform" and self.temp_rect:
            x0, y0 = self.rect_start
            x1, y1 = x, y
            x, y = min(x0, x1), min(y0, y1)
            w, h = abs(x1-x0), abs(y1-y0)
            if w > 5 and h > 5:
                self.platforms.append({
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h,
                    "color": self.current_color,
                    "collider": collider
                })
                self.canvas.itemconfig(self.temp_rect, fill=self.current_color, outline="")
            else:
                self.canvas.delete(self.temp_rect)
            self.temp_rect = None
            self.rect_start = None
        elif self.current_shape.get() == "oval" and self.temp_oval:
            x0, y0 = self.rect_start
            x1, y1 = x, y
            x, y = min(x0, x1), min(y0, y1)
            w, h = abs(x1-x0), abs(y1-y0)
            if w > 5 and h > 5:
                self.objects.append({
                    "type": "oval",
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h,
                    "color": self.current_color,
                    "collider": collider
                })
                self.canvas.itemconfig(self.temp_oval, fill=self.current_color, outline="")
            else:
                self.canvas.delete(self.temp_oval)
            self.temp_oval = None
            self.rect_start = None
        elif self.current_shape.get() == "line" and self.temp_line:
            x0, y0 = self.rect_start
            x1, y1 = x, y
            if abs(x1-x0) > 5 or abs(y1-y0) > 5:
                self.objects.append({
                    "type": "line",
                    "x0": x0, "y0": y0, "x1": x1, "y1": y1, "color": self.current_color, "collider": collider
                })
            else:
                self.canvas.delete(self.temp_line)
            self.temp_line = None
            self.rect_start = None
        self.update_hierarchy()

    def save_level(self):
        if not self.player_spawn:
            messagebox.showerror("Error", "Set player spawn point!")
            return
        level = {
            "background_color": self.bg_color,
            "player": {
                "start_x": self.player_spawn[0],
                "start_y": self.player_spawn[1],
                "width": 30,
                "height": 30,
                "color": "#FF0000"
            },
            "platforms": self.platforms,
            "objects": self.objects
        }
        file = "level.json"
        with open(file, "w") as f:
            json.dump(level, f, indent=2)
        messagebox.showinfo("Saved", f"Level saved to {file}")
        self.update_hierarchy()

    def load_level(self):
        file = "level.json"
        try:
            with open(file, "r") as f:
                level = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load {file}: {e}")
            return
        self.canvas.delete("all")
        self.platforms.clear()
        self.objects.clear()
        self.player_spawn = None
        self.bg_color = level.get("background_color", "#222222")
        self.canvas.config(bg=self.bg_color)
        self.bg_preview.config(bg=self.bg_color)
        # Draw platforms
        for plat in level.get("platforms", []):
            rect = self.canvas.create_rectangle(
                plat["x"], plat["y"], plat["x"]+plat["width"], plat["y"]+plat["height"],
                fill=plat["color"], outline=""
            )
            self.platforms.append(plat)
        # Draw objects
        for obj in level.get("objects", []):
            if obj["type"] == "object":
                rect = self.canvas.create_rectangle(
                    obj["x"]-obj["width"]//2, obj["y"]-obj["height"]//2, obj["x"]+obj["width"]//2, obj["y"]+obj["height"]//2,
                    fill=obj["color"], outline="#FFD700", width=2
                )
                self.objects.append(obj)
            elif obj["type"] == "oval":
                oval = self.canvas.create_oval(
                    obj["x"], obj["y"], obj["x"]+obj["width"], obj["y"]+obj["height"],
                    fill=obj["color"], outline=""
                )
                self.objects.append(obj)
            elif obj["type"] == "line":
                line = self.canvas.create_line(
                    obj["x0"], obj["y0"], obj["x1"], obj["y1"], fill=obj["color"], width=2
                )
                self.objects.append(obj)
        # Draw player spawn
        p = level.get("player", {})
        if p:
            rect = self.canvas.create_rectangle(
                p["start_x"]-15, p["start_y"]-15, p["start_x"]+15, p["start_y"]+15,
                outline="#00FF00", width=2
            )
            self.player_spawn = (p["start_x"], p["start_y"], rect)
        self.update_hierarchy()

    def find_item_at(self, x, y):
        # Check platforms
        for i, plat in enumerate(self.platforms):
            if plat['x'] <= x <= plat['x']+plat['width'] and plat['y'] <= y <= plat['y']+plat['height']:
                return i, 'platform'
        # Check objects (support all prefab types)
        for i, obj in enumerate(self.objects):
            t = obj.get('type', 'object')
            if t in ("object", "crate", "coin", "enemy", "checkpoint", "trigger"):
                if obj['x']-obj['width']//2 <= x <= obj['x']+obj['width']//2 and obj['y']-obj['height']//2 <= y <= obj['y']+obj['height']//2:
                    return i, 'object'
            elif t == 'oval':
                if obj['x'] <= x <= obj['x']+obj['width'] and obj['y'] <= y <= obj['y']+obj['height']:
                    return i, 'object'
            elif t == 'line':
                minx, maxx = min(obj['x0'], obj['x1']), max(obj['x0'], obj['x1'])
                miny, maxy = min(obj['y0'], obj['y1']), max(obj['y0'], obj['y1'])
                if minx <= x <= maxx and miny <= y <= maxy:
                    return i, 'object'
        # Check player spawn
        if self.player_spawn:
            px, py = self.player_spawn[0], self.player_spawn[1]
            if px-15 <= x <= px+15 and py-15 <= y <= py+15:
                # Use the index after all platforms and objects for player
                return len(self.platforms) + len(self.objects), 'player'
        return None, None

    def select_item(self, index, kind):
        self.selected_item = (index, kind)
        # Update hierarchy selection
        self.hierarchy_list.selection_clear(0, tk.END)
        if kind == 'platform':
            self.hierarchy_list.selection_set(index)
            self.show_properties(index, kind)
        elif kind == 'object':
            plat_count = len(self.platforms)
            self.hierarchy_list.selection_set(plat_count + index)
            self.show_properties(index, kind)
        elif kind == 'player':
            self.hierarchy_list.selection_set(len(self.platforms) + len(self.objects))
        # Force focus to hierarchy list for visible highlight
        self.hierarchy_list.focus_set()
        # Make sure the selected item is visible in the list
        if self.hierarchy_list.curselection():
            self.hierarchy_list.see(self.hierarchy_list.curselection()[0])
        self.redraw_canvas()

    def _bind_events(self):
        # Mouse events for canvas
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        self.canvas.bind('<Button-3>', self.on_right_click)
        self.canvas.bind('<B3-Motion>', self.on_right_drag)
        self.canvas.bind('<ButtonRelease-3>', self.on_right_release)
        self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)  # Windows
        self.canvas.bind('<Button-4>', self.on_mouse_wheel)    # Linux scroll up
        self.canvas.bind('<Button-5>', self.on_mouse_wheel)    # Linux scroll down
        # Keyboard events for window
        self.bind('<Delete>', self.on_hierarchy_delete)
        self.bind('<BackSpace>', self.on_hierarchy_delete)

    def on_right_click(self, event):
        self._pan_start = (event.x, event.y, self.camera_offset[0], self.camera_offset[1])

    def on_right_drag(self, event):
        if hasattr(self, '_pan_start') and self._pan_start:
            start_x, start_y, orig_ox, orig_oy = self._pan_start
            dx = event.x - start_x
            dy = event.y - start_y
            self.camera_offset[0] = orig_ox + dx
            self.camera_offset[1] = orig_oy + dy
            self.redraw_canvas()

    def on_right_release(self, event):
        self._pan_start = None

    def on_mouse_wheel(self, event):
        # Zoom in/out centered on mouse
        if not hasattr(self, 'zoom'): self.zoom = 1.0
        # Windows: event.delta, Linux: event.num
        if hasattr(event, 'delta'):
            if event.delta > 0:
                self.zoom *= 1.1
            else:
                self.zoom /= 1.1
        elif hasattr(event, 'num'):
            if event.num == 4:
                self.zoom *= 1.1
            elif event.num == 5:
                self.zoom /= 1.1
        # Clamp zoom
        self.zoom = max(0.2, min(self.zoom, 5.0))
        self.redraw_canvas()

    def redraw_canvas(self):
        self.canvas.delete("all")
        zoom = getattr(self, 'zoom', 1.0)
        ox, oy = self.camera_offset
        # Redraw all platforms
        for i, plat in enumerate(self.platforms):
            is_selected = self.selected_item and self.selected_item[0] == i and self.selected_item[1] == 'platform'
            outline = "#00FF00" if is_selected else ""
            width = 2 if is_selected else 1
            self.canvas.create_rectangle(
                plat['x'] * zoom + ox,
                plat['y'] * zoom + oy,
                (plat['x'] + plat['width']) * zoom + ox,
                (plat['y'] + plat['height']) * zoom + oy,
                fill=plat.get('color', '#FF0000'),
                outline=outline,
                width=width
            )
        # Redraw all objects (support all prefab/event types)
        for i, obj in enumerate(self.objects):
            is_selected = self.selected_item and self.selected_item[0] == i and self.selected_item[1] == 'object'
            outline = "#00FF00" if is_selected else ""
            width = 2 if is_selected else 1
            t = obj.get('type', 'object')
            color = obj.get('color', '#FF0000')
            if t in ("object", "crate", "coin", "enemy", "checkpoint", "trigger"):
                # Draw as rectangle
                self.canvas.create_rectangle(
                    (obj['x'] - obj['width']//2) * zoom + ox,
                    (obj['y'] - obj['height']//2) * zoom + oy,
                    (obj['x'] + obj['width']//2) * zoom + ox,
                    (obj['y'] + obj['height']//2) * zoom + oy,
                    fill=color,
                    outline=outline if outline else ("#FFD700" if t in ("object", "crate", "coin") else ""),
                    width=width
                )
            elif t == 'oval':
                self.canvas.create_oval(
                    obj['x'] * zoom + ox,
                    obj['y'] * zoom + oy,
                    (obj['x'] + obj['width']) * zoom + ox,
                    (obj['y'] + obj['height']) * zoom + oy,
                    fill=color,
                    outline=outline,
                    width=width
                )
            elif t == 'line':
                self.canvas.create_line(
                    obj['x0'] * zoom + ox,
                    obj['y0'] * zoom + oy,
                    obj['x1'] * zoom + ox,
                    obj['y1'] * zoom + oy,
                    fill=color,
                    width=width
                )
        # Redraw player spawn
        if self.player_spawn:
            x, y, rect = self.player_spawn
            self.canvas.create_rectangle(
                (x - 10) * zoom + ox,
                (y - 10) * zoom + oy,
                (x + 10) * zoom + ox,
                (y + 10) * zoom + oy,
                fill="#00FF00",
                outline="#00FF00",
                width=2
            )

if __name__ == "__main__":
    editor = LevelEditor()
    editor.camera_offset = [0, 0]  # Initialize camera offset if not already
    editor.mainloop()
