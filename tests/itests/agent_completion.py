""" """

import typing

import mcmas
from mcmas import ai, ispl
from mcmas.ai import ollama

import pydantic_ai

# from mcmas.ispl import Agent as AgentSpec
# import IPython; IPython.embed(confirm_exit=False)


# download model if necessary
ai.init()


LOGGER = mcmas.util.get_logger(__name__)

weather_agent = pydantic_ai.Agent(
    name="weather_agent",
)


# Declare agent tools as usual
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
    agent = ai.agent_completion(get_weather, max_retries=5)
    assert isinstance(
        agent, (ispl.Agent,)
    ), "expected completion of agent would be agent!"
    assert not agent.advice, "agent does not validate"


def test_model_completion():
    LOGGER.warning(f"ollama models: {ollama.list()}")
    agent = ai.model_completion(
        query=(
            "Suppose that there is a game with 2 players called Alice and Bob.  "
            "Available actions are to call, fold, or hold.  "
            "Alice can see if her cards are green or black. "
        ),
        schema=ispl.Agent,
    )
    data = agent.model_dump()
    data_dumped = agent.model_dump_json(indent=2)
    LOGGER.info(f"\n{data_dumped}\n")
    spec = ispl.Agent(**data)
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
