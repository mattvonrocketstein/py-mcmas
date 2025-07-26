""" """

import typing

import mcmas
from mcmas import ai
from mcmas.ai import ollama
from mcmas.ispl import Agent as AgentSpec

import pydantic_ai

# from mcmas.tests.fixtures import global_env
LOGGER = mcmas.util.get_logger(__name__)

weather_agent = pydantic_ai.Agent(
    name="weather_agent",
)


# declare agent tools as usual
@weather_agent.tool
async def get_weather(ctx, lat: float, lng: float) -> dict[str, typing.Any]:  # noqa
    """Get the weather at a location.
    Args:
        ctx: The context.
        lat: Latitude of the location.
        lng: Longitude of the location.
    """
    temp_response, descr_response = "fake", "response"
    return {
        "temperature": f"{temp_response.text} °C",
        "description": descr_response.text,
    }


def test_agent_completion():
    tmp = ai.agent_completion(get_weather, max_retries=5)
    assert tmp.advice == []
    # import IPython; IPython.embed(confirm_exit=False,)


def test_main():
    LOGGER.warning(f"ollama models: {ollama.list()}")
    agent = ai.model_completion(
        query=(
            "Suppose that there is a game with 2 players called Alice and Bob.  "
            "Available actions are to call, fold, or hold.  "
            "Alice can see if her cards are green or black. "
        ),
        schema=AgentSpec,
    )
    data = agent.model_dump()
    data_dumped = agent.model_dump_json(indent=2)
    LOGGER.info(f"\n{data_dumped}\n")
    spec = AgentSpec(**data)
    LOGGER.info(f"\n{spec.model_dump_json(indent=2)}\n")
    LOGGER.info(f"\nAgent decoded {spec}\n\n")
    LOGGER.critical([spec.advice])


# def test_pydantic_agent_completion():  # noqa
#     society = ai.Society(pydantic_ai)
#     spec = society.get_spec(alice)
#     bspec = society.get_spec(bob)
#     assert type(spec) == mcmas.ispl.Agent
#     assert "tool1" in spec.actions
#     assert "tool2" in bspec.actions
#     assert not bspec.concrete
#     assert len(bspec.advice) > 0

if __name__ == "__main__":
    # test_main()
    test_agent_completion()
