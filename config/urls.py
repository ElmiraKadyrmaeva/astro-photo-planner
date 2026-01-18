from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),  # login/logout/password_*
    path("", include("planner.urls")),

    # ВАЖНО: переопределяем logout, чтобы работал по GET
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
]
