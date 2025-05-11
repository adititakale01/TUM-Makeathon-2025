import helper as helper
import json


def find_matching_hotels(
    query: str, hotels: dict[str, dict[str, object]]
) -> list[str] | None:
    """
    Find matching hotels based on the given query.

    Args:
        query (str): The search query from the user.
        hotels (dict[str, dict[str, object]]): Dictionary containing hotel information.
            Format: {
                "hotel_name": {
                    "name": str,
                    "rating": float,
                    "distance_to_beach": float,
                    ...
                },
                ...
            }

    Returns:
        list[str] | None: List of hotel_names that match the query, or None if the query is not hotel related.
    """
    # TODO: Implement the logic to find matching hotels based on the query.
    client, model = helper.get_llm()
    validity = helper.is_valid_booking_request(query, client, model)
    if not validity:
        return None

    # data_list = helper.generate_list_from_dict(hotels)
    data_list = hotels
    features = helper.find_features_in_list(data_list)
    accepted_columns = helper.find_accepted_columns("accepted_columns.txt")
    ignored_columns = helper.find_ignored_columns("ignored_columns.txt")
    detected_acceptable_columns = helper.detect_accepted_columns(
        client, model, features, accepted_columns=accepted_columns
    )
    filtered_features = [
        col for col in features if col not in detected_acceptable_columns
    ]
    detected_ignored_columns = helper.detect_ignored_columns(
        client, model, filtered_features, ignored_columns=ignored_columns
    )
    filtered_features = [
        col for col in filtered_features if col not in detected_ignored_columns
    ]
    detected_amenity_columns = helper.detect_amenity_columns(
        client,
        model,
        filtered_features,
        detected_accepted_columns=detected_acceptable_columns,
        detected_ignored_columns=detected_ignored_columns,
        user_prompt=None,
    )

    modified_data_list = []
    for item in data_list:
        cleaned_row = {}
        amenities = []
        additional_info = []

        for key in features:
            if key not in item:
                continue
            value = item[key]
            # new_key = f"amenity_{key}" if key in amenity_columns else key

            if key in detected_amenity_columns:
                if value == 1:
                    amenities.append(key)
                elif value != 0:
                    cleaned_row[key] = value if value else []
            elif key in detected_acceptable_columns:
                cleaned_row[key] = value if value else []
            elif key not in detected_ignored_columns:
                if value == 1:
                    additional_info.append(key)
                elif value != 0:
                    cleaned_row[key] = value if value else []

        cleaned_row["amenities"] = amenities
        cleaned_row["additional_info"] = additional_info

        modified_data_list.append(cleaned_row)

    filtered_hotels = helper.filter_valid_hotels(
        modified_data_list, query, client, model
    )
    try:
        if type(filtered_hotels) != list:
            list_start = filtered_hotels.find("[")
            list_end = filtered_hotels.rfind("]")
            if list_end - list_start < 6:
                return []
            else:
                return helper.filter_valid_hotels(
                    modified_data_list, query, client, model
                )
    except Exception as e:
        return helper.filter_valid_hotels(
            modified_data_list, query, client, model
        )
    filtered_hotel_names = [hotel["name"] for hotel in filtered_hotels]

    return filtered_hotels


# hotels = {
#     "Grand Hotel": {
#         "name": "Grand Hotel",
#         "pricepernight": 112.36,
#         "rating": 4.5,
#         "Innenpool": 0,
#     },
#     "Budget Inn": {
#         "name": "Budget Inn",
#         "pricepernight": 83.65,
#         "rating": 3.0,
#         "Innenpool": 0,
#     },
#     "Spa Resort": {
#         "name": "Spa Resort",
#         "pricepernight": 152.20,
#         "rating": 4.2,
#         "Innenpool": 1,
#     },
# }
# filtered_hotels = find_matching_hotels("I want a cheap hostel", hotels)
# print(filtered_hotels)

# helper.make_json("../data/Kopenhagen.csv", "../data/Kopenhagen.json")

with open("../data/Kopenhagen.json", "r") as json_file:
    hotels = json.load(json_file)
filtered_hotels = find_matching_hotels("I'd love to find a family-friendly hotel surrounded by nature, perfect for a peaceful getaway, that also allows an extra bed for children.", hotels)
print(filtered_hotels)