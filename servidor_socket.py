import socket
import threading
import json

BLACKLIST_FILE = 'blacklist.json'

def load_blacklist():
    try:
        with open(BLACKLIST_FILE, 'r') as f:
            return set(json.load(f))
    except:
        return set()

def handle_client(conn):
    try:
        ip = conn.recv(1024).decode()
        blacklist = load_blacklist()
        status = "BLOQUEADO" if ip in blacklist else "ACEITO"
        print(f"Conexão de {ip}: {status}")
    except:
        pass
    finally:
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 9999))
    server.listen(5)
    print("Servidor aguardando conexões na porta 9999...")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn,))
        thread.start()

if __name__ == '__main__':
    start_server()
