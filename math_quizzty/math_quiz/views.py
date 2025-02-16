import json

import environ
import requests
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.text import slugify
from django_htmx.http import replace_url

from .helpers import generate_math_question
from .helpers import paraphrase_math_question
from .helpers import verify_math_question
from .models import Option
from .models import Question
from .models import SolutionStep
from .models import Tag

env = environ.Env()
BASE_URL = env.str("DJANGO_QUESTIONS_URL")


def index(request):
    response = requests.get(f"{BASE_URL}/questions", timeout=10)
    questions = response.json()
    return render(request, "pages/home.html", {"questions": questions})


def question(request, question_id):
    if not request.user.is_authenticated:
        request.session["next_question_id"] = question_id
        return redirect("account_login")

    response = requests.get(f"{BASE_URL}/question/{question_id}", timeout=10)
    # it might not exist on the service we're using
    # so will be infering that it's the ai generated question
    if response.status_code >= 400:
        question = get_object_or_404(Question, id=question_id)
        question = question.to_dict()
    else:
        question = response.json()
    if request.method == "POST":
        action = request.POST.get(
            "action",
        )  # this is to keep track which button trigger an event
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
        if action == "generate":
            generated_question = generate_math_question(json.dumps(question))
            data = paraphrase_math_question(json.dumps(generated_question))

            verify_response = verify_math_question(json.dumps(data))

            # Check if verification failed
            if not verify_response or not verify_response["is_correct"]:
                return render(
                    request,
                    "partials/error.html",
                    {
                        "message": "Unable to generate a valid question. Please try again.",
                        "details": verify_response.get(
                            "message", "Verification failed"
                        ),
                    },
                )

            # Get is_correct from the response directly
            is_correct = verify_response.get("is_correct", False)
            if not is_correct:
                return render(
                    request,
                    "partials/error.html",
                    {
                        "message": "Unable to generate a valid question. Please try again.",
                        "details": verify_response.get(
                            "error_description", "Question validation failed"
                        ),
                    },
                )
            options_data = data.pop("options", [])
            steps_data = data.pop("steps", [])
            tags_data = data.pop("tags", [])
            question_data = Question.objects.create(**data, user=request.user)
            tags_objects = []
            for option in options_data:
                Option.objects.create(question=question_data, option_text=option)
            for step in steps_data:
                SolutionStep.objects.create(
                    question=question_data,
                    **step,
                )
            for tag_data in tags_data:
                name = tag_data.get("name")  # Assuming API sends 'Name'
                if name:
                    tag_obj, _ = Tag.objects.get_or_create(
                        name=name,
                        defaults={"slug": slugify(name)},
                    )
                    tags_objects.append(tag_obj)
            question_data.tags.set(tags_objects)

        response = render(
            request, "pages/question.html", {"question": question_data.to_dict()}
        )
        return replace_url(response, f"/question/{question_data.id}")

    return render(request, "pages/question.html", {"question": question})
