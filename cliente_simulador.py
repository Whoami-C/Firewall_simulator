import socket, threading, time, ipaddress, random

SERVER_HOST, SERVER_PORT = 'localhost', 9999
SEND_INTERVAL = 5  # segundos

# ---------- estado ----------
_ips: list[str] = []          # lista viva de IPs em uso
_lock = threading.Lock()      # evita corrida de threads


def _simulate_client(ip: str) -> None:
    """Loop infinito enviando <ip> ao servidor."""
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((SERVER_HOST, SERVER_PORT))
                s.send(ip.encode())
        except Exception:
            pass
        time.sleep(SEND_INTERVAL)


def add_ips(new_ips):
    """
    Pode receber:
        • um único str  -> '10.0.0.9'
        • um iterável     -> ['10.0.0.9', '10.0.0.10']
        • um int          -> gera N IPs randômicos 192.168.x.x
    """
    # ­normaliza parámetro
    if isinstance(new_ips, int):
        new_ips = [
            f"192.168.{random.randint(0,255)}.{random.randint(1,254)}"
            for _ in range(new_ips)
        ]
    elif isinstance(new_ips, str):
        new_ips = [new_ips]

    for ip in new_ips:
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            print(f"[WARN] IP inválido ignorado: {ip}")
            continue

        with _lock:
            if ip in _ips:
                continue
            _ips.append(ip)

        threading.Thread(target=_simulate_client, args=(ip,),
                         daemon=True).start()
        print(f"[INFO] IP adicionado ao simulador: {ip}")


# ---------- inicial ----------
_DEFAULT_IPS = ['192.168.1.2', '10.0.0.5', '172.16.0.3']
add_ips(_DEFAULT_IPS)               # dispara threads iniciais
_INVADER_IP = random.choice(_DEFAULT_IPS)
print(f"[INFO] IP invasor escolhido: {_INVADER_IP}")

def get_invader_ip():
    """Permite que o Flask saiba qual é o IP invasor."""
    return _INVADER_IP