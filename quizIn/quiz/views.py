from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from .serializers import EventSerializer, UserEventSerializer, LeaderboardSerializer, SubjectSerializer, SectionSerializer, CategorySerializer, QuestionSerializer, QuestionOptionSerializer
from .models import Event, UserEvent, Leaderboard, Subject, Section, Category, Question, QuestionOption, UserStatus, Status
from rest_framework.exceptions import NotFound
from django.utils import timezone
from datetime import datetime
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.views.generic.detail import DetailView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from django.utils.dateparse import parse_date
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from django.core.exceptions import PermissionDenied
import openpyxl
import pandas as pd  
User = get_user_model()
import random
from django.core.cache import cache
from random import sample




from django.conf import settings

class LeaderboardListView(APIView):
    """
    API View to retrieve leaderboard with a configurable limit from settings.
    """
    def get(self, request):
        remuneration_type = request.data.get('remuneration_type')
        test_type = request.data.get('test_type')

        limit = getattr(settings, 'LEADERBOARD_LIMIT', 10)  # Default to 10 if not set in settings.py

        leaderboard_entries = Leaderboard.objects.all()

        # Filter by remuneration type
        if remuneration_type == "1":
            leaderboard_entries = leaderboard_entries.filter(category__isnull=False)
        elif remuneration_type == "2":
            leaderboard_entries = leaderboard_entries.filter(event__isnull=False)
        else:
            return Response({"error": "Invalid 'remuneration_type'."}, status=status.HTTP_400_BAD_REQUEST)

        # Map test_type to status names
        test_type_mapping = {
            "1": "preliminary",
            "2": "intermediary",
            "3": "reward",
        }
        status_name = test_type_mapping.get(str(test_type))
        if status_name:
            status_obj = get_object_or_404(Status, status=status_name)
            leaderboard_entries = leaderboard_entries.filter(status=status_obj)
        elif test_type is not None:
            return Response({"error": "Invalid 'test_type'."}, status=status.HTTP_400_BAD_REQUEST)

        # Apply limit and serialize
        leaderboard_data = [
            {
                "msisdn": entry.msisdn,
                "score": entry.score,
                "status": entry.status.status if entry.status else None,
                "remuneration_type": remuneration_type,
                "test_type": status_name,
                "category": entry.category.name if entry.category else None,
                "event": entry.event.name if entry.event else None,
            } for entry in leaderboard_entries.order_by('-score')[:limit]
        ]

        return Response({"leaderboard": leaderboard_data})

        

