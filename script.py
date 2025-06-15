# Let me create a comprehensive list of New England airports with their ICAO codes
# based on the information gathered from the search results

new_england_airports = {
    # Massachusetts
    "KBOS": {"name": "General Edward Lawrence Logan International Airport", "city": "Boston", "state": "MA"},
    "KMHT": {"name": "Manchester-Boston Regional Airport", "city": "Manchester", "state": "NH"},
    "KBDL": {"name": "Bradley International Airport", "city": "Hartford/Windsor Locks", "state": "CT"},
    "KPVD": {"name": "Theodore Francis Green Airport", "city": "Providence/Warwick", "state": "RI"},
    "KORH": {"name": "Worcester Regional Airport", "city": "Worcester", "state": "MA"},
    "KBGR": {"name": "Bangor International Airport", "city": "Bangor", "state": "ME"},
    "KBTV": {"name": "Patrick Leahy Burlington International Airport", "city": "Burlington", "state": "VT"},
    "KPWM": {"name": "Portland International Jetport", "city": "Portland", "state": "ME"},
    "KHVN": {"name": "Tweed New Haven Airport", "city": "New Haven", "state": "CT"},
    "KACK": {"name": "Nantucket Memorial Airport", "city": "Nantucket", "state": "MA"},
    "KMVT": {"name": "Martha's Vineyard Airport", "city": "Martha's Vineyard", "state": "MA"},
    "KHYA": {"name": "Barnstable Municipal Airport", "city": "Hyannis", "state": "MA"},
    "KPVC": {"name": "Provincetown Municipal Airport", "city": "Provincetown", "state": "MA"},
    "KGHG": {"name": "Marshfield Municipal Airport", "city": "Marshfield", "state": "MA"},
    "KOWD": {"name": "Norwood Memorial Airport", "city": "Norwood", "state": "MA"},
    "KBED": {"name": "Laurence G. Hanscom Field", "city": "Bedford", "state": "MA"},
    "KEWB": {"name": "New Bedford Regional Airport", "city": "New Bedford", "state": "MA"},
    "KFMH": {"name": "Otis Air National Guard Base", "city": "Falmouth", "state": "MA"},
    "KLEB": {"name": "Lebanon Municipal Airport", "city": "Lebanon", "state": "NH"},
    "KASH": {"name": "Boire Field", "city": "Nashua", "state": "NH"},
    "KCON": {"name": "Concord Municipal Airport", "city": "Concord", "state": "NH"},
    "KDAW": {"name": "Rochester Airport", "city": "Rochester", "state": "NH"},
    "KMPV": {"name": "Edward F. Knapp State Airport", "city": "Montpelier", "state": "VT"},
    "KRUT": {"name": "Rutland-Southern Vermont Regional Airport", "city": "Rutland", "state": "VT"},
    "KAUG": {"name": "Augusta State Airport", "city": "Augusta", "state": "ME"},
    "KRKD": {"name": "Knox County Regional Airport", "city": "Rockland", "state": "ME"},
    "KBHB": {"name": "Hancock County-Bar Harbor Airport", "city": "Bar Harbor", "state": "ME"},
    "KPQI": {"name": "Northern Maine Regional Airport", "city": "Presque Isle", "state": "ME"},
    "KGON": {"name": "Groton-New London Airport", "city": "Groton/New London", "state": "CT"},
    "KDXR": {"name": "Danbury Municipal Airport", "city": "Danbury", "state": "CT"},
    "KMMK": {"name": "Meriden Markham Municipal Airport", "city": "Meriden", "state": "CT"},
    "KUUU": {"name": "Newport State Airport", "city": "Newport", "state": "RI"},
    "KSFZ": {"name": "North Central State Airport", "city": "Smithfield", "state": "RI"},
}

print("New England Airports ICAO Codes and Information:")
print("=" * 60)

for icao, info in new_england_airports.items():
    print(f"{icao}: {info['name']} - {info['city']}, {info['state']}")

print(f"\nTotal airports: {len(new_england_airports)}")

# Group by state
by_state = {}
for icao, info in new_england_airports.items():
    state = info['state']
    if state not in by_state:
        by_state[state] = []
    by_state[state].append((icao, info))

print("\nGrouped by State:")
print("=" * 30)
for state in sorted(by_state.keys()):
    print(f"\n{state}:")
    for icao, info in by_state[state]:
        print(f"  {icao}: {info['name']} - {info['city']}")