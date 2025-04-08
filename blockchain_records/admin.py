from django.contrib import admin
from .models import Student, Faculty, Course, AcademicRecord, BlockchainInstance


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'get_full_name', 'department', 'enrollment_year')
    search_fields = ('student_id', 'user__first_name', 'user__last_name', 'department')

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('faculty_id', 'get_full_name', 'department', 'position')
    search_fields = ('faculty_id', 'user__first_name', 'user__last_name', 'department')

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'title', 'credits', 'faculty')
    search_fields = ('course_code', 'title')
    list_filter = ('credits',)


@admin.register(AcademicRecord)
class AcademicRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'record_type', 'course', 'grade', 'issue_date', 'issuer', 'block_hash')
    list_filter = ('record_type', 'issue_date')
    search_fields = ('student__student_id', 'course__course_code', 'block_hash')
    readonly_fields = ('block_hash',)


@admin.register(BlockchainInstance)
class BlockchainInstanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'last_updated')
    readonly_fields = ('blockchain_data', 'last_updated')
