"""One thin wrapper around the model call.

A model does exactly one thing: text in, text out. Everything else
in this repo is scaffolding around that fact.
"""

import os

import anthropic

MODEL = os.environ.get("CANARY_MODEL", "claude-sonnet-4-5")
client = anthropic.Anthropic()

# Counters, so the cost of each approach is visible on screen.
CALLS = 0
TOKENS_IN = 0
TOKENS_OUT = 0


def ask(messages, tools=None, system=None, max_tokens=1024):
    """Send messages to the model. Return the raw response."""
    global CALLS, TOKENS_IN, TOKENS_OUT
    kwargs = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if tools:
        kwargs["tools"] = tools
    if system:
        kwargs["system"] = system

    response = client.messages.create(**kwargs)

    CALLS += 1
    TOKENS_IN += response.usage.input_tokens
    TOKENS_OUT += response.usage.output_tokens
    return response


def text_of(response):
    """Pull the plain text out of a response."""
    return "".join(b.text for b in response.content if b.type == "text")


def report(label, seconds):
    print(
        f"\n  {label}: {CALLS} model calls | "
        f"{TOKENS_IN + TOKENS_OUT} tokens | {seconds:.1f}s"
    )
