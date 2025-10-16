import requests, json, base64, time
import streamlit as st
import os

API_URL = "http://api:3010"
COGNITO_DOMAIN="https://ap-southeast-2pqj6jtcus.auth.ap-southeast-2.amazoncognito.com/"
COGNITO_CLIENT_ID = "s37q4bfradfp2ic1j1rfr1b4j"
REDIRECT_URI = "https%3A%2F%2Fd84l1y8p4kdic.cloudfront.net&response_type=code&scope=aws.cognito.signin.user.admin+email+openid+phone+profile"#"steamapp://auth/callback"

def confirm_account():
    st.header("Confirm Your Account")
    st.info("Please check your email for the confirmation code sent during registration.")
    username = st.text_input("Username", key="confirm_username")
    confirmation_code = st.text_input("Confirmation Code", key="confirm_code")
    if st.button("Confirm Account"):
        r = requests.post(
            f"{API_URL}/auth/confirm",
            json={"username": username, "confirmation_code": confirmation_code},
        )
        if r.status_code == 200:
            st.success("Your account has been successfully verified! You can now log in.")
        else:
            try:
                st.error(f"Confirmation failed: {r.status_code}\n{r.json()['detail']}")
            except Exception:
                st.error(f"Confirmation failed: {r.status_code}\n{r.text}")

def login():
    st.header("Sign In")

    auth_url = (
        f"{COGNITO_DOMAIN}login?"
        f"client_id={COGNITO_CLIENT_ID}&"
        f"response_type=code&"
        f"scope=aws.cognito.signin.user.admin+email+openid+phone+profile&"
        f"redirect_uri={REDIRECT_URI}"
    )
    st.markdown(
        f'<a href="{auth_url}" target="_self" style="display: inline-block; padding: 10px 20px; background-color: #4285F4; color: white; text-align: center; text-decoration: none; border-radius: 4px; font-weight: bold;">Sign in with Google</a>',
        unsafe_allow_html=True,
    )

    st.divider()

    if 'mfa_session_details' in st.session_state:
        st.subheader("Enter Verification Code")
        st.info("A code has been sent to your email address.")
        
        mfa_code = st.text_input("Email Code")
        
        if st.button("Submit Code"):
            details = st.session_state['mfa_session_details']
            
            request_payload = {
                "username": details["username"],
                "session": details["session"],
                "mfa_code": mfa_code
            }
            
            # Create placeholder elements that mimic the timing of the debug expanders
            status_placeholder = st.empty()
            result_placeholder = st.empty()
            
            r = requests.post(
                f"{API_URL}/auth/mfa-challenge", 
                json=request_payload
            )
            status_placeholder.write("Processing MFA verification...")
            
            if r.status_code == 200:
                try:
                    response_json = r.json()
                    token_fields = ["id_token", "IdToken", "access_token", "AccessToken"]
                    found_token = None
                    
                    for field in token_fields:
                        if field in response_json:
                            found_token = response_json[field]
                            break
                    
                    if found_token:
                        # Clear the status placeholder
                        status_placeholder.empty()
                        result_placeholder.success("Login successful!")
                        
                        # Update session state in the correct order
                        st.session_state["token"] = found_token
                        del st.session_state['mfa_session_details']
                        time.sleep(0.1)
                        
                        st.rerun()
                    else:
                        status_placeholder.empty()
                        result_placeholder.error(f"Authentication failed. Please try again.")
                        
                except Exception as e:
                    status_placeholder.empty()
                    result_placeholder.error(f"Error processing response: {str(e)}")
            else:
                try:
                    response_json = r.json()
                    error_detail = response_json.get('detail', 'Invalid MFA code.')
                except:
                    error_detail = "Authentication failed."
                
                status_placeholder.empty()
                result_placeholder.error(f"Login failed: {error_detail}")
    
    else:
        st.subheader("Or sign in with your username")
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Sign In"):
            # Create placeholder for status updates
            status_placeholder = st.empty()
            status_placeholder.write("Authenticating...")
            
            r = requests.post(
                f"{API_URL}/auth/login", 
                json={"username": username, "password": password}
            )
            
            if r.status_code == 200:
                try:
                    response_data = r.json()
                    
                    if "id_token" in response_data:
                        status_placeholder.success("Login successful!")
                        st.session_state["token"] = response_data.get("id_token")
                        time.sleep(0.1)
                        st.rerun()
                    elif response_data.get("challengeName") == "MFA_CHALLENGE":
                        status_placeholder.info("MFA verification required.")
                        st.session_state['mfa_session_details'] = {
                            "session": response_data["session"],
                            "username": response_data["username"]
                        }
                        time.sleep(0.1)
                        st.rerun()
                    else:
                        status_placeholder.error("Unexpected response format.")
                        
                except Exception as e:
                    status_placeholder.error(f"Error processing login response: {str(e)}")
            else:
                try:
                    response_data = r.json()
                    status_placeholder.error(f"Login failed: {response_data.get('detail', 'An error occurred.')}")
                except:
                    status_placeholder.error(f"Login failed: {r.text}")

