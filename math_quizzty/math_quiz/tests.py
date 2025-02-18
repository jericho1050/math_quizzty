import json
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.utils.text import slugify

from math_quizzty.math_quiz.helpers import generate_math_question
from math_quizzty.math_quiz.helpers import paraphrase_math_question
from math_quizzty.math_quiz.helpers import verify_math_question
from math_quizzty.math_quiz.models import Option
from math_quizzty.math_quiz.models import Question
from math_quizzty.math_quiz.models import SolutionStep
from math_quizzty.math_quiz.models import Tag

User = get_user_model()

from django_htmx.http import replace_url  # noqa: E402


@pytest.mark.django_db
class TestHelpers:
    def test_generate_math_question(self):
        mock_response = {
            "choices": [{"message": {"content": json.dumps({"question": "2+2=?"})}}],
        }

        with patch("openai.ChatCompletion.create") as mock_create:  # changed
            mock_create.return_value.choices = [mock_response["choices"][0]]
            result = generate_math_question("Generate a math question")
            assert isinstance(result, dict)
            assert "question" in result

    def test_paraphrase_math_question(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = {
                "body": json.dumps({"paraphrased": "What is the sum of 2 and 2?"}),
            }
            mock_post.return_value.raise_for_status.return_value = None

            result = paraphrase_math_question(json.dumps({"question": "2+2=?"}))
            assert isinstance(result, dict)
            assert "paraphrased" in result

    def test_verify_math_question(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = {
                "body": json.dumps({"is_correct": True}),
            }
            mock_post.return_value.raise_for_status.return_value = None

            result = verify_math_question(json.dumps({"question": "2+2=4"}))
            assert isinstance(result, dict)
            assert result.get("is_correct") is True

    def _handle_generate_action(self, request, base_question):
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

        # Extract custom fields from data and map them to the Question model
        question_text = data.pop("question", "")  # "question" field in the data
        solution_text = data.pop("explanation", "")  # map "explanation" → "solution"
        # "title" is extra text you might want to prepend or ignore
        title = data.pop("title", "")  # an extra field from the test dictionary

        # If you want to store "title" inside question:
        if title and not question_text:
            question_text = title

        # If you have "correct_answer" in the data, keep it. Otherwise, default to blank
        correct_answer = data.pop("correct_answer", "")

        # Create the question in the DB
        question_data = Question.objects.create(
            question=question_text,
            solution=solution_text,
            correct_answer=correct_answer,
            user=request.user,
            # If you have other valid fields in `data`, handle them, or remove them.
            **{k: v for k, v in data.items() if k in ["difficulty", "image_url"]},
        )

        # Handle related models
        options_data = data.pop("options", [])
        steps_data = data.pop("steps", [])
        tags_data = data.pop("tags", [])

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
