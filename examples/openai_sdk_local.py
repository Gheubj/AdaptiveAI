"""Official OpenAI SDK against AdaptiveAI's intentionally small local API subset."""

from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8088/v1", api_key="local-placeholder")
response = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Reply with exactly: ready"}],
    extra_body={"routing_mode": "auto", "provider_scope": "hybrid", "local_only": False},
)
print(response.choices[0].message.content)
