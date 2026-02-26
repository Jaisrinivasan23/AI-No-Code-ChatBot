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
    name = models.CharField(max_length=100, unique=True)
    chatbot_type = models.CharField(max_length=50, choices=CHATBOT_TYPES)
    dataset = models.FileField(upload_to='datasets/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    prompt = models.TextField(null=True, blank=True)
    
    # RAG (Retrieval Augmented Generation) fields
    use_rag = models.BooleanField(default=False, help_text="Enable RAG for better context-aware responses")
    rag_chunk_size = models.IntegerField(default=500, help_text="Size of text chunks for RAG")
    rag_chunks_to_retrieve = models.IntegerField(default=3, help_text="Number of relevant chunks to retrieve")
    rag_index_created = models.BooleanField(default=False, help_text="Whether RAG index has been created")
    rag_last_indexed = models.DateTimeField(null=True, blank=True, help_text="Last time RAG index was created")

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


class RAGStatistics(models.Model):
    """
    Stores statistics and metadata about RAG processing for chatbots
    """
    chatbot = models.OneToOneField(Chatbot, on_delete=models.CASCADE, related_name='rag_stats')
    total_chunks = models.IntegerField(default=0, help_text="Total number of chunks created")
    total_characters = models.IntegerField(default=0, help_text="Total characters in document")
    average_chunk_size = models.FloatField(default=0.0, help_text="Average size of chunks")
    embedding_dimension = models.IntegerField(default=384, help_text="Dimension of embedding vectors")
    processing_time = models.FloatField(default=0.0, help_text="Time taken to process document (seconds)")
    last_processed = models.DateTimeField(auto_now=True, help_text="Last processing timestamp")
    
    def __str__(self):
        return f"RAG Stats for {self.chatbot.name}"
    
    class Meta:
        verbose_name = "RAG Statistics"
        verbose_name_plural = "RAG Statistics"
