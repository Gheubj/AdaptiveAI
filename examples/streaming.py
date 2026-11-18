from adaptiveai.client import AdaptiveAIClient

client = AdaptiveAIClient()
for event in client.stream("Explain local LLM routing briefly.", routing_mode="balanced"):
    for choice in event.get("choices", []):
        print(choice.get("delta", {}).get("content", ""), end="", flush=True)
print()
