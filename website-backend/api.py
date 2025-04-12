from flask import Flask, request, jsonify, session, send_file, redirect, send_from_directory
from flask_cors import CORS
import bcrypt
import os
import psutil
import time
import threading
import requests

app = Flask(__name__, static_folder=None)
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)

app.config.update(
    SESSION_COOKIE_NAME='imtesla_session',  # your cookie name if you would want to
    SESSION_COOKIE_DOMAIN='.imtesla.pl',    # your URL
    SESSION_COOKIE_SECURE=True,             
    SESSION_COOKIE_HTTPONLY=True,           
    SESSION_COOKIE_SAMESITE='Lax',          
    PERMANENT_SESSION_LIFETIME=86400,       
)

correct_passwd = "$2b$12$BaeEya6LgLo77oHglHIq1O5QzO2cVB4/vMcpeJV5sJYfSoh64zuKW"

stats_data = {
    "cpu_usage": 0,
    "memory_usage": 0,
    "memory_total": 0,
    "disk_usage": 0,
    "disk_total": 0,
    "uptime_days": 0
}

# add your services you would want to check, the server will automaticaly check for them if you add them here
# then in HTML, just parse the JSON request, add another div element with service name and description like other ones
services = {
    "kinectvideo": False,
    "nginx": False,
    "kinectaudio": False,
    "dashboard-backend": False
}

@app.route('/auth', methods=['POST'])
def authenticate():
    data = request.get_json()
    if not data or 'password' not in data:
        return jsonify({"error": "Password is required"}), 400

    if bcrypt.checkpw(data['password'].encode('utf-8'), correct_passwd.encode('utf-8')):
        session['authenticated'] = True
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Invalid password"}), 401

@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_public(path):
    if not session.get('authenticated'):
        return redirect('https://imtesla.pl') # your URL
    
    safe_path = os.path.join('public/', path)
    if not os.path.abspath(safe_path).startswith(os.path.abspath('public/')):
        return "Forbidden", 403
    
    try:
        return send_from_directory('public/', path)
    except:
        return send_from_directory('public/', 'index.html') 
    
    
def stats_updater():
    while True:
        try:
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            uptime_seconds = time.time() - psutil.boot_time()
            
            stats_data["cpu_usage"] = cpu
            stats_data["memory_usage"] = round(memory.used / (1024 ** 3), 2)
            stats_data["memory_total"] = round(memory.total / (1024 ** 3), 2)
            stats_data["disk_usage"] = round(disk.used / (1024 ** 3), 2)
            stats_data["disk_total"] = round(disk.total / (1024 ** 3), 2)
            stats_data["uptime_days"] = round(uptime_seconds / (60 * 60 * 24), 2)
        except Exception as e:
            print(f"Error updating stats: {e}")
        time.sleep(1)

def service_updater():
    while True:
        for service in services.keys():
            try:
                output = os.popen(f'systemctl is-active {service}').read().strip()
                if output == 'active':
                    services[service] = True
                else:
                    services[service] = False
            except Exception as e:
                print(f"Error checking service {service}: {e}")
        time.sleep(5)

@app.route('/stats/')
def get_stats():
    if not session.get('authenticated'):
        return redirect('https://imtesla.pl') # your URL

    return jsonify(stats_data)

@app.route('/services/')
def get_services():
    if not session.get('authenticated'):
        return redirect('https://imtesla.pl') # your URL
    
    return jsonify(services)

@app.route('/auth-endpoint') # safety first
def auth_endpoint():
    if session.get('authenticated'):
        return "", 200
    return "", 401

if __name__ == '__main__':
    if not os.path.exists('public'):
        os.makedirs('public')
    threading.Thread(target=stats_updater, daemon=True).start()
    threading.Thread(target=service_updater, daemon=True).start()
    app.run(debug=True, port=3000, host='0.0.0.0')