from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from .serializers import ExamTypeSerializer, UserExamSerializer, PointsTableSerializer, LeaderboardSerializer, SubjectSerializer, SectionSerializer, CategorySerializer, QuestionSerializer, QuestionOptionSerializer
from .models import ExamType, UserExam, PointsTable, Leaderboard, Subject, Section, Category, Question, QuestionOption
from rest_framework.exceptions import NotFound
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.views.generic.detail import DetailView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from django.utils.dateparse import parse_date
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
import openpyxl
import pandas as pd  
User = get_user_model()
import random




class LeaderboardListView(APIView):
    
    def get(self, request):
        exam_type_id = request.data.get('exam_id')  # Get exam_type_id from query parameters
        if not exam_type_id:
            return Response({"error": "Exam Type ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # You can add logic to validate the ExamType ID if necessary
        try:
            # Get top 10 scores for the specified ExamType
            leaderboards = Leaderboard.objects.filter(exam_type__id=exam_type_id).order_by('-score')[:10]
            serializer = LeaderboardSerializer(leaderboards, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Leaderboard.DoesNotExist:
            return Response({"error": "No leaderboard entries found for this Exam Type."}, status=status.HTTP_404_NOT_FOUND)


class ExamDetailView(generics.RetrieveAPIView):
    queryset = ExamType.objects.all()  # Update queryset to use ExamType
    serializer_class = ExamTypeSerializer  # Use the serializer for ExamType

    def get_object(self):
        exam_type_id = self.request.data.get('id')  # Change from exam_id to exam_type_id
        
        if not exam_type_id:
            raise NotFound("Exam Type ID is required.")  # Use NotFound from DRF for consistency
        
        try:
            return ExamType.objects.get(id=exam_type_id)  # Fetch based on the new ID field
        except ExamType.DoesNotExist:
            raise NotFound("Exam Type does not exist.")  # Consistent error handling

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context




    

class ExamViewSet(viewsets.ModelViewSet):
    queryset = ExamType.objects.all()
    serializer_class = ExamTypeSerializer

    def perform_create(self, serializer):
        # Check if the user is a teacher
        if self.request.user.role == 'teacher' or self.request.user.role == 'admin':
            None
        else:
            raise PermissionDenied('You do not have permission to create an exam.')

        # If the user is a teacher, save the exam with the user as the creator
        exam = serializer.save()
        return Response({'exam_id': exam.id}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='start')  # POST method to start exam
    def start_exam(self, request):
        msisdn = request.data.get('msisdn')  # Retrieve msisdn from the request
        exam_type_id = request.data.get('exam_id')  # Retrieve exam_type_id from the request
        subject_id = request.data.get('subject_id')  # New parameter for subject
        section_id = request.data.get('section_id')  # New parameter for section
        category_id = request.data.get('category_id')  # New parameter for category

        # Validate inputs
        if not msisdn:
            return Response({"error": "MSISDN (Mobile number) is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not exam_type_id:
            return Response({"error": "Exam Type ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not subject_id or not section_id or not category_id:
            return Response({"error": "Subject, Section, and Category IDs are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user exists by msisdn
        user, created = User.objects.get_or_create(msisdn=msisdn)

        try:
            # Check if the exam type exists
            exam_type = ExamType.objects.get(id=exam_type_id)
        except ExamType.DoesNotExist:
            raise Http404("Exam Type does not exist.")

        # Proceed to start the exam (you can add any logic needed here)
        return Response({
            'exam_type_id': exam_type.id,
            'title': exam_type.name,
            'total_questions': exam_type.total_questions,  # Assuming a related name for questions
            'msisdn': user.msisdn,
            'start_time': timezone.now(),  # Returning the current time as start time
            'message': "Exam started successfully.",
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='questions')  # POST method to retrieve questions
    def get_questions(self, request):
        exam_type_id = request.data.get('exam_id')
        msisdn = request.data.get('msisdn')
        subject_id = request.data.get('subject_id')  # New parameter for subject
        section_id = request.data.get('section_id')  # New parameter for section
        category_id = request.data.get('category_id')  # New parameter for category

        # Validate inputs
        if not exam_type_id:
            return Response({"error": "Exam Type ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not msisdn:
            return Response({"error": "MSISDN is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not subject_id or not section_id or not category_id:
            return Response({"error": "Subject, Section, and Category IDs are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if the exam type exists
            exam_type = ExamType.objects.get(id=exam_type_id)
            print(exam_type)
        except ExamType.DoesNotExist:
            raise Http404("Exam Type does not exist.")

        # Define difficulty levels based on exam type
        if exam_type.name.lower() == "preliminary":
            difficulty_range = [1, 2]  # Easy difficulties
        elif exam_type.name.lower() == "intermediary":
            difficulty_range = [3, 4]  # Medium difficulties
        elif exam_type.name.lower() == "reward":
            difficulty_range = [5, 6]  # Hard difficulties
        else:
            return Response({"error": "Invalid exam type."}, status=status.HTTP_400_BAD_REQUEST)

        print(section_id)
        # Fetch questions based on the difficulty level and additional parameters
        questions = Question.objects.filter(
            difficulty__in=difficulty_range,
            category__section__subject_id=subject_id,   # Filter through subject
            category__section_id=section_id,            # Filter through section
            category_id=category_id                     # Filter through category
        )

        # Shuffle the questions and pick a random selection based on total_questions
        total_questions_to_select = min(exam_type.total_questions, len(questions))
        random_questions = random.sample(list(questions), total_questions_to_select)

        # Serialize the questions
        serializer = QuestionSerializer(random_questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='submit')  # Use POST since answers and exam_type_id are in the request body
    def submit_exam(self, request):
        msisdn = request.data.get('msisdn')  # Retrieve msisdn from request body
        exam_type_id = request.data.get('exam_id')  # Retrieve exam_type_id from request body

        # Validate inputs
        if not msisdn:
            return Response({"error": "MSISDN is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not exam_type_id:
            return Response({"error": "Exam Type ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if the exam type exists
            exam_type = ExamType.objects.get(id=exam_type_id)
            print(exam_type)
        except ExamType.DoesNotExist:
            raise Http404("Exam Type does not exist.")

        answers = request.data.get('answers', [])  # Get answers from request body
        correct_answers = 0
        wrong_answers = 0

        # Calculate correct and wrong answers
        for answer in answers:
            question_id = answer.get('question_id')
            selected_option_id = answer.get('option')

            try:
                # Fetch the question based on ID and ensure it's linked to the correct exam type
                question = Question.objects.get(id=question_id)  # You may want to filter by exam_type if necessary
                selected_option = QuestionOption.objects.get(id=selected_option_id, question=question)

                if selected_option.is_correct:
                    correct_answers += 1
                else:
                    wrong_answers += 1

            except (Question.DoesNotExist, QuestionOption.DoesNotExist):
                return Response({'detail': 'Invalid question or option provided.'}, status=status.HTTP_400_BAD_REQUEST)
            

        point = correct_answers * int(exam_type.points_multiplier)
        
        user_exam, created = UserExam.objects.update_or_create(
            msisdn=msisdn,
            exam_type=exam_type,
            # points = correct_answers * exam_type.points_multiplier,
            defaults={
                'score': correct_answers,
                'points_earned': point,  # Points calculation based on exam type
                'is_completed': True,  # Mark as completed
            }
        )

        # Optionally call calculate_points if you need further updates
        user_exam.calculate_points()
        # Update the leaderboard with the best score
        Leaderboard.update_best_score(msisdn, exam_type, point)  # Pass msisdn and exam type

        return Response({
            'correct_answers': correct_answers,
            'wrong_answers': wrong_answers,
        }, status=status.HTTP_200_OK)
       
class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer


    def perform_create(self, serializer):
        exam = serializer.validated_data.get('exam')
        question = serializer.save(exam=exam)
        return Response({"question_id": question.id})

    @action(detail=True, methods=['post'])
    def add_option(self, request, pk=None):
        question = self.get_object()
        serializer = QuestionOptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(question=question)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class QuestionOptionViewSet(viewsets.ModelViewSet):
    queryset = QuestionOption.objects.all()
    serializer_class = QuestionOptionSerializer

    def perform_create(self, serializer):
        question = serializer.validated_data.get('question')  # Ensure exam is included
        serializer.save(question=question)

    



class upload_questions(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication] 


    def post(self, request, *args, **kwargs):
        # Check if the user is an admin
        if request.user.role != 'admin':  # Assuming 'admin' is the role value for admin users
            raise PermissionDenied({"error": "You do not have permission to upload questions."})

        if 'file' not in request.FILES:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        
        try:
            df = pd.read_excel(file)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        required_columns = [
            'Question', 
            'Option1', 
            'Option2', 
            'Option3', 
            'Option4', 
            'Answer', 
            'Options_num', 
            'Subject',  
            'Section',  
            'Category',  
            'Difficulty'  # New column for difficulty
        ]
        
        if not all(col in df.columns for col in required_columns):
            return Response({"error": f"Missing one of the required columns: {', '.join(required_columns)}"}, status=status.HTTP_400_BAD_REQUEST)

        question_count = 0

        try:
            with transaction.atomic():
                for _, row in df.iterrows():
                    question_text = row['Question']
                    options = [row['Option1'], row['Option2'], row['Option3'], row['Option4']]
                    correct_answer = row['Answer'].strip().lower()
                    subject_name = row['Subject']
                    section_name = row['Section']
                    category_name = row['Category']
                    difficulty_level = row['Difficulty']  # Get the difficulty level from the row

                    
                    if Question.objects.filter(text=question_text).exists():
                        return Response({"error": f"Question '{question_text}' already exists."}, status=status.HTTP_400_BAD_REQUEST)
                    
                    
                    # Validate difficulty level
                    if difficulty_level not in [1, 2, 3, 4, 5, 6]:
                        return Response({"error": f"Invalid difficulty level '{difficulty_level}' for question '{question_text}'. Must be between 1 and 6."}, status=status.HTTP_400_BAD_REQUEST)

                    # Get or create the Subject
                    subject, _ = Subject.objects.get_or_create(name=subject_name)

                    # Get or create the Section related to the Subject
                    section, _ = Section.objects.get_or_create(name=section_name, subject=subject)

                    # Get or create the Category related to the Section
                    category, _ = Category.objects.get_or_create(name=category_name, section=section)

                    question_count += 1

                    # Create the Question
                    question = Question.objects.create(
                        text=question_text,
                        marks=1,  # Assuming each question carries 1 mark
                        category=category,
                        difficulty=difficulty_level  # Set the difficulty level
                    )

                    # Create Question Options
                    for i, option_text in enumerate(options, start=1):
                        option_label = f"option {i}".strip().lower()
                        is_correct = (option_label == correct_answer)
                        QuestionOption.objects.create(
                            question=question,
                            text=option_text,
                            is_correct=is_correct
                        )

            return Response({"message": "All questions created successfully."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)