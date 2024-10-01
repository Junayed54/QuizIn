from rest_framework import serializers
from .models import ExamType, UserExam, PointsTable, Leaderboard, Subject, Section, Category, Question, QuestionOption

class ExamTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamType
        fields = '__all__'  # Include all fields

class UserExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserExam
        fields = '__all__'  # Include all fields

class PointsTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointsTable
        fields = '__all__'  # Include all fields

class LeaderboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leaderboard
        fields = '__all__'  # Include all fields

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'  # Include all fields

class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = '__all__'  # Include all fields

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'  # Include all fields

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'  # Include all fields

class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = '__all__'  # Include all fields
