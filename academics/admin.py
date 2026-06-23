from django.contrib import admin

from .models import Attendance, FeePayment, GradeResult, SchoolClass, StudentProfile, Subject, TeacherProfile


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ("name", "section")
    search_fields = ("name", "section")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "school_class")
    list_filter = ("school_class",)
    search_fields = ("code", "name")


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("admission_no", "user", "school_class", "guardian_phone", "active")
    list_filter = ("school_class", "active")
    search_fields = ("admission_no", "user__first_name", "user__last_name", "guardian_name")


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "user", "phone")
    filter_horizontal = ("subjects",)
    search_fields = ("employee_id", "user__first_name", "user__last_name")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "status", "marked_by")
    list_filter = ("status", "date")
    search_fields = ("student__admission_no", "student__user__first_name", "student__user__last_name")


@admin.register(GradeResult)
class GradeResultAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "term", "score", "letter_grade")
    list_filter = ("term", "subject")
    search_fields = ("student__admission_no", "student__user__first_name", "student__user__last_name")


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ("student", "term", "amount_due", "amount_paid", "balance", "status", "due_date")
    list_filter = ("status", "term")
    search_fields = ("student__admission_no", "student__user__first_name", "student__user__last_name")
