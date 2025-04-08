from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

from .models import Student, Faculty, Course, AcademicRecord, BlockchainInstance
from .forms import (
    UserRegistrationForm, StudentRegistrationForm, FacultyRegistrationForm,
    CourseForm, AcademicRecordForm, RecordVerificationForm, StudentSearchForm
)
from .blockchain_service import BlockchainService


def home(request):
    """Home page view"""
    # Get blockchain stats
    try:
        stats = BlockchainService.get_blockchain_stats()
    except Exception as e:
        print(f"Error getting blockchain stats: {e}")
        stats = {
            'total_blocks': 0,
            'is_valid': False,
            'difficulty': 0,
            'genesis_block_time': 0
        }

    context = {
        'stats': stats,
        'total_students': Student.objects.count(),
        'total_faculty': Faculty.objects.count(),
        'total_courses': Course.objects.count(),
        'total_records': AcademicRecord.objects.count(),
    }
    return render(request, 'blockchain_records/home.html', context)


def register(request):
    """User registration view"""
    if request.method == 'POST':
        # Create a new user with the built-in UserCreationForm
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        # Basic validation
        if not (username and email and password1 and password2 and first_name and last_name):
            messages.error(request, 'Please fill in all required fields')
            return redirect('register')

        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('register')

        # Create the user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )

            # Check if registering as student or faculty
            user_type = request.POST.get('user_type')

            if user_type == 'student':
                # Create student profile
                student_id = request.POST.get('student_id')
                department = request.POST.get('department')
                enrollment_year = request.POST.get('enrollment_year')

                if not (student_id and department and enrollment_year):
                    user.delete()  # Clean up if validation fails
                    messages.error(request, 'Please fill in all student fields')
                    return redirect('register')

                Student.objects.create(
                    user=user,
                    student_id=student_id,
                    department=department,
                    enrollment_year=enrollment_year
                )

                # Add user to Students group
                group, _ = Group.objects.get_or_create(name='Students')

            elif user_type == 'faculty':
                # Create faculty profile
                faculty_id = request.POST.get('faculty_id')
                department = request.POST.get('department')
                position = request.POST.get('position')

                if not (faculty_id and department and position):
                    user.delete()  # Clean up if validation fails
                    messages.error(request, 'Please fill in all faculty fields')
                    return redirect('register')

                Faculty.objects.create(
                    user=user,
                    faculty_id=faculty_id,
                    department=department,
                    position=position
                )

                # Add user to Faculty group
                group, _ = Group.objects.get_or_create(name='Faculty')

            else:
                user.delete()  # Clean up if validation fails
                messages.error(request, 'Invalid user type')
                return redirect('register')

            # Add user to the appropriate group
            user.groups.add(group)

            messages.success(request, f'Account created successfully. You can now log in.')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('register')

    # GET request - initialize forms
    user_form = UserRegistrationForm()
    student_form = StudentRegistrationForm()
    faculty_form = FacultyRegistrationForm()

    return render(request, 'blockchain_records/register.html', {
        'user_form': user_form,
        'student_form': student_form,
        'faculty_form': faculty_form
    })


@login_required
def dashboard(request):
    """User dashboard view"""
    user = request.user
    context = {}

    # Check if user is a student
    if hasattr(user, 'student_profile'):
        student = user.student_profile
        records = AcademicRecord.objects.filter(student=student)
        context['student'] = student
        context['records'] = records
        return render(request, 'blockchain_records/student_dashboard.html', context)

    # Check if user is a faculty member
    elif hasattr(user, 'faculty_profile'):
        faculty = user.faculty_profile
        courses = Course.objects.filter(faculty=faculty)
        issued_records = AcademicRecord.objects.filter(issuer=faculty)
        context['faculty'] = faculty
        context['courses'] = courses
        context['issued_records'] = issued_records
        return render(request, 'blockchain_records/faculty_dashboard.html', context)

    # If user is neither student nor faculty (e.g., admin)
    else:
        return render(request, 'blockchain_records/admin_dashboard.html', context)


