import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO
import threading
import socket
import json

app = Flask(__name__)
socketio = SocketIO(app)
BLACKLIST_FILE = 'blacklist.json'

# ======= Blacklist Utils =======
def load_blacklist():
    try:
        with open(BLACKLIST_FILE, 'r') as f:
            return set(json.load(f))
    except:
        return set()

def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, 'w') as f:
        json.dump(list(blacklist), f)

# ======= Rotas Web =======
@app.route('/')
def index():
    blacklist = load_blacklist()
    return render_template('index.html', blacklist=blacklist)

@app.route('/bloquear', methods=['POST'])
def bloquear():
    ip = request.form['ip']
    blacklist = load_blacklist()
    blacklist.add(ip)
    save_blacklist(blacklist)
    return redirect(url_for('index'))

@app.route('/liberar', methods=['POST'])
def liberar():
    ip = request.form['ip']
    blacklist = load_blacklist()
    blacklist.discard(ip)
    save_blacklist(blacklist)
    return redirect(url_for('index'))

# ======= Servidor TCP =======
def handle_client(conn):
    try:
        ip = conn.recv(1024).decode()
        blacklist = load_blacklist()
        status = "BLOQUEADO" if ip in blacklist else "ACEITO"
        log = f"Conexão de {ip}: {status}"
        print(log)
        socketio.emit('log', log)
    except:
        pass
    finally:
        conn.close()

def start_tcp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 9999))
    server.listen(5)
    print("Servidor TCP escutando na porta 9999...")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

# ======= Iniciar tudo =======
if __name__ == '__main__':
    threading.Thread(target=start_tcp_server, daemon=True).start()
    socketio.run(app, debug=True, use_reloader=False)
