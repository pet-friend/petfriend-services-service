from typing import BinaryIO
from dataclasses import dataclass


@dataclass
class File:
    file: BinaryIO
