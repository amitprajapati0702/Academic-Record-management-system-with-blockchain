from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Student, Faculty, Course, AcademicRecord


class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')


class StudentRegistrationForm(forms.ModelForm):
    """Form for student registration"""
    class Meta:
        model = Student
        fields = ('student_id', 'department', 'enrollment_year')


class FacultyRegistrationForm(forms.ModelForm):
    """Form for faculty registration"""
    class Meta:
        model = Faculty
        fields = ('faculty_id', 'department', 'position')


class CourseForm(forms.ModelForm):
    """Form for course creation/editing"""
    class Meta:
        model = Course
        fields = ('course_code', 'title', 'credits', 'faculty')


class AcademicRecordForm(forms.ModelForm):
    """Form for academic record creation"""
    class Meta:
        model = AcademicRecord
        fields = ('student', 'record_type', 'course', 'grade', 'description', 'issuer')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If the user is a faculty member, pre-select them as the issuer
        if user and hasattr(user, 'faculty_profile'):
            self.fields['issuer'].initial = user.faculty_profile
            self.fields['issuer'].widget = forms.HiddenInput()


class RecordVerificationForm(forms.Form):
    """Form for verifying academic records"""
    record_id = forms.IntegerField(label="Record ID")
    
    def clean_record_id(self):
        record_id = self.cleaned_data['record_id']
        try:
            record = AcademicRecord.objects.get(id=record_id)
            return record_id
        except AcademicRecord.DoesNotExist:
            raise forms.ValidationError("Record with this ID does not exist")


class StudentSearchForm(forms.Form):
    """Form for searching students"""
    student_id = forms.CharField(required=False, label="Student ID")
    name = forms.CharField(required=False, label="Name")
    department = forms.CharField(required=False, label="Department")
