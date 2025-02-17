from django.urls import path

from math_quizzty.math_quiz.views import delete_question
from math_quizzty.math_quiz.views import index
from math_quizzty.math_quiz.views import question

app_name = "math_quiz"
urlpatterns = [
    path("", index, name="home"),
    path("question/<str:question_id>", question, name="question"),
    path(
        "question/<uuid:question_id>/delete/",
        delete_question,
        name="delete_question",
    ),
]
