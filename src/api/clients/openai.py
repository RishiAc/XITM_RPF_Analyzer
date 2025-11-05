from openai import OpenAI

client = OpenAI()

def get_chat_completion(system_message, user_prompt, response_format):

    completion = client.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ],
        response_format=response_format
    )

    event = completion.choices[0].message.parsed

    return event