from tools.supabase_tool import insert_flight, list_flights


if __name__ == "__main__":
    inserted = insert_flight(
        flight_number="AI101",
        origin="DEL",
        destination="JFK",
        status="scheduled",
    )
    print("Inserted flight:")
    print(inserted)

    print("\nLatest flights:")
    print(list_flights())
