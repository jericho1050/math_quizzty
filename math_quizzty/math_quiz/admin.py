from django.contrib import admin

from math_quizzty.math_quiz.models import Option
from math_quizzty.math_quiz.models import Question
from math_quizzty.math_quiz.models import Tag

admin.site.register(Option)
admin.site.register(Question)
admin.site.register(Tag)
