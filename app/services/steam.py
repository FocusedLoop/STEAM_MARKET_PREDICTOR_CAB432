#SteamID64: 76561198281140980
#SteamID: STEAM_0:0:160437626
import requests, os, json
from urllib.parse import urlencode
from collections import Counter
from typing import Optional

STEAM_COM_BASE = "https://steamcommunity.com"
STEAM_API_BASE = "https://api.steampowered.com"
API_KEY = os.getenv("STEAM_API_KEY", "74540CE2420D90E0816FBA44B026B141")

class steamAPI:
    """
    A simple class for interacting with the Steam Web API and Steam Community.
    Provides methods to fetch user games, inventory, item details, and generate price history URLs.
    """
    def __init__(self, steam_id: int):
        self.steam_com_base = STEAM_COM_BASE
        self.steam_api_base = STEAM_API_BASE
        self.api_key = API_KEY
        self.steam_id = steam_id

    # Get the list of user games
    def _get_game_list(self):
        url = f"{self.steam_api_base}/IPlayerService/GetOwnedGames/v1"
        params = {
            "key": self.api_key,
            "steamid": self.steam_id,
            "include_appinfo": True,
            "include_played_free_games": True
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    # Get the user inventory for a specific game
    def _get_inventory(self, game_id: int):
        url = f"{self.steam_com_base}/inventory/{self.steam_id}/{game_id}/2"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            raise ValueError(f"Steam inventory fetch failed: {e}")

    # Get the hash for the specific item
    def _get_market_hash(self, appid: int, classid: int, instanceid: int):
        url = f"{self.steam_api_base}/ISteamEconomy/GetAssetClassInfo/v1/"
        params = {
            "key": self.api_key,
            "appid": appid,
            "classid0": classid,
            "instanceid0": instanceid,
            "class_count": 1,
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Get the results and search through the key items for the market hash name
        result = data.get("result", {})
        result_keys = [k for k in result.keys() if k != "success"]
        if not result_keys:
            return None
        first_key = result_keys[0]
        class_info = result.get(first_key, {})
        market_hash_name = class_info.get("market_hash_name")
        return market_hash_name

    # Find the top n amount of suitable games with the most playtime
    def find_suitable_games(self, top_n=10, min_playtime=60):
        """
        Returns a list of the user's top games by playtime, with their appids and names.
        Only includes games with playtime above min_playtime (in minutes).
        """
        # Check for games
        games_data = self._get_game_list()
        if not games_data or 'response' not in games_data or 'games' not in games_data['response']:
            return []
        
        games = games_data['response']['games']
        filtered = [g for g in games if g.get('playtime_forever', 0) >= min_playtime] # Filter by minimum playtime
        ranked = sorted(filtered, key=lambda x: x.get('playtime_forever', 0), reverse=True) # Sort by descending playtime
        return [
            {
                'appid': g['appid'],
                'name': g.get('name', ''),
                'playtime_hours': round(g.get('playtime_forever', 0) / 60, 2)
            }
            for g in ranked[:top_n]
        ]

    # Get price history for a specific item (market_hash_name) in a game
    def generate_price_history_url(self, appid: int, marker_hash: Optional[str] = None, classid: Optional[int] = None, instanceid: Optional[int] = None):
        if marker_hash:
            market_hash_name = marker_hash
        elif classid is not None and instanceid is not None:
            market_hash_name = self._get_market_hash(appid, classid, instanceid)
            if not market_hash_name:
                raise ValueError("Could not resolve market_hash_name from classid/instanceid.")
        else:
            raise ValueError("You must provide either marker_hash or both classid and instanceid.")

        # Return a steam market price history URL
        url = f"{self.steam_com_base}/market/pricehistory/"
        params = {
            "appid": appid,
            "market_hash_name": market_hash_name
        }
        full_url = url + "?" + urlencode(params)
        return full_url

    # Search for a specific item in the user's inventory
    def search_item(self, appid: int, item_name: str):
        inventory = self._get_inventory(appid)
        descriptions = inventory.get("descriptions", [])

        # Search for the market hash name
        for desc in descriptions:
            if item_name.lower() in desc.get("market_hash_name", "").lower() or \
            item_name.lower() in desc.get("name", "").lower():
                return {
                    "market_hash_name": desc.get("market_hash_name"),
                    "classid": desc.get("classid"),
                    "instanceid": desc.get("instanceid"),
                    "name": desc.get("name"),
                    "icon_url": desc.get("icon_url"),
                    "tradable": desc.get("tradable"),
                }
        return None

    # Get the top N inventory items
    # NOTE: This is not is use currently, maybe for assignment 2??
    def get_top_inventory_items(self, appid: int, top_n=5, tradable_only=True):
        inventory = self._get_inventory(appid)
        descriptions = inventory.get("descriptions", [])
        if tradable_only:
            descriptions = [d for d in descriptions if d.get("tradable", 0)]
        counts = Counter([d.get("market_hash_name") for d in descriptions])
        top_items = counts.most_common(top_n)
        result = []
        for name, count in top_items:
            for desc in descriptions:
                if desc.get("market_hash_name") == name:
                    result.append({
                        "market_hash_name": name,
                        "count": count,
                        "name": desc.get("name"),
                        "icon_url": desc.get("icon_url"),
                        "tradable": desc.get("tradable"),
                    })
                    break
        return result

# TESTING
if __name__ == "__main__":
    STEAMID = "76561198281140980"
    SAMPLE_GAME = "440"
    SAMPLE_CLASS_ID = 2570543230
    SAMPLE_INSTANCE_ID = 4950542612
    SAMPLE_HASH = "Civic Duty Mk.II Knife (Factory New)"

    steam = steamAPI(STEAMID)
    games = steam._get_game_list()
    inventory = steam._get_inventory(SAMPLE_GAME)
    market_hash = steam._get_market_hash(SAMPLE_GAME)
    print(market_hash)
    price_history = steam.generate_price_history_url(SAMPLE_GAME)
    suitable_games = steam.find_suitable_games()
    search_results = steam.search_item(market_hash)
    print(search_results)
    items = [games, inventory, market_hash, price_history, suitable_games]
    file = ["games.json", "inventory.json", "market_hash.json", "price_history.txt", "suitable_games.json"]
    for i in range(len(file)):
        with open(file[i], "w") as f:
            if i == 3:
                f.write(price_history)
            else:
                json.dump(items[i], f, indent=2)