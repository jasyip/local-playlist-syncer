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
import logging
import os
import shlex
import shutil
from pathlib import Path
import polars

from configargparse import ArgumentParser

import config
import sync

_logger = logging.getLogger(__name__)




def main(*args, **kwargs):
    default_config_files = []
    for path in (
        *os.getenv("XDG_CONFIG_DIRS", "/etc/xdg").split(":"),
        os.getenv("XDG_CONFIG_HOME", "~/.config"),
    ):
        default_config_files.append(
            os.path.join(path, "local-playlist-syncer", "config")
        )

    parser = ArgumentParser(
        # add_config_file_help=False,
        args_for_setting_config_path=("-c", "--config"),
        default_config_files=default_config_files,
    )

    parser.add_argument("spreadsheet", type=Path, help="spreadsheet in csv format")
    parser.add_argument(
        "-o", "--output", type=Path, default="media", help="output folder"
    )
    parser.add_argument(
        "-a",
        "--use-aria2c",
        action=argparse.BooleanOptionalAction,
        help="use aria2c as external downloader",
    )
    parser.add_argument("-y", "--yt-dlp-options", default="", type=shlex.split)

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

    if args.use_aria2c is not False:
        aria2c_path = shutil.which("aria2c", mode=os.X_OK)
        if aria2c_path is not None:
            args.yt_dlp_options.extend(
                (
                    "--external-downloader",
                    aria2c_path,
                    "--external-downloader-args",
                    "-c -j 3 -x 3 -s 3 -k 1M",
                )
            )
        elif args.use_aria2c:
            parser.error("--use-aria2c was specified but cannot locate executable")

    args.output.mkdir(parents=True, exist_ok=True)
    spreadsheet = getattr(polars, "read_" + args.spreadsheet.suffix.removeprefix("."))(args.spreadsheet)
    print(sync.download(spreadsheet).head())


if __name__ == "__main__":
    main()
