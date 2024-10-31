from django.http import JsonResponse
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import *
import os
from django.conf import settings
import openai

openai.api_key = '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'

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard', user_id=user.id)
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def user_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                return render(request, 'signup.html', {'error': 'Username already taken'})
            else:
                User.objects.create_user(username=username, password=password)
                return redirect('login')
        else:
            return render(request, 'signup.html', {'error': 'Passwords do not match'})
    return render(request, 'signup.html')

@login_required
def user_dashboard(request, user_id):
    if request.user.id == user_id:
        chatbots = Chatbot.objects.filter(user=request.user)
        return render(request, 'dashboard.html', {
            'user': request.user,
            'chatbots': chatbots,
        })
    else:
        return redirect('login')
    
@login_required
def chatbot_detail(request, chatbot_id):
    chatbot = get_object_or_404(Chatbot, id=chatbot_id, user=request.user)
    return render(request, 'chatbot_detail.html', {'chatbot': chatbot})

@login_required
@csrf_exempt
def delete_chatbot(request, bot_id):
    if request.method == 'POST':
        bot = get_object_or_404(Chatbot, id=bot_id, user=request.user)
        bot.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')

@login_required
def create_chatbot(request):
    if request.method == 'POST':
        chatbot_type = request.POST.get('chatbot_type')
        chatbot_name = request.POST.get('chatbot_name')

        if chatbot_type and chatbot_name:
            Chatbot.objects.create(
                user=request.user,
                name=chatbot_name,
                chatbot_type=chatbot_type
            )
            return redirect('dashboard', user_id=request.user.id)  # Redirect to the user's dashboard
    return render(request, 'create_chatbot.html')

@login_required
def text_file_based_bot(request):
    if request.method == 'POST':
        chatbot_name = request.POST.get('chatbot_name')
        dataset_file = request.FILES.get('dataset')

        # Save the chatbot details and the dataset file
        chatbot = Chatbot.objects.create(
            user=request.user,
            name=chatbot_name,
            chatbot_type='text_file_based',
            dataset=dataset_file
        )

        # Read the dataset file and generate a prompt
        dataset_path = os.path.join(settings.MEDIA_ROOT, chatbot.dataset.name)
        with open(dataset_path, 'r', encoding='utf-8') as file:
            business_data = file.read()

        # Generate a prompt from the business data
        prompt = f"Based on the provided business data, respond only to business-related queries. Ignore coding or irrelevant queries. Here's the business data:\n\n{business_data[:1500]}..."

        # Save the prompt in the Chatbot instance
        chatbot.prompt = prompt
        chatbot.save()

        # Redirect to chatbot interaction page
        return redirect('multi_question_chatbot', chatbot_id=chatbot.id)

    return render(request, 'text_file_based.html')

def create_dataset_based_prompt(question, dataset_content):
    """
    Create a prompt using the dataset content and user question.
    The prompt instructs the AI to use the dataset to answer the question.
    """
    prompt = (
        f"Here is a business dataset. You must strictly use the information from this dataset to answer the following questions. "
        f"If the answer cannot be found in this dataset, respond with 'I cannot find the answer in the provided dataset.'\n\n"
        f"Dataset:\n{dataset_content[:1500]}...\n\n"  # First 1500 characters from dataset
        f"Question: {question}"
    )
    return prompt

# AI Response Functions (Meta, OpenAI, Gemini, Claude)

def get_meta_response(question, dataset_content):
    try:
        prompt = create_dataset_based_prompt(question, dataset_content)
        # Placeholder for Meta LLaMA 3.1 response
        return f"Meta LLaMA response for: {question} using the dataset."
    except Exception as e:
        return f"Error in Meta LLaMA response: {str(e)}"

def get_openai_response(question, dataset_content):
    try:
        # Creating the prompt for the chat model in the form of a chat message array
        messages = [
            {"role": "system", "content": "You are a helpful assistant limited to answering questions based on a specific dataset."},
            {"role": "user", "content": create_dataset_based_prompt(question, dataset_content)}
        ]

        # Using the 'v1/chat/completions' endpoint for chat-based models
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Correcting the model name to "gpt-4"
            messages=messages,
            max_tokens=200
        )
        return response.choices[0].message['content'].strip()

    except Exception as e:
        return f"Error in OpenAI response: {str(e)}"

