import requests, json, base64
import streamlit as st

API_URL = "http://server:3010"

### Authentication (public)
# Log user into a session
def login():
    st.header("Login to account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        r = requests.post(f"{API_URL}/users/login", json={"username": username, "password": password})
        if r.status_code == 200:
            st.success("Login successful!")
            st.session_state["token"] = r.json().get("authToken")  # Save token in session_state
            st.rerun()
        else:
            st.error("Login failed.")
    return st.session_state.get("token")

# Log the user out of the session
def logout():
    st.header("Logout of account")
    if st.button("Logout"):
        st.session_state["token"] = None
        st.success("Logged out!")
        st.rerun()

# Register the user for an account, then log the user into a session
def register():
    st.header("Register for an account")
    username = st.text_input("New Username", key="register_username")
    password = st.text_input("New Password", type="password", key="register_password")
    steam_id = st.text_input("Steam ID", key="register_steamid")
    if st.button("Register"):
        r = requests.post(f"{API_URL}/users/sign-up", json={
            "username": username,
            "password": password,
            "steam_id": steam_id
        })
        if r.status_code == 200:
            st.success("Registration successful! Logging you in...")
            login_resp = requests.post(f"{API_URL}/users/login", json={
                "username": username,
                "password": password
            })
            if login_resp.status_code == 200:
                st.session_state["token"] = login_resp.json().get("authToken")
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Registration succeeded but login failed.")
        elif r.status_code == 400:
            st.warning("User already exists or invalid input.")
        else:
            st.error("Registration failed.")

### Groups (public)
# Get all created groups across all users
def get_all_groups():
    st.header("All Groups")
    if st.button("Fetch All Groups"):
        r = requests.get(f"{API_URL}/group")
        if r.status_code == 200:
            groups = r.json()
            if isinstance(groups, list) and groups:
                st.success("Fetched all groups!")
                st.table([{k: v for k, v in group.items()} for group in groups])
            else:
                st.info("No groups found.")
        else:
            try:
                st.error(f"Failed to fetch groups: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to fetch groups: {r.status_code}\n{r.text}")

# Get a specific group by its ID
def get_group_by_id():
    st.header("Get Group by ID")
    group_id = st.number_input("Group ID (fetch)", min_value=1, step=1, key="fetch_group_id")
    if st.button("Fetch Group"):
        r = requests.get(f"{API_URL}/group/{group_id}")
        if r.status_code == 200:
            group = r.json()
            st.success("Fetched group!")
            for k, v in group.items():
                st.write(f"**{k}:** {v}")
        else:
            try:
                st.error(f"Failed to fetch groups: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to fetch groups: {r.status_code}\n{r.text}")

### Groups (authenticated)
# Create a new group, gets tied to that user
def create_group(token: str):
    st.header("Create Group")
    title = st.text_input("Group Title")
    if st.button("Create Group"):
        r = requests.post(f"{API_URL}/group", json={"title": title}, headers={"Authorization": f"Bearer {token}"})
        if r.status_code == 200:
            st.success(f"Group created! ID: {r.json().get('id')}")
        else:
            try:
                st.error(f"Failed to create group: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to create group: {r.status_code}\n{r.text}")

# Update a existing group name that the user owns
def update_group_name(token: str):
    st.header("Update Group Name")
    group_id = st.number_input("Group ID (update)", min_value=1, step=1, key="update_group_id")
    new_title = st.text_input("New Group Title")
    if st.button("Update Group"):
        r = requests.put(
            f"{API_URL}/group/{group_id}",
            json={"title": new_title},
            headers={"Authorization": f"Bearer {token}"}
        )
        if r.status_code == 200:
            st.success("Group updated!")
        else:
            try:
                st.error(f"Failed to update group: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to update group: {r.status_code}\n{r.text}")

# Delete a group owned by the user
def delete_group(token: str):
    st.header("Delete Group")
    group_id = st.number_input("Group ID (to delete)", min_value=1, step=1, key="delete_group")
    if st.button("Delete Group"):
        r = requests.delete(f"{API_URL}/group/{group_id}", headers={"Authorization": f"Bearer {token}"})
        if r.status_code == 200:
            st.success("Group deleted!")
        else:
            try:
                st.error(f"Failed to delete group: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to delete group: {r.status_code}\n{r.text}")

# Get all items in a group that the user owns
def get_group_items(token: str):
    st.header("Get Group Items")
    group_id = st.number_input("Group ID", min_value=1, step=1)
    if st.button("Fetch Group Items"):
        r = requests.get(
            f"{API_URL}/group/{group_id}/items",
            headers={"Authorization": f"Bearer {token}"}
        )
        if r.status_code == 200:
            info = r.json()
            st.success("Fetched group items!")
            if isinstance(info, list) and info:
                display_data = []
                for item in info:
                    display_item = item.copy()
                    json_str = json.dumps(display_item.get("item_json", "")) if isinstance(display_item.get("item_json"), dict) else str(display_item.get("item_json"))
                    display_item["item_json"] = (json_str[:60] + "...") if len(json_str) > 60 else json_str
                    display_data.append(display_item)
                st.table(display_data)
                for idx, item in enumerate(info):
                    with st.expander(f"Show full JSON for item '{item.get('item_name', idx)}'"):
                        st.json(item.get("item_json"))
            elif isinstance(info, list):
                st.info("No items found in this group.")
            else:
                st.write(info)
        else:
            try:
                st.error(f"Failed to fetch group items: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to fetch group items: {r.status_code}\n{r.text}")

# Add item to a exisitng group that the user owns
def add_item_to_group(token: str):
    st.header("Add Item to Group")
    group_id = st.number_input("Group ID", min_value=1, step=1)
    item_name = st.text_input("Item Name (for group)")
    item_json = st.text_area("Item JSON (paste price history JSON)")
    if st.button("Add Item"):
        try:
            item_json_obj = json.loads(item_json)
        except Exception:
            st.error("Invalid JSON format.")
            return
        r = requests.post(
            f"{API_URL}/group/{group_id}/items",
            json={"item_name": item_name, "item_json": item_json_obj},
            headers={"Authorization": f"Bearer {token}"}
        )
        if r.status_code == 200:
            st.success(f"Item added! ID: {r.json().get('id')}")
        else:
            try:
                st.error(f"Failed to add item: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to add item: {r.status_code}\n{r.text}")

# Remove an item from a group that the user owns
def remove_item_from_group(token: str):
    st.header("Remove Item from Group")
    group_id = st.number_input("Group ID (remove item)", min_value=1, step=1, key="remove_item_group")
    item_name = st.text_input("Item Name (to remove)")
    if st.button("Remove Item"):
        r = requests.delete(
            f"{API_URL}/group/{group_id}/items",
            json={"item_name": item_name},
            headers={"Authorization": f"Bearer {token}"}
        )
        if r.status_code == 200:
            st.success("Item removed!")
        else:
            try:
                st.error(f"Failed to remove item: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to remove item: {r.status_code}\n{r.text}")

### Steam (Auth)
# Get the user's top games using their steam ID
def get_top_games(token: str):
    st.header("Get Top Games")
    if st.button("Fetch Top Games"):
        r = requests.get(f"{API_URL}/steam/top-games", headers={"Authorization": f"Bearer {token}"})
        if r.status_code == 200:
            games = r.json()
            if isinstance(games, list) and games:
                st.success("Fetched top games!")
                st.table(games)
            else:
                st.info("No games found.")
        else:
            try:
                st.error(f"Failed to get top games: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to get top games: {r.status_code}\n{r.text}")

# Get steam market price history of a steam item
def get_item_history(token: str):
    st.header("Get Item Price History URL")
    appid = st.number_input("AppID", min_value=1, step=1)
    item_name = st.text_input("Item Name")
    if st.button("Get Price History URL"):
        r = requests.post(f"{API_URL}/steam/item-history", json={"appid": appid, "item_name": item_name}, headers={"Authorization": f"Bearer {token}"})
        if r.status_code == 200:
            url = r.json().get("price_history_url")
            st.success(f"Price History URL: {url}")
        else:
            try:
                st.error(f"Failed to fetch item history: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to fetch item history: {r.status_code}\n{r.text}")

### ML Prediction (authenticated)
# Get information about a group's generated model
def get_group_model_info(token: str):
    st.header("Get Group Model Info")
    group_id = st.number_input("Group ID (model info)", min_value=1, step=1, key="model_info_group_id")
    if st.button("Fetch Model Info"):
        group_name = None
        r_group = requests.get(f"{API_URL}/group/{group_id}", headers={"Authorization": f"Bearer {token}"})
        if r_group.status_code == 200:
            group_info = r_group.json()
            group_name = group_info.get("group_name") or group_info.get("title") or group_info.get("name")
        r = requests.get(
            f"{API_URL}/group/{group_id}/model",
            headers={"Authorization": f"Bearer {token}"}
        )
        if r.status_code == 200:
            info = r.json()
            st.success("Fetched model info!")
            if group_name:
                st.subheader(f"Group: {group_name}")
            if isinstance(info, dict) and "items" in info:
                items = info["items"]
                if isinstance(items, list) and items:
                    st.table(items)
                else:
                    st.info("No items found in this group model info.")
            elif isinstance(info, list) and info:
                st.table(info)
            else:
                st.info("No items found in this group model info.")
        else:
            try:
                st.error(f"Failed to fetch model info: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to fetch model info: {r.status_code}\n{r.text}")

# Train all the items in a existing group that the user owns, return a graph of the training process along training metrics
def train_group(token: str):
    st.header("Train Group Model")
    group_id = st.number_input("Group ID (for training)", min_value=1, step=1, key="train_group")
    if st.button("Train Model"):
        group_id = int(group_id)
        r = requests.post(
            f"{API_URL}/group/{group_id}/train",
            headers={"Authorization": f"Bearer {token}"},
            json={"group_id": group_id}
        )
        if r.status_code == 200:
            # Check if the response is a single image
            if r.headers.get("content-type", "").startswith("image/"):
                st.success("Model trained!")
                st.image(r.content, caption="Training Graph")
            else:
                st.success("Model trained!")
                result = r.json()
                trained_models = result.get("trained_models", [])
                if trained_models:
                    for _, model in enumerate(trained_models):
                        st.write(f"### {model.get('item_name')} | Item ID: {model.get('item_id')}")
                        metrics = model.get("metrics", {})
                        if metrics:
                            st.write("**Metrics:**")
                            for k, v in metrics.items():
                                st.write(f"- {k}: {v}")
                        graph_b64 = model.get("graph")
                        if graph_b64:
                            img_bytes = base64.b64decode(graph_b64)
                            st.image(img_bytes, caption=f"Training Graph for Item {model.get('item_id')}")
                        st.write("---")
                else:
                    st.info("No models were trained.")
        else:
            try:
                st.error(f"Failed to train group: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to train group: {r.status_code}\n{r.text}")

# Delete a group of trained models that the user owns
def delete_group_model(token: str):
    st.header("Delete Group Model")
    group_id = st.number_input("Group ID (delete model)", min_value=1, step=1, key="delete_group_model")
    if st.button("Delete Model"):
        r = requests.delete(f"{API_URL}/group/{group_id}/model", headers={"Authorization": f"Bearer {token}"})
        if r.status_code == 200:
            st.success("Model deleted!")
        else:
            try:
                st.error(f"Failed to delete group model: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to delete group model: {r.status_code}\n{r.text}")

# Predict item price from a generated model from one of the groups, return a graph of the predictions
def predict_item(token: str):
    st.header("Predict Item Price")
    group_id = st.number_input("Group ID (for prediction)", min_value=1, step=1, key="predict_group")
    item_id = st.number_input("Item ID", min_value=1, step=1)
    start_time = st.text_input("Start Time (YYYY-MM-DD)")
    end_time = st.text_input("End Time (YYYY-MM-DD)")
    if st.button("Predict"):
        r = requests.post(
            f"{API_URL}/group/{group_id}/predict",
            json={"item_id": item_id, "start_time": start_time, "end_time": end_time},
            headers={"Authorization": f"Bearer {token}"}
        )
        if r.status_code == 200:
            st.success("Prediction complete!")
            if r.headers.get("content-type", "").startswith("image/"):
                st.image(r.content)
            else:
                result = r.json()
                for k, v in result.items():
                    st.write(f"**{k}:** {v}")
        else:
            try:
                st.error(f"Failed to fetch prediction: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to fetch prediction: {r.status_code}\n{r.text}")

# Possible actions for the user
actions_list = {
    "private_actions": [
        "Create Group",
        "Update Group Name",
        "Get Group Items",
        "Get Group Model Info",
        "Add Item to Group",
        "Remove Item from Group",
        "Train Group Model",
        "Predict Item Price",
        "Delete Group",
        "Delete Group Model",
        "Get Top Games",
        "Get Item Price History URL",
        "Logout"
    ],
    "public_actions": [
        "Get All Groups",
        "Get Group by ID"
    ],
    "auth_actions": [
        "Login",
        "Register"
    ]
}

# Main loop for the web app
def main():
    st.title("Steam Market Predictor")
    if "token" not in st.session_state:
        st.session_state["token"] = None

    token = st.session_state.get("token")

    # Auth section (only if not logged in)
    if not token:
        action_list = actions_list["auth_actions"] + actions_list["public_actions"]
    else:
        action_list = actions_list["public_actions"] + actions_list["private_actions"]

    actions = st.sidebar.radio(
        "### Actions",
        action_list,
        key="actions"
    ) 

    if actions == "Login":
        token = login()
    elif actions == "Register":
        register()
    elif actions == "Logout":
        logout()
    elif actions == "Get All Groups":
        get_all_groups()
    elif actions == "Get Group by ID":
        get_group_by_id()
    elif actions == "Create Group":
        create_group(token)
    elif actions == "Update Group Name":
        update_group_name(token)
    elif actions == "Delete Group":
        delete_group(token)
    elif actions == "Add Item to Group":
        add_item_to_group(token)
    elif actions == "Remove Item from Group":
        remove_item_from_group(token)
    elif actions == "Get Group Items":
        get_group_items(token)
    elif actions == "Get Top Games":
        get_top_games(token)
    elif actions == "Get Item Price History URL":
        get_item_history(token)
    elif actions == "Get Group Model Info":
        get_group_model_info(token)
    elif actions == "Train Group Model":
        train_group(token)
    elif actions == "Delete Group Model":
        delete_group_model(token)
    elif actions == "Predict Item Price":
        predict_item(token)

if __name__ == "__main__":
    main()