from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Event(models.Model):
    name = models.CharField(max_length=350, unique=True)
    total_questions = models.IntegerField()
    marks_per_question = models.IntegerField(null=True, blank=True)
    points_multiplier = models.FloatField(null=True, blank=True)
    negative_marks = models.FloatField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (Questions: {self.total_questions}, Points Multiplier: {self.points_multiplier})"


class UserEvent(models.Model):
    """Tracks each user's attempt at a specific event type."""
    msisdn = models.CharField(max_length=15, default=None)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='user_exams')
    score = models.IntegerField(default=0)
    points_earned = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.msisdn} - {self.event.name} - Score: {self.score}"

    def calculate_points(self):
        """Calculate points based on score and event's points multiplier."""
        self.points_earned = int(self.score * self.event.points_multiplier)
        self.save()
        PointsTable.update_user_points(self.msisdn, self.points_earned)


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
        unique_together = ('name', 'subject')  # Ensures section names are unique within a subject.

    def __str__(self):
        return f"{self.name} - {self.subject.name}"


class Category(models.Model):
    """Represents a category within a section, e.g., Poetry, Prose."""
    name = models.CharField(max_length=255)
    section = models.ForeignKey(Section, related_name='categories', on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('name', 'section')  # Ensures categories are unique within a section.

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
    event = models.ForeignKey(Event, related_name='questions', on_delete=models.SET_NULL, null=True, blank=True)
    marks = models.IntegerField()
    category = models.ForeignKey(Category, related_name='questions', on_delete=models.CASCADE)
    difficulty = models.IntegerField(choices=DIFFICULTY_LEVEL_CHOICES, default=3)

    def get_options(self):
        return self.options.all()

    def __str__(self):
        return self.text


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


STAGE_CHOICES = [
    ('preliminary', 'Preliminary'),
    ('intermediary', 'Intermediary'),
    ('reward', 'Reward'),
]

class Status(models.Model):
    """Defines the status levels for users, including points, question limits, and difficulty ranges."""
    status = models.CharField(max_length=15, choices=STAGE_CHOICES, unique=True, help_text="Stage type")    
    questions_limit = models.IntegerField(help_text="Number of questions a user will receive at this status level")
    # question_difficulty_levels = models.ManyToManyField(
    #     'Question', 
    #     limit_choices_to={'difficulty__in': dict(Question.DIFFICULTY_LEVEL_CHOICES).keys()},
    #     related_name="statuses",
    #     help_text="Allowed difficulty levels for this status"
    # )
    correct_answer_points = models.IntegerField(help_text="Points awarded for each correct answer")
    negative_points = models.IntegerField(default=0, help_text="Points deducted for each incorrect answer")
    points_required_to_advance = models.IntegerField(help_text="Points required to move to the next status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.status} - Questions Limit: {self.questions_limit}"


class UserStatus(models.Model):
    """Tracks the user's progression through the stages, points, and status."""
    msisdn = models.CharField(max_length=15, unique=True)
    current_status = models.ForeignKey(Status, on_delete=models.CASCADE, help_text="Current status of the user")
    points = models.IntegerField(default=0, help_text="Total points earned by the user")
    total_questions_attempted = models.IntegerField(default=0, help_text="Total questions the user has attempted")
    status_update_date = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.msisdn} - {self.current_status.status.capitalize()} - Points: {self.points}"

    def add_points(self, is_correct):
        """Updates points based on answer correctness and applies negative or positive scoring."""
        if is_correct:
            self.points += self.current_status.correct_answer_points
        else:
            self.points -= self.current_status.negative_points

        self.total_questions_attempted += 1
        self.save()
        self.check_for_status_update()

    def check_for_status_update(self):
        """Checks if the user has enough points to move to the next stage and updates the status."""
        if self.points >= self.current_status.points_required_to_advance:
            next_status = Status.objects.filter(points_required_to_advance__gt=self.current_status.points_required_to_advance).order_by('points_required_to_advance').first()
            if next_status:
                self.current_status = next_status
                self.save()




class Leaderboard(models.Model):
    """Leaderboard based on total points."""
    msisdn = models.CharField(max_length=15)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='leaderboards', null=True, blank=True, help_text="Associated event.")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='leaderboards', null=True, blank=True, help_text="Associated category.")
    score = models.IntegerField(default=0)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True, blank=True, related_name='leaderboards', help_text="User's current status.")

    class Meta: ordering = ['-score']

    def __str__(self): return f'{self.msisdn} - {self.score}'

    @staticmethod
    def update_best_score(msisdn, score, category=None, event=None, status=None):
        if not category and not event: raise ValueError("Either 'category' or 'event' must be specified.")
        leaderboard_entry, created = Leaderboard.objects.get_or_create(
            msisdn=msisdn, category=category if category else None, event=event if event else None, status=status, defaults={'score': score}
        )
        if leaderboard_entry.score < score: leaderboard_entry.score = score; leaderboard_entry.save()
