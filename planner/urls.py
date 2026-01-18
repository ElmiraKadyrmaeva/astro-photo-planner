from django.urls import path
from . import views
from .views import (
    home,
    LocationListView,
    LocationCreateView,
    LocationUpdateView,
    LocationDeleteView,
    TargetListView,
    TargetCreateView,
    TargetUpdateView,
    TargetDeleteView,
    PlanListView,
    PlanCreateView,
    PlanDetailView,
    PlanRunView,
)

urlpatterns = [
    path("", home, name="home"),

    path("locations/", LocationListView.as_view(), name="location_list"),
    path("locations/create/", LocationCreateView.as_view(), name="location_create"),
    path("locations/<int:pk>/edit/", LocationUpdateView.as_view(), name="location_edit"),
    path("locations/<int:pk>/delete/", LocationDeleteView.as_view(), name="location_delete"),

    path("targets/", TargetListView.as_view(), name="target_list"),
    path("targets/create/", TargetCreateView.as_view(), name="target_create"),
    path("targets/<int:pk>/edit/", TargetUpdateView.as_view(), name="target_edit"),
    path("targets/<int:pk>/delete/", TargetDeleteView.as_view(), name="target_delete"),

    path("plans/", PlanListView.as_view(), name="plan_list"),
    path("plans/create/", PlanCreateView.as_view(), name="plan_create"),
    path("plans/<int:pk>/", PlanDetailView.as_view(), name="plan_detail"),
    path("plans/<int:pk>/run/", PlanRunView.as_view(), name="plan_run"),
    path('register/', views.register, name='register'),  # Страница регистрации
    path('login/', views.login_view, name='login'),      # Страница входа
    path('logout/', views.logout_view, name='logout'),   # Страница выхода
]
