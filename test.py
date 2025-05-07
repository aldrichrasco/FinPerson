import openai

openai.api_key = "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"

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello, how are you?"}]
)

print(response["choices"][0]["message"]["content"])


export OPENAI_API_KEY="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"