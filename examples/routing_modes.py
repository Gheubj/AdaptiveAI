from adaptiveai.client import AdaptiveAIClient

client = AdaptiveAIClient()
for mode in ("fastest", "quality", "balanced", "hardware-aware"):
    response = client.chat("Reply with the word ready.", routing_mode=mode)
    print(mode, response["model"], response["routing"]["reason"])
