import requests
import csv
from datetime import datetime, timedelta

# Replace with your FRED API key (you can get one at https://fred.stlouisfed.org/)
FRED_API_KEY = "5c1fc41bfb9c4550f4d3eae5c5eddd10"

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
SOFR_SERIES_ID = "SOFR"  # Daily
LIBOR_SERIES_ID = "FEDFUNDS"  # 3-month USD LIBOR

def fetch_fred_data(series_id, start_date, end_date):
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
        "observation_end": end_date
    }
    response = requests.get(FRED_BASE_URL, params=params)
    response.raise_for_status()
    raw = response.json().get("observations", [])
    return {
        obs["date"]: float(obs["value"])
        for obs in raw if obs["value"] != "."
    }

def merge_and_fill(libor_data, sofr_data, start_date, end_date):
    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    merged = {}
    last_known_rate = None

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")

        # Prefer SOFR, fallback to LIBOR, then carry-forward
        if date_str in sofr_data:
            last_known_rate = sofr_data[date_str]
        elif date_str in libor_data:
            last_known_rate = libor_data[date_str]

        if last_known_rate is not None:
            merged[date_str] = last_known_rate

        current += timedelta(days=1)
    return merged

def save_csv(rate_series, filename="floating_rate_index.csv"):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "rate"])
        for date, rate in sorted(rate_series.items()):
            writer.writerow([date, rate])
    print(f"[✓] Saved: {filename}")

def main():
    start_date = "2010-01-01"
    end_date = datetime.today().strftime("%Y-%m-%d")

    print("[↓] Fetching LIBOR...")
    libor_data = fetch_fred_data(LIBOR_SERIES_ID, start_date, end_date)

    print("[↓] Fetching SOFR...")
    sofr_data = fetch_fred_data(SOFR_SERIES_ID, "2018-04-03", end_date)

    print("[🔁] Merging and filling rates...")
    floating_rate_index = merge_and_fill(libor_data, sofr_data, start_date, end_date)

    print("[💾] Saving CSV...")
    save_csv(floating_rate_index)

if __name__ == "__main__":
    main()
