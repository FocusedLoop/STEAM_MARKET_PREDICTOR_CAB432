import requests, json, sys, time, threading

BASE_URL = "http://ec2-13-236-117-13.ap-southeast-2.compute.amazonaws.com:3010"
#BASE_URL = "http://localhost:3010"
USERNAME = "testuser"
PASSWORD = "testpass"
STEAM_ID = "76561198281140980"

def print_response(r, allow_error=False):
    print(f"Status: {r.status_code}")
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)
    print("-" * 40)
    if allow_error and r.status_code == 200:
        print("Expected error, but got success (200). Exiting test script.")
        sys.exit(1)
    if not allow_error and (r.status_code == 500 or r.status_code == 400 or r.status_code == 404) and r.status_code != 405:
        print("Error encountered, exiting test script.")
        sys.exit(1)

def get_auth_token():
    # Sign up (ignore if already exists)
    r = requests.post(f"{BASE_URL}/users/sign-up", json={
        "username": USERNAME,
        "password": PASSWORD,
        "steam_id": STEAM_ID
    })
    if r.status_code not in (200, 400):
        print("Sign-up failed:")
        print_response(r)
        return None
    # Login
    r = requests.post(f"{BASE_URL}/users/login", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    print("Login response:")
    print_response(r)
    if r.status_code == 200:
        return r.json().get("authToken")
    return None

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

def test_groups(token):
    print("Testing group endpoints...")

    # Create group (missing title) -- 400 is expected, don't exit
    r = requests.post(f"{BASE_URL}/group", headers=auth_headers(token), json={})
    print("Create group (missing title):")
    print_response(r, allow_error=True)

    # Create group (valid)
    r = requests.post(f"{BASE_URL}/group", headers=auth_headers(token), json={"title": "My Test Group"})
    print("Create group (valid):")
    print_response(r)
    group_id = r.json().get("id") if r.status_code == 200 else None

    # Update group (missing title) -- 400/405 may be expected
    if group_id:
        r = requests.put(f"{BASE_URL}/group/{group_id}", headers=auth_headers(token), json={})
        print("Update group (missing title):")
        print_response(r, allow_error=True)

        # Update group (valid)
        r = requests.put(f"{BASE_URL}/group/{group_id}", headers=auth_headers(token), json={"title": "Renamed Group"})
        print("Update group (valid):")
        print_response(r)

    # Get all groups (no auth)
    r = requests.get(f"{BASE_URL}/group")
    print("Get all groups:")
    print_response(r)

    # Cached get all groups (no auth)
    r = requests.get(f"{BASE_URL}/group")
    print("Get all groups:")
    print_response(r)


    # Get group by ID (no auth, invalid ID)
    r = requests.get(f"{BASE_URL}/group/999999")
    print("Get group by invalid ID:")
    print_response(r, allow_error=True)

    # Get group by ID (no auth, valid)
    if group_id:
        r = requests.get(f"{BASE_URL}/group/{group_id}")
        print("Get group by valid ID:")
        print_response(r)

    # Add item to group (missing fields)
    if group_id:
        r = requests.post(f"{BASE_URL}/group/{group_id}/items", headers=auth_headers(token), json={})
        print("Add item to group (missing fields):")
        print_response(r, allow_error=True)

        # Add item to group (valid)
        item_json = {
            "success": True,
            "prices": [
                ["Oct 21 2017 01: +0", 3.077, "1"],
                ["Oct 22 2017 01: +0", 0.934, "3"]
            ]
        }
        r = requests.post(
            f"{BASE_URL}/group/{group_id}/items",
            headers=auth_headers(token),
            json={"item_name": "Test Item 1", "item_json": item_json}
        )
        print("Add item to group (valid):")
        print_response(r)

        # Get second item
        r = requests.post(
            f"{BASE_URL}/group/{group_id}/items",
            headers=auth_headers(token),
            json={"item_name": "Test Item 2", "item_json": item_json}
        )
        print("Add 2nd item to group (valid):")
        print_response(r)

        # Display both items
        r = requests.get(
            f"{BASE_URL}/group/{group_id}/items",
            headers=auth_headers(token)
        )
        print("Get group items after adding 2 items by valid ID:")
        print_response(r)

        # Remove item from group (missing fields)
        r = requests.delete(f"{BASE_URL}/group/{group_id}/items", headers=auth_headers(token), json={})
        print("Remove item from group (missing fields):")
        print_response(r, allow_error=True)

        # Remove item from group (valid)
        r = requests.delete(
            f"{BASE_URL}/group/{group_id}/items",
            headers=auth_headers(token),
            json={"item_name": "Test Item 2"}
        )
        print("Remove 1 item from group (valid):")
        print_response(r)

        # Display remaining item
        r = requests.get(
            f"{BASE_URL}/group/{group_id}/items",
            headers=auth_headers(token)
        )
        print("Get group items after removing 1 items by valid ID:")
        print_response(r)

        # Delete group (valid)
        r = requests.delete(f"{BASE_URL}/group/{group_id}", headers=auth_headers(token))
        print("Delete group (valid):")
        print_response(r)

        # Delete group (already deleted)
        r = requests.delete(f"{BASE_URL}/group/{group_id}", headers=auth_headers(token))
        print("Delete group (already deleted):")
        print_response(r, allow_error=True)

def test_steam(token):
    print("Testing Steam endpoints...")

    # Top games (auth required)
    r = requests.get(f"{BASE_URL}/steam/top-games", headers=auth_headers(token))
    print("Get top games (auth):")
    print_response(r)

    # Top games (no auth)
    r = requests.get(f"{BASE_URL}/steam/top-games")
    print("Get top games (no auth):")
    print_response(r)

    # Item history (missing params)
    r = requests.post(f"{BASE_URL}/steam/item-history", headers=auth_headers(token), json={})
    print("Get item history (missing params):")
    print_response(r, allow_error=True)

    # Item history (invalid appid)
    r = requests.post(f"{BASE_URL}/steam/item-history", headers=auth_headers(token), json={"appid": 999999, "item_name": "Nonexistent"})
    print("Get item history (invalid appid):")
    print_response(r, allow_error=True)

    # Item history (valid, but may need to adjust appid/item_name for your inventory)
    r = requests.post(f"{BASE_URL}/steam/item-history", headers=auth_headers(token), json={"appid": 440, "item_name": "Civic Duty Mk.II Knife (Factory New)"})
    print("Get item history (valid):")
    print_response(r)

def test_group_models(token):
    print("Testing group model endpoints...")

    # 0. Create a new group
    r = requests.post(f"{BASE_URL}/group", headers=auth_headers(token), json={"title": "Model Test Group"})
    print("Create group for model tests:")
    print_response(r)
    group_id = r.json().get("id")
    if not group_id:
        print("Failed to create group, aborting group model tests.")
        return

    # 0.1 Load price histories
    with open("price_history_raw_1.json") as f:
        price_history_1 = json.load(f)
    with open("price_history_raw_2.json") as f:
        price_history_2 = json.load(f)

    # 0.2 Add item 1
    r = requests.post(
        f"{BASE_URL}/group/{group_id}/items",
        headers=auth_headers(token),
        json={"item_name": "Test Item 1", "item_json": price_history_1}
    )
    print("Add item 1 to group:")
    print_response(r)
    item_id_1 = r.json().get("id")

    # 0.3 Add item 2
    r = requests.post(
        f"{BASE_URL}/group/{group_id}/items",
        headers=auth_headers(token),
        json={"item_name": "Test Item 2", "item_json": price_history_2}
    )
    print("Add item 2 to group:")
    print_response(r)
    item_id_2 = r.json().get("id")

    # 1. Train model (missing group_id)
    r = requests.post(f"{BASE_URL}/group/train", headers=auth_headers(token), json={})
    print("Train model (missing group_id):")
    print_response(r, allow_error=True)

    # 2. Train model (valid)
    r = requests.post(f"{BASE_URL}/group/{group_id}/train", headers=auth_headers(token), json={"group_id": group_id})
    print("Train model (valid):")
    print_response(r)

    # 3. Get group models (invalid group_id)
    r = requests.get(f"{BASE_URL}/group/999999/model", headers=auth_headers(token))
    print("Get group models (invalid group_id):")
    print_response(r, allow_error=True)

    # 4. Get group models (valid group_id)
    r = requests.get(f"{BASE_URL}/group/{group_id}/model", headers=auth_headers(token))
    print("Get group models (valid group_id):")
    print_response(r)

    # 5. Predict (missing fields)
    r = requests.post(f"{BASE_URL}/group/{group_id}/predict", headers=auth_headers(token), json={})
    print("Predict (missing fields):")
    print_response(r, allow_error=True)

    # 6. Predict (invalid item_id)
    r = requests.post(
        f"{BASE_URL}/group/{group_id}/predict",
        headers=auth_headers(token),
        json={"item_id": 999999, "start_time": "2025-01-01", "end_time": "2025-12-31"}
    )
    print("Predict (invalid item_id):")
    print_response(r, allow_error=True)

    # 7. Predict (valid) for both items
    print(item_id_1, item_id_2)
    for item_id in [item_id_1, item_id_2]:
        r = requests.post(
            f"{BASE_URL}/group/{group_id}/predict",
            headers=auth_headers(token),
            json={"item_id": item_id, "start_time": "2025-07-14", "end_time": "2025-10-18"}
        )
        print(f"Predict (valid) for item {item_id}:")
        print(f"Status: {r.status_code}")
        if r.status_code == 200 and r.headers.get("content-type") == "image/png":
            print("Received PNG image.")
        else:
            print_response(r)
        print("-" * 40)

    # 8. Delete group model (invalid group_id)
    r = requests.delete(f"{BASE_URL}/group/999999/model", headers=auth_headers(token), json={"group_id": 999999})
    print("Delete group model (invalid group_id):")
    print_response(r, allow_error=True)

    # 9. Delete group model (valid group_id)
    r = requests.delete(f"{BASE_URL}/group/{group_id}/model", headers=auth_headers(token))
    print("Delete group model (valid group_id):")
    print_response(r)

    # 10. Delete group model (already deleted)
    r = requests.delete(f"{BASE_URL}/group/{group_id}/model", headers=auth_headers(token))
    print("Delete group model (already deleted):")
    print_response(r, allow_error=True)

# Load tester

from concurrent.futures import ThreadPoolExecutor, as_completed

CONCURRENCY = 2 # Number of parallel requests
SUBMIT_DELAY = 0

def worker(token, group_count, price_history):
    print(f"\n--- Creating group #{group_count} with items ---")
    r = requests.post(f"{BASE_URL}/group", headers=auth_headers(token), json={"title": f"Load Test Group {group_count}"})
    if r.status_code != 200:
        print("Failed to create group, aborting this round.")
        print_response(r)
        return
    group_id = r.json().get("id")
    item_ids = []   
    for i in range(1):
        r = requests.post(
            f"{BASE_URL}/group/{group_id}/items",
            headers=auth_headers(token),
            json={"item_name": f"LoadTestItem{i+1}", "item_json": price_history}
        )
        if r.status_code != 200:
            print(f"Failed to add item {i+1}, skipping group.")
            print_response(r)
            return
        item_ids.append(r.json().get("id"))
    print("Training model for group...")
    r = requests.post(f"{BASE_URL}/group/{group_id}/train", headers=auth_headers(token), json={"group_id": group_id})
    print_response(r)

    # Delete the group model after training
    print(f"Deleting model for group {group_id} after training...")
    r = requests.delete(f"{BASE_URL}/group/{group_id}/model", headers=auth_headers(token))
    print_response(r)

    print(f"Deleting group {group_id} after training...")
    r = requests.delete(f"{BASE_URL}/group/{group_id}", headers=auth_headers(token))
    print_response(r)

def test_server_load(token):
    print("Starting steady server load test (Ctrl+C to stop)...")
    with open("price_history_raw_1.json") as f:
        price_history_1 = json.load(f)
    group_count = 0
    try:
        with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
            futures = set()
            while True:
                # Keep CONCURRENCY jobs running at all times
                while len(futures) < CONCURRENCY:
                    group_count += 1
                    future = executor.submit(worker, token, group_count, price_history_1)
                    futures.add(future)
                # Remove completed futures
                done, futures = set(), futures
                for future in list(futures):
                    if future.done():
                        futures.remove(future)
                time.sleep(SUBMIT_DELAY)
    except KeyboardInterrupt:
        print("Load test stopped.")

if __name__ == "__main__":
    token = get_auth_token()
    if not token:
        print("Could not get auth token, aborting tests.")
    elif "--server-load" in sys.argv or "-l" in sys.argv:
        test_server_load(token)
    else:
        item_id = test_groups(token)
        test_steam(token)
        test_group_models(token)