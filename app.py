import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import subprocess
import logging
from logging.handlers import RotatingFileHandler
import platform
from datetime import datetime
import paramiko  # Add paramiko for SSH
import uuid

# Set the working directory
WORKING_DIR = os.getenv('WORKING_DIR', os.path.dirname(os.path.abspath(__file__)))
os.chdir(WORKING_DIR)

app = Flask(__name__)

# Use environment variables for configuration
DATA_DIR = os.getenv('DATA_DIR', os.path.join(WORKING_DIR, 'data'))
DATA_FILE = os.path.join(DATA_DIR, "items.json")
LOG_DIR = os.getenv('LOG_DIR', os.path.join(WORKING_DIR, 'logs'))

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Helper functions
def load_items():
    print(f"Attempting to load data from: {DATA_FILE}")
    if not os.path.exists(DATA_FILE):
        print(f"Data file not found: {DATA_FILE}. Creating a new one.")
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump([], f)
        except Exception as e:
            print(f"Error creating new data file: {e}")
            return []
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {DATA_FILE}: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error accessing {DATA_FILE}: {e}")
        return []

def save_items(items):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(items, f, indent=4)
    except Exception as e:
        print(f"Error saving items: {e}")

# Function to ping a device
def ping_device(ip_address):
    # Determine the command based on the operating system
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', ip_address]

    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
        return "unreachable" not in output.lower() and "timed out" not in output.lower()
    except subprocess.CalledProcessError as e:
        print(f"Ping failed for {ip_address}: {e.output}")
        return False

def traceroute(ip_address):
    param = '-n' if platform.system().lower() == 'windows' else '-q'
    command = ['tracert' if platform.system().lower() == 'windows' else 'traceroute', ip_address]
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
        return output
    except subprocess.CalledProcessError as e:
        print(f"Traceroute failed for {ip_address}: {e.output}")
        return None

# Function to setup logging for a device
def setup_device_logger(device_id):
    logger = logging.getLogger(f'device_{device_id}')
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(os.path.join(LOG_DIR, f'device_{device_id}.log'), maxBytes=100*1024, backupCount=5)
    logger.addHandler(handler)
    return logger

# Routes
@app.route('/')
def index():
    items = load_items()
    physical_hosts = [item for item in items if item['type'] == 'physical']
    for host in physical_hosts:
        host['vms'] = [item for item in items if item.get('hosted_on') == host['hostname']]
    return render_template('index.html', items=items, physical_hosts=physical_hosts)

@app.route('/add_item', methods=['POST'])
def add_item():
    items = load_items()
    new_item = {
        'id': str(uuid.uuid4()),
        'ip_address': request.form['ip_address'],
        'note': request.form.get('note', ''),
        'hostname': request.form['hostname'],
        'type': request.form['type'],
        'os': request.form.get('os', ''),
        'username': request.form.get('username', ''),
        'password': request.form.get('password', ''),
        'last_ping_status': 'Unknown',
        'hosted_on': request.form.get('hosted_on', 'NA')
    }
    items.append(new_item)
    save_items(items)
    return redirect(url_for('index'))

@app.route('/delete_item/<item_id>', methods=['POST'])
def delete_item(item_id):
    items = load_items()
    items = [item for item in items if item['id'] != item_id]
    save_items(items)
    return redirect(url_for('index'))

@app.route('/edit_item/<item_id>', methods=['POST'])
def edit_item(item_id):
    items = load_items()
    for item in items:
        if item['id'] == item_id:
            item['ip_address'] = request.form['ip_address']
            item['note'] = request.form['note']
            item['hostname'] = request.form['hostname']
            item['type'] = request.form['type']
            item['os'] = request.form['os']
            item['username'] = request.form.get('username', item.get('username'))
            item['password'] = request.form.get('password', item.get('password'))
            break
    save_items(items)
    return redirect(url_for('index'))

@app.route('/api/device_status', methods=['GET'])
def api_device_status():
    return jsonify(load_items())

@app.route('/add_service/<item_id>', methods=['POST'])
def add_service(item_id):
    items = load_items()
    for item in items:
        if item['id'] == item_id:
            service = {
                'url': request.form['url'],
                'port': request.form['port']
            }
            item['services'].append(service)
            break
    save_items(items)
    return redirect(url_for('index'))

@app.route('/delete_service/<item_id>/<service_index>', methods=['POST'])
def delete_service(item_id, service_index):
    items = load_items()
    for item in items:
        if item['id'] == item_id:
            try:
                del item['services'][int(service_index)]
            except (IndexError, ValueError):
                pass
            break
    save_items(items)
    return redirect(url_for('index'))

@app.route('/ping_device/<item_id>', methods=['GET'])
def ping_device_route(item_id):
    items = load_items()
    for item in items:
        if item['id'] == item_id:
            is_reachable = ping_device(item['ip_address'])
            logger = setup_device_logger(item_id)
            logger.info(f"Pinged {item['ip_address']}: {'Reachable' if is_reachable else 'Unreachable'}")
            
            # Update the item's last ping status and time
            item['last_ping_status'] = 'Reachable' if is_reachable else 'Unreachable'
            item['last_ping_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Log the updated time for debugging
            print(f"Updated last_ping_time for {item_id}: {item['last_ping_time']}")
            
            # Save the updated items
            save_items(items)
            
            return jsonify({'status': 'success', 'reachable': is_reachable})
    return jsonify({'status': 'error', 'message': 'Device not found'})

@app.route('/traceroute_device/<item_id>', methods=['GET'])
def traceroute_device_route(item_id):
    items = load_items()
    for item in items:
        if item['id'] == item_id:
            result = traceroute(item['ip_address'])
            if result:
                # Parse traceroute output to find new devices
                new_devices = parse_traceroute(result, items)
                return jsonify({'status': 'success', 'result': result, 'new_devices': new_devices})
            else:
                return jsonify({'status': 'error', 'message': 'Traceroute failed'})
    return jsonify({'status': 'error', 'message': 'Device not found'})

def parse_traceroute(output, existing_items):
    new_devices = []
    lines = output.splitlines()
    for line in lines:
        # Extract IP addresses from traceroute output
        if '(' in line and ')' in line:
            ip_address = line.split('(')[1].split(')')[0]
            if not any(item['ip_address'] == ip_address for item in existing_items):
                new_devices.append(ip_address)
    return new_devices

def ssh_into_device(ip_address, username, password):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip_address, username=username, password=password)
        stdin, stdout, stderr = client.exec_command('esxcli vm process list')
        output = stdout.read().decode()
        client.close()
        return output
    except Exception as e:
        print(f"SSH connection failed: {e}")
        return None

@app.route('/ssh_device/<item_id>', methods=['GET'])
def ssh_device_route(item_id):
    items = load_items()
    for item in items:
        if item['id'] == item_id:
            username = item.get('username')
            password = item.get('password')
            if not username or not password:
                return jsonify({'status': 'error', 'message': 'Credentials required'})
            
            output = ssh_into_device(item['ip_address'], username, password)
            if output:
                # Process output to extract VM information
                return jsonify({'status': 'success', 'output': output})
            else:
                return jsonify({'status': 'error', 'message': 'SSH failed'})
    return jsonify({'status': 'error', 'message': 'Device not found'})

if __name__ == '__main__':
    app.run(debug=True)
