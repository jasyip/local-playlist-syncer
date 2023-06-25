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
import io
import logging
import os
import re
import shlex
import shutil
import sys
from pathlib import Path, PurePath

import polars
from configargparse import ArgumentParser

import config
import sync
import yt_dlp

_logger = logging.getLogger(__name__)


_filetype_map = ((re.compile(r"xls[xmb]?"), "excel"),)


def scan_spreadsheet(f, /, parser, *, format=None):
    match (f, format):
        case ("-", None):
            parser.error("format must be specified when reading from stdin")
        case ("-", _):
            f = sys.stdin.buffer
            object.__setattr__(f, "name", None)
        case (_, None):
            format = PurePath(f).suffix.removeprefix(".")
            for file_type_regex, destination_format in _filetype_map:
                if file_type_regex.fullmatch(format):
                    format = destination_format
                    break

    read_method = getattr(polars, "scan_" + format, getattr(polars, "read_" + format, None))
    if read_method is None:
        parser.error("unparseable spreadsheet format")
    return read_method(f)


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

    parser.add_argument(
        "spreadsheet",
        help="either a spreadsheet (in csv/Apache Parquet/JSON/Excel Spreadsheet format), or '-' to read data from standard input",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default="media", help="output folder"
    )
    parser.add_argument(
        "-f",
        "--format",
        help="spreadsheet format (automatically inferred from file extension, mandatory for standard input data)",
    )
    parser.add_argument(
        "-1",
        "--just-one",
        action="store_true",
        help="sync just the first one as a trial",
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

    if args.use_aria2c:
        if shutil.which("aria2c", mode=os.X_OK) is None:
            parser.error("--use-aria2c was specified but cannot locate executable")

        args.yt_dlp_options.extend(
            (
                "--downloader",
                "aria2c",
                "--downloader-args",
                "aria2c:-c -j 3 -x 3 -s 3 -k 1M",
            )
        )
    args.yt_dlp_options

    args.output.mkdir(parents=True, exist_ok=True)
    spreadsheet = scan_spreadsheet(args.spreadsheet, parser, format=args.format)
    ydl_opts = vars(yt_dlp.parseOpts(args.yt_dlp_options, ignore_config_files=False)[1])
    for k, v in vars(yt_dlp.parse_options([])).items():
        if k in ydl_opts and v == ydl_opts[k]:
            del ydl_opts[k]
    bad_default_options = {
        "download_ranges" : None
    }
    for k, v in bad_default_options.items():
        if k in ydl_opts and v == ydl_opts[k]:
            del ydl_opts[k]

    _logger.debug(f"options to pass to YoutubeDL object: {ydl_opts=}")
    print(
        sync.download(
            spreadsheet,
            output=args.output,
            yt_dlp_options=ydl_opts,
            just_one=args.just_one,
        ).head()
    )


if __name__ == "__main__":
    main()
