import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load the JSON data from the file with 'utf-8' encoding
with open('data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Initialize variables for tracking
seen_combinations = set()
items_removed = 0
total_items = 0
lock = threading.Lock()  # To avoid race conditions with shared data

# Pre-calculate total number of items across all vaults
for vault in data["vaults"].values():
    total_items += len(vault['items'])

def process_vault(vault_key, vault):
    global items_removed, seen_combinations
    local_removed = 0
    new_items = []

    print(f"Vault: {vault['name']}")
    total_passwords = len(vault['items'])
    print(f"Total passwords: {total_passwords}")

    for item in vault['items']:
        # Safely retrieve username and password
        username = item['data']['content'].get('itemUsername')
        password = item['data']['content'].get('password')
        url = item['data']['content']['urls'][0] if item['data']['content'].get('urls') else "No URL"

        # Skip items that don't have both a username and password
        if username and password:
            with lock:  # Protect shared resource
                if (username, password) in seen_combinations:
                    items_removed += 1
                    local_removed += 1
                    print(f"[{items_removed} | {total_items}] Removed duplicate: {url} + {username}")
                else:
                    seen_combinations.add((username, password))
                    new_items.append(item)
        else:
            # If no username or password is present, keep the item without modification
            new_items.append(item)

    # Update vault with filtered items (duplicates removed)
    vault['items'] = new_items
    return local_removed

# Use multithreading to process vaults concurrently
with ThreadPoolExecutor() as executor:
    futures = [executor.submit(process_vault, vault_key, vault) for vault_key, vault in data["vaults"].items()]

    for future in as_completed(futures):
        future.result()  # Wait for each thread to complete

# Write the cleaned-up data back to a file
with open('cleaned_data.json', 'w', encoding='utf-8') as output_file:
    json.dump(data, output_file, indent=4)

print(f"Total items removed: {items_removed}")
