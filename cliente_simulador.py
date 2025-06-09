import socket
import threading
import time

def simulate_client(ip):
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('localhost', 9999))
            s.send(ip.encode())
            s.close()
        except:
            pass
        time.sleep(2)

ips = ['192.168.1.2', '10.0.0.5', '172.16.0.3']

for ip in ips:
    threading.Thread(target=simulate_client, args=(ip,), daemon=True).start()

while True:
    time.sleep(1)
