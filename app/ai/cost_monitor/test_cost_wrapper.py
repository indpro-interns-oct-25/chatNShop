from app.ai.cost_monitor.openai_cost_wrapper import CostAwareOpenAIClient

client = CostAwareOpenAIClient(api_key="dummy-key", model_name="gpt-4o-mini")
response = client.complete({"messages": [{"role": "user", "content": "hello"}]})
print(response)