class EventDetailView(generics.RetrieveAPIView):
    queryset = Event.objects.all()  # Update queryset to use Event
    serializer_class = EventSerializer  # Use the serializer for Event

    def get_object(self):
        exam_type_id = self.request.data.get('id')  # Change from exam_id to exam_type_id
        
        if not exam_type_id:
            raise NotFound("Exam Type ID is required.")  # Use NotFound from DRF for consistency
        
        try:
            return Event.objects.get(id=exam_type_id)  # Fetch based on the new ID field
        except Event.DoesNotExist:
            raise NotFound("Exam Type does not exist.")  # Consistent error handling

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context




    

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def perform_create(self, serializer):
        # Check if the user is a teacher or admin
        if self.request.user.role not in ['teacher', 'admin']:
            raise PermissionDenied('You do not have permission to create an exam.')

        # Create the event
        event = serializer.save()

        # Handle file upload for questions
        if 'file' not in self.request.FILES:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        file = self.request.FILES['file']

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
                    difficulty_level = row['Difficulty']

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
                        difficulty=difficulty_level
                    )

                    # Create Question Options
                    for i, option_text in enumerate(options, start=1):
                        option_text = str(option_text).strip().lower()

                        # Determine the label for the option
                        option_label = f"option {i}".lower()

                        # Check if the current option is the correct answer
                        is_correct = (option_label == correct_answer.strip().lower()) or (option_text == correct_answer.strip().lower())

                        # Create the QuestionOption object
                        QuestionOption.objects.create(
                            question=question,
                            text=option_text,
                            is_correct=is_correct
                        )

                    # After creating the question, associate it with the event
                    question.event = event
                    question.save()

            # After processing all questions, create the exam for the event
            total_marks = sum([q['marks'] for q in df.to_dict(orient='records')])  # Calculate total marks
            total_questions = len(df)

            exam = Exam.objects.create(
                event=event,
                title=event.name,
                total_questions=total_questions,
                total_marks=total_marks
            )

            return Response({"exam_id": exam.id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        
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
            exam_type = Event.objects.get(id=exam_type_id)
        except Event.DoesNotExist:
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


    # @action(detail=False, methods=['post'], url_path='questions')
    # def get_questions(self, request):
    #     exam_type_id = request.data.get('event_id', None)
    #     msisdn = request.data.get('msisdn')
    #     subject_id = request.data.get('subject_id')
    #     section_id = request.data.get('section_id')
    #     category_id = request.data.get('category_id')

    #     if not msisdn:
    #         return Response({"error": "MSISDN is required."}, status=status.HTTP_400_BAD_REQUEST)

    #     # Define difficulty levels for each status using integer choices
    #     difficulty_mapping = {
    #         'preliminary': [1, 2],          # Very Easy, Easy
    #         'intermediate': [3, 4],         # Medium, Hard
    #         'rewards': [5, 6]               # Very Hard, Expert
    #     }

    #     # Get or create user status
    #     user_status, created = UserStatus.objects.get_or_create(
    #         msisdn=msisdn,
    #         defaults={
    #             'current_status': Status.objects.first(),  # Set an initial status
    #             'points': 0,
    #             'total_questions_attempted': 0,
    #         }
    #     )

    #     # Get difficulty levels based on user status
    #     current_status_name = user_status.current_status.status
    #     allowed_difficulties = difficulty_mapping.get(current_status_name.lower(), [])

    #     if exam_type_id:
    #         # Fetch questions directly associated with the event, ignoring difficulty levels
    #         event = get_object_or_404(Event, id=exam_type_id)
    #         questions = Question.objects.filter(
    #             category__section__subject_id=subject_id,
    #             category__section_id=section_id,
    #             category_id=category_id
    #         )
    #     else:
    #         # No event specified; use UserStatus to determine allowed difficulties and question limit
    #         questions_limit = user_status.current_status.questions_limit
    #         print(type(questions_limit))
    #         # questions = Question.objects.filter(
    #         #     difficulty__in=allowed_difficulties,
    #         #     category__section__subject_id=subject_id,
    #         #     category__section_id=section_id,
    #         #     category_id=category_id
    #         # )[:questions_limit]
            
    #         question_ids = list(
    #             Question.objects.filter(
    #                 difficulty__in=allowed_difficulties,
    #                 category__section__subject_id=subject_id,
    #                 category__section_id=section_id,
    #                 category_id=category_id
    #             ).values_list('id', flat=True)
    #         )
    #         questions_to_select = min(len(question_ids), questions_limit)

    #         # Randomly select question IDs based on the limit
    #         selected_question_ids = sample(question_ids, questions_to_select)

    #         # Retrieve the Question objects using the randomly selected IDs
    #         questions = Question.objects.filter(id__in=selected_question_ids)

    #     # Get previously answered questions from cache
    #     # redis_key = f"user_{msisdn}_answered_questions_{exam_type_id or 'general'}"
    #     # answered_question_ids = cache.get(redis_key, [])
    #     # available_questions = questions.exclude(id__in=answered_question_ids)

    #     # if not available_questions.exists():
    #     #     return Response({"error": "No new questions available at the moment."}, status=status.HTTP_404_NOT_FOUND)

    #     # # Randomly select questions if needed
    #     # question_ids = [question.id for question in available_questions]
    #     # random_questions = random.sample(question_ids, min(len(question_ids), user_status.current_status.questions_limit))

    #     # # Cache answered question IDs
    #     # answered_question_ids.extend(random_questions)
    #     # cache_duration = (event.lock_duration_days * 86400) if exam_type_id else 86400
    #     # cache.set(redis_key, answered_question_ids, timeout=cache_duration)

    #     # Serialize and return questions
    #     # question_serializer = QuestionSerializer(Question.objects.filter(id__in=random_questions), many=True)
    #     print(questions)
    #     question_serializer = QuestionSerializer(questions, many=True)
    #     return Response({"questions": question_serializer.data}, status=status.HTTP_200_OK)


    @action(detail=False, methods=['post'], url_path='questions')
    def get_questions(self, request):
        exam_type_id = request.data.get('event_id', None)
        msisdn = request.data.get('msisdn')
        
        # Ensure these fields are integers, default to None if not valid
        try:
            subject_id = int(request.data.get('subject_id'))
        except (ValueError, TypeError):
            subject_id = None

        try:
            section_id = int(request.data.get('section_id'))
        except (ValueError, TypeError):
            section_id = None

        try:
            category_id = int(request.data.get('category_id'))
        except (ValueError, TypeError):
            category_id = None

        if not msisdn:
            return Response({"error": "MSISDN is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Define difficulty levels for each status using integer choices
        difficulty_mapping = {
            'preliminary': [1, 2],          # Very Easy, Easy
            'intermediate': [3, 4],         # Medium, Hard
            'rewards': [5, 6]               # Very Hard, Expert
        }

        # Get or create user status
        user_status, created = UserStatus.objects.get_or_create(
            msisdn=msisdn,
            defaults={
                'current_status': Status.objects.first(),  # Set an initial status
                'points': 0,
                'total_questions_attempted': 0,
            }
        )

        # Get difficulty levels based on user status
        current_status_name = user_status.current_status.status
        allowed_difficulties = difficulty_mapping.get(current_status_name.lower(), [])

        if exam_type_id:
            # Fetch questions directly associated with the event, ignoring difficulty levels
            event = get_object_or_404(Event, id=exam_type_id)
            questions = Question.objects.filter(
                category__section__subject_id=subject_id,
                category__section_id=section_id,
                category_id=category_id
            )
        else:
            # No event specified; use UserStatus to determine allowed difficulties and question limit
            questions_limit = user_status.current_status.questions_limit

            # Get the IDs of questions based on allowed difficulties and category filters
            question_ids = list(
                Question.objects.filter(
                    difficulty__in=allowed_difficulties,
                    category__section__subject_id=subject_id,
                    category__section_id=section_id,
                    category_id=category_id
                ).values_list('id', flat=True)
            )

            # Ensure we select only the number of questions based on the question limit
            questions_to_select = min(len(question_ids), questions_limit)

            # Randomly select question IDs based on the limit
            selected_question_ids = sample(question_ids, questions_to_select)

            # Retrieve the Question objects using the randomly selected IDs
            questions = Question.objects.filter(id__in=selected_question_ids)

        # Serialize and return questions
        question_serializer = QuestionSerializer(questions, many=True)
        return Response({"questions": question_serializer.data}, status=status.HTTP_200_OK)



    @action(detail=False, methods=['post'], url_path='submit')
    def submit_exam(self, request):
        msisdn = request.data.get('msisdn')
        event_id = request.data.get('event_id')
        category_id = request.data.get('category_id')
        section_id = request.data.get('section_id')
        subject_id = request.data.get('subject_id')
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')

        # Validate inputs (as before)
        if not msisdn:
            return Response({"error": "MSISDN is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not (event_id or (category_id and section_id and subject_id)):
            return Response({"error": "Either event_id or category_id, section_id, and subject_id must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate start_time and end_time
        try:
            start_time = timezone.make_aware(datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S'))
            end_time = timezone.make_aware(datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S'))
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DDTHH:MM:SS."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the event or category (as before)
        if event_id:
            try:
                event = Event.objects.get(id=event_id)
            except Event.DoesNotExist:
                return Response({"error": "Event does not exist."}, status=status.HTTP_404_NOT_FOUND)
        else:
            subject = get_object_or_404(Subject, id=subject_id)
            section = get_object_or_404(Section, id=section_id, subject=subject)
            category = get_object_or_404(Category, id=category_id, section=section)
            questions = Question.objects.filter(category=category)

            if not questions.exists():
                return Response({"error": "No questions found for the provided category."}, status=status.HTTP_404_NOT_FOUND)

        # Calculate the total score
        total_score = 0
        for question in questions:
            answer = request.data.get(str(question.id))
            if answer:
                correct_options = question.options.filter(is_correct=True)
                selected_options = QuestionOption.objects.filter(id__in=answer)
                if all(option in correct_options for option in selected_options):
                    total_score += question.marks

        # Update or create a leaderboard entry
        try:
            status = UserStatus.objects.get(msisdn=msisdn).status  # Assuming status is part of UserStatus
            if event_id:
                Leaderboard.update_best_score(msisdn=msisdn, score=total_score, event=event, status=status)
            else:
                Leaderboard.update_best_score(msisdn=msisdn, score=total_score, category=category, status=status)
        except UserStatus.DoesNotExist:
            return Response({"error": "User status not found."}, status=status.HTTP_404_NOT_FOUND)

        # Return response
        return Response({
            "message": "Exam submitted successfully.",
            "score": total_score,
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
        # if request.user.role != 'admin':  # Assuming 'admin' is the role value for admin users
        #     raise PermissionDenied({"error": "You do not have permission to upload questions."})

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
                    correct_answer = row['Answer'].strip().lower().replace(" ", "")
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
                    # Ensure option_text is treated as a string
                        option_text = str(option_text).lower()
                        
                        # Determine the label for the option
                        # option_label = f"option {i}".lower()
                        
                        # Check if the current option is the correct answer
                        is_correct = (f"option{i}".strip().lower() == correct_answer)
                        
                        # Create the QuestionOption object
                        QuestionOption.objects.create(
                            question=question,
                            text=option_text,
                            is_correct=is_correct
                        )


            return Response({"message": "All questions uploaded successfully."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    