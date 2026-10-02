"""Download NOAA hourly station data, calculate historical curves, and update the dashboard."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, time as datetime_time, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
DEFAULT_MARKDOWN = ROOT / "weather-temperature-curves.md"
DEFAULT_HTML = ROOT / "weather-forecast.html"
JSON_BLOCK = re.compile(r"```json\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL)
HTML_BLOCK = re.compile(
    r'(<script\s+id="temperature-curve-data"\s+type="application/json">)'
    r".*?(</script>)",
    re.DOTALL | re.IGNORECASE,
)
EXPECTED_LOCATIONS = {
    "palo_duro": ("Palo Duro Canyon, TX", "2026-12-26"),
    "dauphin_island": ("Dauphin Island, AL", "2026-12-31"),
}
EXPECTED_HOURS = list(range(25))
CURVE_KEYS = ("colder_than_average_f", "average_f", "warmer_than_average_f")
NOAA_BASE_URL = "https://www.ncei.noaa.gov/data/global-hourly/access"
NOAA_SOURCE_NAME = "NOAA/NCEI Integrated Surface Database (Global Hourly)"
DEFAULT_START_YEAR = 1991
DEFAULT_END_YEAR = 2025
DEFAULT_MIN_SAMPLES = 20
DEFAULT_MIN_DAILY_HOURS = 18
USER_AGENT = "WinterLoopWeather/1.0 (historical temperature scenario utility)"
STATION_CONFIG = {
    "palo_duro": {
        "file_id": "72363023047",
        "display_id": "723630-23047 (USAF-WBAN)",
        "target_lat": 34.9669813,
        "target_lon": -101.6713214,
        "month": 12,
        "day": 26,
    },
    "dauphin_island": {
        "file_id": "72223013894",
        "display_id": "722230-13894 (USAF-WBAN)",
        "target_lat": 30.255,
        "target_lon": -88.110,
        "month": 12,
        "day": 31,
    },
}
REPORT_TYPE_PRIORITY = {"FM-12": 3, "FM-15": 2, "FM-16": 1}


class CurveDataError(ValueError):
    """Input is not a complete, documented hourly-curve dataset."""


def require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CurveDataError(f"{field} must be a non-empty string.")
    return value.strip()


def reject_json_constant(value: str) -> None:
    raise CurveDataError(f"Invalid JSON numeric constant: {value}.")


def load_markdown(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise CurveDataError(f"Markdown data file not found: {path}")
    text = path.read_text(encoding="utf-8")
    if "INSUFFICIENT_HISTORICAL_DATA" in text:
        report = text[text.find("INSUFFICIENT_HISTORICAL_DATA") :].strip()
        raise CurveDataError("Gemini reported insufficient historical data; no curves were loaded. Report:\n" + report)
    blocks = JSON_BLOCK.findall(text)
    if len(blocks) != 1:
        raise CurveDataError("Expected exactly one fenced json block in the Markdown data file.")
    try:
        data = json.loads(blocks[0], parse_constant=reject_json_constant)
    except json.JSONDecodeError as error:
        raise CurveDataError(f"Invalid JSON: {error}") from error
    if not isinstance(data, dict):
        raise CurveDataError("The JSON root must be an object.")
    return data


def validate(data: dict[str, Any]) -> None:
    if data.get("schema_version") != 1:
        raise CurveDataError("schema_version must be 1.")
    try:
        date.fromisoformat(require_text(data.get("generated_on"), "generated_on"))
    except ValueError as error:
        raise CurveDataError("generated_on must use YYYY-MM-DD format.") from error
    require_text(data.get("methodology"), "methodology")
    require_text(data.get("scenario_definition"), "scenario_definition")

    period = data.get("historical_period")
    if not isinstance(period, dict):
        raise CurveDataError("historical_period must contain start_year and end_year.")
    start, end = period.get("start_year"), period.get("end_year")
    if (
        not isinstance(start, int) or isinstance(start, bool)
        or not isinstance(end, int) or isinstance(end, bool)
        or start > end or end > 2025
    ):
        raise CurveDataError("historical_period must be a valid historical range ending no later than 2025.")

    locations = data.get("locations")
    if not isinstance(locations, dict) or set(locations) != set(EXPECTED_LOCATIONS):
        raise CurveDataError("locations must contain exactly palo_duro and dauphin_island.")

    for key, (label, target_date) in EXPECTED_LOCATIONS.items():
        place = locations[key]
        if not isinstance(place, dict):
            raise CurveDataError(f"locations.{key} must be an object.")
        if place.get("label") != label or place.get("target_date") != target_date:
            raise CurveDataError(f"locations.{key} must match {label} on {target_date}.")
        if place.get("timezone") != "America/Chicago":
            raise CurveDataError(f"locations.{key}.timezone must be America/Chicago.")
        for field in ("station_name", "station_id", "source_name", "source_notes"):
            require_text(place.get(field), f"locations.{key}.{field}")
        url = require_text(place.get("source_url"), f"locations.{key}.source_url")
        if not url.startswith("https://"):
            raise CurveDataError(f"locations.{key}.source_url must be HTTPS.")

        years = place.get("years_used")
        if (
            not isinstance(years, list)
            or any(not isinstance(year, int) or isinstance(year, bool) for year in years)
            or years != sorted(set(years))
            or len(years) < 20
        ):
            raise CurveDataError(f"locations.{key}.years_used must list at least 20 distinct ascending years.")
        if any(year < start or year > end for year in years):
            raise CurveDataError(f"locations.{key}.years_used must fall inside historical_period.")
        if place.get("hours_local") != EXPECTED_HOURS:
            raise CurveDataError(f"locations.{key}.hours_local must be integers 0 through 24 inclusive.")

        sample_counts = place.get("hourly_sample_counts")
        if (
            not isinstance(sample_counts, list)
            or len(sample_counts) != 25
            or any(not isinstance(count, int) or isinstance(count, bool) for count in sample_counts)
        ):
            raise CurveDataError(f"locations.{key}.hourly_sample_counts must contain 25 integer counts.")
        if any(count < 20 for count in sample_counts):
            raise CurveDataError(f"locations.{key}.hourly_sample_counts must be at least 20 at every hour.")

        for curve_key in CURVE_KEYS:
            curve = place.get(curve_key)
            if not isinstance(curve, list) or len(curve) != 25:
                raise CurveDataError(f"locations.{key}.{curve_key} must contain exactly 25 hourly values.")
            for hour, value in enumerate(curve):
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    or value < -80
                    or value > 140
                ):
                    raise CurveDataError(
                        f"locations.{key}.{curve_key}[{hour}] must be a finite Fahrenheit value from -80 to 140."
                    )

        colder, average, warmer = (place[key_name] for key_name in CURVE_KEYS)
        for hour, triple in enumerate(zip(colder, average, warmer, strict=True)):
            if not triple[0] <= triple[1] <= triple[2]:
                raise CurveDataError(f"locations.{key} scenario curves cross at hour {hour}.")
        if not any(low < high for low, high in zip(colder, warmer, strict=True)):
            raise CurveDataError(f"locations.{key} colder and warmer curves must not be identical.")


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_miles = 3958.7613
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    value = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return 2 * radius_miles * math.asin(math.sqrt(value))


def station_year_tasks(start_year: int, end_year: int) -> set[tuple[str, int]]:
    tasks: set[tuple[str, int]] = set()
    for station in STATION_CONFIG.values():
        for target_year in range(start_year, end_year + 1):
            target_day = date(target_year, station["month"], station["day"])
            window_start = datetime.combine(target_day, datetime_time.min) + timedelta(hours=6)
            window_end = window_start + timedelta(days=1)
            for source_year in range(window_start.year, window_end.year + 1):
                tasks.add((station["file_id"], source_year))
    return tasks


def download_station_year(
    station_id: str,
    year: int,
    cache_dir: Path,
    refresh: bool,
) -> Path | None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{station_id}-{year}.csv"
    if cache_path.is_file() and cache_path.stat().st_size and not refresh:
        return cache_path

    url = f"{NOAA_BASE_URL}/{year}/{station_id}.csv"
    temporary_path = cache_path.with_suffix(".csv.part")
    last_error: Exception | None = None
    for attempt in range(3):
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/csv"})
        try:
            with urlopen(request, timeout=90) as response, temporary_path.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            if not temporary_path.stat().st_size:
                temporary_path.unlink(missing_ok=True)
                return None
            temporary_path.replace(cache_path)
            return cache_path
        except HTTPError as error:
            temporary_path.unlink(missing_ok=True)
            if error.code == 404:
                return None
            last_error = error
            if error.code < 500 and error.code != 429:
                break
        except (TimeoutError, URLError, OSError) as error:
            temporary_path.unlink(missing_ok=True)
            last_error = error
        if attempt < 2:
            time.sleep(1.5 * (attempt + 1))
    raise CurveDataError(f"Could not retrieve NOAA station file {station_id}/{year}: {last_error}")


def download_station_files(
    tasks: set[tuple[str, int]], cache_dir: Path, refresh: bool
) -> dict[tuple[str, int], Path | None]:
    files: dict[tuple[str, int], Path | None] = {}
    ordered_tasks = sorted(tasks)
    print(f"Retrieving {len(ordered_tasks)} NOAA station-year files (cached files are reused)...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(download_station_year, station_id, year, cache_dir, refresh): (station_id, year)
            for station_id, year in ordered_tasks
        }
        completed = 0
        for future in as_completed(futures):
            key = futures[future]
            files[key] = future.result()
            completed += 1
            if completed % 10 == 0 or completed == len(ordered_tasks):
                print(f"  checked {completed}/{len(ordered_tasks)} station-year files")
    return files


def parse_temperature(raw_value: str) -> tuple[float, int] | None:
    parts = (raw_value or "").strip().split(",")
    if len(parts) < 2 or not re.fullmatch(r"[+-]\d{4}", parts[0]):
        return None
    quality = parts[1].strip()
    if quality not in {"1", "5"} or parts[0][1:] == "9999":
        return None
    celsius = int(parts[0]) / 10
    return round(celsius * 9 / 5 + 32, 1), int(quality)


def extract_target_year(
    station_id: str,
    target_year: int,
    target_date: date,
    station_files: dict[tuple[str, int], Path | None],
) -> tuple[dict[int, float], dict[str, str] | None]:
    window_start_utc = datetime.combine(target_date, datetime_time.min) + timedelta(hours=6)
    window_end_utc = window_start_utc + timedelta(days=1)
    utc_dates = {window_start_utc.date().isoformat(), window_end_utc.date().isoformat()}
    best_by_hour: dict[int, tuple[tuple[int, int, int], float]] = {}
    metadata: dict[str, str] | None = None

    for source_year in range(window_start_utc.year, window_end_utc.year + 1):
        station_file = station_files.get((station_id, source_year))
        if station_file is None:
            continue
        with station_file.open("r", encoding="utf-8-sig", newline="") as source:
            for row in csv.DictReader(source):
                if metadata is None:
                    metadata = {
                        "name": (row.get("NAME") or "").strip(),
                        "latitude": (row.get("LATITUDE") or "").strip(),
                        "longitude": (row.get("LONGITUDE") or "").strip(),
                        "elevation": (row.get("ELEVATION") or "").strip(),
                    }
                date_text = row.get("DATE", "")
                if date_text[:10] not in utc_dates:
                    continue
                try:
                    observed_utc = datetime.fromisoformat(date_text[:19])
                except ValueError:
                    continue
                if observed_utc < window_start_utc or observed_utc > window_end_utc:
                    continue
                observed_local = observed_utc - timedelta(hours=6)
                if observed_local.date() == target_date:
                    hour = observed_local.hour
                elif observed_local.date() == target_date + timedelta(days=1) and observed_local.hour == 0:
                    hour = 24
                else:
                    continue

                parsed = parse_temperature(row.get("TMP", ""))
                if parsed is None:
                    continue
                temperature_f, quality = parsed
                report_type = (row.get("REPORT_TYPE") or "").strip()
                report_rank = REPORT_TYPE_PRIORITY.get(report_type, 0)
                minute_rank = -abs(observed_local.minute - 30)
                rank = (int(quality == 5), report_rank, minute_rank)
                if hour not in best_by_hour or rank > best_by_hour[hour][0]:
                    best_by_hour[hour] = (rank, temperature_f)

    return {hour: record[1] for hour, record in best_by_hour.items()}, metadata


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def build_location_curves(
    key: str,
    station_files: dict[tuple[str, int], Path | None],
    start_year: int,
    end_year: int,
    min_samples: int,
    min_daily_hours: int,
) -> dict[str, Any]:
    config = STATION_CONFIG[key]
    label, target_iso = EXPECTED_LOCATIONS[key]
    target_month, target_day = config["month"], config["day"]
    observations: dict[int, dict[int, float]] = {}
    station_metadata = None
    for year in range(start_year, end_year + 1):
        profile, metadata = extract_target_year(
            config["file_id"], year, date(year, target_month, target_day), station_files
        )
        if metadata:
            station_metadata = metadata
        if profile:
            observations[year] = profile

    if not station_metadata:
        raise CurveDataError(f"No station metadata or observations found for {label} ({config['display_id']}).")
    try:
        station_latitude = float(station_metadata["latitude"])
        station_longitude = float(station_metadata["longitude"])
        float(station_metadata["elevation"])
    except (TypeError, ValueError) as error:
        raise CurveDataError(f"NOAA station metadata is incomplete for {label}.") from error

    hourly_samples = [
        [profile[hour] for profile in observations.values() if hour in profile]
        for hour in EXPECTED_HOURS
    ]
    counts = [len(samples) for samples in hourly_samples]
    under_sampled = [(hour, count) for hour, count in enumerate(counts) if count < min_samples]
    if under_sampled:
        details = ", ".join(f"{hour:02d}:00={count}" for hour, count in under_sampled)
        raise CurveDataError(f"{label} has fewer than {min_samples} observations at these local hours: {details}.")
    average = [round(sum(samples) / len(samples), 1) for samples in hourly_samples]

    daily_means: dict[int, float] = {}
    for year, profile in observations.items():
        available_hours = [hour for hour in range(24) if hour in profile]
        if len(available_hours) >= min_daily_hours:
            daily_means[year] = sum(profile[hour] for hour in available_hours) / len(available_hours)
    if len(daily_means) < 20:
        raise CurveDataError(
            f"{label} has only {len(daily_means)} years with at least {min_daily_hours} valid daytime/nighttime hours; 20 are required."
        )

    daily_center = sum(daily_means.values()) / len(daily_means)
    anomalies = [value - daily_center for value in daily_means.values()]
    cold_offset = percentile(anomalies, 0.25)
    warm_offset = percentile(anomalies, 0.75)
    colder = [round(value + cold_offset, 1) for value in average]
    warmer = [round(value + warm_offset, 1) for value in average]

    distance = haversine_miles(
        config["target_lat"], config["target_lon"], station_latitude, station_longitude
    )
    station_name = station_metadata["name"] or config["display_id"]
    latest_used_year = max(daily_means)
    station_source_url = f"{NOAA_BASE_URL}/{latest_used_year}/{config['file_id']}.csv"
    source_notes = (
        f"Regional proxy station at {station_latitude:.4f}, {station_longitude:.4f}, "
        f"approximately {distance:.1f} miles from the target coordinates. "
        "This airport station may not capture campsite microclimates. Only TMP observations with "
        "NOAA quality flags 1 or 5 were used. One observation per local hour and year was selected, "
        "preferring quality flag 5, then FM-12/FM-15/FM-16 report priority; missing hours were excluded "
        "without interpolation. Hourly sample counts can vary."
    )
    return {
        "label": label,
        "target_date": target_iso,
        "timezone": "America/Chicago",
        "station_name": station_name,
        "station_id": config["display_id"],
        "source_name": NOAA_SOURCE_NAME,
        "source_url": station_source_url,
        "years_used": sorted(daily_means),
        "source_notes": source_notes,
        "hours_local": EXPECTED_HOURS,
        "hourly_sample_counts": counts,
        "colder_than_average_f": colder,
        "average_f": average,
        "warmer_than_average_f": warmer,
    }


def retrieve_noaa_curves(
    start_year: int,
    end_year: int,
    min_samples: int,
    min_daily_hours: int,
    refresh: bool,
) -> dict[str, Any]:
    cache_dir = Path(tempfile.gettempdir()) / "winter-loop-noaa-global-hourly"
    tasks = station_year_tasks(start_year, end_year)
    station_files = download_station_files(tasks, cache_dir, refresh)
    missing_files = [key for key, value in station_files.items() if value is None]
    if missing_files:
        print(f"Note: {len(missing_files)} station-year files were not present in the NOAA archive and will be skipped.")

    locations = {
        key: build_location_curves(key, station_files, start_year, end_year, min_samples, min_daily_hours)
        for key in EXPECTED_LOCATIONS
    }
    generated_on = date.today().isoformat()
    methodology = (
        "Calculated from NOAA/NCEI Global Hourly station CSVs. UTC timestamps were converted to local "
        "Central Standard Time by subtracting six hours. TMP values with quality flags 1 or 5 were used; "
        "one record per local station-hour/year was selected, preferring quality 5 and routine report types. "
        f"Each hourly mean uses available observations only and requires at least {min_samples} years; no "
        "missing temperatures were interpolated. Annual daily means require at least "
        f"{min_daily_hours} valid hours from 00:00–23:00. Annual anomalies are centered on their sample mean; "
        "their 25th and 75th percentiles shift the average hourly profile to form colder and warmer scenarios. "
        "The selected airport stations are regional proxies, not campsite observations."
    )
    return {
        "schema_version": 1,
        "generated_on": generated_on,
        "historical_period": {"start_year": start_year, "end_year": end_year},
        "methodology": methodology,
        "scenario_definition": (
            "The average line is the per-hour mean of available quality-checked observations. Colder and warmer "
            "lines add the 25th and 75th percentile of annual daily temperature anomalies centered on the mean "
            "of valid annual daily means."
        ),
        "locations": locations,
    }


def write_markdown(data: dict[str, Any], markdown_path: Path) -> None:
    markdown = (
        "# Historical Temperature Curves\n\n"
        "Generated locally from NOAA/NCEI Global Hourly observations. These regional-station historical "
        "scenarios are planning context, not a forecast for the trip dates. See each location's station, "
        "sample count, and proxy limitations.\n\n"
        "```json\n"
        + json.dumps(data, ensure_ascii=False, indent=2)
        + "\n```\n"
    )
    temporary_path = markdown_path.with_suffix(markdown_path.suffix + ".tmp")
    try:
        temporary_path.write_text(markdown, encoding="utf-8", newline="\n")
        temporary_path.replace(markdown_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def update_html(data: dict[str, Any], html_path: Path, check_only: bool) -> None:
    if not html_path.is_file():
        raise CurveDataError(f"Weather HTML file not found: {html_path}")
    html = html_path.read_text(encoding="utf-8")
    matches = list(HTML_BLOCK.finditer(html))
    if len(matches) != 1:
        raise CurveDataError('Expected exactly one script block with id="temperature-curve-data".')
    if check_only:
        print("Validation passed; HTML was not changed (--check).")
        return

    encoded = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    updated = HTML_BLOCK.sub(
        lambda match: match.group(1) + "\n" + encoded + "\n" + match.group(2),
        html,
        count=1,
    )
    temporary = html_path.with_suffix(html_path.suffix + ".tmp")
    try:
        temporary.write_text(updated, encoding="utf-8", newline="\n")
        temporary.replace(html_path)
    finally:
        if temporary.exists():
            temporary.unlink()

    print(f"Updated {html_path.name} with validated curves:")
    for key, place in data["locations"].items():
        print(f"  {key}: {len(place['years_used'])} years, {place['target_date']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Retrieve NOAA hourly station records, calculate scenarios, and update the weather dashboard."
    )
    parser.add_argument("--data", type=Path, default=DEFAULT_MARKDOWN, help="Markdown curve-data file (also used by --check and --from-markdown).")
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML, help="Weather HTML file to update.")
    parser.add_argument("--check", action="store_true", help="Validate existing Markdown data without modifying files.")
    parser.add_argument("--from-markdown", action="store_true", help="Import/validate a researched Markdown response instead of retrieving NOAA station files.")
    parser.add_argument("--start-year", type=int, default=DEFAULT_START_YEAR, help=f"First observation year (default: {DEFAULT_START_YEAR}).")
    parser.add_argument("--end-year", type=int, default=DEFAULT_END_YEAR, help=f"Last observation year (default: {DEFAULT_END_YEAR}).")
    parser.add_argument("--min-samples", type=int, default=DEFAULT_MIN_SAMPLES, help=f"Minimum valid station-year observations required at each hour (default: {DEFAULT_MIN_SAMPLES}).")
    parser.add_argument("--min-daily-hours", type=int, default=DEFAULT_MIN_DAILY_HOURS, help=f"Minimum valid target-day hours needed for an annual anomaly (default: {DEFAULT_MIN_DAILY_HOURS}).")
    parser.add_argument("--refresh", action="store_true", help="Redownload NOAA station-year files instead of using the temp cache.")
    args = parser.parse_args()
    try:
        if args.check or args.from_markdown:
            data = load_markdown(args.data)
        else:
            if args.start_year < 1900 or args.end_year > 2025 or args.start_year > args.end_year:
                raise CurveDataError("Choose a valid historical range from 1900 through 2025.")
            if args.min_samples < 2 or args.min_daily_hours < 1 or args.min_daily_hours > 24:
                raise CurveDataError("Sample thresholds must be positive; min-daily-hours cannot exceed 24.")
            data = retrieve_noaa_curves(
                args.start_year,
                args.end_year,
                args.min_samples,
                args.min_daily_hours,
                args.refresh,
            )
        validate(data)
        update_html(data, args.html, args.check)
        if not args.check:
            write_markdown(data, args.data)
    except (CurveDataError, OSError) as error:
        print(f"Weather curve update failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())