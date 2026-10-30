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

# Every call, not just the total. The whole point of episode 2 is that
# calls are not the same size as each other -- the API is stateless, so
# each one carries every turn before it.
CALL_LOG = []        # list of (call_number, input_tokens, output_tokens)


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
    CALL_LOG.append((CALLS, response.usage.input_tokens,
                     response.usage.output_tokens))
    return response


def last_call():
    """(input_tokens, output_tokens) for the most recent call."""
    return (CALL_LOG[-1][1], CALL_LOG[-1][2]) if CALL_LOG else (0, 0)


def text_of(response):
    """Pull the plain text out of a response."""
    return "".join(b.text for b in response.content if b.type == "text")


def report(label, seconds):
    print(
        f"\n  {label}: {CALLS} model calls | "
        f"{TOKENS_IN + TOKENS_OUT} tokens | {seconds:.1f}s"
    )


def growth():
    """What the first call cost, what the last one cost, and the ratio.

    If the loop were simply N calls, these would match.
    """
    if len(CALL_LOG) < 2:
        return ""
    first, last = CALL_LOG[0][1], CALL_LOG[-1][1]
    return (f"  first call {first:,} in  ->  last call {last:,} in"
            f"   ({last / first:.1f}x)")
