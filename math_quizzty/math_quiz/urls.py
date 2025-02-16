from django.urls import path

from math_quizzty.math_quiz.views import index
from math_quizzty.math_quiz.views import question

app_name = "math_quiz"
urlpatterns = [
    path("", index, name="home"),
    path("question/<str:question_id>", question, name="question"),
]
