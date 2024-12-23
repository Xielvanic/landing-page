import uuid

def create_new_item(ip_address='', note=None, hostname=None, type='network', os='unknown', hosted_on='NA'):
    return {
        'id': str(uuid.uuid4()),  # Generate a unique ID
        'ip_address': ip_address,
        'note': note,
        'hostname': hostname,
        'last_ping_status': 'Unknown',  # Add last_ping_status field
        'type': type,  # Ensure type is set here
        'os': os,  # Add OS field
        'hosted_on': hosted_on  # Add hosted_on field
    }

def validate_item(item):
    required_keys = ['id', 'ip_address', 'note', 'hostname']
    for key in required_keys:
        if key not in item:
            return False
    return True 