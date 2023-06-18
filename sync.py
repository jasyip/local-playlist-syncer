#!/usr/bin/env python

"""
local-playlist-syncer: synchronizes media files with yt-dlp from
    spreadsheet/csv of media metadata
Copyright © 2023 Jason Yip

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

__author__ = "Jason Yip"
__copyright__ = "Copyright © 2023 Jason Yip"
__license__ = "GNU Affero General Public License"
__version__ = "0.1.0"

import argparse
import csv
import logging
from pathlib import Path

from configargparse import ArgumentParser

import config

_logger = logging.getLogger(__name__)


def read_csv(file: Path):
    pass


def output_directory(x):
    x = Path(x)
    if x.exists():
        if not x.is_dir():
            raise ValueError(f"{x} is not a directory")
    else:
        x.mkdir(parents=True)


def main(*args, **kwargs):
    parser = ArgumentParser(
        add_config_file_help=False,
        args_for_setting_config_path=("-c", "--config"),
        default_config_files=[],
    )

    parser.add_argument("spreadsheet", type=Path, help="spreadsheet in csv format")
    parser.add_argument(
        "-o", "--output", type=output_directory, default="media", help="output folder"
    )
    parser.add_argument(
        "-a",
        "--use-aria2c",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="use aria2c as external downloader",
    )
    parser.add_argument("-y", "--yt-dlp-options", default="")

    log_level_group = parser.add_argument_group(
        "logging"
    ).add_mutually_exclusive_group()
    config.add_log_level_flags(
        log_level_group, "log_level", "-l", env_var="LPS_LOG_LEVEL", debug="-d"
    )
    log_level_group.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        dest="log_level",
        const=False,
        is_config_file_arg=False,
    )

    args = parser.parse_args(*args, **kwargs)

    if args.log_level is not False:
        logging.basicConfig(level=args.log_level)
    _logger.debug(f"parsed arguments: {args}")


if __name__ == "__main__":
    main()
