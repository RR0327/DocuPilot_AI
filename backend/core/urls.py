from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, ask, health, upload, invoices, invoice_dashboard, invoice_report, invoice_export, invoice_payment_status, invoice_line_items, review_queue, review_record, invoice_analytics, processing_job_detail, retry_processing_job

router = DefaultRouter()
router.register("documents", DocumentViewSet, basename="document")
urlpatterns = [
    path("health/", health, name="health"),
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
