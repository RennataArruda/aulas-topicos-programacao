from groq import Groq

client = Groq()

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "Você é um especialista em saúde animal. Ajude os usuários a tratarem bem seus animais de estimação"
        },
        {
            "role": "user",
            "content": "Meu cachorro está comendo muito e está engordando. O que eu faço? Responda em português.",
        }
    ],

    model="deepseek-r1-distill-qwen-32b",
    temperature=0.5,
    max_completion_tokens=1024,
    top_p=1,
    stop=None,
    stream=False,
)

print(chat_completion.choices[0].message.content)