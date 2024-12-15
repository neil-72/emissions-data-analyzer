from typing import Optional
import json

def save_json(data: dict, filepath: str) -> None:
    """Save data to JSON file with proper formatting."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def load_json(filepath: str) -> Optional[dict]:
    """Load data from JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {str(e)}")
        return None