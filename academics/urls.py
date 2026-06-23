from django.urls import path

from . import views

urlpatterns = [
    path("signup/student/", views.student_signup, name="student_signup"),
    path("", views.dashboard, name="dashboard"),
    path("portal/student/", views.student_portal, name="student_portal"),
    path("students/", views.students, name="students"),
    path("students/<int:pk>/edit/", views.student_edit, name="student_edit"),
    path("students/<int:pk>/delete/", views.student_delete, name="student_delete"),
    path("attendance/", views.attendance, name="attendance"),
    path("attendance/<int:pk>/edit/", views.attendance_edit, name="attendance_edit"),
    path("attendance/<int:pk>/delete/", views.attendance_delete, name="attendance_delete"),
    path("results/", views.results, name="results"),
    path("results/export/", views.results_export, name="results_export"),
    path("results/template/", views.results_template, name="results_template"),
    path("results/import/", views.results_import, name="results_import"),
    path("results/<int:pk>/edit/", views.result_edit, name="result_edit"),
    path("results/<int:pk>/delete/", views.result_delete, name="result_delete"),
    path("fees/", views.fees, name="fees"),
    path("fees/<int:pk>/edit/", views.fee_edit, name="fee_edit"),
    path("fees/<int:pk>/delete/", views.fee_delete, name="fee_delete"),
    path("reports/", views.reports, name="reports"),
]
