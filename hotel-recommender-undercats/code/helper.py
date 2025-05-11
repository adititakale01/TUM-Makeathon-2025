import json
import os
import re
import unicodedata

from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()


def normalize_text(text):
    # Replace German umlauts first
    text = (
        text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    )

    # Unicode normalize to remove other accents
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

    # Lowercase everything
    text = text.lower()

    # Replace dashes with underscores
    text = text.replace("-", "_")

    # Remove all characters except letters, numbers, spaces, underscores, and slashes
    text = re.sub(r"[^a-z0-9 _/()[]]", "", text)

    return text


def find_ignored_columns(file_path):
    with open(file_path, "r") as file:
        # Read the first line
        first_line = file.readline().strip()

        # Split the line by commas to create a list
        ignored_columns = first_line.split(",")

    # Optional: Remove extra whitespace around each item
    ignored_columns = [normalize_text(col.strip()) for col in ignored_columns]

    return ignored_columns


def find_accepted_columns(file_path):
    with open(file_path, "r") as file:
        # Read the first line
        first_line = file.readline().strip()

        # Split the line by commas to create a list
        accepted_columns = first_line.split(",")

    # Optional: Remove extra whitespace around each item
    accepted_columns = [normalize_text(col.strip()) for col in accepted_columns]

    return accepted_columns


def get_llm():
    client = AzureOpenAI(
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        api_version="2025-01-01-preview",
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    )
    model = "gpt-4o-0806-eu"
    return client, model


def detect_accepted_columns(client, model, columns, accepted_columns=[]):
    if type(accepted_columns) != list:
        accepted_columns = []
    prompt = f"""
    You are given a list of original column names from a hotel dataset:
    original_columns={columns}
    You are given another list of columns:
    accepted_columns={accepted_columns}

    Identify which columns in original_columns list are related in context to columns in accepted_columns list.

    Return a list as json where items are exact column names that refer to accepted_columns.

    **Important:**
    - ONLY return a plain Python list as json.
    - Do NOT add any headings, explanations, code blocks, spaces or extra text.
"""

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that classifies hotel dataset fields.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    # print(completion.choices[0].message.content)

    # Try to parse the JSON response
    try:
        content = completion.choices[0].message.content
        content_list = json.loads(content)
        # list_start = content.find("[")
        # list_end = content.rfind("]") + 1
        # list_str = content[list_start+1:list_end-1]
        # str_list = list_str.split(",")
        # str_list = [item.strip().strip('\'').strip('"') for item in str_list]
        # print("LLM Response list:", str_list)
        for column in columns:
            if column in accepted_columns and column not in content_list:
                content_list.append(column)
        return content_list
    except Exception as e:
        return detect_accepted_columns(
            client, model, columns, accepted_columns=accepted_columns)


def detect_ignored_columns(client, model, columns, ignored_columns=[]):
    if type(ignored_columns) != list:
        ignored_columns = []
    prompt = f"""
    You are given a list of original column names from a hotel dataset:
    original_columns={columns}
    You are given another list of columns:
    ignored_columns={ignored_columns}

    Identify which columns in original_columns list are related in context to columns in ignored_columns list.

    Return a list of exact column names that refer to ignored_columns.

    **Important:**
    - ONLY return a plain Python list as json.
    - Do NOT add any headings, explanations, code blocks, spaces or extra text.
"""

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that classifies hotel dataset fields.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    # print(completion.choices[0].message.content)

    # Try to parse the JSON response
    try:
        content = completion.choices[0].message.content
        content_list = json.loads(content)
        for column in columns:
            if column in ignored_columns and column not in content_list:
                content_list.append(column)
        return content_list
    except Exception as e:
        return detect_ignored_columns(
            client, model, columns, ignored_columns=ignored_columns)


