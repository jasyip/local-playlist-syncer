import logging
import shutil
from pathlib import Path

import json
import polars as pl
import yt_dlp

_logger = logging.getLogger(__name__)

_link_column_re = r"^\w+ Link$"
# _relevant_columns = ("Name", _link_column_re, "Start Time", "End Time")


def download(df, /, *, output, yt_dlp_options={}, just_one=False):
    df = df.lazy()
    # Must have at least one link and Name
    df = df.filter(pl.any(pl.col(_link_column_re).is_not_null()) & pl.col("Name").is_not_null())

    with yt_dlp.YoutubeDL(yt_dlp_options) as ydl:

        def process(values):
            if values["Audio Link"]:
                call = ydl.extract_info(values["Audio Link"], download=False)
                print(f"{call=}")
                return json.dumps(ydl.sanitize_info(call))
            return None

        df = df.with_columns(
            pl.struct(pl.all())
            .apply(process, return_dtype=str)
            .alias("Status")
        )
        return df.fetch(1) if just_one else df.collect()
