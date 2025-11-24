from openai import OpenAI

client = OpenAI()

# TODO: fix error when adding temperature and max_tokens

def get_chat_completion(system_message, user_prompt, response_format):

    completion = client.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ],
        response_format=response_format,
        # temperature=0.2,
        # max_tokens=10000
    )

    event = completion.choices[0].message.parsed

    return event