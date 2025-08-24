# import requests
# import time

# url = "http://3.90.236.235:3018/tasks/"
# numberOfRequests = 500

# totalTime = 0

# def time_ms():
#     return round(time.time() * 1000)

# for i in range(numberOfRequests):
#     startTime = time_ms()
#     response = requests.get(url)
#     request_time = time_ms() - startTime
#     totalTime += request_time

#     print(f'Request {i + 1} returned with status: {response.status_code} in {request_time}ms')

# print(f'Average time {totalTime / numberOfRequests}')

import requests, json, sys

#BASE_URL = "http://3.90.236.235:3018"
BASE_URL = "http://localhost:3018"
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
    # Only exit if not allowed and status is 400/500 (but not 405)
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
        print_response(r, allow_error=True)

    # Get all groups (no auth)
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
    r = requests.get(f"{BASE_URL}/group/steam/top-games", headers=auth_headers(token))
    print("Get top games (auth):")
    print_response(r)

    # Top games (no auth)
    r = requests.get(f"{BASE_URL}/group/steam/top-games")
    print("Get top games (no auth):")
    print_response(r)

    # Item history (missing params)
    r = requests.post(f"{BASE_URL}/group/steam/item-history", headers=auth_headers(token), json={})
    print("Get item history (missing params):")
    print_response(r, allow_error=True)

    # Item history (invalid appid)
    r = requests.post(f"{BASE_URL}/group/steam/item-history", headers=auth_headers(token), json={"appid": 999999, "item_name": "Nonexistent"})
    print("Get item history (invalid appid):")
    print_response(r, allow_error=True)

    # Item history (valid, but may need to adjust appid/item_name for your inventory)
    r = requests.post(f"{BASE_URL}/group/steam/item-history", headers=auth_headers(token), json={"appid": 440, "item_name": "Civic Duty Mk.II Knife (Factory New)"})
    print("Get item history (valid):")
    print_response(r)

if __name__ == "__main__":
    token = get_auth_token()
    if not token:
        print("Could not get auth token, aborting tests.")
    else:
        test_groups(token)
        test_steam(token)