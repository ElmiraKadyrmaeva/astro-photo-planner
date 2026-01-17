import datetime as dt
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from planner.models import AstroWindow, ForecastHour, SessionRequest
from planner.services.astro_calc import compute_hour_astro
from planner.services.open_meteo import fetch_and_cache_forecast


@dataclass(frozen=True)
class HourScore:
    timestamp: dt.datetime
    score: float
    cloud_cover: int
    moon_illumination: float
    target_alt: float
    is_dark: bool


def _compute_score(plan: SessionRequest, fh: ForecastHour, astro) -> HourScore:
    cloud = int(fh.cloud_cover)
    target_alt = float(astro.target_alt_deg)
    moon_illum = float(astro.moon_illumination)
    moon_alt = float(astro.moon_alt_deg)
    sun_alt = float(astro.sun_alt_deg)

    is_dark = sun_alt < -18.0  # астрономическая ночь

    score = 100.0

    # Облачность
    score -= 0.8 * cloud

    # Штраф за осадки (простейший, можно уточнять)
    if float(fh.precipitation) > 0:
        score -= 15.0

    # Бонус за темноту
    if is_dark:
        score += 10.0
    else:
        # если сумерки - штраф
        score -= 5.0

    # Бонус за высоту цели
    if target_alt > plan.min_target_altitude:
        score += min(20.0, (target_alt - plan.min_target_altitude) * 0.7)
    else:
        # если цель ниже минимума - сильный штраф
        score -= 30.0

    # Штраф за Луну (если план просит учитывать Луну)
    if plan.avoid_moon:
        # Чем выше луна и чем ярче — тем хуже
        moon_factor = max(0.0, moon_alt / 90.0)
        score -= 40.0 * moon_illum * moon_factor

    # Ограничим score
    score = max(0.0, min(100.0, score))

    return HourScore(
        timestamp=fh.timestamp,
        score=float(score),
        cloud_cover=cloud,
        moon_illumination=moon_illum,
        target_alt=target_alt,
        is_dark=is_dark,
    )


def _merge_to_windows(plan: SessionRequest, good_hours: list[HourScore]) -> list[AstroWindow]:
    """
    Склеиваем последовательные хорошие часы в окна
    """
    if not good_hours:
        return []

    good_hours = sorted(good_hours, key=lambda x: x.timestamp)

    windows: list[AstroWindow] = []
    cur_start = good_hours[0].timestamp
    cur_end = good_hours[0].timestamp
    scores = [good_hours[0].score]
    clouds = [good_hours[0].cloud_cover]
    moon_ills = [good_hours[0].moon_illumination]
    max_alt = good_hours[0].target_alt
    dark_flag = good_hours[0].is_dark

    for h in good_hours[1:]:
        # ожидаем следующий час
        if h.timestamp == cur_end + dt.timedelta(hours=1):
            cur_end = h.timestamp
            scores.append(h.score)
            clouds.append(h.cloud_cover)
            moon_ills.append(h.moon_illumination)
            max_alt = max(max_alt, h.target_alt)
            dark_flag = dark_flag or h.is_dark
        else:
            windows.append(
                AstroWindow(
                    plan=plan,
                    start_time=cur_start,
                    end_time=cur_end + dt.timedelta(hours=1),
                    score=sum(scores) / len(scores),
                    avg_cloud_cover=int(round(sum(clouds) / len(clouds))),
                    moon_illumination=sum(moon_ills) / len(moon_ills),
                    max_target_altitude=max_alt,
                    is_astronomical_dark=dark_flag,
                )
            )
            cur_start = h.timestamp
            cur_end = h.timestamp
            scores = [h.score]
            clouds = [h.cloud_cover]
            moon_ills = [h.moon_illumination]
            max_alt = h.target_alt
            dark_flag = h.is_dark

    windows.append(
        AstroWindow(
            plan=plan,
            start_time=cur_start,
            end_time=cur_end + dt.timedelta(hours=1),
            score=sum(scores) / len(scores),
            avg_cloud_cover=int(round(sum(clouds) / len(clouds))),
            moon_illumination=sum(moon_ills) / len(moon_ills),
            max_target_altitude=max_alt,
            is_astronomical_dark=dark_flag,
        )
    )

    return windows


@transaction.atomic
def run_planning(plan: SessionRequest) -> list[HourScore]:
    """
    1) Загружает/кэширует прогноз
    2) Считает астрономию на каждый час
    3) Считает score
    4) Сохраняет окна AstroWindow (перезаписывая старые)
    Возвращает массив почасовых HourScore (для графиков)
    """
    # 1) forecast
    forecast = fetch_and_cache_forecast(plan.location, plan.date_from, plan.date_to)

    # 2-3) compute scores
    hour_scores: list[HourScore] = []
    for fh in forecast:
        astro = compute_hour_astro(plan.location, plan.target, fh.timestamp)
        hs = _compute_score(plan, fh, astro)
        hour_scores.append(hs)

    # хорошие часы (по порогам плана)
    good = [
        h for h in hour_scores
        if h.cloud_cover <= plan.max_cloud_cover
        and h.target_alt >= plan.min_target_altitude
        and h.score >= 60.0
    ]

    # 4) windows
    AstroWindow.objects.filter(plan=plan).delete()
    windows = _merge_to_windows(plan, good)
    if windows:
        AstroWindow.objects.bulk_create(windows)

    return hour_scores
