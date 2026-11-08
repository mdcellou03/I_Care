"""Nearby eye care: finds optometrists and opticians around the user's location.

The browser sends only a latitude and longitude. We round them to about 1 km before
they leave our server, search OpenStreetMap's Nominatim service, and return the
results in the same shape the map code already reads. Nothing is stored or logged.
"""

import json
import math
import time
import urllib.parse
import urllib.request
from functools import lru_cache

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.errors import ApiError

router = APIRouter(prefix="/api/v1", tags=["nearby"])

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# Nominatim's usage policy asks for an identifying User-Agent and at most 1 request per second.
USER_AGENT = "ICheck educational eye-care finder (student hackathon project)"
SEARCH_TERMS = ("optometrist", "optician", "eye care")
SEARCH_RADIUS_KM = 5  # matches the "Within 5 km" label on the map
KM_PER_DEGREE_LAT = 111.0


class Location(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


def _search(term: str, lat: float, lon: float) -> list[dict]:
    """One Nominatim search for `term`, limited to a box around the user."""
    # viewbox is "left,top,right,bottom", in degrees. A degree of longitude shrinks with
    # cos(latitude), so the box is wider in degrees east-west to cover the same distance.
    d_lat = SEARCH_RADIUS_KM / KM_PER_DEGREE_LAT
    d_lon = d_lat / math.cos(math.radians(lat))
    params = urllib.parse.urlencode({
        "q": term,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 20,
        "bounded": 1,
        "viewbox": f"{lon - d_lon},{lat + d_lat},{lon + d_lon},{lat - d_lat}",
    })
    request = urllib.request.Request(f"{NOMINATIM_URL}?{params}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


@lru_cache(maxsize=256)
def _nearby(lat: float, lon: float) -> tuple[dict, ...]:
    """All search terms combined, de-duplicated. Cached, so repeat searches don't hit Nominatim."""
    places: dict[int, dict] = {}
    for i, term in enumerate(SEARCH_TERMS):
        if i:
            time.sleep(1)  # stay within Nominatim's 1 request/second limit
        for place in _search(term, lat, lon):
            places.setdefault(place["osm_id"], place)
    return tuple(places.values())


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance on the Earth's surface (haversine formula)."""
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(a))


def _to_element(place: dict) -> dict:
    """Convert a Nominatim result to the OpenStreetMap-style element the frontend renders."""
    address = place.get("address", {})
    return {
        "lat": float(place["lat"]),
        "lon": float(place["lon"]),
        "tags": {
            "name": place.get("name") or place["display_name"].split(",")[0],
            "addr:housenumber": address.get("house_number"),
            "addr:street": address.get("road"),
            "addr:city": address.get("city") or address.get("town"),
            "addr:postcode": address.get("postcode"),
        },
    }


@router.post("/nearby-eye-care")
def nearby_eye_care(location: Location) -> dict:
    """Return eye-care providers near the given location."""
    # Round to 2 decimals (about 1 km): the exact position never leaves our server,
    # and people searching from the same area share cached results.
    lat, lon = round(location.latitude, 2), round(location.longitude, 2)
    try:
        places = _nearby(lat, lon)
    except (OSError, ValueError) as exc:  # network errors and timeouts are OSError subclasses
        raise ApiError(
            502, "nearby_unavailable", "Nearby provider search is unavailable right now. You can still open Google Maps."
        ) from exc
    # The search box is square, so drop the results in its corners that are beyond the radius.
    nearby = [p for p in places if _distance_km(lat, lon, float(p["lat"]), float(p["lon"])) <= SEARCH_RADIUS_KM]
    return {"elements": [_to_element(place) for place in nearby]}