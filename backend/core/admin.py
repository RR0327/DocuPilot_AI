from django.contrib import admin
from .models import Document, DocumentPage, ExtractedRecord, QuestionAnswer, DocumentChunk

admin.site.register(Document)
admin.site.register(DocumentPage)
admin.site.register(ExtractedRecord)
admin.site.register(QuestionAnswer)
admin.site.register(DocumentChunk)

from .models import InvoicePaymentState
admin.site.register(InvoicePaymentState)

from .models import InvoiceLineItem, ExtractionReview
admin.site.register(InvoiceLineItem)

admin.site.register(ExtractionReview)
