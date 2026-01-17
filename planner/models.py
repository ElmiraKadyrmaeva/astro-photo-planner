from django.conf import settings
from django.db import models


class Location(models.Model):
    """
    Локация съёмки: координаты + часовой пояс.
    Привязана к владельцу (owner).
    """
    name = models.CharField("Название", max_length=120)
    latitude = models.DecimalField("Широта", max_digits=8, decimal_places=5)
    longitude = models.DecimalField("Долгота", max_digits=8, decimal_places=5)
    timezone = models.CharField("Часовой пояс", max_length=64, default="UTC")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="locations",
        verbose_name="Владелец",
    )

    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Локация"
        verbose_name_plural = "Локации"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.latitude}, {self.longitude})"


class Target(models.Model):
    """
    Цель съёмки: DSO/MilkyWay и т.д.
    Для DSO храним RA/Dec (в градусах)
    """
    class TargetType(models.TextChoices):
        MOON = "Moon", "Луна"
        PLANET = "Planet", "Планета"
        DSO = "DSO", "Deep Sky Object"
        MILKY_WAY = "MilkyWay", "Млечный путь"

    name = models.CharField("Название", max_length=120)
    target_type = models.CharField("Тип цели", max_length=20, choices=TargetType.choices)

    # Для DSO: прямое восхождение и склонение.
    # Чтобы не усложнять — храним в градусах (удобно для AstroPy).
    right_ascension = models.DecimalField(
        "Прямое восхождение (RA, °)",
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
    )
    declination = models.DecimalField(
        "Склонение (Dec, °)",
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="targets",
        verbose_name="Владелец",
    )

    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Цель"
        verbose_name_plural = "Цели"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.target_type})"


class SessionRequest(models.Model):
    """
    План съёмки: пользователь выбирает локацию + цель и ограничения для расчёта
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="session_requests",
        verbose_name="Пользователь",
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="session_requests",
        verbose_name="Локация",
    )
    target = models.ForeignKey(
        Target,
        on_delete=models.CASCADE,
        related_name="session_requests",
        verbose_name="Цель",
    )

    date_from = models.DateField("Начало периода")
    date_to = models.DateField("Конец периода")

    min_target_altitude = models.PositiveSmallIntegerField(
        "Мин. высота цели (°)",
        default=20,
        help_text="0..90",
    )
    max_cloud_cover = models.PositiveSmallIntegerField(
        "Макс. облачность (%)",
        default=40,
        help_text="0..100",
    )
    avoid_moon = models.BooleanField(
        "Учитывать влияние Луны",
        default=True,
    )

    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "План съёмки"
        verbose_name_plural = "Планы съёмки"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"План #{self.id}: {self.location} / {self.target}"


class ForecastHour(models.Model):
    """
    Кэш почасового прогноза погоды (Open-Meteo) для конкретной локации
    """
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="forecast_hours",
        verbose_name="Локация",
    )
    timestamp = models.DateTimeField("Время (час прогноза)")

    cloud_cover = models.PositiveSmallIntegerField("Облачность (%)", default=0)
    precipitation = models.DecimalField(
        "Осадки",
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Единицы зависят от API (обычно мм)",
    )
    visibility = models.PositiveIntegerField(
        "Видимость",
        default=0,
        help_text="Единицы зависят от API (обычно метры)",
    )

    source = models.CharField("Источник", max_length=64, default="open-meteo")
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Почасовой прогноз"
        verbose_name_plural = "Почасовые прогнозы"
        ordering = ["-timestamp"]
        constraints = [
            models.UniqueConstraint(
                fields=["location", "timestamp"],
                name="uniq_forecast_location_timestamp",
            )
        ]

    def __str__(self) -> str:
        return f"{self.location.name} — {self.timestamp}"


class AstroWindow(models.Model):
    """
    Рассчитанное окно съёмки - результат аналитики.
    """
    plan = models.ForeignKey(
        SessionRequest,
        on_delete=models.CASCADE,
        related_name="astro_windows",
        verbose_name="План",
    )

    start_time = models.DateTimeField("Начало окна")
    end_time = models.DateTimeField("Конец окна")

    score = models.DecimalField("Оценка", max_digits=6, decimal_places=2)

    avg_cloud_cover = models.PositiveSmallIntegerField("Средняя облачность (%)", default=0)
    moon_illumination = models.DecimalField(
        "Освещённость Луны (0..1)",
        max_digits=4,
        decimal_places=3,
        default=0,
    )
    max_target_altitude = models.DecimalField(
        "Макс. высота цели (°)",
        max_digits=6,
        decimal_places=2,
        default=0,
    )
    is_astronomical_dark = models.BooleanField("Астрономическая ночь", default=False)

    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Окно съёмки"
        verbose_name_plural = "Окна съёмки"
        ordering = ["-score", "start_time"]

    def __str__(self) -> str:
        return f"Окно {self.start_time} — {self.end_time} (score={self.score})"
