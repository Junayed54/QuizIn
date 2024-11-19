from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LeaderboardListView,
    EventDetailView,
    EventViewSet,
    QuestionViewSet,
    QuestionOptionViewSet,
    upload_questions
)

# Create a router for the viewsets
router = DefaultRouter()
router.register(r'exams', EventViewSet)
router.register(r'questions', QuestionViewSet)
router.register(r'question-options', QuestionOptionViewSet)

urlpatterns = [
    path('leaderboard/', LeaderboardListView.as_view(), name='leaderboard-list'),
    path('exam-detail/', EventDetailView.as_view(), name='exam-detail'),  # Assuming the detail view is mapped to this endpoint
    path('upload-questions/', upload_questions.as_view(), name='upload-questions'),  # For uploading questions via file
    
    path('', include(router.urls)),  # Include all the router-generated URLs
]