@login_required
def add_record(request):
    """View for adding a new academic record"""
    # Only faculty members can add records
    if not hasattr(request.user, 'faculty_profile'):
        messages.error(request, 'Only faculty members can add academic records')
        return redirect('dashboard')

    if request.method == 'POST':
        form = AcademicRecordForm(request.POST, user=request.user)
        if form.is_valid():
            record = form.save()

            # Add the record to the blockchain
            block_hash = BlockchainService.add_record_to_blockchain(record)

            messages.success(request, f'Record added successfully and secured on the blockchain. Block hash: {block_hash[:10]}...')
            return redirect('record_detail', record_id=record.id)
    else:
        form = AcademicRecordForm(user=request.user)

    return render(request, 'blockchain_records/add_record.html', {'form': form})


@login_required
def record_detail(request, record_id):
    """View for displaying record details"""
    record = get_object_or_404(AcademicRecord, id=record_id)

    # Check if user has permission to view this record
    user = request.user
    if not (user.is_staff or
            (hasattr(user, 'student_profile') and record.student == user.student_profile) or
            (hasattr(user, 'faculty_profile') and record.issuer == user.faculty_profile)):
        messages.error(request, 'You do not have permission to view this record')
        return redirect('dashboard')

    # Verify the record on the blockchain
    verification = BlockchainService.verify_record(record)

    context = {
        'record': record,
        'verification': verification
    }
    return render(request, 'blockchain_records/record_detail.html', context)


def verify_record(request):
    """View for verifying academic records"""
    verification_result = None

    if request.method == 'POST':
        form = RecordVerificationForm(request.POST)
        if form.is_valid():
            record_id = form.cleaned_data['record_id']
            record = AcademicRecord.objects.get(id=record_id)
            verification_result = BlockchainService.verify_record(record)
            verification_result['record'] = record
    else:
        form = RecordVerificationForm()

    return render(request, 'blockchain_records/verify_record.html', {
        'form': form,
        'verification_result': verification_result
    })


@login_required
def blockchain_explorer(request):
    """View for exploring the blockchain"""
    blockchain = BlockchainService.get_blockchain()
    blocks = blockchain.chain

    return render(request, 'blockchain_records/blockchain_explorer.html', {
        'blocks': blocks,
        'stats': BlockchainService.get_blockchain_stats()
    })


@login_required
def student_records(request, student_id):
    """View for displaying all records of a specific student"""
    student = get_object_or_404(Student, student_id=student_id)

    # Check if user has permission to view these records
    user = request.user
    if not (user.is_staff or
            (hasattr(user, 'student_profile') and student == user.student_profile) or
            hasattr(user, 'faculty_profile')):
        messages.error(request, 'You do not have permission to view these records')
        return redirect('dashboard')

    records = AcademicRecord.objects.filter(student=student)

    return render(request, 'blockchain_records/student_records.html', {
        'student': student,
        'records': records
    })


@login_required
def search_students(request):
    """View for searching students"""
    # Only faculty and staff can search students
    if not (request.user.is_staff or hasattr(request.user, 'faculty_profile')):
        messages.error(request, 'You do not have permission to search students')
        return redirect('dashboard')

    students = []
    if request.method == 'POST':
        form = StudentSearchForm(request.POST)
        if form.is_valid():
            student_id = form.cleaned_data['student_id']
            name = form.cleaned_data['name']
            department = form.cleaned_data['department']

            query = Q()
            if student_id:
                query |= Q(student_id__icontains=student_id)
            if name:
                query |= Q(user__first_name__icontains=name) | Q(user__last_name__icontains=name)
            if department:
                query |= Q(department__icontains=department)

            students = Student.objects.filter(query)
    else:
        form = StudentSearchForm()

    return render(request, 'blockchain_records/search_students.html', {
        'form': form,
        'students': students
    })


