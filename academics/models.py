from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class SchoolClass(models.Model):
    name = models.CharField(max_length=80, unique=True)
    section = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["name", "section"]

    def __str__(self):
        return f"{self.name} {self.section}".strip()


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="subjects")

    class Meta:
        ordering = ["school_class__name", "name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class TeacherProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="teacher_profile")
    employee_id = models.CharField(max_length=30, unique=True)
    phone = models.CharField(max_length=30, blank=True)
    subjects = models.ManyToManyField(Subject, blank=True, related_name="teachers")

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")
    admission_no = models.CharField(max_length=30, unique=True)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.PROTECT, related_name="students")
    guardian_name = models.CharField(max_length=120)
    guardian_phone = models.CharField(max_length=30)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["school_class__name", "admission_no"]

    def __str__(self):
        return f"{self.admission_no} - {self.user.get_full_name() or self.user.username}"


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LATE = "LATE", "Late"

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="attendance")
    date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ("student", "date")
        ordering = ["-date", "student__admission_no"]

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"


class GradeResult(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="results")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="results")
    term = models.CharField(max_length=60)
    score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("student", "subject", "term")
        ordering = ["student__admission_no", "term", "subject__name"]

    @property
    def letter_grade(self):
        score = float(self.score)
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.score}"


class FeePayment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PARTIAL = "PARTIAL", "Partial"
        PAID = "PAID", "Paid"

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="fees")
    term = models.CharField(max_length=60)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        unique_together = ("student", "term")
        ordering = ["status", "due_date"]

    @property
    def balance(self):
        return self.amount_due - self.amount_paid

    def save(self, *args, **kwargs):
        if self.amount_paid <= 0:
            self.status = self.Status.PENDING
        elif self.amount_paid < self.amount_due:
            self.status = self.Status.PARTIAL
        else:
            self.status = self.Status.PAID
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.term} - {self.status}"
