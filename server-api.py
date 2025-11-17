#!/usr/bin/env python3
"""
Simple API Server untuk Remote Control
Deploy ini di server/PC Anda, lalu saya bisa remote dari chat ini!
"""

from flask import Flask, request, jsonify
import subprocess
import os
import hashlib
import hmac
from functools import wraps

app = Flask(__name__)

# GANTI INI DENGAN SECRET KEY ANDA!
SECRET_KEY = os.getenv("API_SECRET", "CHANGE-THIS-SECRET-KEY-123")

def require_auth(f):
    """Decorator untuk authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Unauthorized"}), 401

        token = auth_header.replace('Bearer ', '')
        if token != SECRET_KEY:
            return jsonify({"error": "Invalid token"}), 403

        return f(*args, **kwargs)
    return decorated

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Server is running"})

@app.route('/execute', methods=['POST'])
@require_auth
def execute_command():
    """Execute shell command"""
    data = request.get_json()
    command = data.get('command')

    if not command:
        return jsonify({"error": "No command provided"}), 400

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )

        return jsonify({
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Command timeout"}), 408
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/git/pull', methods=['POST'])
@require_auth
def git_pull():
    """Git pull in specified directory"""
    data = request.get_json()
    directory = data.get('directory', '.')

    try:
        os.chdir(directory)
        result = subprocess.run(['git', 'pull'], capture_output=True, text=True)
        return jsonify({
            "success": result.returncode == 0,
            "output": result.stdout + result.stderr
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/service/restart', methods=['POST'])
@require_auth
def restart_service():
    """Restart systemd service or PM2 process"""
    data = request.get_json()
    service_type = data.get('type', 'systemd')  # systemd, pm2, docker
    service_name = data.get('name')

    if not service_name:
        return jsonify({"error": "No service name provided"}), 400

    try:
        if service_type == 'systemd':
            cmd = f'sudo systemctl restart {service_name}'
        elif service_type == 'pm2':
            cmd = f'pm2 restart {service_name}'
        elif service_type == 'docker':
            cmd = f'docker restart {service_name}'
        else:
            return jsonify({"error": "Invalid service type"}), 400

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return jsonify({
            "success": result.returncode == 0,
            "output": result.stdout + result.stderr
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/service/status', methods=['GET'])
@require_auth
def service_status():
    """Check service status"""
    service_type = request.args.get('type', 'systemd')
    service_name = request.args.get('name')

    if not service_name:
        return jsonify({"error": "No service name provided"}), 400

    try:
        if service_type == 'systemd':
            cmd = f'systemctl status {service_name}'
        elif service_type == 'pm2':
            cmd = f'pm2 status {service_name}'
        elif service_type == 'docker':
            cmd = f'docker ps --filter name={service_name}'
        else:
            return jsonify({"error": "Invalid service type"}), 400

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return jsonify({
            "output": result.stdout,
            "running": result.returncode == 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logs', methods=['GET'])
@require_auth
def get_logs():
    """Get logs from file or service"""
    log_file = request.args.get('file')
    lines = request.args.get('lines', '100')

    if not log_file:
        return jsonify({"error": "No log file specified"}), 400

    try:
        result = subprocess.run(
            f'tail -n {lines} {log_file}',
            shell=True,
            capture_output=True,
            text=True
        )
        return jsonify({
            "logs": result.stdout,
            "error": result.stderr
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/deploy', methods=['POST'])
@require_auth
def deploy():
    """Deploy application (git pull + restart)"""
    data = request.get_json()
    directory = data.get('directory', '.')
    service_type = data.get('service_type', 'pm2')
    service_name = data.get('service_name')

    if not service_name:
        return jsonify({"error": "No service name provided"}), 400

    try:
        # Git pull
        os.chdir(directory)
        git_result = subprocess.run(['git', 'pull'], capture_output=True, text=True)

        # Install dependencies (if package.json or requirements.txt exists)
        install_output = ""
        if os.path.exists('package.json'):
            install_result = subprocess.run(['npm', 'install'], capture_output=True, text=True)
            install_output = install_result.stdout
        elif os.path.exists('requirements.txt'):
            install_result = subprocess.run(['pip', 'install', '-r', 'requirements.txt'], capture_output=True, text=True)
            install_output = install_result.stdout

        # Restart service
        if service_type == 'pm2':
            restart_cmd = f'pm2 restart {service_name}'
        elif service_type == 'systemd':
            restart_cmd = f'sudo systemctl restart {service_name}'
        elif service_type == 'docker':
            restart_cmd = f'docker restart {service_name}'
        else:
            restart_cmd = None

        restart_output = ""
        if restart_cmd:
            restart_result = subprocess.run(restart_cmd, shell=True, capture_output=True, text=True)
            restart_output = restart_result.stdout

        return jsonify({
            "success": True,
            "git_pull": git_result.stdout,
            "install": install_output,
            "restart": restart_output
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/system/info', methods=['GET'])
@require_auth
def system_info():
    """Get system information"""
    try:
        # CPU, Memory, Disk
        cpu = subprocess.run("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'", shell=True, capture_output=True, text=True).stdout.strip()
        memory = subprocess.run("free -h | awk '/^Mem:/ {print $3\"/\"$2}'", shell=True, capture_output=True, text=True).stdout.strip()
        disk = subprocess.run("df -h / | awk 'NR==2 {print $3\"/\"$2\" (\"$5\" used)\"}'", shell=True, capture_output=True, text=True).stdout.strip()
        uptime = subprocess.run("uptime -p", shell=True, capture_output=True, text=True).stdout.strip()

        return jsonify({
            "cpu_usage": cpu,
            "memory": memory,
            "disk": disk,
            "uptime": uptime
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 Server API running on port {port}")
    print(f"⚠️  Make sure to set API_SECRET environment variable!")
    app.run(host='0.0.0.0', port=port, debug=False)
