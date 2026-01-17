import datetime as dt
from dataclasses import dataclass
from typing import Iterable

import requests
from django.utils import timezone

from planner.models import ForecastHour, Location


@dataclass(frozen=True)
class HourForecast:
    timestamp_utc: dt.datetime
    cloud_cover: int
    precipitation: float
    visibility: int


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def _date_range_days(date_from: dt.date, date_to: dt.date) -> int:
    return (date_to - date_from).days + 1


def fetch_and_cache_forecast(location: Location, date_from: dt.date, date_to: dt.date) -> list[ForecastHour]:
    """
    Загружает почасовой прогноз из Open-Meteo и кэширует в ForecastHour (UTC)
    Возвращает список ForecastHour в диапазоне [date_from, date_to]
    """

    days = _date_range_days(date_from, date_to)
    if days > 14:
        raise ValueError("Период слишком большой. Выберите диапазон до 14 дней.")

    tz_name = (location.timezone or "").strip()
    if not tz_name:
        tz_name = "auto"  # Open-Meteo сам определит timezone по координатам

    params = {
        "latitude": float(location.latitude),
        "longitude": float(location.longitude),
        "hourly": "cloud_cover,precipitation,visibility",
        "start_date": date_from.isoformat(),
        "end_date": date_to.isoformat(),
        "timezone": tz_name,
    }

    resp = requests.get(OPEN_METEO_URL, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    hourly = data.get("hourly") or {}
    times = hourly.get("time") or []
    cloud_list = hourly.get("cloud_cover") or []
    precip_list = hourly.get("precipitation") or []
    vis_list = hourly.get("visibility") or []

    n = min(len(times), len(cloud_list), len(precip_list), len(vis_list))

    objs: list[ForecastHour] = []
    for i in range(n):
        # Open-Meteo возвращает время в timezone=tz_name
        ts_naive = dt.datetime.fromisoformat(times[i])

        ts_aware = timezone.make_aware(ts_naive, dt.timezone.utc)

        cloud = int(cloud_list[i] or 0)
        precip = float(precip_list[i] or 0.0)
        vis = int(vis_list[i] or 0)

        obj, _ = ForecastHour.objects.update_or_create(
            location=location,
            timestamp=ts_aware,
            defaults={
                "cloud_cover": max(0, min(100, cloud)),
                "precipitation": precip,
                "visibility": max(0, vis),
                "source": "open-meteo",
            },
        )
        objs.append(obj)

    start_dt = timezone.make_aware(dt.datetime.combine(date_from, dt.time.min), dt.timezone.utc)
    end_dt = timezone.make_aware(dt.datetime.combine(date_to, dt.time.max), dt.timezone.utc)

    return list(
        ForecastHour.objects.filter(location=location, timestamp__range=(start_dt, end_dt)).order_by("timestamp")
    )
