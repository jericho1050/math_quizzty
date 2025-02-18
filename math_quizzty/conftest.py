import pytest
from django.test import RequestFactory

from math_quizzty.users.models import User
from math_quizzty.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def sample_question():
    return {
        "Id": "1",
        "title": "Test Question",
        "content": "What is 2+2?",
        "correct_answer": "4",
        "options": ["2", "3", "4", "5"],
        "explanation": "Basic addition",
        "steps": [{"step": 1, "content": "Add numbers"}],
        "tags": [{"name": "math"}],
    }
