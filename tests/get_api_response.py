import requests
import json

def get_api_response(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None

if __name__ == "__main__":
    popular_api_url = "https://ads.tiktok.com/creative_radar_api/v1/popular_trend/sound/rank_list?period=7&page=1&limit=100&rank_type=popular&new_on_board=false&commercial_music=false&country_code=KR"
    
    print(f"Fetching data from: {popular_api_url}")
    data = get_api_response(popular_api_url)
    
    if data:
        print(json.dumps(data, indent=2))
    else:
        print("Failed to retrieve data.")
