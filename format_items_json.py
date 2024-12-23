import os
import json
from data_schema import validate_item, create_new_item

DATA_DIR = r'\\10.0.10.31\Media\Dev\[001] landing page\data'  # Use raw string for network path
DATA_FILE = os.path.join(DATA_DIR, 'items.json')

def format_items_json():
    # Ensure the data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # Check if the data file exists
    if not os.path.exists(DATA_FILE):
        print(f"{DATA_FILE} does not exist. Creating a new file.")
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)
        return

    # Load and validate the JSON data
    try:
        with open(DATA_FILE, 'r+') as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Data is not a list")

            # Validate each item in the list
            for i, item in enumerate(data):
                if not validate_item(item):
                    print(f"Item at index {i} is invalid. Resetting to default.")
                    data[i] = create_new_item()

            # Rewind and rewrite the file with formatted data
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=4)
            print(f"{DATA_FILE} has been formatted successfully.")

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error reading {DATA_FILE}: {e}. Resetting the file.")
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)

if __name__ == "__main__":
    format_items_json() 