# Optional Gemini Import: Historical Hourly Temperature Curves

## Workflow

The normal workflow is local NOAA retrieval: run `python update_weather_curves.py`. This optional prompt is only for a separate researched dataset/import. The local updater remains the authoritative repeatable workflow. If using Gemini, copy its complete Markdown response into `weather-temperature-curves.md`, run `python update_weather_curves.py --check`, then run `python update_weather_curves.py --from-markdown` only if validation passes.

## Reusable Prompt

```text
Optionally research historically based, 24-hour temperature scenario profiles for these two overnight locations for manual import. The preferred project workflow retrieves NOAA Global Hourly files locally with Python. Use actual documented historical hourly observations here; do not use a current forecast and do not invent measurements, years, stations, sources, citations, or URLs.

LOCATIONS
1. Palo Duro Canyon / Hackberry Campground near Canyon, Texas. Target local date: 2026-12-26. Approximate coordinates: 34.9670, -101.6713.
2. Dauphin Island, Alabama. Target local date: 2026-12-31. Approximate coordinates: 30.2550, -88.1100.

DATA REQUIREMENTS AND METHOD
- Use the same configured NOAA Global Hourly proxy stations as the local script where possible: Amarillo Airport, USAF-WBAN `72363023047`, for Palo Duro; Mobile Regional Airport, USAF-WBAN `72223013894`, for Dauphin Island. These are regional airport proxies, not on-site stations; disclose distance and exposure limits. If using another station, explain why and provide actual metadata and a direct HTTPS source URL.
- Consider the target local calendar date for each year from 1991 through 2025. Convert timestamps to Fahrenheit and America/Chicago local standard time. Build hourly positions 00:00 through 23:00 on the target date and 24:00 at the following local midnight; do not duplicate 23:00 as 24:00.
- Follow the local script's report selection: use temperature (`TMP`) records with NOAA quality flag 1 or 5; select no more than one record per local station-hour/year, preferring flag 5, then report type FM-12, FM-15, FM-16, and then the observation nearest minute 30. Document that rule. Missing hours are expected: average available valid annual values separately at each hour without interpolation. Report the actual per-hour sample count in `hourly_sample_counts`; every count must be at least 20 and can exceed `years_used`.
- For scenario spread, use years having at least 18 valid target-date observations from local hours 00:00-23:00. List those ascending years in `years_used`; require at least 20. Calculate each such year's mean of available 00:00-23:00 observations, center the annual means on their multi-year mean, and use their 25th/75th percentile anomalies to shift all 25 average-profile points for the colder/warmer curves. No interpolation or imputation. Describe proxy and sampling limitations.
- These are historical context scenarios, not a deterministic prediction for 2026. Round to one decimal Fahrenheit. Do not substitute daily normals for hourly observations. If either location has fewer than 20 valid samples at any hour or fewer than 20 valid annual daily means, do not fabricate values; return the error format below.
- Error output must begin with the exact marker `INSUFFICIENT_HISTORICAL_DATA`, name the affected location(s), identify the sources checked, and explain which minimum sample requirement failed. It must contain no JSON block so the updater rejects it explicitly.

OUTPUT FORMAT IF BOTH LOCATIONS SUCCEED
Return the complete contents to paste into weather-temperature-curves.md. No commentary outside the file. Include a heading, one short note saying the results are historical scenarios and not a forecast, and exactly one fenced json block. JSON must parse strictly: no comments, trailing commas, NaN, Infinity, null values, or ellipses.

Use exactly these property names and structure. Replace examples/placeholders with verified values and put exactly 25 numeric values in each curve array:
{
  "schema_version": 1,
  "generated_on": "YYYY-MM-DD",
  "historical_period": {"start_year": 1991, "end_year": 2025},
  "methodology": "Concise truthful description of source, sampling, timezone, missing-data rule, and calculation.",
  "scenario_definition": "Colder and warmer are the 25th and 75th percentiles of historical annual temperature anomalies shifted from the mean hourly profile.",
  "locations": {
    "palo_duro": {
      "label": "Palo Duro Canyon, TX",
      "target_date": "2026-12-26",
      "timezone": "America/Chicago",
      "station_name": "Actual selected station name",
      "station_id": "Actual station identifier",
      "source_name": "Dataset/provider name",
      "source_url": "Direct HTTPS source URL",
      "years_used": [1991, 1992],
      "source_notes": "Station distance, representativeness, missing-data handling, and limitations.",
      "hours_local": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
      "hourly_sample_counts": [25 integer counts, one for each hour; every count must be at least 20],
      "colder_than_average_f": [25 numeric Fahrenheit values],
      "average_f": [25 numeric Fahrenheit values],
      "warmer_than_average_f": [25 numeric Fahrenheit values]
    },
    "dauphin_island": {
      "label": "Dauphin Island, AL",
      "target_date": "2026-12-31",
      "timezone": "America/Chicago",
      "station_name": "Actual selected station name",
      "station_id": "Actual station identifier",
      "source_name": "Dataset/provider name",
      "source_url": "Direct HTTPS source URL",
      "years_used": [1991, 1992],
      "source_notes": "Station distance, representativeness, missing-data handling, and limitations.",
      "hours_local": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
      "hourly_sample_counts": [25 integer counts, one for each hour; every count must be at least 20],
      "colder_than_average_f": [25 numeric Fahrenheit values],
      "average_f": [25 numeric Fahrenheit values],
      "warmer_than_average_f": [25 numeric Fahrenheit values]
    }
  }
}

Before returning, verify both locations have at least 20 distinct ascending `years_used` inside historical_period, at least 20 hourly samples at every point, valid source attribution, exactly 25 finite values in `hours_local`, `hourly_sample_counts`, and each temperature curve, and exact hours 0 through 24. Verify colder <= average <= warmer at every hour. Do not claim false precision or imply this predicts the actual 2026 weather.
```