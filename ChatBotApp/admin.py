from django.contrib import admin
from .models import *

admin.site.register(ChatbotInteraction)
admin.site.register(Conversation)
admin.site.register(SelectedBot)


admin.site.register(Chatbot)
admin.site.register(Question)