def detect_amenity_columns(
    client,
    model,
    columns,
    detected_accepted_columns=[],
    detected_ignored_columns=[],
    user_prompt=None,
):
    if type(detected_accepted_columns) != list:
        detected_accepted_columns = []
    if type(detected_ignored_columns) != list:
        detected_ignored_columns = []
    columns = [col for col in columns if col not in detected_ignored_columns]
    columns = [col for col in columns if col not in detected_accepted_columns]

    if not user_prompt:
        prompt = f"""
    You are given a list of original column names from a hotel dataset:
    original_columns={columns}

    Identify which columns are related in context to amenities (like pool, gym, wifi, etc.), and exclude any related to room category or other non-amenity features.

    Return a list of exact column names that refer to amenities.

    **Important:**
    - ONLY return a plain Python list as json.
    - Do NOT add any headings, explanations, code blocks, spaces or extra text.
"""
    else:
        prompt = f"""
    You are given a list of original column names from a hotel dataset:
    original_columns={columns}

    Return a list of exact column names that match either of the two below conditions:
    1. Columns are related in context to amenities (like pool, gym, wifi, etc.), and exclude any related to room category or other non-amenity features.
    2. Columns are related in context to amenities requested by the user in the following user_prompt:
    "{user_prompt}"

    **Important:**
    - ONLY return a plain Python list as json.
    - Do NOT add any headings, explanations, code blocks, spaces or extra text.
"""

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that classifies hotel dataset fields.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    # print(completion.choices[0].message.content)

    # Try to parse the JSON response
    try:
        content = completion.choices[0].message.content
        content_list = json.loads(content)
        return content_list
    except Exception as e:
        return detect_amenity_columns(
            client, model, columns, detected_accepted_columns, detected_ignored_columns, user_prompt=user_prompt
        )

    # import pandas as pd


def generate_list_from_dict(hotels: dict[str, dict[str, object]]):
    data = []
    for hotel in hotels.items():
        hotel_name = hotel[0]
        hotel_info = hotel[1]
        normalized_hotel_info = {normalize_text(k): v for k, v in hotel_info.items()}
        # Flatten the dictionary and add the hotel name
        flat_hotel_info = {"hotel_name": hotel_name, **normalized_hotel_info}
        flat_hotel_info.pop("name", None)  # Remove the name key if it exists
        data.append(flat_hotel_info)

    return data


def find_features_in_list(data_list):
    features = set()
    for item in data_list:
        for key, value in item.items():
            normalized_key = normalize_text(key)
            features.add(normalized_key)
    return list(features)


def is_valid_booking_request(user_prompt, client, model):
    """
    This function checks if the user prompt is a valid booking request.

    Args:
    user_prompt (str): The user's input prompt.

    Returns:
    bool: True if the prompt is a valid booking request, False otherwise.
    """
    prompt = f"""
You are a classification system. Given a user input, determine whether it is a valid accommodation booking request.

- A valid hotel booking request can mention: accommodation preferences, amenities, budget, stay details, possible activities, or similar relevant information.
- Garbage includes anything unrelated to booking accommodation, impossible or nonsensical.

Respond only with:
- "VALID" if it is a valid hotel booking request
- "INVALID" if it is not.

Examples:
- User Input: "I want to book a hotel in Paris from May 5 to May 10 with a pool at 30000 feet"
  Answer: INVALID

- User Input: "What's the weather like in Paris?"
  Answer: INVALID

- User Input: "Book me a hotel in New York near Central Park for next weekend"
  Answer: VALID

- User Input: "Book me a hotel in New York near Central Park for last weekend"
  Answer: INVALID

- User Input: "dghasjkdhgasdjkhg"
  Answer: INVALID

Now classify the following input:
User Input: "{user_prompt}"
Answer:

    """

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that classifies hotel booking requests.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    # print(completion.choices[0].message.content)

    # Try to parse the JSON response
    try:
        content = completion.choices[0].message.content
        if content.strip() == "VALID":
            return True
        elif content.strip() == "INVALID":
            return False
        else:
            return is_valid_booking_request(user_prompt, client, model)
    except Exception as e:
        return is_valid_booking_request(user_prompt, client, model)


