import random
from types import SimpleNamespace
import asyncio
from openai import AsyncOpenAI
import os

class Agent:
    def __init__(self, name, instructions, tools=None):
        self.name = name
        self.instructions = instructions
        self.tools = tools or []

class Runner:
    @staticmethod
    def run_streamed(agent, input, name):
        async def stream_events():
            from asyncio import sleep
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("❌ Open AI API key not set")
                # Fallback response
                yield SimpleNamespace(
                    type="run_item_stream_event",
                    item=SimpleNamespace(
                        type="message_output_item",
                        text="Error: Open AI API key not configured."
                    )
                )
                return

            client = AsyncOpenAI(api_key=api_key)
            print(f"Calling Open AI API with input: {input}")
            try:
                stream = await client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"You are JokeBot, a humorous chatbot. Respond playfully and include a joke if appropriate. Personalize replies with the user's name: {name}."},
                        {"role": "user", "content": input}
                    ],
                    stream=True
                )
                async for chunk in stream:
                    content = chunk.choices[0].delta.content or ""
                    if content:
                        print(f"Streaming chunk: {content}")
                        yield SimpleNamespace(
                            type="run_item_stream_event",
                            item=SimpleNamespace(
                                type="message_output_item",
                                text=content
                            )
                        )
                        await sleep(0.1)  # Maintain streaming effect
            except Exception as e:
                print(f"Open AI API error: {str(e)}")
                error_msg = "Sorry, I couldn't generate a response. Here's a joke instead: Why did the tomato turn red? It saw the salad dressing! 😎"
                for word in error_msg.split():
                    yield SimpleNamespace(
                        type="run_item_stream_event",
                        item=SimpleNamespace(
                            type="message_output_item",
                            text=word + " "
                        )
                    )
                    await sleep(0.1)
        return SimpleNamespace(stream_events=stream_events)

class ItemHelpers:
    @staticmethod
    def text_message_output(item):
        return getattr(item, "text", "")