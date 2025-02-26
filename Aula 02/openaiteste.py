from openai import OpenAI
client = OpenAI()
completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Você é uma vendedora de pastel eficiente"},
        {"role": "user", "content": "Me indique os melhores pasteis para hoje!"}
    ]
)

print(completion.choices[0].message.content)