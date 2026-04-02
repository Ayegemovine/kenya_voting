from django.contrib import admin
from .models import VoterProfile, Question, Choice, Vote

@admin.register(VoterProfile)
class VoterProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'national_id', 'county', 'has_voted']
    list_filter = ['county', 'has_voted']
    search_fields = ['user__username', 'national_id']
    readonly_fields = ['national_id']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['order', 'text', 'is_text_answer']
    list_display_links = ['text']  # Fixed the admin.E124 error here
    list_editable = ['order', 'is_text_answer']
    list_filter = ['is_text_answer']
    ordering = ['order']

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['option_text', 'party', 'question', 'votes']
    list_editable = ['votes', 'party']
    list_filter = ['question', 'party']
    search_fields = ['option_text', 'party']

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['voter', 'question', 'choice', 'voted_at']
    list_filter = ['question', 'voted_at']
    
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    
    readonly_fields = ['voter', 'question', 'choice', 'text_answer', 'voted_at']