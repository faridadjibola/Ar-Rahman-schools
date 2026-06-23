import csv
from decimal import Decimal, InvalidOperation
from io import StringIO

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User

from .forms import AttendanceForm, FeePaymentForm, GradeResultForm, StudentProfileForm, StudentSignUpForm
from .models import Attendance, FeePayment, GradeResult, SchoolClass, StudentProfile, Subject


def role_queryset(user, queryset):
    model = queryset.model
    if user.is_superuser or user.role == User.Role.ADMIN:
        return queryset
    if user.role == User.Role.STUDENT and hasattr(user, "student_profile"):
        if model is StudentProfile:
            return queryset.filter(pk=user.student_profile.pk)
        return queryset.filter(student=user.student_profile)
    if user.role == User.Role.TEACHER and hasattr(user, "teacher_profile"):
        subject_ids = user.teacher_profile.subjects.values_list("id", flat=True)
        class_ids = Subject.objects.filter(id__in=subject_ids).values_list("school_class_id", flat=True)
        if model is GradeResult:
            return queryset.filter(subject_id__in=subject_ids)
        if model is StudentProfile:
            return queryset.filter(school_class_id__in=class_ids)
        if model is Attendance:
            return queryset.filter(student__school_class_id__in=class_ids)
    return queryset.none()


def can_manage(user):
    return user.is_superuser or user.role in [User.Role.ADMIN, User.Role.TEACHER]


def require_permission(allowed):
    if not allowed:
        raise PermissionDenied


def editable_object(user, model, pk, admin_only=False):
    require_permission(user.is_admin_role if admin_only else can_manage(user))
    queryset = role_queryset(user, model.objects.all())
    return get_object_or_404(queryset, pk=pk)


def allowed_students_for_results(user):
    return role_queryset(user, StudentProfile.objects.select_related("user", "school_class"))


def allowed_subjects_for_results(user):
    if user.is_superuser or user.role == User.Role.ADMIN:
        return Subject.objects.select_related("school_class")
    if user.role == User.Role.TEACHER and hasattr(user, "teacher_profile"):
        return user.teacher_profile.subjects.select_related("school_class")
    return Subject.objects.none()


def student_signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = StudentSignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome to the Ar-Rahman Schools student portal.")
        return redirect("student_portal")

    return render(request, "registration/student_signup.html", {"form": form})


@login_required
def student_portal(request):
    require_permission(request.user.is_student_role and hasattr(request.user, "student_profile"))
    student = request.user.student_profile
    results_qs = GradeResult.objects.filter(student=student).select_related("subject")
    attendance_qs = Attendance.objects.filter(student=student).select_related("marked_by")
    fees_qs = FeePayment.objects.filter(student=student)
    context = {
        "student": student,
        "results": results_qs,
        "attendance": attendance_qs[:12],
        "fees": fees_qs,
        "passed": results_qs.filter(score__gte=60).count(),
        "failed": results_qs.filter(score__lt=60).count(),
        "present_count": attendance_qs.filter(status=Attendance.Status.PRESENT).count(),
        "absent_count": attendance_qs.filter(status=Attendance.Status.ABSENT).count(),
    }
    return render(request, "academics/student_portal.html", context)


@login_required
def dashboard(request):
    students_qs = role_queryset(request.user, StudentProfile.objects.select_related("user", "school_class"))
    attendance_qs = role_queryset(request.user, Attendance.objects.select_related("student"))
    results_qs = role_queryset(request.user, GradeResult.objects.select_related("student", "subject"))
    fees_qs = role_queryset(request.user, FeePayment.objects.select_related("student"))

    today = timezone.localdate()
    context = {
        "student_count": students_qs.count(),
        "class_count": SchoolClass.objects.count() if request.user.is_admin_role else students_qs.values("school_class").distinct().count(),
        "attendance_today": attendance_qs.filter(date=today).values("status").annotate(total=Count("id")),
        "pending_fees": fees_qs.exclude(status=FeePayment.Status.PAID).aggregate(total=Sum("amount_due") - Sum("amount_paid"))["total"] or 0,
        "recent_results": results_qs[:8],
        "recent_attendance": attendance_qs[:8],
        "role": request.user.get_role_display(),
    }
    return render(request, "academics/dashboard.html", context)


