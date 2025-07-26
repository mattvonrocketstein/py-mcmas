from mcmas import ISPL, Agent, engine
from mcmas.util import get_logger

LOGGER = get_logger(__name__)

# from mcmas import engine, examples, transforms, ispl
# data_dir = Path(__file__).parent.parent / "data"
# with open(str(data_dir/'muddy_children.json'),'r') as fhandle:
#     json_data = fhandle.read()


def test_class2ispl():
    spec = ISPL(
        agents=dict(
            player1=Agent(
                vars=dict(step="{s1, s2, s3, s4}"),
                actions="{keep, swap, distribute, check, reset};",
                protocol=[
                    "step=s1: {distribute};",
                    "step=s2: {keep,swap};",
                    "step=s3: {check};",
                    "step=s4: {reset};",
                ],
                evolution=[
                    "step=s2 if step=s1;",
                    "step=s3 if step=s2;",
                    "step=s4 if step=s3;",
                    "step=s1 if step=s4 and Environment.win=false;",
                ],
            )
        )
    )
    validates = engine.validate(model=spec)
    assert not validates  # == False
    # print(model.model_dump_source())