def filter_valid_hotels(hotel_list, user_prompt, client, model):
    """
    This function filters a list of hotels based on the user's booking request.

    Args:
    hotel_list (list): A list of hotel dictionaries to filter.
    user_prompt (str): The user's input prompt.

    Returns:
    list: A list of valid hotels that match the user's request.
    """

    prompt = f"""
You are a hotel booking assistant.

Input:

1. A user query describing what they want in a hotel booking (e.g., "a 4-star hotel near the beach with free breakfast and spa").

2. A JSON list of hotel dictionaries, where each dictionary contains hotel attributes like name, price, rating, star category, amenities, etc. Note: Some hotels might have additional keys, and the amenities/additional_info lists can be empty.

Your task:

1. Understand the user query and infer all explicit and implicit preferences (e.g., if user mentions "luxury", prefer higher star ratings and amenities like spa, wellness center, etc.).

2. Filter the hotels according to the user's requirements exactly, unless relaxed by user. A perfect match fulfills all key user preferences; partial matches are allowed only if explicitly allowed by user.

3. Rank the matching hotels from best to worst based on how well they satisfy the user's query. The strongest matches should come first.

4. Return a list of up to 10 hotel dictionaries, in decreasing order of match quality. List can be shorter than 10 or even zero if fewer hotels match.

5. If no hotels satisfy the user's needs reasonably well, return an empty list.

Important notes:

1. ALL user queries are VALID hotel booking requests. You can assume that the user is looking for a hotel and has provided a reasonable query.

2. Amenities and additional_info may use German terms (e.g., "schwimmbad" = swimming pool), so match thoughtfully.

3. Be flexible with minor variations in spelling or phrasing (e.g., "pool" could match "schwimmbad").

4. Prioritize user preferences over general hotel popularity or starcategory.

5. Do not invent hotels or change any data fields.

6. Try to match the user query as closely as possible, even if it means there are less than 10 or even zero matches.

7. Focus on context of hotel properties, not just exact values

8. Interpret "[A|A]" type value as roomconfiguration, and use it to filter hotels. For example, "2A" means 2 adults, and "2A1C" means 2 adults and 1 child. If the user query has "2A", it means the user is looking for a hotel that can accommodate 2 adults. If the hotel has "2A" in its roomconfiguration, it is a match. If the hotel has "2A1C", it is also a match, but if the hotel has "1A" or "3A", it is not a match. If beds are less than required, then check if additional bed is available for same price or not. And choose more beds than required only if no other option is available.

9. BE CONSISTENT FOR SAME USER PROMPT. If the same user prompt is given, the same hotels should be returned in the same order.

Ranking criteria:

- For budget-friendly options, prefer lower pricepernight, but also free meals, free cancellation, and other free necessary amenities that save money. But they will not be prioritized over luxury amenities.

- For good location, use popular_location_rank. If the user mentions a specific location, prioritize hotels within a reasonable distance from that location.

- Users who mention having car or want parking, can also prefer free parking for saving money. Users who do not mention having a car will prioritize less distance to locations of interest for cheaper travel.

- For luxury options, prefer higher starcategory, and amenities beyond necessary ones.

- For special adjectives in user prompt, prefer hotels with exclusive and luxury features.

- For family-friendly options, prefer hotels with amenities, activities and places of interest that are family-friendly and kid-friendly .

- For business-friendly options, prefer hotels with meeting rooms, business centers, and amenities like free Wi-Fi.

- For fun options, prefer hotels with entertainment and party options, activities, and amenities like bars or pubs, and proximity to attractions, popular_location_rank.

- For couple options, prefer hotels with amenities like spas, pools, and romantic or adult settings.

- For pet-friendly options, prefer hotels that allow pets and have pet-friendly amenities.

- For wellness or relaxation options, prefer hotels with spas, wellness centers, and fitness facilities.

- For hotels with similar ratings, prefer the one with more ratingscount.

- If two hotels have same relevance, ALWAYS prefer the one with more ltr score.


Output format: A JSON list of up to 10 hotel dictionaries, sorted from best to worst match. If no match, output an empty JSON list. Each hotel dictionary should include the following fields:
- name: hotel name
- features: Upto 3 top factors that influenced this hotel's ranking

**Important:**
- ONLY return a plain Python list as json.
- Do NOT add any headings, explanations, code blocks, spaces or extra text.

Input:
User query: "{user_prompt}"
Hotel list: {hotel_list}
Output:
"""
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that ranks hotels.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    # print(completion.choices[0].message.content)

    # Try to parse the JSON response
    try:
        content = completion.choices[0].message.content
        # print("LLM Response:", content)
        content_list = json.loads(content)
        return content_list
    except Exception as e:
        return content

import csv
def make_json(csvFilePath, jsonFilePath):
    
    # create a dictionary
    data = []
    
    # Open a csv reader called DictReader
    with open(csvFilePath, encoding='utf-8') as csvf:
        csvReader = csv.DictReader(csvf)
        headers = csvReader.fieldnames
        
        # Convert each row into a dictionary 
        # and add it to data
        for rows in csvReader:
            dictionary = {}
            for key in headers:
                dictionary[key] = rows[key]
            data.append(dictionary)

    # Open a json writer, and use the json.dumps() 
    # function to dump data
    with open(jsonFilePath, 'w', encoding='utf-8') as jsonf:
        jsonf.write(json.dumps(data, indent=4))
