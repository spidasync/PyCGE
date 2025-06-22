import socket
import threading
import json

class HostConnection:
    def __init__(self, host_port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", host_port))
        self.clients = {}  # addr -> player_id
        self.player_states = {}  # player_id -> state
        self.running = True
        self.lock = threading.Lock()
        self.recv_queue = []
        self.thread = threading.Thread(target=self.listen, daemon=True)
        self.thread.start()

    def listen(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                msg = json.loads(data.decode())
                player_id = msg.get('id', str(addr))
                with self.lock:
                    self.clients[addr] = player_id
                    self.player_states[player_id] = msg
                    self.recv_queue.append((player_id, msg))
                # Broadcast all player states to all clients
                all_states = {pid: state for pid, state in self.player_states.items()}
                for c_addr in self.clients:
                    try:
                        self.sock.sendto(json.dumps(all_states).encode(), c_addr)
                    except Exception:
                        pass
            except Exception:
                pass

    def send(self, data):
        # Host doesn't send to itself, but can update its own state
        player_id = data.get('id', 'host')
        with self.lock:
            self.player_states[player_id] = data
        # Broadcast all player states to all clients
        all_states = {pid: state for pid, state in self.player_states.items()}
        for c_addr in self.clients:
            try:
                self.sock.sendto(json.dumps(all_states).encode(), c_addr)
            except Exception:
                pass

    def get_latest(self):
        with self.lock:
            if self.recv_queue:
                return self.recv_queue.pop(0)
        return None

    def get_all_states(self):
        with self.lock:
            return dict(self.player_states)

    def close(self):
        self.running = False
        self.sock.close()

class ClientConnection:
    def __init__(self, host_ip, host_port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host_addr = (host_ip, host_port)
        self.running = True
        self.lock = threading.Lock()
        self.latest_states = None
        self.thread = threading.Thread(target=self.listen, daemon=True)
        self.thread.start()

    def listen(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                all_states = json.loads(data.decode())
                with self.lock:
                    self.latest_states = all_states
            except Exception:
                pass

    def send(self, data):
        try:
            self.sock.sendto(json.dumps(data).encode(), self.host_addr)
        except Exception:
            pass

    def get_latest(self):
        with self.lock:
            states = self.latest_states
            self.latest_states = None
        return states

    def close(self):
        self.running = False
        self.sock.close()
