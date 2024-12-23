import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import subprocess
import logging
from logging.handlers import RotatingFileHandler
import platform
from datetime import datetime

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
        'id': str(len(items) + 1),
        'ip_address': request.form['ip_address'],
        'note': request.form['note'],
        'hostname': request.form['hostname'],
        'type': request.form['type'],
        'os': request.form['os'],
        'hosted_on': request.form.get('hosted_on', 'NA'),
        'services': []
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

@app.route('/edit_item_details/<item_id>', methods=['POST'])
def edit_item_details(item_id):
    items = load_items()
    for item in items:
        if item['id'] == item_id:
            item['ip_address'] = request.form['ip_address']
            item['note'] = request.form['note']
            item['hostname'] = request.form['hostname']
            item['type'] = request.form['type']
            item['os'] = request.form['os']
            item['hosted_on'] = request.form.get('hosted_on', 'NA')
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
            
            # Save the updated items
            save_items(items)
            
            return jsonify({'status': 'success', 'reachable': is_reachable})
    return jsonify({'status': 'error', 'message': 'Device not found'})

if __name__ == '__main__':
    app.run(debug=True)
