from django.contrib import admin

from .models import (
    Location,
    Target,
    SessionRequest,
    ForecastHour,
    AstroWindow,
    PlanHourScore,
)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "latitude", "longitude", "timezone", "created_at")
    search_fields = ("name", "owner__username")
    list_filter = ("timezone", "created_at")


@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "target_type", "owner", "created_at")
    search_fields = ("name", "owner__username")
    list_filter = ("target_type", "created_at")


@admin.register(SessionRequest)
class SessionRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "location",
        "target",
        "date_from",
        "date_to",
        "min_target_altitude",
        "max_cloud_cover",
        "avoid_moon",
        "created_at",
    )
    search_fields = ("user__username", "location__name", "target__name")
    list_filter = ("avoid_moon", "created_at")


@admin.register(ForecastHour)
class ForecastHourAdmin(admin.ModelAdmin):
    list_display = ("id", "location", "timestamp", "cloud_cover", "precipitation", "visibility", "source")
    search_fields = ("location__name",)
    list_filter = ("source", "location")
    date_hierarchy = "timestamp"


@admin.register(AstroWindow)
class AstroWindowAdmin(admin.ModelAdmin):
    list_display = ("id", "plan", "start_time", "end_time", "score", "avg_cloud_cover", "max_target_altitude", "is_astronomical_dark")
    search_fields = ("plan__user__username", "plan__location__name", "plan__target__name")
    list_filter = ("is_astronomical_dark",)
    date_hierarchy = "start_time"


@admin.register(PlanHourScore)
class PlanHourScoreAdmin(admin.ModelAdmin):
    list_display = ("id", "plan", "timestamp", "score", "cloud_cover", "target_altitude", "moon_illumination", "is_astronomical_dark")
    search_fields = ("plan__user__username", "plan__location__name", "plan__target__name")
    list_filter = ("is_astronomical_dark",)
    date_hierarchy = "timestamp"
