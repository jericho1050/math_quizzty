import environ
import requests
from django.shortcuts import render

env = environ.Env()
BASE_URL = env.str("DJANGO_QUESTIONS_URL")


def index(request):
    response = requests.get(f"{BASE_URL}/questions", timeout=10)
    questions = response.json()
    return render(request, "pages/home.html", {"questions": questions})


def question(request, question_id):
    response = requests.get(f"{BASE_URL}/question/{question_id}", timeout=10)
    question = response.json()
    if request.method == "POST":
        action = request.POST.get("action") # this is to keep track which button trigger an event
        if action == "check":
            selected_answer = request.POST.get("selected_answer")
            return render(
                request,
                "partials/explanation.html",
                {
                    "question": question,
                    "selected_answer": selected_answer,
                },
            )
        elif action == "generate":
            ...
    return render(request, "pages/question.html", {"question": question})
