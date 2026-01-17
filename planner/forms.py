from django import forms

from .models import Location, Target, SessionRequest


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ["name", "latitude", "longitude", "timezone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def clean_latitude(self):
        lat = self.cleaned_data["latitude"]
        if lat < -90 or lat > 90:
            raise forms.ValidationError("Широта должна быть в диапазоне от -90 до 90.")
        return lat

    def clean_longitude(self):
        lon = self.cleaned_data["longitude"]
        if lon < -180 or lon > 180:
            raise forms.ValidationError("Долгота должна быть в диапазоне от -180 до 180.")
        return lon


class TargetForm(forms.ModelForm):
    class Meta:
        model = Target
        fields = ["name", "target_type", "right_ascension", "declination"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "target_type":
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

    def clean(self):
        cleaned = super().clean()
        target_type = cleaned.get("target_type")
        ra = cleaned.get("right_ascension")
        dec = cleaned.get("declination")

        if target_type == Target.TargetType.DSO:
            if ra is None or dec is None:
                raise forms.ValidationError(
                    "Для DSO необходимо указать прямое восхождение (RA) и склонение (Dec)."
                )

        return cleaned


class SessionRequestForm(forms.ModelForm):
    class Meta:
        model = SessionRequest
        fields = [
            "location",
            "target",
            "date_from",
            "date_to",
            "min_target_altitude",
            "max_cloud_cover",
            "avoid_moon",
        ]
        widgets = {
            "date_from": forms.DateInput(attrs={"type": "date"}),
            "date_to": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in ("location", "target"):
                field.widget.attrs["class"] = "form-select"
            elif name == "avoid_moon":
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"

    def clean(self):
        cleaned = super().clean()
        date_from = cleaned.get("date_from")
        date_to = cleaned.get("date_to")
        min_alt = cleaned.get("min_target_altitude")
        max_cloud = cleaned.get("max_cloud_cover")

        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("Дата начала не может быть позже даты окончания.")

        if min_alt is not None and (min_alt < 0 or min_alt > 90):
            raise forms.ValidationError(
                "Минимальная высота цели должна быть в диапазоне от 0 до 90 градусов."
            )

        if max_cloud is not None and (max_cloud < 0 or max_cloud > 100):
            raise forms.ValidationError(
                "Максимальная облачность должна быть в диапазоне от 0 до 100%."
            )

        return cleaned
