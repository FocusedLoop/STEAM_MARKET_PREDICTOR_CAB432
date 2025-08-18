#SteamID64: 76561198281140980
#SteamID: STEAM_0:0:160437626
import requests, os, json
from urllib.parse import urlencode

STEAM_COM_BASE = "https://steamcommunity.com"
STEAM_API_BASE = "https://api.steampowered.com"
API_KEY = os.getenv("STEAM_API_KEY", "74540CE2420D90E0816FBA44B026B141")
STEAMID = "76561198281140980"


SAMPLE_GAME = "440"
SAMPLE_CLASS_ID = 2570543230
SAMPLE_INSTANCE_ID = 4950542612
SAMPLE_HASH = "Civic Duty Mk.II Knife (Factory New)"

COOKIES = {
    'sessionid': 'ff9f380482882503ad448476',
    'steamLoginSecure': '76561198281140980%7C%7CeyAidHlwIjogIkpXVCIsICJhbGciOiAiRWREU0EiIH0.eyAiaXNzIjogInI6MDAwOV8yNkM2QzM5OV9CNzdBNSIsICJzdWIiOiAiNzY1NjExOTgyODExNDA5ODAiLCAiYXVkIjogWyAid2ViOnN0b3JlIiBdLCAiZXhwIjogMTc1NTIzMjQxNSwgIm5iZiI6IDE3NDY1MDU1MjUsICJpYXQiOiAxNzU1MTQ1NTI1LCAianRpIjogIjAwMDNfMjZDNkM0QzNfQUY2N0QiLCAib2F0IjogMTc1NTE0NTUyNSwgInJ0X2V4cCI6IDE3NzMyNzU4MTcsICJwZXIiOiAwLCAiaXBfc3ViamVjdCI6ICIxMDEuMTgwLjIwMC40NyIsICJpcF9jb25maXJtZXIiOiAiMTAxLjE4MC4yMDAuNDciIH0.6cV1cXgwcGxUv-eztM9XAh-PDBOYdpalShFBNp3kOk9HHhl1jT3fuPgnkxQLBokvXmipLv_qyRV_2P0h6G3-AQ'
}

class steamAPI:
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
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    # Get the hash for the specific item
    def _get_market_hash(self, appid: int):
        url = f"{self.steam_api_base}/ISteamEconomy/GetAssetClassInfo/v1/"
        params = {
            "key": self.api_key,
            "appid": appid,
            "classid0": SAMPLE_CLASS_ID,
            "instanceid0": SAMPLE_INSTANCE_ID,
            "class_count": 1,
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    # Get price history for a specific item (market_hash_name) in a game
    def _generate_price_history_url(self, appid: int, market_hash_name: str):
        url = f"{self.steam_com_base}/market/pricehistory/"
        params = {
            "appid": appid,
            "market_hash_name": market_hash_name
        }
        full_url = url + "?" + urlencode(params)
        return full_url
    
    # TODO REFINE, TEST, ETC
    # SAVE TO MARIA DB
    def find_suitable_games(self, top_n=5, min_playtime=60):
        """
        Returns a list of the user's best games to get price histories for, ranked by a combination of playtime and estimated inventory value.
        Only includes games with playtime above min_playtime (in minutes).
        """
        games_data = self._get_game_list()
        if not games_data or 'response' not in games_data or 'games' not in games_data['response']:
            return []
        games = games_data['response']['games']
        # Filter by minimum playtime
        filtered = [g for g in games if g.get('playtime_forever', 0) >= min_playtime]
        game_scores = []
        for g in filtered:
            appid = g['appid']
            playtime = g.get('playtime_forever', 0)
            # Try to get inventory for this game
            try:
                inventory = self._get_inventory(appid)
                # Estimate value: count number of items (could be improved with price lookup)
                num_items = len(inventory.get('descriptions', []))
            except Exception:
                num_items = 0
            # Score: weighted sum of playtime and inventory size
            score = playtime + (num_items * 100)  # You can adjust the weight as needed
            game_scores.append({
                'appid': appid,
                'name': g.get('name', ''),
                'playtime_forever': playtime,
                'inventory_items': num_items,
                'score': score
            })
        # Sort by score (descending)
        ranked = sorted(game_scores, key=lambda x: x['score'], reverse=True)
        return ranked[:top_n]
    
    # CONTINUE HERE
    #def
    

if __name__ == "__main__":
    steam = steamAPI(STEAMID)
    games = steam._get_game_list()
    inventory = steam._get_inventory(SAMPLE_GAME)
    market_hash = steam._get_market_hash(SAMPLE_GAME)
    print(market_hash)
    price_history = steam._generate_price_history_url(SAMPLE_GAME, SAMPLE_HASH)
    items = [games, inventory, market_hash, price_history]
    file = ["games.json", "inventory.json", "market_hash.json", "price_history.txt"]
    for i in range(len(file)):
        with open(file[i], "w") as f:
            if i == 4:
                f.write(price_history)
            else:
                json.dump(items[i], f, indent=2)