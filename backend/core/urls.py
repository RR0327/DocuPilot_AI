from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, ask, health, upload, invoices, invoice_dashboard, invoice_report, invoice_export, invoice_payment_status, invoice_line_items, review_queue, review_record

router = DefaultRouter()
router.register("documents", DocumentViewSet, basename="document")
urlpatterns = [
    path("health/", health, name="health"),
    path("documents/upload/", upload, name="document-upload"),
    path("ask/", ask, name="ask"),
    path("invoices/", invoices, name="invoices"),
    path("reviews/", review_queue, name="review-queue"),
    path("reviews/<int:record_id>/", review_record, name="review-record"),
    path("invoices/report/", invoice_report, name="invoice-report"),
    path("invoices/dashboard/", invoice_dashboard, name="invoice-dashboard"),
    path("invoices/export/", invoice_export, name="invoice-export"),
    path("invoices/<int:record_id>/line-items/", invoice_line_items, name="invoice-line-items"),
    path("invoices/<int:record_id>/payment-status/", invoice_payment_status, name="invoice-payment-status"),
    path("", include(router.urls)),
]
