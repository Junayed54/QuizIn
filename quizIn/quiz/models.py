from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class ExamType(models.Model):
    TYPE_CHOICES = [
        ('preliminary', 'Preliminary Test'),
        ('intermediary', 'Intermediary Test'),
        ('reward', 'Reward Test'),
    ]
    name = models.CharField(max_length=50, choices=TYPE_CHOICES, unique=True)
    total_questions = models.IntegerField()  # Number of questions for this exam type
    marks_per_question = models.IntegerField(null=True, blank=True)  # Marks per question (e.g., 1 for Preliminary, 2 for Intermediary)
    points_multiplier = models.FloatField(default=1.0)  # Multiplier for points (e.g., 1 for Preliminary, 2 for Intermediary)

    def __str__(self):
        return f"{self.name} (Questions: {self.total_questions}, Points Multiplier: {self.points_multiplier})"


class UserExam(models.Model):
    """Tracks each user's attempt at a specific exam type."""
    msisdn = models.CharField(max_length=15, default=None)
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE, related_name='user_exams')
    score = models.IntegerField(default=0)  # Score for this attempt
    points_earned = models.IntegerField(default=0)  # Points earned for this attempt
    is_completed = models.BooleanField(default=False)  # Whether the user completed the exam
    timestamp = models.DateTimeField(auto_now=True)  # When the exam was taken

    # class Meta:
    #     unique_together = ('msisdn', 'exam_type')  # Each user can take each exam type once

    def __str__(self):
        return f"{self.msisdn} - {self.exam_type.name} - Score: {self.score}"

    def calculate_points(self):
        """Calculate points based on score and exam type's points multiplier."""
        self.points_earned = int(self.score * self.exam_type.points_multiplier)
        self.save()

        # Update user's total points in the PointsTable
        PointsTable.update_user_points(self.msisdn, self.points_earned)


class PointsTable(models.Model):
    """Keeps track of total points for each user."""
    msisdn = models.CharField(max_length=15) 
    total_points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.msisdn} - Total Points: {self.total_points}"

    @staticmethod
    def update_user_points(msisdn, points_earned):
        """Update total points for the user."""
        points_entry, created = PointsTable.objects.get_or_create(msisdn=msisdn)
        points_entry.total_points += points_earned
        points_entry.save()


class Leaderboard(models.Model):
    """Leaderboard based on total points."""
    msisdn = models.CharField(max_length=15)
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE, related_name='leaderboards')
    score = models.IntegerField(default=0)

    class Meta:
        ordering = ['-score']  # Order by score descending

    def __str__(self):
        return f'{self.msisdn} - {self.score}'

    @staticmethod
    def update_best_score(msisdn, exam_type, score):
        print("score:", score)
        """Update the leaderboard with the user's best score."""
        leaderboard_entry, created = Leaderboard.objects.get_or_create(msisdn=msisdn, exam_type=exam_type)
        
        if leaderboard_entry.score < score:
            leaderboard_entry.score = score
            leaderboard_entry.save()



    
class Subject(models.Model):
    """Represents a subject like English, General Knowledge, etc."""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Section(models.Model):
    """Represents a section within a subject, e.g., Literature, Grammar."""
    name = models.CharField(max_length=255)
    subject = models.ForeignKey(Subject, related_name='sections', on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('name', 'subject')  # Ensure section names are unique within a subject.

    def __str__(self):
        return f"{self.name} - {self.subject.name}"


class Category(models.Model):
    """Represents a category within a section, e.g., Poetry, Prose."""
    name = models.CharField(max_length=255)
    section = models.ForeignKey(Section, related_name='categories', on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('name', 'section')  # Ensure categories are unique within a section.

    def __str__(self):
        return f"{self.name} - {self.section.name}"



class Question(models.Model):
    DIFFICULTY_LEVEL_CHOICES = [
        (1, 'Very Easy'),
        (2, 'Easy'),
        (3, 'Medium'),
        (4, 'Hard'),
        (5, 'Very Hard'),
        (6, 'Expert'),
    ]
    
    text = models.CharField(max_length=255, unique=True)
    marks = models.IntegerField()
    category = models.ForeignKey(Category, related_name='questions', on_delete=models.CASCADE)
    difficulty = models.IntegerField(choices=DIFFICULTY_LEVEL_CHOICES, default=3)
    def get_options(self):
        return self.options.all()

    def __str__(self):
        return f"{self.text}"

class QuestionOption(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

