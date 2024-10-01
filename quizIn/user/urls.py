from django.urls import path, include
from .views import SignupView, CustomTokenObtainPairView, CustomUserViewSet
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='user')
urlpatterns = [
    path('', include(router.urls)),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    # path('profile/', CustomUserViewSet.as_view(), name='profile'),
]
