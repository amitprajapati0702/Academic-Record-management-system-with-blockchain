from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from .models import Student, Faculty, Course, AcademicRecord, BlockchainInstance
from .blockchain import Block, Blockchain
from .blockchain_service import BlockchainService
import json
import time


class BlockchainTests(TestCase):
    """Tests for the blockchain implementation"""

    def test_block_creation(self):
        """Test creating a block"""
        # Create a block
        block = Block(1, time.time(), {"test": "data"}, "0")

        # Check block properties
        self.assertEqual(block.index, 1)
        self.assertEqual(block.data, {"test": "data"})
        self.assertEqual(block.previous_hash, "0")
        self.assertIsNotNone(block.hash)

    def test_blockchain_creation(self):
        """Test creating a blockchain"""
        # Create a blockchain
        blockchain = Blockchain()

        # Check blockchain properties
        self.assertEqual(len(blockchain.chain), 1)  # Genesis block
        self.assertEqual(blockchain.chain[0].index, 0)
        self.assertEqual(blockchain.chain[0].previous_hash, "0")

    def test_adding_block(self):
        """Test adding a block to the blockchain"""
        # Create a blockchain
        blockchain = Blockchain()
        initial_length = len(blockchain.chain)

        # Add a block
        blockchain.add_block({"test": "data"})

        # Check blockchain properties
        self.assertEqual(len(blockchain.chain), initial_length + 1)
        self.assertEqual(blockchain.chain[-1].data, {"test": "data"})
        self.assertEqual(blockchain.chain[-1].previous_hash, blockchain.chain[-2].hash)

    def test_blockchain_validation(self):
        """Test blockchain validation"""
        # Create a blockchain
        blockchain = Blockchain()

        # Add some blocks
        blockchain.add_block({"test": "data1"})
        blockchain.add_block({"test": "data2"})

        # Validate the blockchain
        self.assertTrue(blockchain.is_chain_valid())

        # Tamper with the blockchain
        blockchain.chain[1].data = {"test": "tampered"}

        # Validate the blockchain again
        self.assertFalse(blockchain.is_chain_valid())

    def test_blockchain_serialization(self):
        """Test blockchain serialization and deserialization"""
        # Create a blockchain
        blockchain = Blockchain()
        blockchain.add_block({"test": "data"})

        # Serialize the blockchain
        blockchain_dict = blockchain.to_dict()

        # Deserialize the blockchain
        new_blockchain = Blockchain.from_dict(blockchain_dict)

        # Check if the blockchains are the same
        self.assertEqual(len(new_blockchain.chain), len(blockchain.chain))
        self.assertEqual(new_blockchain.chain[0].hash, blockchain.chain[0].hash)
        self.assertEqual(new_blockchain.chain[1].hash, blockchain.chain[1].hash)
        self.assertEqual(new_blockchain.chain[1].data, blockchain.chain[1].data)


class ModelTests(TestCase):
    """Tests for the Django models"""

    def setUp(self):
        """Set up test data"""
        # Create user groups
        self.student_group = Group.objects.create(name='Students')
        self.faculty_group = Group.objects.create(name='Faculty')

        # Create users
        self.student_user = User.objects.create_user(
            username='student',
            password='password',
            email='student@example.com',
            first_name='Student',
            last_name='User'
        )
        self.student_user.groups.add(self.student_group)

        self.faculty_user = User.objects.create_user(
            username='faculty',
            password='password',
            email='faculty@example.com',
            first_name='Faculty',
            last_name='User'
        )
        self.faculty_user.groups.add(self.faculty_group)

        # Create student and faculty profiles
        self.student = Student.objects.create(
            user=self.student_user,
            student_id='S12345',
            department='Computer Science',
            enrollment_year=2023
        )

        self.faculty = Faculty.objects.create(
            user=self.faculty_user,
            faculty_id='F12345',
            department='Computer Science',
            position='Professor'
        )

        # Create a course
        self.course = Course.objects.create(
            course_code='CS101',
            title='Introduction to Computer Science',
            credits=3,
            faculty=self.faculty
        )

    def test_student_model(self):
        """Test the Student model"""
        self.assertEqual(str(self.student), f"Student User (S12345)")
        self.assertEqual(self.student.department, 'Computer Science')
        self.assertEqual(self.student.enrollment_year, 2023)

    def test_faculty_model(self):
        """Test the Faculty model"""
        self.assertEqual(str(self.faculty), f"Faculty User (Professor)")
        self.assertEqual(self.faculty.department, 'Computer Science')
        self.assertEqual(self.faculty.position, 'Professor')

    def test_course_model(self):
        """Test the Course model"""
        self.assertEqual(str(self.course), f"CS101: Introduction to Computer Science")
        self.assertEqual(self.course.credits, 3)
        self.assertEqual(self.course.faculty, self.faculty)

    def test_academic_record_model(self):
        """Test the AcademicRecord model"""
        # Create an academic record
        record = AcademicRecord.objects.create(
            student=self.student,
            record_type='GRADE',
            course=self.course,
            grade='A',
            description='Excellent performance',
            issuer=self.faculty
        )

        self.assertEqual(str(record), f"S12345 - CS101 - A")
        self.assertEqual(record.student, self.student)
        self.assertEqual(record.course, self.course)
        self.assertEqual(record.grade, 'A')

        # Test blockchain data conversion
        blockchain_data = record.to_blockchain_data()
        self.assertEqual(blockchain_data['student_id'], 'S12345')
        self.assertEqual(blockchain_data['record_type'], 'GRADE')
        self.assertEqual(blockchain_data['course_code'], 'CS101')
        self.assertEqual(blockchain_data['grade'], 'A')


