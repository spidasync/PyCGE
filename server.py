import socket
import json
import threading
import time
import queue
from collections import deque

class GameServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Enable keepalive
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        # Set TCP keepalive settings
        if hasattr(socket, 'TCP_KEEPIDLE'):
            self.server.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
        if hasattr(socket, 'TCP_KEEPINTVL'):
            self.server.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3)
        if hasattr(socket, 'TCP_KEEPCNT'):
            self.server.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
        # Allow reuse of address
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        
        # Set a reasonable timeout
        self.server.settimeout(1.0)
        
        self.server.bind((host, port))
        self.server.listen()
        
        self.clients = {}  # client_id -> connection
        self.client_queues = {}  # client_id -> message queue
        self.players = {}  # client_id -> player_data
        self.client_counter = 0
        self.running = True
        self.broadcast_thread = None
        self.message_lock = threading.Lock()
        
        print(f"Server started on {host}:{port}")
        
    def start(self):
        # Start the broadcast thread
        self.broadcast_thread = threading.Thread(target=self._broadcast_loop)
        self.broadcast_thread.daemon = True
        self.broadcast_thread.start()
        
        while self.running:
            try:
                conn, addr = self.server.accept()
                conn.settimeout(5)
                
                # Perform initial handshake
                try:
                    # Send welcome message with client ID
                    welcome_msg = json.dumps({
                        "type": "welcome",
                        "client_id": self.client_counter
                    }) + '\n'
                    conn.send(welcome_msg.encode())
                    
                    # Wait for acknowledgment
                    data = conn.recv(1024).decode()
                    if not data:
                        print(f"No acknowledgment from {addr}")
                        conn.close()
                        continue
                    
                    try:
                        ack = json.loads(data.strip())
                        if ack.get('type') != 'ack' or ack.get('client_id') != self.client_counter:
                            raise ValueError("Invalid acknowledgment")
                    except (json.JSONDecodeError, ValueError) as e:
                        print(f"Invalid acknowledgment from {addr}: {e}")
                        conn.close()
                        continue
                    
                    client_id = self.client_counter
                    self.client_counter += 1
                    
                    # Create message queue for this client
                    self.client_queues[client_id] = queue.Queue()
                    
                    # Send initial state
                    initial_state = {
                        "type": "state",
                        "players": self.players
                    }
                    conn.send((json.dumps(initial_state) + '\n').encode())
                    
                    # Send connection confirmation
                    confirm_msg = json.dumps({
                        "type": "connected",
                        "client_id": client_id
                    }) + '\n'
                    conn.send(confirm_msg.encode())
                    
                    thread = threading.Thread(target=self.handle_client, args=(conn, client_id))
                    thread.daemon = True
                    thread.start()
                    
                    print(f"New connection from {addr}, assigned ID: {client_id}")
                    
                except Exception as e:
                    print(f"Error during handshake with {addr}: {e}")
                    try:
                        conn.close()
                    except:
                        pass
                    continue
                    
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error accepting connection: {e}")
                if not self.running:
                    break
                time.sleep(1)
                continue
    
    def _broadcast_loop(self):
        """Separate thread for broadcasting game state"""
        last_broadcast = 0
        broadcast_interval = 1/60  # 60Hz broadcast rate
        
        while self.running:
            current_time = time.time()
            if current_time - last_broadcast >= broadcast_interval and self.clients:
                with self.message_lock:
                    state = {
                        "type": "state",
                        "players": self.players
                    }
                    state_msg = json.dumps(state) + '\n'
                    
                    disconnected = []
                    for cid, client_queue in self.client_queues.items():
                        try:
                            client_queue.put_nowait(state_msg)
                        except queue.Full:
                            print(f"Message queue full for client {cid}")
                            disconnected.append(cid)
                    
                    for cid in disconnected:
                        self._remove_client(cid)
                
                last_broadcast = current_time
            time.sleep(0.001)
    
    def _remove_client(self, client_id):
        """Safely remove a client and their data"""
        with self.message_lock:
            try:
                if client_id in self.clients:
                    try:
                        disconnect_msg = json.dumps({
                            "type": "disconnect",
                            "message": "Client disconnected"
                        }) + '\n'
                        self.clients[client_id].send(disconnect_msg.encode())
                    except:
                        pass
                    self.clients[client_id].close()
                    del self.clients[client_id]
                if client_id in self.client_queues:
                    del self.client_queues[client_id]
                if client_id in self.players:
                    del self.players[client_id]
                print(f"Removed client {client_id}")
            except Exception as e:
                print(f"Error removing client {client_id}: {e}")
    
    def handle_client(self, conn, client_id):
        """Handle individual client connection"""
        self.clients[client_id] = conn
        client_queue = self.client_queues[client_id]
        receive_buffer = ""
        
        try:
            last_received = time.time()
            last_ping = time.time()
            timeout_duration = 10
            ping_interval = 1.0
            
            while self.running:
                current_time = time.time()
                
                # Send periodic ping
                if current_time - last_ping >= ping_interval:
                    ping_msg = json.dumps({"type": "ping"}) + '\n'
                    conn.send(ping_msg.encode())
                    last_ping = current_time
                
                # Check for timeout
                if current_time - last_received > timeout_duration:
                    raise ConnectionError(f"Client {client_id} timed out")
                
                # Handle incoming data
                try:
                    conn.settimeout(0.1)
                    data = conn.recv(4096).decode()
                    if not data:
                        raise ConnectionError("Client disconnected")
                    
                    last_received = current_time
                    receive_buffer += data
                    
                    # Process complete messages
                    while '\n' in receive_buffer:
                        message, receive_buffer = receive_buffer.split('\n', 1)
                        try:
                            msg_data = json.loads(message)
                            msg_type = msg_data.get('type', 'state')
                            
                            if msg_type == 'ping':
                                conn.send(json.dumps({"type": "pong"}).encode() + b'\n')
                            elif msg_type == 'state':
                                with self.message_lock:
                                    self.players[str(client_id)] = msg_data.get('player_data', {})
                            

                        except json.JSONDecodeError as e:
                            print(f"Invalid message from client {client_id}: {e}")
                            continue
                
                except socket.timeout:
                    continue
                
                # Send queued messages
                try:
                    while not client_queue.empty():
                        message = client_queue.get_nowait()
                        conn.send(message.encode())
                except Exception as e:
                    print(f"Error sending to client {client_id}: {e}")
                    break
                
                time.sleep(0.001)
                
        except Exception as e:
            print(f"Client {client_id} error: {e}")
        finally:
            self._remove_client(client_id)
    
    def stop(self):
        """Gracefully stop the server"""
        self.running = False
        for client_id in list(self.clients.keys()):
            self._remove_client(client_id)
        try:
            self.server.close()
        except:
            pass
        print("Server stopped")

if __name__ == "__main__":
    server = GameServer()
    print("Waiting for connections...")
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop()
    except Exception as e:
        print(f"Server error: {e}")
        server.stop()
