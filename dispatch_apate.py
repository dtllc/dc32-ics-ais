#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This script consumes the output of `apate.pl` and forwards the AIVDM frames to the `ais-simulator` WebSocket server to be transmitted over an SDR.

Authors
- Nicholas Haltmeyer <nick.haltmeyer@liberas.com>
- Duncan Woodbury <duncan.woodbury@liberas.com>

Copyright Liberas 2024 (C)
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import logging
import os
import sys
import time
from collections.abc import Iterator
from os import PathLike
from pathlib import Path
from typing import Final

from pyais import decode
from websocket import WebSocket, create_connection

_log_handler = logging.StreamHandler(sys.stdout)
_log_formatter = logging.Formatter(
    "[%(threadName)s] %(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s"
)
_log_handler.setFormatter(_log_formatter)
logger = logging.getLogger()
logger.addHandler(_log_handler)
logger.setLevel(logging.DEBUG)

AIS_WEBSOCKET: Final[str] = "ws://localhost:52002/"
TRANSMIT_COUNT: Final[int] = 2
assert TRANSMIT_COUNT >= 1


def decode_replay_file(ais_file: PathLike) -> Iterator[tuple[float, str]]:
    """Parses an `apate.pl` replay file into an iterator of (timestamp, frame) pairs."""
    i = 1

    with open(ais_file, "r") as f:
        for line in f:
            split = line.split("-", 1)

            if len(split) != 2:
                raise RuntimeError(f"Replay file not formatted corrected on line {i}")

            seconds = int(split[0])
            frame = split[1].rstrip()
            i += 1
            yield (float(seconds), frame)


def encode_aivdm(frame: str) -> str:
    """Converts the AIVDM frame into a sequence of '0' and '1' ASCII characters for `ais-simulator`."""
    try:
        return decode(frame).to_bitarray().to01()
    except Exception as error:
        logger.error("Unable to coerce AIVDM frame: %s", error)
        return ""


def dispatch_aivdm(ws: WebSocket, frame: str) -> None:
    encoded = encode_aivdm(frame)

    for i in range(TRANSMIT_COUNT):
        logger.debug("Transmission attempt %s: %s", i, encoded)
        ws.send(encoded)


def main(av: list[str]) -> int:
    if len(av) != 2:
        print("Usage: dispatch_apate.py DATA_replay.txt", file=sys.stderr)
        return os.EX_USAGE

    ais_file = Path(av[1]).resolve()

    if not ais_file.exists():
        print(f"Provided AIS replay file '{ais_file}' does not exist.", file=sys.stderr)
        return os.EX_OSFILE

    ws = create_connection(AIS_WEBSOCKET)
    ais_replay = decode_replay_file(ais_file)
    logger.info("Starting to replay AIS frames...")
    start_time = time.time()
    cursor = 0.0

    while True:
        try:
            timestamp, frame = next(ais_replay)
        except StopIteration:
            logger.warning("AIS replay file exhausted.")
            break

        if timestamp > cursor:
            drift = cursor - (time.time() - start_time)
            sleep_duration = timestamp - cursor + drift
            logger.debug("Sleeping for %s seconds.", sleep_duration)
            time.sleep(sleep_duration)
            cursor = time.time() - start_time

        logger.info("[%s] Transmitting: (%s, %s)", cursor, timestamp, frame)
        dispatch_aivdm(ws, frame)

    ws.close()

    return os.EX_OK


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        pass
