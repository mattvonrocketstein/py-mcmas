"""
mcmas.ctx.
"""

import inspect
import typing

import pydantic

import mcmas
from mcmas import util

LOGGER = util.get_logger(__name__)


def patch_pydantic():
    """
    Patches current and future pydantic_ai.Agent instances to
    have an additional `specification` attribute, which resolves
    to a `mcmas.ispl.Agent`.
    """
    LOGGER.warning("patching pydantic agent")
    pydantic_ai = get_pydantic_ai()
    if pydantic_ai:
        pydantic_ai.Agent.specification = property(
            lambda self: mcmas.ispl.Agent(**agent_builder[self])
        )
        oinit = pydantic_ai.Agent.__init__
        otool = pydantic_ai.Agent.tool

        def agent_data(obj):
            return {
                "actions": ["none"],
                "metadata": {"file": inspect.getfile(obj.__class__)},
            }

        def init(self, *args, **kwargs):
            LOGGER.warning("running patched init")
            oinit(self, *args, **kwargs)
            agent_builder.add_tag(self, **agent_data(self))

        def tool(self, fxn, *args, **kwargs):
            out = otool(self, fxn, *args, **kwargs)
            agent_builder.add_tag(
                self,
                **{
                    **agent_data(self),
                    **{
                        "actions": agent_builder[self].get("actions", [])
                        + [f"{fxn.__name__}"],
                    },
                },
            )
            # raise Exception([args,kwargs])
            return out

        LOGGER.warning(f"patching class: {pydantic_ai.Agent}")
        pydantic_ai.Agent.__init__ = init
        pydantic_ai.Agent.tool = tool

        for obj in util.find_instances(pydantic_ai.Agent):
            LOGGER.warning(f"patching {obj}")
            obj.__init__ = init
            obj.tool = tool
            agent_builder.add_tag(obj)
            agent_builder.add_tag(
                obj,
                **{
                    **agent_data(obj),
                    **{
                        "actions": agent_builder[obj].get("actions", [])
                        + list(obj._function_toolset.tools.keys()),
                    },
                },
            )


class ModelBuilder:
    """
    
    """

    def __init__(self):
        self.TAGS = {}

    @property
    def wrapping(self):
        from mcmas.models import Agent

        return Agent

    def __call__(self, obj: typing.Any, **data) -> typing.Any:
        """
        
        """
        LOGGER.warning(f"updating {obj} with {data}")
        key = self.key_for(obj)
        orig = self.TAGS.get(key, {})
        orig.update(**data)
        self.TAGS[key] = orig
        return self.wrapping(**orig)

    @pydantic.validate_call
    def key_for(self, obj: typing.Any) -> str:
        """
        
        """
        skey = getattr(obj, "name", str(obj))
        key = f"{obj.__class__.__module__}.{obj.__class__.__name__}.{skey}"
        return key

    @pydantic.validate_call
    def __getitem__(self, other) -> typing.Dict:
        return self.TAGS.get(self.key_for(other), {})

    @pydantic.validate_call
    def __setitem__(self, obj, val: typing.Dict) -> typing.Any:
        return self.add_tag(self.key_for(obj), **val)

    def add_tag(self, obj, **tags) -> typing.Any:
        """
        
        """
        LOGGER.warning(f"tagging {obj}")
        # skey = getattr(obj, 'name', str(obj))
        key = self.key_for(obj)
        # f"{obj.__class__.__module__}.{obj.__class__.__name__}.{skey}"
        _tags = self.TAGS.get(key, {})
        _tags.update(**tags)
        self.TAGS[key] = _tags
        # .setdefault(key, {}).update(**tag)
        LOGGER.warning(f"tagged {obj} with {_tags}")

        return obj


agent_builder = ModelBuilder()


def get_pydantic_ai():
    try:
        import pydantic_ai

        return pydantic_ai
    except (ImportError,):
        LOGGER.critical(
            "`pydantic_ai` module not available.  "
            "pip install py-mcmas[ai] or pydantic-ai"
        )
        return None