@login_required
def students(request):
    form = StudentProfileForm()
    if request.method == "POST" and request.user.is_admin_role:
        form = StudentProfileForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student record saved.")
            return redirect("students")

    context = {
        "students": role_queryset(request.user, StudentProfile.objects.select_related("user", "school_class")),
        "form": form,
        "can_create": request.user.is_admin_role,
    }
    return render(request, "academics/students.html", context)


@login_required
def student_edit(request, pk):
    student = editable_object(request.user, StudentProfile, pk, admin_only=True)
    form = StudentProfileForm(request.POST or None, instance=student)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Student record updated.")
        return redirect("students")
    return render(request, "academics/record_form.html", {"form": form, "title": "Edit Student", "back_url": "students"})


@login_required
def student_delete(request, pk):
    student = editable_object(request.user, StudentProfile, pk, admin_only=True)
    if request.method == "POST":
        student.delete()
        messages.success(request, "Student record deleted.")
        return redirect("students")
    return render(request, "academics/confirm_delete.html", {"object": student, "title": "Delete Student", "back_url": "students"})


@login_required
def attendance(request):
    form = AttendanceForm(user=request.user)
    if request.method == "POST" and can_manage(request.user):
        form = AttendanceForm(request.POST, user=request.user)
        if form.is_valid():
            record = form.save(commit=False)
            record.marked_by = request.user
            record.save()
            messages.success(request, "Attendance saved.")
            return redirect("attendance")

    context = {
        "attendance": role_queryset(request.user, Attendance.objects.select_related("student", "student__user", "marked_by")),
        "form": form,
        "can_create": can_manage(request.user),
    }
    return render(request, "academics/attendance.html", context)


@login_required
def attendance_edit(request, pk):
    record = editable_object(request.user, Attendance, pk)
    form = AttendanceForm(request.POST or None, instance=record, user=request.user)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.marked_by = request.user
        item.save()
        messages.success(request, "Attendance updated.")
        return redirect("attendance")
    return render(request, "academics/record_form.html", {"form": form, "title": "Edit Attendance", "back_url": "attendance"})


@login_required
def attendance_delete(request, pk):
    record = editable_object(request.user, Attendance, pk)
    if request.method == "POST":
        record.delete()
        messages.success(request, "Attendance deleted.")
        return redirect("attendance")
    return render(request, "academics/confirm_delete.html", {"object": record, "title": "Delete Attendance", "back_url": "attendance"})


@login_required
def results(request):
    form = GradeResultForm(user=request.user)
    if request.method == "POST" and can_manage(request.user):
        form = GradeResultForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Result saved.")
            return redirect("results")

    context = {
        "results": role_queryset(request.user, GradeResult.objects.select_related("student", "student__user", "subject")),
        "form": form,
        "can_create": can_manage(request.user),
    }
    return render(request, "academics/results.html", context)


@login_required
def results_export(request):
    require_permission(can_manage(request.user))
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="results.csv"'
    writer = csv.writer(response)
    writer.writerow(["admission_no", "student_name", "subject_code", "subject_name", "term", "score", "grade", "remarks"])

    queryset = role_queryset(
        request.user,
        GradeResult.objects.select_related("student", "student__user", "subject"),
    )
    for result in queryset:
        writer.writerow(
            [
                result.student.admission_no,
                result.student.user.get_full_name() or result.student.user.username,
                result.subject.code,
                result.subject.name,
                result.term,
                result.score,
                result.letter_grade,
                result.remarks,
            ]
        )
    return response


@login_required
def results_template(request):
    require_permission(can_manage(request.user))
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="results_upload_template.csv"'
    writer = csv.writer(response)
    writer.writerow(["admission_no", "subject_code", "term", "score", "remarks"])
    writer.writerow(["ADM001", "MATH101", "Term 1", "87", "Good progress"])
    return response


