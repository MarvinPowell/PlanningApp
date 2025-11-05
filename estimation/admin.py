from django.contrib import admin
from .models import EstimationSession, Participant, UserStory, Task, Vote


@admin.register(EstimationSession)
class EstimationSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['name', 'session', 'role', 'is_online', 'joined_at']
    list_filter = ['role', 'is_online', 'joined_at']
    search_fields = ['name', 'session__name']


@admin.register(UserStory)
class UserStoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'session', 'order', 'created_at']
    list_filter = ['session', 'created_at']
    search_fields = ['title', 'description']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'user_story', 'final_estimate', 'is_voting', 'created_at']
    list_filter = ['is_voting', 'final_estimate', 'created_at']
    search_fields = ['title', 'description']


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['participant', 'task', 'estimate', 'created_at']
    list_filter = ['estimate', 'created_at']
    search_fields = ['participant__name', 'task__title']
