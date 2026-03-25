import socket, threading, select, sys, time, os

# Cloud Run binding
LISTENING_ADDR = '0.0.0.0'
LISTENING_PORT = int(os.environ.get("PORT", 8080))

# ENV for default target
VPS_IP = os.environ.get("VPS_IP", "127.0.0.1")
PORT_TUNNEL = int(os.environ.get("PORT_TUNNEL", 22))

# Default host now uses VPS
DEFAULT_HOST = f"{VPS_IP}:{PORT_TUNNEL}"

PASS = ''
BUFLEN = 4096 * 4
TIMEOUT = 60

RESPONSE = b'HTTP/1.1 101 TheGlock\r\n\r\n'


class Server(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.running = False
        self.host = host
        self.port = port
        self.threads = []

    def run(self):
        self.soc = socket.socket(socket.AF_INET)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.soc.settimeout(2)

        self.soc.bind((self.host, self.port))
        self.soc.listen(100)
        self.running = True

        print(f"[+] Listening on {self.host}:{self.port}")
        print(f"[+] Default target: {DEFAULT_HOST}")

        try:
            while self.running:
                try:
                    c, addr = self.soc.accept()
                except socket.timeout:
                    continue

                conn = ConnectionHandler(c, self, addr)
                conn.start()
                self.threads.append(conn)
        finally:
            self.running = False
            self.soc.close()


class ConnectionHandler(threading.Thread):
    def __init__(self, client, server, addr):
        super().__init__()
        self.client = client
        self.server = server
        self.addr = addr
        self.target = None

    def run(self):
        try:
            data = self.client.recv(BUFLEN).decode(errors='ignore')

            hostPort = self.find_header(data, 'X-Real-Host')

            # 🔥 Fallback to VPS if not provided
            if not hostPort:
                hostPort = DEFAULT_HOST

            print(f"[+] Incoming from {self.addr} → {hostPort}")

            self.method_CONNECT(hostPort)

        except Exception as e:
            print("Error:", e)
        finally:
            self.close()

    def find_header(self, data, header):
        for line in data.split("\r\n"):
            if line.lower().startswith(header.lower()):
                return line.split(":", 1)[1].strip()
        return ''

    def connect_target(self, host):
        try:
            host, port = host.split(":")
            port = int(port)
        except:
            host = VPS_IP
            port = PORT_TUNNEL

        self.target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.target.connect((host, port))

    def method_CONNECT(self, hostPort):
        print(f"[+] CONNECT {hostPort}")

        self.connect_target(hostPort)

        self.client.sendall(RESPONSE)

        self.tunnel()

    def tunnel(self):
        sockets = [self.client, self.target]

        while True:
            r, _, _ = select.select(sockets, [], [], TIMEOUT)

            if not r:
                break

            for s in r:
                try:
                    data = s.recv(BUFLEN)
                    if not data:
                        return

                    if s is self.client:
                        self.target.sendall(data)
                    else:
                        self.client.sendall(data)
                except:
                    return

    def close(self):
        try:
            self.client.close()
        except:
            pass

        try:
            if self.target:
                self.target.close()
        except:
            pass


if __name__ == "__main__":
    print("=== Python Relay Tunnel ===")
    print(f"PORT: {LISTENING_PORT}")
    print(f"DEFAULT: {DEFAULT_HOST}")

    server = Server(LISTENING_ADDR, LISTENING_PORT)
    server.start()

    while True:
        time.sleep(10)
