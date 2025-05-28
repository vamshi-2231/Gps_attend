from geopy.distance import geodesic

# Reference location (e.g., your office/school location)
REFERENCE_LOCATION = (17.385044, 78.486671)  # Example: Hyderabad coordinates

def is_within_range(user_lat, user_lon, allowed_radius_km=0.1):
    user_location = (user_lat, user_lon)
    distance = geodesic(user_location, REFERENCE_LOCATION).km
    return distance <= allowed_radius_km
