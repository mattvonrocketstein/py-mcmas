"""

"""

import re

from mcmas import util

LOGGER = util.get_logger(__name__)


def extract_block(
    text: str,
    pattern=None,
    block_start: str = "^Agent",
    block_end: str = r"end\s+Agent\b",
    name=None,
    value_only: bool = False,
) -> dict:
    """
    Extract ...
    """
    if not pattern:
        pattern = block_start + r"\s+(\w+)\s*\n(.*?)^\s*" + block_end
    pattern = re.compile(pattern, re.MULTILINE | re.DOTALL)
    out = {}
    block = ""
    for match in pattern.finditer(text):
        name = match.group(1) if name is None else name
        block = match.group(2) if name is None else match.group(1)
        # Split into lines, strip trailing newline
        # lines = [line.rstrip() for line in block.strip('\n').splitlines()]
        out[name] = block  # lines
    if value_only:
        return block
    else:
        return out


def normalize(x):
    """
    Extract ...
    """
    return re.sub(r" +", " ", x)


# def extract_formula(txt: str, section="Formulae") -> list:
#     return extract_toplevel(txt, section=section)


def extract_toplevel(txt: str, section="Formulae") -> list:
    """
    Extract ...
    """
    pattern = re.compile(
        r"^" + section + r"\s*\n(.*?)^\s*end\s+" + section + r"\b",
        re.MULTILINE | re.DOTALL,
    )
    for match in pattern.finditer(txt):
        if match:
            return [
                normalize(x.strip()).replace("\n", "")
                for x in match.group(1).split(";")
                if x.strip()
            ]


def extract_agents(txt: str) -> dict:
    """
    Extract ...
    """
    pattern = re.compile(
        r"^Agent\s+(\w+)\s*\n(.*?)^\s*end\s+Agent\b", re.MULTILINE | re.DOTALL
    )
    agents = {}
    for match in pattern.finditer(txt):
        name = match.group(1)
        block = match.group(2)
        # Split into lines, strip trailing newline
        [line.rstrip() for line in block.strip("\n").splitlines()]
        agents[name] = block  # lines

    for agent in agents:
        path = [agent]
        block = agents[agent]
        agents[agent] = {}
        LOGGER.critical(f"parsing agent={agent}")
        for sub in ["Lobsvars", "Actions"]:
            section = sub.lower()
            path += [sub]
            pattern = rf"\s*{sub}\s*" + r"=\s*\{([\s\S]*?)\};"
            pattern = re.compile(pattern, re.MULTILINE | re.DOTALL)
            match = re.search(pattern, block)
            if match:
                sub_block = match.group(1).strip()
            else:
                sub_block = ""
            sub_block = normalize(sub_block)
            if agent.lower() == "child1" and section == "actions":
                pass
            agents[agent][section] = sub_block

        for sub in ["Protocol", "Vars", "Obsvars", "Evolution"]:
            section = sub.lower()
            if all(
                [
                    sub in ["Obsvars"],
                    agent not in ["Environment", "environment"],
                ]
            ):
                continue
            path += [sub]
            sub_block = extract_block(
                block,
                name=sub,
                pattern=rf"{sub}:\s*\n(.*?)^\s*end\s+{sub}\b",
                value_only=True,
            )
            sub_block = sub_block.replace("\t", "")
            sub_block = "\n".join(
                [
                    line
                    for line in sub_block.split("\n")
                    if not line.lstrip().startswith("--")
                ]
            )
            # sub_block = sub_block.replace("\n", "")
            sub_block = normalize(sub_block)
            sub_block = sub_block.split(";")
            agents[agent][section] = [x.strip() for x in sub_block if x.strip()]
            if not agents[agent][section]:
                if all([agent in ["environment", "Environment"], section == "obsvars"]):
                    LOGGER.info("skipping section {agent}.{section}, expected missing")
                else:
                    LOGGER.warning(
                        f"could not extract {agent}.{section} from block:\n{block}\n\n{sub_block}"
                    )
            path.pop(-1)
    return agents


# @validate_call
def parser(txt, strict=False, file: str = None):
    """NB: fname is purely informational, only txt is used."""
    # from mcmas import models
    from mcmas import ispl as ns

    # ns = models if not strict else models.strict
    tmp = txt.lstrip().split("\n")
    tmp = tmp and tmp[0]
    tmp = tmp.startswith("--") and tmp.replace("--", "").lstrip().strip()
    title = tmp if tmp else "untitled spec"
    # txt.strip().startswith('--')
    agents = extract_agents(txt)
    # raise Exception(agents)
    # assert "Environment" in agents
    environment = agents.pop("Environment", {})
    ns.Environment(**environment)
    agents = {k: ns.Agent(**v) for k, v in agents.items()}
    return ns.ISPL(
        metadata={"file": file, "parser": f"{__name__}"},
        title=title,
        environment=environment,
        agents=agents,
        formulae=extract_toplevel(txt, section="Formulae"),
        groups=extract_toplevel(txt, section="Groups"),
        evaluation=extract_toplevel(txt, section="Evaluation"),
        init_states=extract_toplevel(txt, section="InitStates"),
    )


parse = parser
