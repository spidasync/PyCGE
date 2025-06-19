import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import math
import time
import socket
import json
import threading

class GameEngine:
    def __init__(self, config=None):
        # Default configuration
        self.config = {
            'window_title': "PyCGE Engine",
            'window_width': 1280,
            'window_height': 720,
            'background_color': 'black',
            'debug_enabled': True,
            'multiplayer_enabled': False,
            'server_ip': 'localhost',
            'server_port': 5555,
            'physics': {
                'gravity': 0.65,
                'jump_force': -14.5,
                'move_speed': 6.5,
                'friction': 0.8
            },
            'camera': {
                'enabled': True,
                'smoothness': 0.1
            },
            'player': {
                'width': 30,
                'height': 30,
                'color': 'red',
                'start_x': 640,
                'start_y': 360
            }
        }
        
        # Update config with user settings
        if config:
            self._update_config(config)
        
        # Initialize player properties
        self.player = {
            'x': self.config['player']['start_x'],
            'y': self.config['player']['start_y'],
            'width': self.config['player']['width'],
            'height': self.config['player']['height'],
            'velocity_x': 0,
            'velocity_y': 0,
            'on_ground': False,
            'color': self.config['player']['color']
        }
        
        self.platforms = []
        self.other_players = {}
        self.network_running = False
        
        # Setup multiplayer if enabled
        if self.config['multiplayer_enabled']:
            self.setup_network()
        
        self._setup_window()
        self._setup_input_handling()
        
        # Physics properties from config
        self.gravity = self.config['physics']['gravity']
        self.jump_force = self.config['physics']['jump_force']
        self.move_speed = self.config['physics']['move_speed']
        self.friction = self.config['physics']['friction']
        
        # Camera properties
        self.camera = {
            'x': 0,
            'y': 0,
            'target_x': 0,
            'target_y': 0,
            'smoothness': self.config['camera']['smoothness']
        }
        
        # FPS tracking
        self.last_frame_time = time.time()
        self.fps = 0
        
        # Custom update function
        self.custom_update = None
    
    def _update_config(self, new_config):
        """Deep update of configuration dictionary"""
        def update_dict(d, u):
            for k, v in u.items():
                if isinstance(v, dict) and k in d:
                    d[k] = update_dict(d[k], v)
                else:
                    d[k] = v
            return d
        self.config = update_dict(self.config, new_config)
    
    def _setup_window(self):
        """Setup the game window and UI elements"""
        self.root = tk.Tk()
        self.root.title(self.config['window_title'])
        
        # Create main container
        self.main_container = tk.Frame(self.root, bg='#1a1a1a')
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create game frame
        self.game_frame = tk.Frame(self.main_container, bg='#1a1a1a')
        self.game_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas
        self.canvas = tk.Canvas(
            self.game_frame,
            width=self.config['window_width'],
            height=self.config['window_height'],
            bg=self.config['background_color'],
            highlightthickness=0
        )
        self.canvas.pack()
        
        if self.config['debug_enabled']:
            self._setup_debug()
    
    def _setup_debug(self):
        """Setup debug information display"""
        self.debug_frame = tk.Frame(self.canvas, bg='black')
        self.debug_frame.place(x=10, y=10)
        
        self.fps_label = tk.Label(
            self.debug_frame,
            text="FPS: 0",
            bg='black', fg='white',
            font=('Consolas', 12)
        )
        self.fps_label.pack(side=tk.LEFT, padx=(0, 15))
        
        self.pos_label = tk.Label(
            self.debug_frame,
            text="Pos: (0, 0)",
            bg='black', fg='white',
            font=('Consolas', 12)
        )
        self.pos_label.pack(side=tk.LEFT, padx=(0, 15))
        
        self.vel_label = tk.Label(
            self.debug_frame,
            text="Vel: (0, 0)",
            bg='black', fg='white',
            font=('Consolas', 12)
        )
        self.vel_label.pack(side=tk.LEFT)
    
    def _setup_input_handling(self):
        """Setup keyboard input handling"""
        self.keys = {'left': False, 'right': False, 'up': False}
        self.root.bind('<KeyPress>', self._key_press)
        self.root.bind('<KeyRelease>', self._key_release)
    
    def setup_network(self):
        """Setup multiplayer networking"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.sock.connect((self.config['server_ip'], self.config['server_port']))
            
            self.client_id = int(self.sock.recv(1024).decode())
            self.sock.send(f"ACK{self.client_id}".encode())
            print(f"Connected to server with ID: {self.client_id}")
            
            self.network_running = True
            self.network_thread = threading.Thread(target=self._network_update)
            self.network_thread.daemon = True
            self.network_thread.start()
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            messagebox.showerror("Connection Error", 
                               f"Failed to connect to server: {e}")
            self.sock = None
    
    def add_platform(self, x, y, width, height, color='green'):
        """Add a platform to the game"""
        self.platforms.append({
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'color': color
        })
    
    def set_custom_update(self, func):
        """Set a custom update function to be called each frame"""
        self.custom_update = func
    
    def world_to_screen(self, x, y):
        """Convert world coordinates to screen coordinates"""
        if self.config['camera']['enabled']:
            return x - self.camera['x'], y - self.camera['y']
        return x, y
    
    def _update_camera(self):
        """Update camera position to follow player"""
        if not self.config['camera']['enabled']:
            return
            
        self.camera['target_x'] = (
            self.player['x'] - self.config['window_width']/2 + self.player['width']/2
        )
        self.camera['target_y'] = (
            self.player['y'] - self.config['window_height']/2 + self.player['height']/2
        )
        
        self.camera['x'] += (self.camera['target_x'] - self.camera['x']) * self.camera['smoothness']
        self.camera['y'] += (self.camera['target_y'] - self.camera['y']) * self.camera['smoothness']
    
    def _update_debug_info(self):
        """Update debug information display"""
        if not self.config['debug_enabled']:
            return
            
        current_time = time.time()
        dt = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        if dt > 0:
            self.fps = 1.0 / dt
        
        self.fps_label.config(text=f"FPS: {self.fps:.1f}")
        self.pos_label.config(text=f"Pos: ({self.player['x']:.1f}, {self.player['y']:.1f})")
        self.vel_label.config(text=f"Vel: ({self.player['velocity_x']:.1f}, {self.player['velocity_y']:.1f})")
    
    def _key_press(self, event):
        key = event.keysym.lower()
        if key == 'a':
            self.keys['left'] = True
        elif key == 'd':
            self.keys['right'] = True
        elif key == 'w':
            self.keys['up'] = True
        elif key == 'r':
            self.reset_position()
    
    def _key_release(self, event):
        key = event.keysym.lower()
        if key == 'a':
            self.keys['left'] = False
        elif key == 'd':
            self.keys['right'] = False
        elif key == 'w':
            self.keys['up'] = False
    
    def reset_position(self):
        """Reset player position and camera"""
        self.player['x'] = self.config['player']['start_x']
        self.player['y'] = self.config['player']['start_y']
        self.player['velocity_x'] = 0
        self.player['velocity_y'] = 0
        self.camera['x'] = 0
        self.camera['y'] = 0
        self.camera['target_x'] = 0
        self.camera['target_y'] = 0
    
    def check_collision(self, x, y):
        """Check for collision between player and platforms"""
        player_rect = (x, y, self.player['width'], self.player['height'])
        for platform in self.platforms:
            if (x < platform['x'] + platform['width'] and
                x + player_rect[2] > platform['x'] and
                y < platform['y'] + platform['height'] and
                y + player_rect[3] > platform['y']):
                return True
        return False    
    
    def _network_update(self):
        """Handle network updates for multiplayer"""
        if not self.config['multiplayer_enabled']:
            return
            
        last_send_time = 0
        send_interval = 1.0 / 60  # 60Hz update rate
        
        while self.network_running and self.sock:
            current_time = time.time()
            
            try:
                if current_time - last_send_time >= send_interval:
                    player_data = {
                        'x': self.player['x'],
                        'y': self.player['y'],
                        'velocity_x': self.player['velocity_x'],
                        'velocity_y': self.player['velocity_y'],
                        'on_ground': self.player['on_ground'],
                        'color': self.player['color'],
                        'width': self.player['width'],
                        'height': self.player['height']
                    }
                    message = json.dumps(player_data) + '\n'  # Add newline as message delimiter
                    self.sock.send(message.encode())
                    last_send_time = current_time
                
                # Receive and process data
                self.sock.setblocking(False)
                try:
                    data = self.sock.recv(4096).decode()  # Increased buffer size
                    if data:
                        # Split received data by newlines in case multiple messages arrived
                        messages = data.strip().split('\n')
                        for message in messages:
                            if message:
                                try:
                                    all_players = json.loads(message)
                                    self.other_players = {
                                        int(pid): pdata for pid, pdata in all_players.items()
                                        if int(pid) != self.client_id
                                    }
                                except json.JSONDecodeError as e:
                                    print(f"JSON decode error: {e}")
                                    continue
                except BlockingIOError:
                    pass
                except Exception as e:
                    print(f"Receive error: {e}")
                finally:
                    self.sock.setblocking(True)
                
            except Exception as e:
                print(f"Network error: {e}")
                self.sock = None
                break
            
            time.sleep(0.001)
    
    def _draw_platforms(self):
        """Draw all platforms"""
        for platform in self.platforms:
            screen_x, screen_y = self.world_to_screen(platform['x'], platform['y'])
            self.canvas.create_rectangle(
                screen_x, screen_y,
                screen_x + platform['width'],
                screen_y + platform['height'],
                fill=platform['color']
            )
    
    def _draw_players(self):
        """Draw current player and other players"""
        # Draw current player
        screen_x, screen_y = self.world_to_screen(self.player['x'], self.player['y'])
        self.canvas.create_rectangle(
            screen_x, screen_y,
            screen_x + self.player['width'],
            screen_y + self.player['height'],
            fill=self.player['color'],
            outline='white'
        )
        
        # Draw other players in multiplayer mode
        if self.config['multiplayer_enabled']:
            for pid, data in self.other_players.items():
                try:
                    screen_x, screen_y = self.world_to_screen(data['x'], data['y'])
                    self.canvas.create_rectangle(
                        screen_x, screen_y,
                        screen_x + data['width'],
                        screen_y + data['height'],
                        fill=data['color'],
                        outline='white'
                    )
                except KeyError as e:
                    print(f"Missing data for player {pid}: {e}")
                    continue
    
    def _update_physics(self):
        """Update player physics"""
        # Handle horizontal movement
        if self.keys['left']:
            self.player['velocity_x'] = -self.move_speed
        elif self.keys['right']:
            self.player['velocity_x'] = self.move_speed
        else:
            self.player['velocity_x'] *= self.friction
        
        # Apply gravity
        if not self.player['on_ground']:
            self.player['velocity_y'] += self.gravity
        
        # Handle jumping
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
    
    def _update(self):
        """Main update loop"""
        # Update camera position
        self._update_camera()
        
        # Update physics
        self._update_physics()
        
        # Call custom update function if set
        if self.custom_update:
            self.custom_update(self)
        
        # Clear and redraw everything
        self.canvas.delete('all')
        
        # Draw game elements
        self._draw_platforms()
        self._draw_players()
        
        # Update debug info
        self._update_debug_info()
        
        # Schedule next update
        self.root.after(16, self._update)  # ~60 FPS
    
    def run(self):
        """Start the game loop"""
        self._update()
        self.root.mainloop()

class Server:
    def __init__(self, host='0.0.0.0', port=5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.server.bind((host, port))
        self.server.listen()
        
        self.clients = {}
        self.players = {}
        self.client_counter = 0
        self.running = True
        
        print(f"Server started on {host}:{port}")
        print(f"Local IP: {socket.gethostbyname(socket.gethostname())}")
    
    def start(self):
        while self.running:
            try:
                conn, addr = self.server.accept()
                client_id = self.client_counter
                self.client_counter += 1
                
                thread = threading.Thread(target=self.handle_client, args=(conn, client_id))
                thread.daemon = True
                thread.start()
                
                print(f"New connection from {addr}, assigned ID: {client_id}")
            except Exception as e:
                print(f"Error accepting connection: {e}")
                continue

    def handle_client(self, conn, client_id):
        try:
            self.clients[client_id] = conn
            
            # Send client ID with newline delimiter
            conn.send((str(client_id) + '\n').encode())
            ack = conn.recv(1024).decode().strip()
            if ack != f"ACK{client_id}":
                raise Exception("Client failed to acknowledge ID")
            
            self.players[client_id] = {
                'x': 640,
                'y': 360,
                'velocity_x': 0,
                'velocity_y': 0,
                'on_ground': False,
                'width': 30,
                'height': 30,
                'color': 'red' if client_id == 0 else 'blue'
            }
            
            self.broadcast_state()
            
            # Buffer for incomplete messages
            buffer = ""
            
            while self.running:
                try:
                    data = conn.recv(4096).decode()  # Increased buffer size
                    if not data:
                        break
                    
                    # Add received data to buffer
                    buffer += data
                    
                    # Process complete messages
                    while '\n' in buffer:
                        message, buffer = buffer.split('\n', 1)
                        if message:
                            try:
                                player_data = json.loads(message)
                                self.players[client_id].update(player_data)
                                self.broadcast_state()
                            except json.JSONDecodeError as e:
                                print(f"Invalid JSON from client {client_id}: {e}")
                                continue
                    
                except Exception as e:
                    print(f"Error handling client {client_id}: {e}")
                    break
        except Exception as e:
            print(f"Client {client_id} error: {e}")
        finally:
            print(f"Client {client_id} disconnected")
            if client_id in self.clients:
                del self.clients[client_id]
            if client_id in self.players:
                del self.players[client_id]
            conn.close()

    def broadcast_state(self):
        state = json.dumps(self.players) + '\n'  # Add newline as message delimiter
        disconnected = []
        
        for cid, client_conn in self.clients.items():
            try:
                client_conn.send(state.encode())
            except:
                print(f"Failed to send to client {cid}")
                disconnected.append(cid)
        
        for cid in disconnected:
            if cid in self.clients:
                del self.clients[cid]
            if cid in self.players:
                del self.players[cid]
    
    def stop(self):
        self.running = False
        for conn in self.clients.values():
            conn.close()
        self.server.close()
