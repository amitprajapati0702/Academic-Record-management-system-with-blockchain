# Generated by Django 4.2.20 on 2025-04-07 13:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BlockchainInstance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('blockchain_data', models.TextField()),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.CharField(max_length=20, unique=True)),
                ('department', models.CharField(max_length=100)),
                ('enrollment_year', models.IntegerField()),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='student_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Faculty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('faculty_id', models.CharField(max_length=20, unique=True)),
                ('department', models.CharField(max_length=100)),
                ('position', models.CharField(max_length=100)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='faculty_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_code', models.CharField(max_length=20, unique=True)),
                ('title', models.CharField(max_length=200)),
                ('credits', models.IntegerField()),
                ('faculty', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='courses', to='blockchain_records.faculty')),
            ],
        ),
        migrations.CreateModel(
            name='AcademicRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_type', models.CharField(choices=[('GRADE', 'Course Grade'), ('CERTIFICATE', 'Certificate'), ('DEGREE', 'Degree'), ('TRANSCRIPT', 'Transcript')], max_length=20)),
                ('grade', models.CharField(blank=True, max_length=5, null=True)),
                ('description', models.TextField(blank=True)),
                ('issue_date', models.DateTimeField(auto_now_add=True)),
                ('block_hash', models.CharField(blank=True, max_length=64, null=True)),
                ('course', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='blockchain_records.course')),
                ('issuer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='issued_records', to='blockchain_records.faculty')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='academic_records', to='blockchain_records.student')),
            ],
        ),
    ]