def get_gemini_response(question, dataset_content):
    try:
        prompt = create_dataset_based_prompt(question, dataset_content)
        # Placeholder for Gemini API response
        return f"Gemini response for: {question} using the dataset."
    except Exception as e:
        return f"Error in Gemini response: {str(e)}"

def get_claude_response(question, dataset_content):
    try:
        prompt = create_dataset_based_prompt(question, dataset_content)
        # Placeholder for Claude API response
        return f"Claude response for: {question} using the dataset."
    except Exception as e:
        return f"Error in Claude response: {str(e)}"

@login_required
def multi_question_chatbot(request, chatbot_id):
    chatbot = Chatbot.objects.get(id=chatbot_id)

    # Read the dataset file for this chatbot
    dataset_path = os.path.join(settings.MEDIA_ROOT, chatbot.dataset.name)
    with open(dataset_path, 'r', encoding='utf-8') as file:
        dataset_content = file.read()

    if request.method == 'POST':
        user_question = request.POST.get('question')

        # Generate responses for each AI
        meta_response = get_meta_response(user_question, dataset_content)
        openai_response = get_openai_response(user_question, dataset_content)
        gemini_response = get_gemini_response(user_question, dataset_content)
        claude_response = get_claude_response(user_question, dataset_content)

        # Store the interaction in the database
        ChatbotInteraction.objects.create(
            chatbot=chatbot,
            user=request.user,
            user_question=user_question,
            meta_response=meta_response,
            openai_response=openai_response,
            gemini_response=gemini_response,
            claude_response=claude_response
        )

        # Return the responses as part of the context to append dynamically
        return render(request, 'multi_question_chatbot.html', {
            'chatbot': chatbot,
            'user_question': user_question,
            'meta_response': meta_response,
            'openai_response': openai_response,
            'gemini_response': gemini_response,
            'claude_response': claude_response
        })

    return render(request, 'multi_question_chatbot.html', {
        'chatbot': chatbot
    })

@login_required
def selected_bot_chat(request, chatbot_id, bot_name):
    chatbot = Chatbot.objects.get(id=chatbot_id)
    selected_bot = bot_name  # The selected bot's name (Meta, OpenAI, etc.)

    if request.method == 'POST':
        user_input = request.POST.get('user_input')

        # Generate the response based on the selected bot
        if selected_bot == 'Meta':
            bot_response = get_meta_response(user_input, chatbot.prompt)
        elif selected_bot == 'OpenAI':
            bot_response = get_openai_response(user_input, chatbot.prompt)
        elif selected_bot == 'Gemini':
            bot_response = get_gemini_response(user_input, chatbot.prompt)
        elif selected_bot == 'Claude':
            bot_response = get_claude_response(user_input, chatbot.prompt)

        # Store the conversation
        Conversation.objects.create(
            chatbot=chatbot,
            user=request.user,
            ai_bot=selected_bot,
            user_input=user_input,
            bot_response=bot_response
        )

        return render(request, 'File_Based/selected_bot_chat.html', {
            'chatbot': chatbot,
            'selected_bot': selected_bot,
            'user_input': user_input,
            'bot_response': bot_response
        })

    return render(request, 'selected_bot_chat.html', {
        'chatbot': chatbot,
        'selected_bot': selected_bot
    })

@login_required
def select_ai_bot(request, chatbot_id, selected_bot):
    chatbot = Chatbot.objects.get(id=chatbot_id)

    # Store the selected bot in the database
    SelectedBot.objects.create(
        user=request.user,
        chatbot=chatbot,
        selected_bot=selected_bot
    )

    # Redirect to the selected AI's interaction page
    return redirect('selected_bot_chat', chatbot_id=chatbot_id, bot_name=selected_bot)

