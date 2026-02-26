from django.contrib import admin
from .models import *

# Register standard models
admin.site.register(ChatbotInteraction)
admin.site.register(Conversation)
admin.site.register(SelectedBot)
admin.site.register(Chatbot)
admin.site.register(Question)

# Register RAG Statistics model
@admin.register(RAGStatistics)
class RAGStatisticsAdmin(admin.ModelAdmin):
    list_display = ('chatbot', 'total_chunks', 'total_characters', 'processing_time', 'last_processed')
    list_filter = ('last_processed',)
    search_fields = ('chatbot__name',)
    readonly_fields = ('last_processed',)