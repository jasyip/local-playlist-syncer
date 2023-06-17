#!/usr/bin/env python
import csv
import logging
from argparse import ArgumentParser

from pygtrie import Trie

_logger = logging.getLogger(__name__)


_log_level_trie = Trie()


def read_csv(file):
    pass


def log_level_value(l):
    l = l.upper()
    node_info = _log_level_trie.has_node(l)
    if node_info & Trie.HAS_VALUE:
        return _log_level_trie[l]
    if node_info & Trie.HAS_SUBTRIE:
        value_set = set(_log_level_trie.itervalues(prefix=l, shallow=True))
        if len(value_set) == 1:
            return next(iter(value_set))
        raise ValueError("provided log level name is ambiguous")
    raise ValueError("invalid log level name")


def add_log_level_flags(parser):
    log_level_map = logging.getLevelNamesMapping()
    log_level_map.pop("NOTSET", None)
    to_delete = set()
    for log_level, value in sorted(log_level_map.items(), key=lambda p: len(p[0])):
        for prefix in _log_level_trie.prefixes(log_level):
            if prefix.value == value:
                to_delete.add("".join(prefix.key))
        _log_level_trie[log_level] = value

    for log_level in to_delete:
        del log_level_map[log_level]
        del _log_level_trie[log_level]

    log_level_group = parser.add_mutually_exclusive_group()
    log_level_group.add_argument(
        "-l",
        "--log-level",
        default="WARNING",
        type=log_level_value,
        help="set logging level, default is %(default)s when omitted",
    )
    for level_name in log_level_map.keys():
        shortest_unique_len = 1
        for step in _log_level_trie.walk_towards(level_name[:-1]):
            if len(step._node.children) > 1 or step.is_set:
                shortest_unique_len = step._pos + 1
        flags = [
            "-" + level_name[:shortest_unique_len].lower(),
            "--" + level_name.lower(),
        ]

        log_level_group.add_argument(
            *flags,
            dest="log_level",
            action="store_const",
            const=log_level_value(level_name),
            help=f"set logging level to {level_name}",
        )


if __name__ == "__main__":
    parser = ArgumentParser()
    add_log_level_flags(parser)

    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)
