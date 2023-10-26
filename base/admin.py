from django.contrib import admin

from .models import (
    UploadHistory,
    Announcement
)

@admin.register(UploadHistory)
class UploadHistoryAdmin(admin.ModelAdmin):
    model = UploadHistory

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    model = Announcement
    list_display = ('title', 'created','last_updated', 'version')