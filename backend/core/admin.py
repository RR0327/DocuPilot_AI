from django.contrib import admin
from .models import Document, DocumentPage, ExtractedRecord, QuestionAnswer, DocumentChunk

admin.site.register(Document)
admin.site.register(DocumentPage)
admin.site.register(ExtractedRecord)
admin.site.register(QuestionAnswer)
admin.site.register(DocumentChunk)