@login_required
def question_chatbot(request):
    if request.method == 'POST':
        chatbot_name = request.POST.get('chatbot_name')
        questions = request.POST.getlist('question_text')

        # Create the chatbot and associate it with the current logged-in user
        chatbot = Chatbot.objects.create(
            user=request.user,
            name=chatbot_name,
            chatbot_type='flow_based'
        )

        # Loop through questions and options to save them in the database
        for i, question_text in enumerate(questions, start=1):
            options = request.POST.getlist(f'options_{i}')
            options_dict = {"options": options} if options else None
            Question.objects.create(chatbot=chatbot, question_text=question_text, options=options_dict)

        # Redirect directly to the chatbot test page
        return redirect('test_chatbot', chatbot_id=chatbot.id)

    return render(request, 'Flow_Based/create_question.html')

@login_required
def test_chatbot(request, chatbot_id):
    chatbot = get_object_or_404(Chatbot, id=chatbot_id)
    questions = list(chatbot.questions.all())  # Convert to list to index questions in sequence

    if request.method == 'POST':
        user_message = request.POST.get('user_message')
        question_id = int(request.POST.get('question_id'))

        # Save the interaction in the database
        ChatbotInteraction.objects.create(
            chatbot=chatbot,
            user=request.user,
            user_question=user_message
        )

        # Find the current question index
        try:
            current_question_index = next(index for index, q in enumerate(questions) if q.id == question_id)
        except StopIteration:
            current_question_index = None

        # Get the next question in sequence, if any
        if current_question_index is not None and current_question_index + 1 < len(questions):
            next_question = questions[current_question_index + 1]
            bot_response = next_question.question_text
            options = next_question.options['options'] if next_question.options else None
            return JsonResponse({
                'bot_response': bot_response,
                'options': options,
                'next_question_id': next_question.id
            })
        else:
            # No more questions left
            return JsonResponse({
                'bot_response': "Thank you for interacting with the bot!",
                'options': None,
                'next_question_id': None
            })

    # Render the initial page with the first question
    first_question = questions[0] if questions else None
    return render(request, 'Flow_Based/test_chatbot.html', {
        'chatbot': chatbot,
        'first_question': first_question,
    })

@login_required
def form_based_bot(request):
    if request.method == 'POST':
        chatbot_name = request.POST.get('chatbot_name')
        question_answer_pairs = []

        # Collect question-answer pairs from the form data
        for key in request.POST:
            if key.startswith('question_'):
                index = key.split('_')[1]
                question = request.POST.get(f'question_{index}')
                answer = request.POST.get(f'answer_{index}')
                if question and answer:
                    question_answer_pairs.append((question, answer))

        # Generate the prompt based on question-answer pairs
        prompt = "Answer only based on the following questions and answers:\n"
        for q, a in question_answer_pairs:
            prompt += f"Q: {q}\nA: {a}\n"

        # Save the chatbot instance
        chatbot = Chatbot.objects.create(
            user=request.user,
            name=chatbot_name,
            chatbot_type='form_based',
            prompt=prompt
        )

        # Redirect to the form-based test page
        return redirect('form_based_test', chatbot_id=chatbot.id)

    return render(request, 'Form_Based/form_based.html')


@login_required
def test_Form_chatbot(request, chatbot_id):
    chatbot = get_object_or_404(Chatbot, id=chatbot_id)

    if request.method == 'POST':
        user_message = request.POST.get('user_message')
        
        # Check if user_message is empty
        if not user_message:
            return JsonResponse({'error': 'User message cannot be empty.'}, status=400)

        # Set OpenAI API key securely
        openai.api_key = settings.OPENAI_API_KEY

        # Generate chatbot response using OpenAI
        try:
            response = openai.Completion.create(
                model="gpt-4",
                prompt=f"{chatbot.prompt}\n\nUser: {user_message}\nChatbot:",
                max_tokens=50
            )
            bot_response = response.choices[0].text.strip()

            # Store the interaction
            ChatbotInteraction.objects.create(
                chatbot=chatbot,
                user=request.user,
                user_question=user_message,
                openai_response=bot_response
            )

            return JsonResponse({'bot_response': bot_response})

        except openai.error.OpenAIError as e:
            # Handle OpenAI-specific errors
            return JsonResponse({'error': f"OpenAI error: {str(e)}"}, status=500)
        except Exception as e:
            # Handle general errors
            return JsonResponse({'error': f"An unexpected error occurred: {str(e)}"}, status=500)

    return render(request, 'Form_Based/test_form.html', {'chatbot': chatbot})