def enrollment(request):
    """View for student enrollment"""
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        student_form = StudentRegistrationForm(request.POST)

        if user_form.is_valid() and student_form.is_valid():
            # Create user
            user = user_form.save()

            # Create student profile
            student = student_form.save(commit=False)
            student.user = user
            student.save()

            # Add user to Students group
            group, _ = Group.objects.get_or_create(name='Students')
            user.groups.add(group)

            messages.success(request, f'Enrollment successful! You can now log in.')
            return redirect('login')
    else:
        user_form = UserRegistrationForm()
        student_form = StudentRegistrationForm()

    return render(request, 'blockchain_records/enrollment.html', {
        'user_form': user_form,
        'student_form': student_form
    })


def test_form(request):
    """Test form view"""
    if request.method == 'POST':
        print("Test form POST request received")
        print(f"POST data: {request.POST}")
        messages.success(request, 'Form submitted successfully!')
        return redirect('test_form')

    return render(request, 'blockchain_records/test_form.html')


@login_required
def course_list(request):
    """View for listing all courses"""
    courses = Course.objects.all().order_by('course_code')

    return render(request, 'blockchain_records/course_list.html', {
        'courses': courses
    })


@login_required
def course_detail(request, course_id):
    """View for displaying course details"""
    course = get_object_or_404(Course, id=course_id)

    # Get students who have academic records for this course
    enrolled_students = Student.objects.filter(academic_records__course=course).distinct()

    return render(request, 'blockchain_records/course_detail.html', {
        'course': course,
        'enrolled_students': enrolled_students
    })


@login_required
def add_course(request):
    """View for adding a new course"""
    # Only faculty and staff can add courses
    if not (request.user.is_staff or hasattr(request.user, 'faculty_profile')):
        messages.error(request, 'Only faculty members and administrators can add courses')
        return redirect('course_list')

    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course {course.course_code} added successfully')
            return redirect('course_detail', course_id=course.id)
    else:
        # If user is faculty, pre-select them as the faculty for the course
        initial = {}
        if hasattr(request.user, 'faculty_profile'):
            initial['faculty'] = request.user.faculty_profile
        form = CourseForm(initial=initial)

    return render(request, 'blockchain_records/course_form.html', {
        'form': form
    })


@login_required
def edit_course(request, course_id):
    """View for editing a course"""
    course = get_object_or_404(Course, id=course_id)

    # Only the assigned faculty or staff can edit the course
    if not (request.user.is_staff or
            (hasattr(request.user, 'faculty_profile') and course.faculty == request.user.faculty_profile)):
        messages.error(request, 'You do not have permission to edit this course')
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Course {course.course_code} updated successfully')
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseForm(instance=course)

    return render(request, 'blockchain_records/course_form.html', {
        'form': form,
        'course': course
    })


def simple_register(request):
    """Simple registration view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        if not (username and email and password and first_name and last_name):
            messages.error(request, 'Please fill in all fields')
            return redirect('simple_register')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists. Please choose a different username.')
            return redirect('simple_register')

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists. Please use a different email.')
            return redirect('simple_register')

        try:
            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Create a student profile for the user
            student_id = f"S{User.objects.count():05d}"
            Student.objects.create(
                user=user,
                student_id=student_id,
                department="General",
                enrollment_year=2025
            )

            # Add user to Students group
            group, _ = Group.objects.get_or_create(name='Students')
            user.groups.add(group)

            messages.success(request, f'Account created successfully with Student ID: {student_id}. You can now log in.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('simple_register')

    return render(request, 'blockchain_records/simple_register.html')


@method_decorator(csrf_exempt, name='dispatch')
class BlockchainAPIView(View):
    """API view for blockchain operations"""

    def get(self, request, *args, **kwargs):
        """Get blockchain stats"""
        stats = BlockchainService.get_blockchain_stats()
        return JsonResponse(stats)

    def post(self, request, *args, **kwargs):
        """Verify a record through API"""
        try:
            record_id = request.POST.get('record_id')
            if not record_id:
                return JsonResponse({'error': 'Record ID is required'}, status=400)

            record = AcademicRecord.objects.get(id=record_id)
            verification = BlockchainService.verify_record(record)

            return JsonResponse(verification)
        except AcademicRecord.DoesNotExist:
            return JsonResponse({'error': 'Record not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
