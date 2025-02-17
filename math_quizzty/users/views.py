from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView

from math_quizzty.math_quiz.models import Question
from math_quizzty.users.models import User


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offset = int(self.request.GET.get("offset", 0))
        limit = 10

        questions = Question.objects.filter(user=self.request.user)[
            offset : offset + limit
        ]
        total = Question.objects.filter(user=self.request.user).count()

        user_questions = [question.to_dict() for question in questions]
        context.update(
            {
                "user_questions": user_questions,
                "offset": offset,
                "limit": limit,
                "total": total,
            }
        )

        if self.request.headers.get("HX-Request"):
            return context

        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("HX-Request"):
            return render(
                self.request,
                "partials/user_question_items.html",
                context,
                **response_kwargs,
            )
        return super().render_to_response(context, **response_kwargs)


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()


def custom_login_redirect(request):
    # Check if there's a stored question_id
    next_question_id = request.session.pop("next_question_id", None)
    if next_question_id:
        return redirect("math_quiz:question", question_id=next_question_id)
    return redirect("math_quiz:home")  # Default redirect

