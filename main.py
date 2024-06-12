import os
from dotenv import load_dotenv
load_dotenv()

import discord

app_token = os.getenv('DISCORD_APP_TOKEN')
intents = discord.Intents.all()
# intents.messages = True
client = discord.Client(intents=intents)

from openai import OpenAI
gpt_client = OpenAI(api_key = os.getenv('OPENAI_KEY'))

error_message = ''
system_prompts = ['<empty>'] * 10
system_prompt = ''
system_counter = 0

import re
from zhconv import convert

def message_to_json(message):
    content = re.sub('<.+>', '', message.content)
    if message.author == client.user:
        return {'role': 'assistant', 'content': content}
    else:
        return {'role': 'user', 'content': content}


async def get_chat_history(message):
    messages = []
    messages.append(message_to_json(message))
    while message.reference is not None:
        try:
            if message.reference.cached_message is None:
                channel = (client.get_channel_or_thread(
                    message.reference.channel_id) or await
                           client.fetch_channel(message.reference.channel_id))
                message = await channel.fetch_message(
                    message.reference.message_id)
            else:
                message = message.reference.cached_message
            messages.append(message_to_json(message))
        except Exception as e:
            print(e)
            break
    # print(system_prompt)
    # print(system_counter)
    messages.append({'role': 'system', 'content': system_prompt})
    messages.reverse()
    print(messages)
    return messages


@client.event
async def on_message(message):
    global system_prompt
    global system_counter
    global error_message

    if message.author == client.user:
        return

    content = re.sub('<.+>', '', message.content)
    print(content)

    if content.split()[0] == 'set_error_message':
        try:
            error_message = content.split()[1]
            print(content)
        except Exception as e:
            print(e)
        return

    if content.split()[0] == 'set_system_prompt':
        try:
            if content.split()[1].isnumeric():
                system_counter = int(content.split()[1]) % 10
            else:
                system_prompts[(system_counter + 1) % 10] = content[content.index('set_system_prompt') + len('set_system_prompt'):].strip()
                print(content)
                system_counter += 1
        except Exception as e:
            print(e)
        system_prompt = system_prompts[system_counter]
        return
    
    if content.split()[0] == 'get_system_prompt':
        try:
            answer = 'system prompts:\n'
            for i in range(10):
                answer += str(i) + '. ' + system_prompts[i] + '\n'
                print(answer)
                await message.reply(answer)
        except Exception as e:
            print(e)
        return

    if client.user in message.mentions:
        messages = await get_chat_history(message)
        answer = ''
        try:
            completion = gpt_client.chat.completions.create(model="gpt-3.5-turbo-0125",
                                                            messages=messages,
                                                            max_tokens=1000)
            print(completion)
            answer = completion.choices[0].message.content
            answer = convert(answer, 'zh-tw')
            print(answer)
        except Exception as e:
            print(e)
            answer = error_message
        await message.reply(answer)


if __name__ == '__main__':
    client.run(app_token)
