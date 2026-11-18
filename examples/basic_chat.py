from adaptiveai.client import AdaptiveAIClient

client = AdaptiveAIClient()
response = client.chat("Return only the integer: 2 + 2", routing_mode="fastest")
print(response["choices"][0]["message"]["content"])
print(response["routing"])
