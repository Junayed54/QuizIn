from django.contrib import admin
from .models import (
    Subject, Section, Category, Question, QuestionOption, Status,
    UserStatus, Event, UserEvent, Leaderboard
)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'subject', 'description')
    search_fields = ('name', 'subject__name')
    list_filter = ('subject',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'section', 'description')
    search_fields = ('name', 'section__name')
    list_filter = ('section',)


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 1


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'marks', 'category', 'difficulty', 'event')
    search_fields = ('text',)
    list_filter = ('category', 'difficulty')
    inlines = [QuestionOptionInline]


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'text', 'is_correct')
    list_filter = ('is_correct',)
    search_fields = ('text', 'question__text')


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'questions_limit', 'correct_answer_points', 'negative_points', 'points_required_to_advance')
    list_filter = ('status',)
    search_fields = ('status',)


@admin.register(UserStatus)
class UserStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'msisdn', 'current_status', 'points', 'total_questions_attempted', 'status_update_date')
    search_fields = ('msisdn',)
    list_filter = ('current_status',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'total_questions', 'marks_per_question', 'points_multiplier', 'start_time', 'end_time')
    search_fields = ('name',)
    list_filter = ('start_time', 'end_time')


@admin.register(UserEvent)
class UserEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'msisdn', 'event', 'score', 'points_earned', 'is_completed', 'start_time', 'end_time')
    search_fields = ('msisdn', 'event__name')
    list_filter = ('is_completed', 'event')


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('id', 'msisdn', 'event', 'score')
    search_fields = ('msisdn', 'event__name')
    list_filter = ('event',)
