from django.urls import path
from . import views

urlpatterns = [
    path('', views.check_accessibility, name='home'),
    path('check/', views.check_accessibility, name='check_accessibility'),
    path('report/', views.report_view, name='report'),
    path('api/ai-fix/', views.ai_fix_suggestion, name='ai_fix_suggestion'), 
    path("download-report/", views.download_report, name="download_report"),
    path("checklist/", views.checklist_view, name="checklist"),
]