class ViewTests(TestCase):
    """Tests for the Django views"""

    def setUp(self):
        """Set up test data"""
        # Create a client
        self.client = Client()

        # Create user groups
        self.student_group = Group.objects.create(name='Students')
        self.faculty_group = Group.objects.create(name='Faculty')

        # Create users
        self.student_user = User.objects.create_user(
            username='student',
            password='password',
            email='student@example.com',
            first_name='Student',
            last_name='User'
        )
        self.student_user.groups.add(self.student_group)

        self.faculty_user = User.objects.create_user(
            username='faculty',
            password='password',
            email='faculty@example.com',
            first_name='Faculty',
            last_name='User'
        )
        self.faculty_user.groups.add(self.faculty_group)

        # Create student and faculty profiles
        self.student = Student.objects.create(
            user=self.student_user,
            student_id='S12345',
            department='Computer Science',
            enrollment_year=2023
        )

        self.faculty = Faculty.objects.create(
            user=self.faculty_user,
            faculty_id='F12345',
            department='Computer Science',
            position='Professor'
        )

        # Create a course
        self.course = Course.objects.create(
            course_code='CS101',
            title='Introduction to Computer Science',
            credits=3,
            faculty=self.faculty
        )

    def test_home_view(self):
        """Test the home view"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blockchain_records/home.html')

    def test_enrollment_view(self):
        """Test the enrollment view"""
        response = self.client.get(reverse('enrollment'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blockchain_records/enrollment.html')

        # Test enrollment submission
        enrollment_data = {
            'username': 'newstudent',
            'email': 'newstudent@example.com',
            'first_name': 'New',
            'last_name': 'Student',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
            'student_id': 'S67890',
            'department': 'Physics',
            'enrollment_year': 2023
        }

        response = self.client.post(reverse('enrollment'), enrollment_data, follow=True)
        self.assertRedirects(response, reverse('login'))

        # Check if the student was created
        self.assertTrue(User.objects.filter(username='newstudent').exists())
        self.assertTrue(Student.objects.filter(student_id='S67890').exists())

    def test_dashboard_view(self):
        """Test the dashboard view"""
        # Login as student
        self.client.login(username='student', password='password')

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blockchain_records/student_dashboard.html')

        # Logout and login as faculty
        self.client.logout()
        self.client.login(username='faculty', password='password')

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blockchain_records/faculty_dashboard.html')

    def test_add_record_view(self):
        """Test the add record view"""
        # Login as faculty
        self.client.login(username='faculty', password='password')

        response = self.client.get(reverse('add_record'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blockchain_records/add_record.html')

        # Test adding a record
        record_data = {
            'student': self.student.id,
            'record_type': 'GRADE',
            'course': self.course.id,
            'grade': 'A',
            'description': 'Excellent performance',
            'issuer': self.faculty.id
        }

        response = self.client.post(reverse('add_record'), record_data, follow=True)

        # Check if the record was created
        self.assertTrue(AcademicRecord.objects.filter(student=self.student, course=self.course).exists())

        # Check if the record was added to the blockchain
        record = AcademicRecord.objects.get(student=self.student, course=self.course)
        self.assertIsNotNone(record.block_hash)

    def test_verify_record_view(self):
        """Test the verify record view"""
        # Create a record and add it to the blockchain
        record = AcademicRecord.objects.create(
            student=self.student,
            record_type='GRADE',
            course=self.course,
            grade='A',
            description='Excellent performance',
            issuer=self.faculty
        )

        # Add the record to the blockchain
        BlockchainService.add_record_to_blockchain(record)

        # Test the verify record view
        response = self.client.get(reverse('verify_record'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blockchain_records/verify_record.html')

        # Test verifying a record
        verify_data = {
            'record_id': record.id
        }

        response = self.client.post(reverse('verify_record'), verify_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('verification_result' in response.context)
        self.assertTrue(response.context['verification_result']['verified'])
