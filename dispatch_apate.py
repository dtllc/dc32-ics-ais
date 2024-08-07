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
from os import PathLike
from pathlib import Path
from typing import Final

from pyais import ANY_MESSAGE, decode
from pyais.exceptions import MissingMultipartMessageException
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


def decode_replay_file(ais_file: PathLike) -> dict[float, list[str]]:
    """Parses an `apate.pl` replay file into a mapping of timestamp to AIVDM frames."""
    mapping: dict[float, list[str]] = {}
    i = 1

    with open(ais_file, "r") as f:
        for line in f:
            split = line.split("-", 1)

            if len(split) != 2:
                raise RuntimeError(f"Replay file not formatted correctly on line {i}.")

            seconds = float(split[0])
            frame = split[1].rstrip()

            if seconds in mapping:
                mapping[seconds].append(frame)
            else:
                mapping[seconds] = [frame]

    return mapping


def decode_batch(batch: list[str]) -> list[ANY_MESSAGE]:
    """Converts batches of AIVDM frames into full AIS messages."""
    if not batch:
        return []

    i = 0
    cursor = [batch[i]]

    while i < len(batch):
        try:
            return [decode(*cursor)] + decode_batch(batch[i + 1 :])
        except MissingMultipartMessageException:
            cursor.append(batch[i + 1])
            i += 1

    raise MissingMultipartMessageException


def encode_message(msg: ANY_MESSAGE) -> str:
    """Converts AIS message to ASCII-encoded binary."""
    return msg.to_bitarray().to01()


def transmit_message(ws: WebSocket, msg: ANY_MESSAGE) -> None:
    """Transmits the given AIS message over WebSocket to the `ais-simulator.py` server."""
    encoded = encode_message(msg)

    for i in range(TRANSMIT_COUNT):
        logger.debug("Transmission attempt %s: %s", i + 1, encoded)
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

    for timestamp in sorted(ais_replay.keys()):
        batch = ais_replay[timestamp]
        messages = decode_batch(batch)

        if timestamp > cursor:
            drift = cursor - (time.time() - start_time)
            sleep_duration = timestamp - cursor + drift
            logger.debug("Sleeping for %s seconds.", sleep_duration)
            time.sleep(sleep_duration)
            cursor = time.time() - start_time

        for msg in messages:
            logger.info("[%s] Transmitting: (%s, %s)", cursor, timestamp, msg)
            transmit_message(ws, msg)

    ws.close()

    return os.EX_OK


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        pass
