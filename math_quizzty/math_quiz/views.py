import environ
import requests
from django.shortcuts import redirect
from django.shortcuts import render

from .helpers import _fetch_question as fetch_question
from .helpers import _handle_check_action as handle_check_action
from .helpers import _handle_generate_action as handle_generate_action

env = environ.Env()
BASE_URL = env.str("DJANGO_QUESTIONS_URL")


def index(request):
    offset = int(request.GET.get("offset", 0))
    limit = 10

    response = requests.get(
        f"{BASE_URL}/questions", timeout=10, params={"limit": limit, "offset": offset}
    )
    questions = response.json()

    # Add pagination data to context
    context = {
        "questions": questions["items"],
        "offset": offset,
        "limit": limit,
        "total": questions["count"],
    }

    if request.headers.get("HX-Request"):
        return render(request, "partials/question_items.html", context)

    return render(request, "pages/home.html", context)


def question(request, question_id):
    if not request.user.is_authenticated:
        request.session["next_question_id"] = question_id
        return redirect("account_login")

    question_data = fetch_question(question_id, request.user)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "check":
            return handle_check_action(request, question_data)
        if action == "generate":
            return handle_generate_action(request, question_data)

        if action == "next":
            response = fetch_question(int(question_id) + 1)
            next_id = int(question_id) + 1
            response = fetch_question(next_id)
            if response.get("error"):
                return render(
                    request,
                    "partials/error.html",
                    {
                        "message": f"No more questions, ID of {next_id} not found",
                        "status_code": 404,
                    },
                    status=404,
                )

            return redirect("math_quiz:question", question_id=str(response["Id"]))
    return render(request, "pages/question.html", {"question": question_data})
