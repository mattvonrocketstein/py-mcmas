""" """

import os

import mcmas

LOGGER = mcmas.util.get_logger(__name__)

# Dummy keys for Ollama
os.environ["OPENAI_API_KEY"] = "ollama"
os.environ["OPENAI_BASE_URL"] = "http://fake:11434/v1"

from agents import Agent

charlie = Agent(name="chuck")


def test_openai_agents():
    assert charlie in mcmas.ai.Society.openai, "failed to detect openai agent"


def test_tags():
    b = mcmas.ctx.agent_builder
    b.add_tag(charlie, vars=dict(card1="a q k".split()))
    assert "vars" in b[charlie]
