from rest_framework import serializers
from .models import Subject, Section, Category, Question, QuestionOption, Status, UserStatus, Event, UserEvent, Leaderboard

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'description']


class SectionSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = Section
        fields = ['id', 'name', 'subject', 'description']


class CategorySerializer(serializers.ModelSerializer):
    section = SectionSerializer(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'section', 'description']


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ['id', 'text', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'marks', 'category', 'difficulty', 'options']


class StatusSerializer(serializers.ModelSerializer):
    question_difficulty_levels = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Status
        fields = [
            'id', 'status', 'questions_limit', 'question_difficulty_levels',
            'correct_answer_points', 'negative_points', 'points_required_to_advance',
            'created_at', 'updated_at'
        ]


class UserStatusSerializer(serializers.ModelSerializer):
    current_status = StatusSerializer(read_only=True)

    class Meta:
        model = UserStatus
        fields = [
            'id', 'msisdn', 'current_status', 'points',
            'total_questions_attempted', 'status_update_date', 'created_at', 'updated_at'
        ]


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'id', 'name', 'total_questions', 'marks_per_question', 'points_multiplier',
            'negative_marks', 'duration', 'start_time', 'end_time', 'created_at', 'updated_at'
        ]


class UserEventSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)

    class Meta:
        model = UserEvent
        fields = [
            'id', 'msisdn', 'event', 'score', 'points_earned', 'is_completed',
            'start_time', 'end_time'
        ]


class LeaderboardSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)

    class Meta:
        model = Leaderboard
        fields = ['id', 'msisdn', 'event', 'score']
