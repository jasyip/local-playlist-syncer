import logging
import re
from collections import namedtuple

from configargparse import ArgumentParser
from pygtrie import Trie

_log_level_trie = Trie()


def to_identifier(s, *, delim="_"):
    return re.sub("[^a-zA-Z0-9]+", delim, s).lower()


def log_level_value(l):
    if type(l) == int:
        return l

    as_identifier = to_identifier(l)
    node_info = _log_level_trie.has_node(as_identifier)

    if node_info & Trie.HAS_VALUE:
        return _log_level_trie[as_identifier]
    if node_info & Trie.HAS_SUBTRIE:
        value_set = set(_log_level_trie.itervalues(prefix=as_identifier, shallow=True))
        if len(value_set) == 1:
            value = next(iter(value_set))
            return value

        raise ValueError(f"log level {l} is ambiguous")

    raise ValueError(f"invalid log level {l}")


_LogLevel = namedtuple("LogLevel", "original_name standardized_name value")


def add_log_level_flags(
    parser,
    dest,
    log_level_short_flag,
    log_level_long_flag=None,
    *,
    env_var=None,
    **kwargs,
):
    excluded_levels = {"NOTSET"}

    log_levels = []
    for original_name, value in logging.getLevelNamesMapping().items():
        standardized_name = to_identifier(original_name)
        if excluded_levels.isdisjoint({original_name, standardized_name}):
            log_levels.append(
                _LogLevel(original_name, to_identifier(original_name), value)
            )

    to_delete = set()
    for log_level in sorted(log_levels, key=lambda p: len(p.standardized_name)):
        for prefix in _log_level_trie.prefixes(log_level.standardized_name):
            if prefix.value == log_level.value:
                key = "".join(prefix.key)
                del _log_level_trie[key]
                to_delete.add(key)

        _log_level_trie[log_level.standardized_name] = log_level.value

    temp_log_levels_list = []
    for log_level in log_levels:
        if log_level.standardized_name not in to_delete:
            temp_log_levels_list.append(log_level)
    log_levels = temp_log_levels_list

    parser.add_argument(
        log_level_short_flag,
        log_level_long_flag or "--" + to_identifier(dest, delim="-"),
        dest=dest,
        default=logging.WARNING,
        type=log_level_value,
        help=f"set logging level",
        env_var=env_var,
    )

    for log_level in log_levels:
        log_level_short_flag = kwargs.pop(log_level.standardized_name, None)
        parser.add_argument(
            *([log_level_short_flag] if log_level_short_flag else []),
            "--" + log_level.standardized_name,
            dest=dest,
            action="store_const",
            const=log_level.value,
            help=f"set logging level to {log_level.original_name}",
            is_config_file_arg=False,
        )
