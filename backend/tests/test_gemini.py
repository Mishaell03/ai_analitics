
import os
from google import genai

api_key = "AIzaSyAvAzNSmVsATjvrK83tN4nzHF0SuYEi1ro"

if not api_key:
    raise SystemExit("Ошибка: GEMINI_API_KEY не задан")

try:
    client = genai.Client(api_key=api_key)

    print("Отправляю запрос Gemini...")

    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input="hi"
    )

    print("Ответ:", interaction.output_text)
    print("ID запроса:", interaction.id)

except Exception as e:
    print(f"Ошибка: {type(e).__name__}: {e}")
