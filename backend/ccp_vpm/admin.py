from django.contrib import admin
from django.db.models import Count
from .models import Session, Item, Trial

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display  = ("id", "vpm_mode", "started_at", "user_id", "trials_count")
    list_filter   = ("vpm_mode", "started_at")
    search_fields = ("id", "user_id")
    date_hierarchy = "started_at"
    ordering = ("-started_at",)
    readonly_fields = ("started_at",)
    list_per_page = 50

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_trials_count=Count("trial"))

    @admin.display(description="Trials", ordering="_trials_count")
    def trials_count(self, obj):
        return getattr(obj, "_trials_count", 0)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display  = ("id", "submodality", "difficulty_level", "correct_index")
    list_filter   = ("submodality", "difficulty_level")
    search_fields = ("id",)
    ordering      = ("submodality", "difficulty_level", "id")
    list_per_page = 50


@admin.register(Trial)
class TrialAdmin(admin.ModelAdmin):
    list_display  = ("id", "session", "item", "is_correct", "response_time_ms", "chosen_index")
    list_filter   = ("is_correct", "item__difficulty_level")
    search_fields = ("session__id", "item__id")
    ordering      = ("-id",)
    list_select_related = ("session", "item")
    list_per_page = 50