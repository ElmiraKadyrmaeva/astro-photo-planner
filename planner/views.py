from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import LocationForm, TargetForm, SessionRequestForm
from .models import Location, Target, SessionRequest


def home(request):
    return render(request, "planner/home.html")


class LocationListView(LoginRequiredMixin, ListView):
    model = Location
    template_name = "planner/location_list.html"
    context_object_name = "locations"

    def get_queryset(self):
        # показываем только локации владельца
        return Location.objects.filter(owner=self.request.user).order_by("-created_at")


class LocationCreateView(LoginRequiredMixin, CreateView):
    model = Location
    form_class = LocationForm
    template_name = "planner/form.html"
    success_url = reverse_lazy("location_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Добавить локацию"
        return context


class LocationUpdateView(LoginRequiredMixin, UpdateView):
    model = Location
    form_class = LocationForm
    template_name = "planner/form.html"
    success_url = reverse_lazy("location_list")

    def get_queryset(self):
        return Location.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Редактировать локацию"
        return context


class LocationDeleteView(LoginRequiredMixin, DeleteView):
    model = Location
    template_name = "planner/confirm_delete.html"
    success_url = reverse_lazy("location_list")

    def get_queryset(self):
        return Location.objects.filter(owner=self.request.user)


class TargetListView(LoginRequiredMixin, ListView):
    model = Target
    template_name = "planner/target_list.html"
    context_object_name = "targets"

    def get_queryset(self):
        return Target.objects.filter(owner=self.request.user).order_by("-created_at")


class TargetCreateView(LoginRequiredMixin, CreateView):
    model = Target
    form_class = TargetForm
    template_name = "planner/form.html"
    success_url = reverse_lazy("target_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Добавить цель"
        return context


class TargetUpdateView(LoginRequiredMixin, UpdateView):
    model = Target
    form_class = TargetForm
    template_name = "planner/form.html"
    success_url = reverse_lazy("target_list")

    def get_queryset(self):
        return Target.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Редактировать цель"
        return context


class TargetDeleteView(LoginRequiredMixin, DeleteView):
    model = Target
    template_name = "planner/confirm_delete.html"
    success_url = reverse_lazy("target_list")

    def get_queryset(self):
        return Target.objects.filter(owner=self.request.user)


class PlanListView(LoginRequiredMixin, ListView):
    model = SessionRequest
    template_name = "planner/plan_list.html"
    context_object_name = "plans"

    def get_queryset(self):
        return (
            SessionRequest.objects.filter(user=self.request.user)
            .annotate(windows_count=Count("astro_windows"))
            .order_by("-created_at")
        )


class PlanCreateView(LoginRequiredMixin, CreateView):
    model = SessionRequest
    form_class = SessionRequestForm
    template_name = "planner/form.html"
    success_url = reverse_lazy("plan_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # показываем только локации/цели текущего пользователя
        form.fields["location"].queryset = Location.objects.filter(owner=self.request.user)
        form.fields["target"].queryset = Target.objects.filter(owner=self.request.user)
        return form

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Создать план съёмки"
        return context


class PlanDetailView(LoginRequiredMixin, DetailView):
    model = SessionRequest
    template_name = "planner/plan_detail.html"
    context_object_name = "plan"

    def get_queryset(self):
        return SessionRequest.objects.filter(user=self.request.user)
