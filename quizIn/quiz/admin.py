from django.contrib import admin
from .models import ExamType, UserExam, PointsTable, Leaderboard, Subject, Section, Category, Question, QuestionOption

@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'total_questions', 'marks_per_question', 'points_multiplier')
    search_fields = ('name',)

@admin.register(UserExam)
class UserExamAdmin(admin.ModelAdmin):
    list_display = ('id', 'msisdn', 'exam_type', 'score', 'points_earned', 'is_completed', 'timestamp')
    list_filter = ('exam_type', 'is_completed')
    search_fields = ('msisdn',)

@admin.register(PointsTable)
class PointsTableAdmin(admin.ModelAdmin):
    list_display = ('id', 'msisdn', 'total_points')
    search_fields = ('msisdn',)

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('msisdn', 'exam_type', 'score')
    list_filter = ('exam_type',)
    search_fields = ('msisdn',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    search_fields = ('name',)

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'subject')
    list_filter = ('subject',)
    search_fields = ('name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'section')
    list_filter = ('section',)
    search_fields = ('name',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'marks', 'category', 'difficulty')
    list_filter = ('category', 'difficulty')
    search_fields = ('text',)

@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'text', 'is_correct')
    list_filter = ('question', 'is_correct')
    search_fields = ('text',)