@login_required
def results_import(request):
    require_permission(can_manage(request.user))
    if request.method != "POST":
        return redirect("results")

    upload = request.FILES.get("results_file")
    if not upload:
        messages.error(request, "Choose a CSV file before uploading.")
        return redirect("results")

    try:
        content = upload.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        messages.error(request, "The uploaded file must be a UTF-8 CSV file.")
        return redirect("results")

    reader = csv.DictReader(StringIO(content))
    required_columns = {"admission_no", "subject_code", "term", "score"}
    if not reader.fieldnames or not required_columns.issubset(set(reader.fieldnames)):
        messages.error(request, "CSV must include admission_no, subject_code, term, and score columns.")
        return redirect("results")

    students = {student.admission_no: student for student in allowed_students_for_results(request.user)}
    subjects = {subject.code: subject for subject in allowed_subjects_for_results(request.user)}
    errors = []
    created = 0
    updated = 0

    with transaction.atomic():
        for index, row in enumerate(reader, start=2):
            admission_no = (row.get("admission_no") or "").strip()
            subject_code = (row.get("subject_code") or "").strip()
            term = (row.get("term") or "").strip()
            remarks = (row.get("remarks") or "").strip()

            if not admission_no or not subject_code or not term:
                errors.append(f"Row {index}: admission_no, subject_code, and term are required.")
                continue

            student = students.get(admission_no)
            subject = subjects.get(subject_code)
            if not student:
                errors.append(f"Row {index}: student admission number '{admission_no}' is not available.")
                continue
            if not subject:
                errors.append(f"Row {index}: subject code '{subject_code}' is not available.")
                continue

            try:
                score = Decimal((row.get("score") or "").strip())
            except InvalidOperation:
                errors.append(f"Row {index}: score must be a number.")
                continue
            if score < 0 or score > 100:
                errors.append(f"Row {index}: score must be between 0 and 100.")
                continue

            _, was_created = GradeResult.objects.update_or_create(
                student=student,
                subject=subject,
                term=term,
                defaults={"score": score, "remarks": remarks},
            )
            if was_created:
                created += 1
            else:
                updated += 1

        if errors:
            transaction.set_rollback(True)

    if errors:
        for error in errors[:8]:
            messages.error(request, error)
        if len(errors) > 8:
            messages.error(request, f"{len(errors) - 8} more errors were found. No rows were imported.")
        else:
            messages.error(request, "No rows were imported. Fix the CSV and upload again.")
    else:
        messages.success(request, f"Results import complete: {created} created, {updated} updated.")

    return redirect("results")


@login_required
def result_edit(request, pk):
    result = editable_object(request.user, GradeResult, pk)
    form = GradeResultForm(request.POST or None, instance=result, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Result updated.")
        return redirect("results")
    return render(request, "academics/record_form.html", {"form": form, "title": "Edit Result", "back_url": "results"})


@login_required
def result_delete(request, pk):
    result = editable_object(request.user, GradeResult, pk)
    if request.method == "POST":
        result.delete()
        messages.success(request, "Result deleted.")
        return redirect("results")
    return render(request, "academics/confirm_delete.html", {"object": result, "title": "Delete Result", "back_url": "results"})


@login_required
def fees(request):
    form = FeePaymentForm()
    if request.method == "POST" and request.user.is_admin_role:
        form = FeePaymentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Fee record saved.")
            return redirect("fees")

    context = {
        "fees": role_queryset(request.user, FeePayment.objects.select_related("student", "student__user")),
        "form": form,
        "can_create": request.user.is_admin_role,
    }
    return render(request, "academics/fees.html", context)


@login_required
def fee_edit(request, pk):
    fee = editable_object(request.user, FeePayment, pk, admin_only=True)
    form = FeePaymentForm(request.POST or None, instance=fee)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Fee record updated.")
        return redirect("fees")
    return render(request, "academics/record_form.html", {"form": form, "title": "Edit Fee", "back_url": "fees"})


@login_required
def fee_delete(request, pk):
    fee = editable_object(request.user, FeePayment, pk, admin_only=True)
    if request.method == "POST":
        fee.delete()
        messages.success(request, "Fee record deleted.")
        return redirect("fees")
    return render(request, "academics/confirm_delete.html", {"object": fee, "title": "Delete Fee", "back_url": "fees"})


@login_required
def reports(request):
    students = role_queryset(request.user, StudentProfile.objects.all())
    attendance_summary = role_queryset(request.user, Attendance.objects.all()).values("status").annotate(total=Count("id"))
    fee_summary = role_queryset(request.user, FeePayment.objects.all()).aggregate(
        due=Sum("amount_due"),
        paid=Sum("amount_paid"),
    )
    grade_summary = role_queryset(request.user, GradeResult.objects.all()).filter(score__gte=0).aggregate(
        passed=Count("id", filter=Q(score__gte=60)),
        failed=Count("id", filter=Q(score__lt=60)),
    )
    return render(
        request,
        "academics/reports.html",
        {
            "students": students,
            "attendance_summary": attendance_summary,
            "fee_summary": fee_summary,
            "grade_summary": grade_summary,
        },
    )
