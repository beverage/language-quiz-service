import asyncclick
import functools


def sentence_options(f):
    @asyncclick.option("-v", "--verb-infinitive", type=str, required=False, default="")
    @asyncclick.option(
        "-cod", "--direct-object", type=str, required=False, default="none"
    )
    @asyncclick.option(
        "-coi", "--indirect-object", type=str, required=False, default="none"
    )
    @asyncclick.option("-neg", "--negation", type=str, required=False, default="none")
    @asyncclick.option("-c", "--is-correct", type=bool, required=False, default=True)
    @asyncclick.option("--validate", is_flag=True, default=False, help="Enable LLM validation of generated sentences")
    @functools.wraps(f)
    def wrapper_common_options(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper_common_options


def random_options(f):
    @asyncclick.option("-c", "--is-correct", type=bool, required=False, default=True)
    @functools.wraps(f)
    def wrapper_common_options(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper_common_options
