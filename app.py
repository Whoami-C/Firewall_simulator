from flask import Flask, render_template, request, redirect, url_for
import json

app = Flask(__name__)
BLACKLIST_FILE = 'blacklist.json'

# Carrega blacklist de arquivo
def load_blacklist():
    try:
        with open(BLACKLIST_FILE, 'r') as f:
            return set(json.load(f))
    except:
        return set()

# Salva blacklist no arquivo
def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, 'w') as f:
        json.dump(list(blacklist), f)

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

if __name__ == '__main__':
    app.run(debug=True)
