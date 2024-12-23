from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os

app = Flask(__name__)
DATA_DIR = r"\\10.0.10.31\Media\Dev\[001] landing page\data"
DATA_FILE = os.path.join(DATA_DIR, "items.json")

# Helper functions
def load_items():
    print(f"Attempting to load data from: {DATA_FILE}")
    if not os.path.exists(DATA_DIR):
        print(f"Data directory not found: {DATA_DIR}. Creating a new one.")
        try:
            os.makedirs(DATA_DIR)
        except Exception as e:
            print(f"Error creating data directory: {e}")
            return []

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

if __name__ == '__main__':
    app.run(debug=True)
