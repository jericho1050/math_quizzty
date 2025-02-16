import uuid

from django.conf import settings
from django.db import models


# Create your views here.
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]
    question = models.TextField()
    solution = models.TextField()
    correct_answer = models.CharField(max_length=255)
    image_url = models.URLField(blank=True, null=True)  # noqa: DJ001
    tags = models.ManyToManyField("Tag", related_name="questions", blank=True)
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default="easy",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_questions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.question[:50]

    def to_dict(self):
        """Serialize the question instance to a dictionary"""
        return {
            "Id": str(self.id),
            "Question": self.question,
            "Options": [opt.option_text for opt in self.options.all()],
            "CorrectAnswer": self.correct_answer,
            "Solution": self.solution,
            "Steps": [
                {
                    "Title": step.title,
                    "Result": step.result,
                    "ImageUrl": step.image_url if hasattr(step, "image_url") else None,
                }
                for step in self.steps.all()
            ],
            "Tags": [{"name": tag.name} for tag in self.tags.all()],
        }


class Option(models.Model):
    question = models.ForeignKey(
        "Question",
        related_name="options",
        on_delete=models.CASCADE,
    )
    option_text = models.CharField(max_length=255)

    def __str__(self):
        return self.option_text


class SolutionStep(models.Model):
    question = models.ForeignKey(
        Question,
        related_name="steps",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    result = models.TextField()
    image_url = models.URLField(blank=True, null=True)  # noqa: DJ001
    step_number = models.PositiveIntegerField()

    class Meta:
        ordering = ["step_number"]

    def __str__(self):
        return f"{self.title} - {self.question}"
