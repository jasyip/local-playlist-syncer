import logging
import shutil
from pathlib import Path
import polars as pl
import yt_dlp
import time

_logger = logging.getLogger(__name__)

DEBUG=True

def download(df, columns=r"^\w+ Link$", *args, **kwargs):

    df = df.lazy()
    df = df.filter(pl.any(pl.col(columns).is_not_null()) & pl.col("Name").is_not_null())

    #with yt_dlp.YoutubeDL(*args, **kwargs) as ydl:
    def process(values):
        print(values)
        return values["Video Link"] is not None

    df = df.select(pl.struct("Name", columns).apply(process, return_dtype=bool).alias("Status"))
    return df.fetch(3) if DEBUG else df.collect()

