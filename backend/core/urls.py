from django.urls import include, path
from .auth_views import csrf, session_login, session_me, session_logout, session_register
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, ask, health, upload, invoices, invoice_dashboard, invoice_report, invoice_export, invoice_payment_status, invoice_line_items, review_queue, review_record, invoice_analytics, processing_job_detail, retry_processing_job, processing_overview, classification_evaluation, classification_feedback_evaluation, classification_feedback_quality, classification_label_export, classification_reliability

router = DefaultRouter()
router.register("documents", DocumentViewSet, basename="document")
urlpatterns = [
    path("auth/csrf/", csrf, name="auth-csrf"),
    path("auth/register/", session_register, name="auth-register"),
    path("auth/login/", session_login, name="auth-login"),
    path("auth/me/", session_me, name="auth-me"),
    path("auth/logout/", session_logout, name="auth-logout"),
    path("health/", health, name="health"),
    path("classification/reliability/", classification_reliability, name="classification-reliability"),
    path("classification/feedback-quality/", classification_feedback_quality, name="classification-feedback-quality"),
    path("classification/feedback-label-export/", classification_label_export, name="classification-label-export"),
    path("classification/feedback-evaluation/", classification_feedback_evaluation, name="classification-feedback-evaluation"),
    path("classification/evaluation/", classification_evaluation, name="classification-evaluation"),
    path("processing-jobs/overview/", processing_overview, name="processing-overview"),
    path("processing-jobs/<uuid:job_id>/", processing_job_detail, name="processing-job-detail"),
    path("processing-jobs/<uuid:job_id>/retry/", retry_processing_job, name="processing-job-retry"),
    path("documents/upload/", upload, name="document-upload"),
    path("ask/", ask, name="ask"),
    path("invoices/", invoices, name="invoices"),
    path("reviews/", review_queue, name="review-queue"),
    path("reviews/<int:record_id>/", review_record, name="review-record"),
    path("invoices/report/", invoice_report, name="invoice-report"),
    path("invoices/analytics/", invoice_analytics, name="invoice-analytics"),
    path("invoices/dashboard/", invoice_dashboard, name="invoice-dashboard"),
    path("invoices/export/", invoice_export, name="invoice-export"),
    path("invoices/<int:record_id>/line-items/", invoice_line_items, name="invoice-line-items"),
    path("invoices/<int:record_id>/payment-status/", invoice_payment_status, name="invoice-payment-status"),
    path("", include(router.urls)),
]
