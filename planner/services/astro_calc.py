from astropy.utils import iers
iers.conf.auto_download = False
iers.conf.use_network = False
import datetime as dt
from dataclasses import dataclass

from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_body, get_sun
from astropy.time import Time
import astropy.units as u

from planner.models import Location, Target


@dataclass(frozen=True)
class HourAstro:
    sun_alt_deg: float
    moon_alt_deg: float
    moon_illumination: float  # 0..1
    target_alt_deg: float


def _earth_location(location: Location) -> EarthLocation:
    return EarthLocation(lat=float(location.latitude) * u.deg, lon=float(location.longitude) * u.deg)


def _moon_illumination_fraction(time: Time) -> float:
    """
    Приближение: освещённость Луны через угловое расстояние (элонгацию) между Солнцем и Луной
    new moon ~ 0, full moon ~ 1
    """
    sun = get_sun(time)
    moon = get_body("moon", time)
    elong = sun.separation(moon).rad  # 0..pi
    # 0 -> 0, pi -> 1
    frac = (1.0 - __import__("math").cos(elong)) / 2.0
    return max(0.0, min(1.0, float(frac)))


def compute_hour_astro(location: Location, target: Target, timestamp_utc: dt.datetime) -> HourAstro:
    """
    timestamp_utc должен быть aware (UTC)
    Возвращает высоты Солнца, Луны, цели и освещённость Луны
    """
    loc = _earth_location(location)

    t = Time(timestamp_utc)

    altaz = AltAz(obstime=t, location=loc)

    sun_alt = get_sun(t).transform_to(altaz).alt.degree

    moon = get_body("moon", t).transform_to(altaz)
    moon_alt = moon.alt.degree
    moon_illum = _moon_illumination_fraction(t)

    # Высота цели:
    # - DSO: используем RA/Dec
    # - MilkyWay: упростим (как первая версия) — берем центр Галактики (примерно)
    # - Moon: цель = Луна
    # - Planet: пытаемся интерпретировать name как тело (mars/jupiter/venus...), иначе target_alt = 0
    target_alt = 0.0

    if target.target_type == Target.TargetType.DSO and target.right_ascension is not None and target.declination is not None:
        coord = SkyCoord(ra=float(target.right_ascension) * u.deg, dec=float(target.declination) * u.deg)
        target_alt = coord.transform_to(altaz).alt.degree

    elif target.target_type == Target.TargetType.MILKY_WAY:
        # Центр Галактики (приближение): RA=266.4168°, Dec=-29.0078°
        coord = SkyCoord(ra=266.4168 * u.deg, dec=-29.0078 * u.deg)
        target_alt = coord.transform_to(altaz).alt.degree

    elif target.target_type == Target.TargetType.MOON:
        target_alt = moon_alt

    elif target.target_type == Target.TargetType.PLANET:
        try:
            body = get_body(target.name.strip().lower(), t).transform_to(altaz)
            target_alt = body.alt.degree
        except Exception:
            target_alt = 0.0

    return HourAstro(
        sun_alt_deg=float(sun_alt),
        moon_alt_deg=float(moon_alt),
        moon_illumination=float(moon_illum),
        target_alt_deg=float(target_alt),
    )
