import socket
import threading
import json

class HostConnection:
    def __init__(self, host_port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", host_port))
        self.peer_addr = None
        self.running = True
        self.recv_data = None
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self.listen, daemon=True)
        self.thread.start()

    def listen(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                with self.lock:
                    self.recv_data = json.loads(data.decode())
                if not self.peer_addr:
                    self.peer_addr = addr
            except Exception:
                pass

    def send(self, data):
        if self.peer_addr:
            try:
                self.sock.sendto(json.dumps(data).encode(), self.peer_addr)
            except Exception:
                pass

    def get_latest(self):
        with self.lock:
            data = self.recv_data
            self.recv_data = None
        return data

    def close(self):
        self.running = False
        self.sock.close()

class ClientConnection:
    def __init__(self, host_ip, host_port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host_addr = (host_ip, host_port)
        self.running = True
        self.recv_data = None
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self.listen, daemon=True)
        self.thread.start()

    def listen(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                with self.lock:
                    self.recv_data = json.loads(data.decode())
            except Exception:
                pass

    def send(self, data):
        try:
            self.sock.sendto(json.dumps(data).encode(), self.host_addr)
        except Exception:
            pass

    def get_latest(self):
        with self.lock:
            data = self.recv_data
            self.recv_data = None
        return data

    def close(self):
        self.running = False
        self.sock.close()
