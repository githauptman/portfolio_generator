# utils/hist_sofr.py

from datetime import datetime, timedelta
import requests

FRED_API_KEY = '5c1fc41bfb9c4550f4d3eae5c5eddd10'
FRED_URL = 'https://api.stlouisfed.org/fred/series/observations'
SOFR_SERIES_ID = 'SOFR'


def get_sofr_on_date(date_str):
    """
    Try to get SOFR for a specific date. Returns None if missing.
    """
    params = {
        'series_id': SOFR_SERIES_ID,
        'observation_start': date_str,
        'observation_end': date_str,
        'api_key': FRED_API_KEY,
        'file_type': 'json'
    }

    response = requests.get(FRED_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        observations = data.get('observations', [])
        if observations and observations[0]['value'] != ".":
            return float(observations[0]['value'])
        else:
            return None
    else:
        raise RuntimeError(f"[FRED API Error] {response.status_code}: {response.text}")


def get_next_available_sofr(start_date_str, max_lookahead_days=7):
    """
    Find the next date with available SOFR, up to N days ahead.
    Returns a tuple: (sofr_value, date_str) or (None, None) if not found.
    """
    date = datetime.strptime(start_date_str, "%Y-%m-%d")

    for i in range(max_lookahead_days):
        date_str = date.strftime("%Y-%m-%d")
        sofr = get_sofr_on_date(date_str)
        if sofr is not None:
            return sofr, date_str
        date += timedelta(days=1)

    print(f"[!] No SOFR found within {max_lookahead_days} days after {start_date_str}")
    return None, None
