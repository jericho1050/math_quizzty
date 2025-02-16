import json
import uuid

import environ
import requests
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils.text import slugify
from django_htmx.http import replace_url
from openai import OpenAI

from .models import Option
from .models import Question
from .models import SolutionStep
from .models import Tag

env = environ.Env()
BASE_URL = env.str("DJANGO_QUESTIONS_URL")


DO_MATH_QUESTION_GENERATOR_AGENT_KEY = env.str("DO_MATH_QUESTION_GENERATOR_AGENT_KEY")
DO_MATH_QUESTION_GENERATOR_URL = env.str("DO_MATH_QUESTION_GENERATOR_URL") + "/api/v1"
DO_MATH_QUESTION_PARAPHRASER_URL = env.str("DO_MATH_QUESTION_PARAPHRASER_URL")
DO_MATH_QUESTION_VERIFIER_URL = env.str("DO_MATH_QUESTION_VERIFIER_URL")
DO_PERSONAL_ACCESS_TOKEN = env.str("DO_PERSONAL_ACCESS_TOKEN")


def generate_math_question(prompt: str) -> str:
    """Generate a math question using OpenAI."""

    client = OpenAI(
        base_url=DO_MATH_QUESTION_GENERATOR_URL,
        api_key=DO_MATH_QUESTION_GENERATOR_AGENT_KEY,
    )
    response = client.chat.completions.create(
        model="n/a",
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(response.choices[0].message.content)


def paraphrase_math_question(prompt: str) -> dict:
    """Paraphrase a math question using the external service."""

    if not DO_PERSONAL_ACCESS_TOKEN:
        msg = "DO_PERSONAL_ACCESS_TOKEN is not set in environment variables"
        raise ValueError(msg)

    url = DO_MATH_QUESTION_PARAPHRASER_URL

    # Query parameters
    params = {
        "blocking": "true",
        "result": "true",
    }

    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {DO_PERSONAL_ACCESS_TOKEN}",
    }

    try:
        payload = {"body": prompt}
        response = requests.post(
            url,
            params=params,
            headers=headers,
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        return json.loads(response.json()["body"])

    except requests.exceptions.RequestException as e:
        print(f"Error: {str(e)}")  # noqa: RUF010, T201
        return {
            "error": True,
            "message": str(e),
            "details": {
                "type": type(e).__name__,
                "url": url,
            },
        }


def verify_math_question(prompt: str) -> dict:
    """Verify a math question using the external service."""

    if not DO_PERSONAL_ACCESS_TOKEN:
        msg = "DO_PERSONAL_ACCESS_TOKEN is not set in environment variables"
        raise ValueError(msg)

    url = DO_MATH_QUESTION_VERIFIER_URL

    # Query parameters
    params = {"blocking": "true", "result": "true"}

    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {DO_PERSONAL_ACCESS_TOKEN}",
    }

    try:
        payload = {"body": prompt}
        response = requests.post(
            url,
            params=params,
            headers=headers,
            json=payload,
            timeout=20,
        )
        print("invoked verifier math", response.json())
        response.raise_for_status()
        return json.loads(response.json()["body"])
    except requests.exceptions.RequestException as e:
        print(f"Error: {str(e)}")  # noqa: RUF010, T201
        return {
            "error": True,
            "message": str(e),
            "details": {"type": type(e).__name__, "url": url},
        }


def _fetch_question(question_id, user=None):
    """Fetch a question from external API or local database."""
    try:
        response = requests.get(f"{BASE_URL}/question/{question_id}", timeout=10)
        if response.status_code >= 400:  # noqa: PLR2004
            # Try local database
            try:
                question_obj = get_object_or_404(Question, id=question_id)
                return question_obj.to_dict()
            except Http404:
                # If not found in either external API or local DB
                return {
                    "error": True,
                    "message": f"Question {question_id} not found",
                    "status_code": 404,
                }
        return response.json()
    except requests.RequestException as e:
        return {
            "error": True,
            "message": f"Failed to fetch question: {str(e)}",
            "status_code": 500,
        }


def _handle_check_action(request, question):
    """Handle the check answer action."""

    selected_answer = request.POST.get("selected_answer")
    is_uuid = False

    try:
        uuid.UUID(str(question["Id"]))
        is_uuid = True
    except (ValueError, AttributeError, TypeError):
        is_uuid = False

    return render(
        request,
        "partials/explanation.html",
        {
            "question": question,
            "selected_answer": selected_answer,
            "is_generated_question": is_uuid,
        },
    )


def _handle_generate_action(request, base_question):
    """Handle the generate new question action."""
    generated_question = generate_math_question(json.dumps(base_question))
    data = paraphrase_math_question(json.dumps(generated_question))
    verify_response = verify_math_question(json.dumps(data))
    if not verify_response or not verify_response.get("is_correct"):
        return render(
            request,
            "partials/error.html",
            {
                "message": "Unable to generate a valid question. Please try again.",
                "details": verify_response.get("message", "Verification failed"),
            },
        )
    options_data = data.pop("options", [])
    steps_data = data.pop("steps", [])
    tags_data = data.pop("tags", [])
    question_data = Question.objects.create(**data, user=request.user)
    for option_text in options_data:
        Option.objects.create(question=question_data, option_text=option_text)
    for step in steps_data:
        SolutionStep.objects.create(question=question_data, **step)
    tags_objects = []
    for tag_info in tags_data:
        name = tag_info.get("name")
        if name:
            tag_obj, _ = Tag.objects.get_or_create(
                name=name,
                defaults={"slug": slugify(name)},
            )
            tags_objects.append(tag_obj)
    question_data.tags.set(tags_objects)
    response = render(
        request,
        "pages/question.html",
        {"question": question_data.to_dict()},
    )
    return replace_url(response, f"/question/{question_data.id}")


if __name__ == "__main__":
    pass
