import json

import environ
import requests
from openai import OpenAI

env = environ.Env()

DO_MATH_QUESTION_GENERATOR_AGENT_KEY = env.str("DO_MATH_QUESTION_GENERATOR_AGENT_KEY")
DO_MATH_QUESTION_GENERATOR_URL = env.str("DO_MATH_QUESTION_GENERATOR_URL") + "/api/v1"
DO_MATH_QUESTION_PARAPHRASER_URL = env.str("DO_MATH_QUESTION_PARAPHRASER_URL")
DO_MATH_QUESTION_VERIFIER_URL = env.str("DO_MATH_QUESTION_VERIFIER_URL")
DO_PERSONAL_ACCESS_TOKEN = env.str("DO_PERSONAL_ACCESS_TOKEN")


def generate_math_question(prompt: str) -> str:
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
        print("invoked paraphraser math", response.json())
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


if __name__ == "__main__":
    pass
