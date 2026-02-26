# Generated migration for RAG features

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ChatBotApp', '0018_alter_chatbot_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatbot',
            name='use_rag',
            field=models.BooleanField(default=False, help_text='Enable RAG for better context-aware responses'),
        ),
        migrations.AddField(
            model_name='chatbot',
            name='rag_chunk_size',
            field=models.IntegerField(default=500, help_text='Size of text chunks for RAG'),
        ),
        migrations.AddField(
            model_name='chatbot',
            name='rag_chunks_to_retrieve',
            field=models.IntegerField(default=3, help_text='Number of relevant chunks to retrieve'),
        ),
        migrations.AddField(
            model_name='chatbot',
            name='rag_index_created',
            field=models.BooleanField(default=False, help_text='Whether RAG index has been created'),
        ),
        migrations.AddField(
            model_name='chatbot',
            name='rag_last_indexed',
            field=models.DateTimeField(blank=True, help_text='Last time RAG index was created', null=True),
        ),
        migrations.CreateModel(
            name='RAGStatistics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_chunks', models.IntegerField(default=0, help_text='Total number of chunks created')),
                ('total_characters', models.IntegerField(default=0, help_text='Total characters in document')),
                ('average_chunk_size', models.FloatField(default=0.0, help_text='Average size of chunks')),
                ('embedding_dimension', models.IntegerField(default=384, help_text='Dimension of embedding vectors')),
                ('processing_time', models.FloatField(default=0.0, help_text='Time taken to process document (seconds)')),
                ('last_processed', models.DateTimeField(auto_now=True, help_text='Last processing timestamp')),
                ('chatbot', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='rag_stats', to='ChatBotApp.chatbot')),
            ],
            options={
                'verbose_name': 'RAG Statistics',
                'verbose_name_plural': 'RAG Statistics',
            },
        ),
    ]
