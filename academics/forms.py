from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import User

from .models import Attendance, FeePayment, GradeResult, SchoolClass, StudentProfile, Subject, TeacherProfile


def teacher_class_ids(user):
    if not user or not getattr(user, "is_teacher_role", False) or not hasattr(user, "teacher_profile"):
        return SchoolClass.objects.none().values_list("id", flat=True)
    return Subject.objects.filter(teachers=user.teacher_profile).values_list("school_class_id", flat=True)


class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ["name", "section"]


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name", "code", "school_class"]


class StudentProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.filter(role=User.Role.STUDENT).order_by("username")

    class Meta:
        model = StudentProfile
        fields = ["user", "admission_no", "school_class", "guardian_name", "guardian_phone", "date_of_birth", "address", "active"]
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"})}


class StudentSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    admission_no = forms.CharField(max_length=30, label="Admission number")
    school_class = forms.ModelChoiceField(queryset=SchoolClass.objects.all(), label="Class")
    guardian_name = forms.CharField(max_length=120)
    guardian_phone = forms.CharField(max_length=30)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]

    def clean_admission_no(self):
        admission_no = self.cleaned_data["admission_no"].strip()
        if StudentProfile.objects.filter(admission_no__iexact=admission_no).exists():
            raise forms.ValidationError("A student with this admission number already exists.")
        return admission_no

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STUDENT
        user.email = self.cleaned_data.get("email", "")
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                admission_no=self.cleaned_data["admission_no"],
                school_class=self.cleaned_data["school_class"],
                guardian_name=self.cleaned_data["guardian_name"],
                guardian_phone=self.cleaned_data["guardian_phone"],
                date_of_birth=self.cleaned_data.get("date_of_birth"),
                address=self.cleaned_data.get("address", ""),
            )
        return user


class TeacherProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.filter(role=User.Role.TEACHER).order_by("username")

    class Meta:
        model = TeacherProfile
        fields = ["user", "employee_id", "phone", "subjects"]
        widgets = {"subjects": forms.CheckboxSelectMultiple}


class AttendanceForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and getattr(user, "is_teacher_role", False):
            self.fields["student"].queryset = StudentProfile.objects.filter(school_class_id__in=teacher_class_ids(user))

    class Meta:
        model = Attendance
        fields = ["student", "date", "status"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}


class GradeResultForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and getattr(user, "is_teacher_role", False):
            subject_ids = user.teacher_profile.subjects.values_list("id", flat=True) if hasattr(user, "teacher_profile") else []
            self.fields["subject"].queryset = Subject.objects.filter(id__in=subject_ids)
            self.fields["student"].queryset = StudentProfile.objects.filter(school_class_id__in=teacher_class_ids(user))

    class Meta:
        model = GradeResult
        fields = ["student", "subject", "term", "score", "remarks"]


class FeePaymentForm(forms.ModelForm):
    class Meta:
        model = FeePayment
        fields = ["student", "term", "amount_due", "amount_paid", "due_date"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}
