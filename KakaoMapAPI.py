import requests
from bs4 import BeautifulSoup
import pandas as pd
from auth import *

def KakaoMapAPI(regions):
    # Create an empty DataFrame to store all the restaurant information
    all_df = pd.DataFrame()
    
    # Iterate over each region and search for restaurants using the Kakao Map API
    for region in regions:
        # Set the API endpoint URL
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        
        # Set the headers for the API request
        headers = {"Authorization": f"KakaoAK {REST_API_KEY}"}
        
        # Set the search parameters, including the radius of the search (20km), the category of the search (food), 
        # and the search query (the region name followed by "restaurant" in Korean)
        params = {
            "radius" : "20000",
            "category_group_code" : "FD6",
            "query": f"{region} 맛집"
        }
        
        # Iterate over each page of search results (up to 45 pages) and append the restaurant information to the DataFrame
        for i in range(1,46):
            # Set the page parameter for the search request
            params['page'] = str(i)
            
            # Send the search request and get the response as JSON
            response = requests.get(url, headers=headers, params=params)
            tmp_json = response.json()['documents']
            
            # Convert the JSON to a DataFrame and append it to the main DataFrame
            df = pd.DataFrame(tmp_json)
            all_df = pd.concat([all_df, df])
    
    # Rename the DataFrame columns to be more descriptive
    all_df = all_df.rename(columns={
        'x': 'diner_lat',
        'y' : 'diner_lon',
        'road_address_name': 'diner_address',
        'place_name' : 'diner_name',
        'category_name' : 'diner_category',
        'phone' : 'diner_phone',
        'id' : 'diner_id'
    })
    
    # Return the final DataFrame with all the restaurant information
    return all_df
