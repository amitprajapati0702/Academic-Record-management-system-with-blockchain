from django.db import models
from django.contrib.auth.models import User
import json


class Student(models.Model):
    """Model representing a student"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    enrollment_year = models.IntegerField()

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"


class Faculty(models.Model):
    """Model representing a faculty member"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='faculty_profile')
    faculty_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.position})"


class Course(models.Model):
    """Model representing an academic course"""
    course_code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    credits = models.IntegerField()
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, related_name='courses')

    def __str__(self):
        return f"{self.course_code}: {self.title}"


class AcademicRecord(models.Model):
    """Model representing an academic record (grade, certificate, etc.)"""
    RECORD_TYPES = (
        ('GRADE', 'Course Grade'),
        ('CERTIFICATE', 'Certificate'),
        ('DEGREE', 'Degree'),
        ('TRANSCRIPT', 'Transcript'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='academic_records')
    record_type = models.CharField(max_length=20, choices=RECORD_TYPES)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    grade = models.CharField(max_length=5, null=True, blank=True)
    description = models.TextField(blank=True)
    issue_date = models.DateTimeField(auto_now_add=True)
    issuer = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, related_name='issued_records')
    block_hash = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        if self.record_type == 'GRADE':
            return f"{self.student.student_id} - {self.course.course_code} - {self.grade}"
        return f"{self.student.student_id} - {self.record_type}"

    def to_blockchain_data(self):
        """Convert record to format suitable for blockchain storage"""
        data = {
            'record_id': self.id,
            'student_id': self.student.student_id,
            'record_type': self.record_type,
            'issue_date': self.issue_date.isoformat(),
            'issuer_id': self.issuer.faculty_id if self.issuer else None,
        }

        if self.course:
            data['course_code'] = self.course.course_code
            data['course_title'] = self.course.title
            data['credits'] = self.course.credits

        if self.grade:
            data['grade'] = self.grade

        if self.description:
            data['description'] = self.description

        return data


class BlockchainInstance(models.Model):
    """Model to store the serialized blockchain"""
    blockchain_data = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)

    def save_blockchain(self, blockchain):
        """Serialize and save the blockchain"""
        self.blockchain_data = json.dumps(blockchain.to_dict())
        self.save()

    def load_blockchain(self):
        """Deserialize and load the blockchain"""
        from .blockchain import Blockchain
        blockchain_dict = json.loads(self.blockchain_data)
        return Blockchain.from_dict(blockchain_dict)
