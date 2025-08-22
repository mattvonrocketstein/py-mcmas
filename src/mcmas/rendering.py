"""
mcmas.rendering.
"""

import functools
import os
from pathlib import Path

import jinja2
import pydantic

from mcmas.util import lme, typing

LOGGER = lme.get_logger(__name__)


INCLUDES = Path(__file__).parents[0] / "templates"
INCLUDES = (
    # INCLUDES / "types",
    # INCLUDES / "sub",
    INCLUDES,
    # / "top",
)
for x in INCLUDES:
    assert x.exists()


def get_jinja_includes(*includes) -> typing.List[Path]:
    """
    
    """
    includes = list(includes)
    includes += list(INCLUDES)
    return [Path(t) for t in includes]


# def get_jinja_env():
#     includes = get_jinja_includes()
#     env = Environment(
#         loader=FileSystemLoader([str(t) for t in includes]),
#         undefined=StrictUndefined,
#         # trim_blocks=True,
#         # lstrip_blocks=True
#     )
#     env.filters.update(**get_jinja_filters())
#     # env.pynchon_includes = includes

#     env.globals.update(
#         # include=include_template,
#         **get_jinja_globals())

#     known_templates = list(map(Path, set(env.loader.list_templates())))

#     if known_templates:
#         # from pynchon.util import text as util_text

#         msg = "Known template search paths (includes folders only): "
#         tmp = list({p.parents[0] for p in known_templates})
#         # LOGGER.info(msg + util_text.to_json(tmp))
# return env


@functools.cache
def get_jinja_env(
    *includes,
    # quiet: bool = False,
) -> jinja2.Environment:
    """
    
    """
    # events.lifecycle.send(__name__, msg="finalizing jinja-Env")
    includes = get_jinja_includes(*includes)
    for template_dir in includes:
        if not template_dir.exists:
            err = f"template directory @ `{template_dir}` does not exist"
            raise ValueError(err)
    # includes and (not quiet) and LOGGER.warning(f"Includes: {includes}")
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader([str(t) for t in includes]),
        undefined=jinja2.StrictUndefined,
        # trim_blocks=True,
        # lstrip_blocks=True
    )

    # def include_template(template_name):
    #     "Function to include a template programmatically"
    #     env = Environment(loader=jinja2.FileSystemLoader('templates'))
    #     template = env.get_template(template_name)
    #     return template.render()
    #
    # env.filters["include"] = include_template

    env.filters.update(**get_jinja_filters())
    env.pynchon_includes = includes

    env.globals.update(
        # include=include_template,
        **get_jinja_globals()
    )

    known_templates = list(map(Path, set(env.loader.list_templates())))

    if known_templates:
        list({p.parents[0] for p in known_templates})
    return env


@functools.cache
def get_jinja_filters():
    def strip_empty_lines(s):
        lines = s.split("\n")
        filtered_lines = [line for line in lines if line.strip() != ""]
        return "\n".join(filtered_lines)

    return {
        "Path": Path,
        "strip_empty_lines": strip_empty_lines,
    }


@functools.cache
def get_jinja_globals():
    """
    
    """
    return {
        "str": str,
        "open": open,
        "map": map,
        "eval": eval,
        "env": os.getenv,
        "filter": filter,
    }


@pydantic.validate_call
def get_template(
    template_name: typing.Union[str, Path] = None,
    env=None,
    from_string: str = None,
    **jinja_context,
) -> jinja2.Template:
    """
    
    """
    env = env or get_jinja_env()
    if isinstance(template_name, (Path,)):
        template_path = template_name
        template_name = str(template_name)
    elif template_name:
        template_path = Path(template_name)
    else:
        template_path = None
    try:
        if from_string:
            template = env.from_string(from_string)
        else:
            LOGGER.info(f"Looking up {template_path}")
            template = env.get_template(template_name)
    except (jinja2.exceptions.TemplateNotFound,) as exc:
        LOGGER.critical(f"Template exception: {exc}")
        LOGGER.critical(f"Jinja-includes: {env.pynchon_includes}")
        err = getattr(exc, "templates", exc.message)
        LOGGER.critical(f"Problem template: {err}")
        raise
    jinja_context.update(__template__=template_path)
    filter(None, template_path.name[template_path.name.find(".") :].split("."))
    # if template_path and "md" in all_extensions:
    #     LOGGER.warning("template is markdown, trying to parse metadata")
    #     import markdown
    #     from pynchon.util.text import loads
    #     try:
    #         # https://python-markdown.github.io/extensions/meta_data/#accessing-the-meta-data
    #         md = markdown.Markdown(extensions=["meta"])
    #         html = md.convert(open(template_name).read())
    #         md_meta = md.Meta
    #         md_meta and LOGGER.warning(f"extracted metadata: {md_meta}")
    #         # the metadata extension doesn't really do much parsing,
    #         # so we treat it here as potentially yaml
    #         tmp = {}
    #         for k, v in md_meta.items():
    #             z = "\n".join(v)
    #             tmp.update(**loads.yaml(f"{k}: {z}"))
    #         md_meta = tmp
    #         jinja_context.update(**md_meta)
    #     except (Exception,) as exc:
    #         LOGGER.warning(f"failed extracting markdown metadata: {exc}")

    def panic():
        raise Exception(jinja_context)

    def jinja_debug():
        LOGGER.critical(f"jinja_debug: {jinja_context}")
        return str(jinja_context)

    env.globals.update(
        jinja_debug=jinja_debug,
        panic=panic,
        isinstance=isinstance,
        type=type,
    )

    def _render(*args, **kwargs):
        # kwargs.update(**jinja_context)
        return "\n".join(x for x in ooo(*args, **kwargs).split("\n") if x)

    ooo = template.render
    template.render = _render
    return template


def get_template_from_string(content, **kwargs):
    """
    
    """
    return get_template(from_string=content, **kwargs)


def get_template_from_file(
    file: str = None,
    **kwargs,
):
    """
    
    """
    with open(file) as fhandle:
        content = fhandle.read()
    return get_template_from_string(content, file=file, **kwargs)
