import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO
from enum import Enum
import threading
import socket
import json
import cliente_simulador

INVADER_IP = cliente_simulador.get_invader_ip()

app = Flask(__name__)
socketio = SocketIO(app)
BLACKLIST_FILE = 'blacklist.json'
RULES_FILE = "rules.json"                 
class Proto(str, Enum): TCP="TCP"; UDP="UDP"; ANY="ANY"

# ========== UTILS de regras ==========
def load_rules():
    """Retorna lista de dicts: [{'ip':'1.1.1.1','port':80,'proto':'TCP'}, …]"""
    try:
        with open(RULES_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_rules(rules):
    with open(RULES_FILE, "w") as f:
        json.dump(rules, f, indent=2)

def match_rule(ip, port, proto):
    """True se (ip,port,proto) bate qualquer regra."""
    for r in load_rules():
        if r["ip"] != ip:          # IP precisa bater
            continue
        if r["proto"] != "ANY" and r["proto"] != proto:
            continue
        if r["port"] != 0 and r["port"] != port:
            continue
        return True
    return False
# =====================================

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
    return render_template(
        'index.html', 
        blacklist=blacklist, 
        rules=load_rules()
        )

@app.route('/bloquear', methods=['POST'])
def bloquear():
    ip = request.form['ip']
    blacklist = load_blacklist()
    blacklist.add(ip)
    save_blacklist(blacklist)
    return redirect(url_for('index'))

@app.route('/liberar', methods=['POST'])
def liberar():
    ip    = request.form['ip']
    port  = request.form.get('port', '')
    proto = request.form.get('proto', '').upper()

    # ❶  – se porta ou proto preenchidos ⇒ remover regra específica
    if port or proto:
        port   = int(port or 0)
        rules  = load_rules()
        rules  = [r for r in rules if not (r['ip']==ip and r['port']==port and r['proto']==proto)]
        save_rules(rules)
    # ❷  – caso contrário ⇒ liberar IP da blacklist simples
    else:
        bl = load_blacklist()
        bl.discard(ip)
        save_blacklist(bl)

    return redirect(url_for('index'))


# ---------- rota /simular -----------
@app.route('/simular', methods=['POST'])
def simular():
    ip    = request.form['ip']
    port  = int(request.form['port'] or 0)
    proto = request.form['proto'].upper() or 'TCP'

    # se porta 0 ⇒ gera tráfego em portas aleatórias (funcionalidade antiga)
    if port == 0:
        cliente_simulador.add_ips(ip)
    else:
        cliente_simulador.add_client(ip, port, proto)

    return redirect(url_for('index'))
# ------------------------------------


# -------- NOVA rota: /bloquear_regra ---
@app.route("/bloquear_regra", methods=["POST"])
def bloquear_regra():
    ip    = request.form["ip"]
    port  = int(request.form["port"] or 0)            # 0  ⇒ “qualquer porta”
    proto = request.form["proto"].upper()             # TCP/UDP/ANY

    rules = load_rules()
    rule  = {"ip": ip, "port": port, "proto": proto}
    if rule not in rules:
        rules.append(rule)
        save_rules(rules)
    return redirect(url_for("index"))
# --------------------------------------

# ===== servidor TCP =====
def handle_client(conn):
    try:
        ip = conn.recv(1024).decode()
        status = "BLOQUEADO" if ip in load_blacklist() else "ACEITO"
        log = f"Conexão de {ip}: {status}"
        print(log)
        socketio.emit('log', log)
    finally:
        conn.close()

def start_tcp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 9999));  server.listen(5)
    print("Servidor TCP escutando na porta 9999…")
    while True:
        conn, _ = server.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

# ======= Servidor TCP =======
def handle_client(conn):
    try:
        raw = conn.recv(1024).decode().strip()        # "IP|PORT|PROTO"
        ip, port, proto = raw.split("|")
        port  = int(port)
        proto = proto.upper()

        blocked = match_rule(ip, port, proto) or (ip in load_blacklist())
        status  = "BLOQUEADO" if blocked else "ACEITO"

        tag = " <span class='tag-invader'>[INVASOR]</span>" if ip == INVADER_IP else ""
        log = f"Conexão de {ip}:{port}/{proto}: {status}{tag}"
        print(log)
        socketio.emit("log", log)
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
