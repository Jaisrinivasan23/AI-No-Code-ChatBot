from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Chatbot(models.Model):
    CHATBOT_TYPES = [
        ('text_file_based', 'Text File Based Bot'),
        ('form_based', 'Form Based Bot'),
        ('flow_based', 'Flow Based Bot')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    chatbot_type = models.CharField(max_length=50, choices=CHATBOT_TYPES)
    dataset = models.FileField(upload_to='datasets/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    prompt = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_chatbot_type_display()})"


class ChatbotInteraction(models.Model):
    chatbot = models.ForeignKey(Chatbot, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_question = models.TextField()
    meta_response = models.TextField(blank=True, null=True)
    openai_response = models.TextField(blank=True, null=True)
    gemini_response = models.TextField(blank=True, null=True)
    claude_response = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.chatbot.name} - {self.user.username} - {self.timestamp}"


class SelectedBot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chatbot = models.ForeignKey(Chatbot, on_delete=models.CASCADE)
    selected_bot = models.CharField(max_length=100)  # Stores the selected AI bot name (Meta, OpenAI, etc.)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} selected {self.selected_bot} for {self.chatbot.name}"


class Conversation(models.Model):
    chatbot = models.ForeignKey(Chatbot, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ai_bot = models.CharField(max_length=100)  # Which bot the conversation is for (e.g., Meta, OpenAI)
    user_input = models.TextField()
    bot_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation with {self.ai_bot} for {self.chatbot.name} - {self.user.username}"


class Question(models.Model):
    QUESTION_TYPES = [
        ('text', 'Text Input'),
        ('multiple_choice', 'Multiple Choice')
    ]

    chatbot = models.ForeignKey(Chatbot, related_name='questions', on_delete=models.CASCADE)
    question_text = models.CharField(max_length=255)
    options = models.JSONField(blank=True, null=True)  # Stores options as a JSON object
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='text')
    order = models.PositiveIntegerField(default=0)
    is_mandatory = models.BooleanField(default=False)
    help_text = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question_text