def logout():
    st.header("Logout of account")
    if st.button("Logout"):
        st.session_state["token"] = None
        st.success("Logged out!")
        st.rerun()


def register():
    st.header("Register for an account")
    username = st.text_input("New Username", key="register_username")
    email = st.text_input("Email Address", key="register_email")
    steam_id = st.text_input("Steam ID", key="register_steam_id")
    password = st.text_input("New Password", type="password", key="register_password")

    if st.button("Register"):
        r = requests.post(
            f"{API_URL}/auth/register",
            json={
                "username": username, 
                "email": email, 
                "password": password, 
                "steam_id": steam_id
            },
        )
        if r.status_code == 201:
            st.success("Registration successful!")
            st.info("Please check your email for a verification code, then go to the 'Confirm Account' page.")
        else:
            try:
                st.error(f"Registration failed: {r.status_code}\n{r.json()['detail']}")
            except Exception:
                st.error(f"Registration failed: {r.status_code}\n{r.text}")


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


def get_group_by_id():
    st.header("Get Group by ID")
    group_id = st.number_input(
        "Group ID (fetch)", min_value=1, step=1, key="fetch_group_id"
    )
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

def update_group_name(token: str):
    st.header("Update Group Name")
    group_id = st.number_input(
        "Group ID (update)", min_value=1, step=1, key="update_group_id"
    )
    new_title = st.text_input("New Group Title")
    if st.button("Update Group"):
        r = requests.put(
            f"{API_URL}/group/{group_id}",
            json={"title": new_title},
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code == 200:
            st.success("Group updated!")
        else:
            try:
                st.error(f"Failed to update group: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to update group: {r.status_code}\n{r.text}")


def delete_group(token: str):
    st.header("Delete Group")
    group_id = st.number_input(
        "Group ID (to delete)", min_value=1, step=1, key="delete_group"
    )
    if st.button("Delete Group"):
        r = requests.delete(
            f"{API_URL}/group/{group_id}", headers={"Authorization": f"Bearer {token}"}
        )
        if r.status_code == 200:
            st.success("Group deleted!")
        else:
            try:
                st.error(f"Failed to delete group: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to delete group: {r.status_code}\n{r.text}")


def get_group_items(token: str):
    st.header("Get Group Items")
    group_id = st.number_input("Group ID", min_value=1, step=1)
    if st.button("Fetch Group Items"):
        r = requests.get(
            f"{API_URL}/group/{group_id}/items",
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code == 200:
            info = r.json()
            st.success("Fetched group items!")
            if isinstance(info, list) and info:
                display_data = []
                for item in info:
                    display_item = item.copy()
                    json_str = (
                        json.dumps(display_item.get("item_json", ""))
                        if isinstance(display_item.get("item_json"), dict)
                        else str(display_item.get("item_json"))
                    )
                    display_item["item_json"] = (
                        (json_str[:60] + "...") if len(json_str) > 60 else json_str
                    )
                    display_data.append(display_item)
                st.table(display_data)
                for idx, item in enumerate(info):
                    with st.expander(
                        f"Show full JSON for item '{item.get('item_name', idx)}'"
                    ):
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
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code == 200:
            st.success(f"Item added! ID: {r.json().get('id')}")
        else:
            try:
                st.error(f"Failed to add item: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to add item: {r.status_code}\n{r.text}")


def remove_item_from_group(token: str):
    st.header("Remove Item from Group")
    group_id = st.number_input(
        "Group ID (remove item)", min_value=1, step=1, key="remove_item_group"
    )
    item_name = st.text_input("Item Name (to remove)")
    if st.button("Remove Item"):
        r = requests.delete(
            f"{API_URL}/group/{group_id}/items",
            json={"item_name": item_name},
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code == 200:
            st.success("Item removed!")
        else:
            try:
                st.error(f"Failed to remove item: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to remove item: {r.status_code}\n{r.text}")


def get_top_games(token: str):
    st.header("Get Top Games")
    if st.button("Fetch Top Games"):
        r = requests.get(
            f"{API_URL}/steam/top-games", headers={"Authorization": f"Bearer {token}"}
        )
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


def get_item_history(token: str):
    st.header("Get Item Price History URL")
    appid = st.number_input("AppID", min_value=1, step=1)
    item_name = st.text_input("Item Name")
    if st.button("Get Price History URL"):
        r = requests.post(
            f"{API_URL}/steam/item-history",
            json={"appid": appid, "item_name": item_name},
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code == 200:
            url = r.json().get("price_history_url")
            st.success(f"Price History URL: {url}")
        else:
            try:
                st.error(f"Failed to fetch item history: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to fetch item history: {r.status_code}\n{r.text}")


def get_group_model_info(token: str):
    st.header("Get Group Model Info")
    group_id = st.number_input(
        "Group ID (model info)", min_value=1, step=1, key="model_info_group_id"
    )
    if st.button("Fetch Model Info"):
        group_name = None
        r_group = requests.get(
            f"{API_URL}/group/{group_id}", headers={"Authorization": f"Bearer {token}"}
        )
        if r_group.status_code == 200:
            group_info = r_group.json()
            group_name = (
                group_info.get("group_name")
                or group_info.get("title")
                or group_info.get("name")
            )
        r = requests.get(
            f"{API_URL}/group/{group_id}/model",
            headers={"Authorization": f"Bearer {token}"},
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


def train_group(token: str):
    st.header("Train Group Model")
    group_id = st.number_input(
        "Group ID (for training)", min_value=1, step=1, key="train_group"
    )
    if st.button("Train Model"):
        group_id = int(group_id)
        r = requests.post(
            f"{API_URL}/group/{group_id}/train",
            headers={"Authorization": f"Bearer {token}"},
            json={"group_id": group_id},
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
                        st.write(
                            f"### {model.get('item_name')} | Item ID: {model.get('item_id')}"
                        )
                        metrics = model.get("metrics", {})
                        if metrics:
                            st.write("**Metrics:**")
                            for k, v in metrics.items():
                                st.write(f"- {k}: {v}")
                        graph_b64 = model.get("graph")
                        if graph_b64:
                            img_bytes = base64.b64decode(graph_b64)
                            st.image(
                                img_bytes,
                                caption=f"Training Graph for Item {model.get('item_id')}",
                            )
                        st.write("---")
                else:
                    st.info("No models were trained.")
        else:
            try:
                st.error(f"Failed to train group: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to train group: {r.status_code}\n{r.text}")


def delete_group_model(token: str):
    st.header("Delete Group Model")
    group_id = st.number_input(
        "Group ID (delete model)", min_value=1, step=1, key="delete_group_model"
    )
    if st.button("Delete Model"):
        r = requests.delete(
            f"{API_URL}/group/{group_id}/model",
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code == 200:
            st.success("Model deleted!")
        else:
            try:
                st.error(f"Failed to delete group model: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to delete group model: {r.status_code}\n{r.text}")


def predict_item(token: str):
    st.header("Predict Item Price")
    group_id = st.number_input(
        "Group ID (for prediction)", min_value=1, step=1, key="predict_group"
    )
    item_id = st.number_input("Item ID", min_value=1, step=1)
    start_time = st.text_input("Start Time (YYYY-MM-DD)")
    end_time = st.text_input("End Time (YYYY-MM-DD)")
    if st.button("Predict"):
        r = requests.post(
            f"{API_URL}/group/{group_id}/predict",
            json={"item_id": item_id, "start_time": start_time, "end_time": end_time},
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code == 200:
            st.success("Prediction complete!")
            if r.headers.get("content-type", "").startswith("image/"):
                st.image(r.content, caption="Prediction Graph")
            else:
                result = r.json()
                
                # Display the prediction graph if it exists
                graph_b64 = result.get("graph")
                if graph_b64:
                    try:
                        img_bytes = base64.b64decode(graph_b64)
                        st.image(img_bytes, caption="Prediction Graph")
                    except Exception as e:
                        st.error(f"Error decoding prediction graph: {e}")
                
                # Display the graph URL if available
                graph_url = result.get("graph_url")
                if graph_url:
                    st.markdown(f'[View Prediction Graph]({graph_url})')
                
                # Display any other result data
                other_data = {k: v for k, v in result.items() if k not in ['graph', 'graph_url']}
                if other_data:
                    st.subheader("Additional Data:")
                    for k, v in other_data.items():
                        st.write(f"**{k}:** {v}")
        else:
            try:
                st.error(f"Failed to fetch prediction: {r.status_code}\n{r.json()}")
            except Exception:
                st.error(f"Failed to fetch prediction: {r.status_code}\n{r.text}")


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
        "Logout",
    ],
    "public_actions": ["Get All Groups", "Get Group by ID"],
    "auth_actions": ["Sign In", "Register", "Confirm Account"],
}

def main():
    st.title("Steam Market Predictor")
    if "token" not in st.session_state:
        st.session_state["token"] = None

    auth_code = st.query_params.get("code")
    if auth_code and not st.session_state.get("token"):
        try:
            r = requests.post(
                f"{API_URL}/auth/token",
                json={"code": auth_code, "redirect_uri": REDIRECT_URI},
            )
            r.raise_for_status() 
            tokens = r.json()
            st.session_state["token"] = tokens.get("id_token")
            st.query_params.clear()
            st.rerun()
        except requests.exceptions.RequestException as e:
            st.error(f"Google login failed. Could not exchange code for token. Error: {e}")
            st.query_params.clear()

    # Update action list based on authentication state
    token = st.session_state.get("token")
    if "next_action" in st.session_state:
        st.session_state["actions"] = st.session_state["next_action"]
        del st.session_state["next_action"]
    if not token:
        action_list = actions_list["auth_actions"] + actions_list["public_actions"]
    else:
        action_list = actions_list["public_actions"] + actions_list["private_actions"]
    actions = st.sidebar.radio("### Actions", action_list, key="actions")

    if actions == "Sign In":
        login() 
    elif actions == "Register":
        register()
    elif actions == "Confirm Account": 
        confirm_account()
    elif actions == "Logout":
        logout()
    elif actions == "Get All Groups":
        get_all_groups()
    elif actions == "Get Group by ID":
        get_group_by_id()
    elif token:
        if actions == "Create Group":
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
    else:
        st.warning("You must be logged in to perform this action.")

if __name__ == "__main__":
    main()