import os
import re
import requests
from dotenv import load_dotenv
from tools.network import disable_local_proxy

load_dotenv()
disable_local_proxy()

API_KEY = os.getenv("AVIATIONSTACK_API_KEY") or os.getenv("AVIATION_API_KEY")


AIRPORTS = {
    "delhi": "DEL",
    "new delhi": "DEL",
    "india": "DEL",
    "mumbai": "BOM",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "chennai": "MAA",
    "kolkata": "CCU",
    "hyderabad": "HYD",
    "bangkok": "BKK",
    "thailand": "BKK",
    "dubai": "DXB",
    "paris": "CDG",
    "tokyo": "HND",
    "japan": "HND",
    "bali": "DPS",
    "rome": "FCO",
    "london": "LHR",
    "new york": "JFK",
    "jfk": "JFK",
}


def _detect_route(query):
    query_text = query.lower()
    origin = None
    destination = None

    route_match = re.search(r"\bfrom\s+(.+?)\s+to\s+(.+?)(?:\s|$|,|\.| under| for| in)", query_text)
    if route_match:
        origin_text, destination_text = route_match.groups()
        origin = _find_airport(origin_text)
        destination = _find_airport(destination_text)

    if not destination:
        destination = _find_airport(query_text)

    if not origin and any(word in query_text for word in ("india", "indian", "delhi")):
        origin = "DEL"

    return origin, destination


def _find_airport(text):
    for name, code in sorted(AIRPORTS.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"\b{re.escape(name)}\b", text):
            return code
    return None


def search_flights(query):
    if not API_KEY:
        return "Flight search is not configured. Add AVIATION_API_KEY to your .env file."

    url = "http://api.aviationstack.com/v1/flights"

    params = {
        "access_key": API_KEY,
        "limit": 5
    }

    origin_iata, destination_iata = _detect_route(query)
    if origin_iata:
        params["dep_iata"] = origin_iata
    if destination_iata:
        params["arr_iata"] = destination_iata

    session = requests.Session()
    session.trust_env = False

    try:
        response = session.get(url, params=params, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        return f"Flight search is temporarily unavailable: {exc}"

    try:
        data = response.json()
    except ValueError:
        return "Flight search returned an invalid response."

    if data.get("error"):
        error = data["error"]
        message = error.get("message") if isinstance(error, dict) else str(error)
        return f"Flight search error: {message}"

    flights = []
    route_note = ""

    if origin_iata or destination_iata:
        route_parts = []
        if origin_iata:
            route_parts.append(f"departure {origin_iata}")
        if destination_iata:
            route_parts.append(f"arrival {destination_iata}")
        route_note = f"Filtered live flights by {', '.join(route_parts)}.\n\n"
    else:
        route_note = (
            "Showing sample live flights because no supported origin/destination "
            "airport was detected in the request.\n\n"
        )

    if "data" in data:

        for flight in data["data"][:5]:

            airline = flight.get("airline", {}).get("name") or "Unknown airline"

            departure_info = flight.get("departure", {})
            arrival_info = flight.get("arrival", {})

            departure = departure_info.get("airport") or departure_info.get("iata") or "Unknown"
            arrival = arrival_info.get("airport") or arrival_info.get("iata") or "Unknown"

            status = flight.get("flight_status", "Unknown")
            flight_number = flight.get("flight", {}).get("iata") or "Unknown flight"

            flights.append(
                "\n".join(
                    [
                        f"Airline: {airline}",
                        f"Flight: {flight_number}",
                        f"Departure: {departure}",
                        f"Arrival: {arrival}",
                        f"Status: {status}",
                    ]
                )
            )

    return route_note + ("\n\n".join(flights) or "No matching live flight data returned.")
