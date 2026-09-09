from dataclasses import dataclass
from pntos.cobra.config import PreprocessorConfig


@dataclass
class ZuptConfig(PreprocessorConfig):
    # INHERITED FIELDS
    group: str

    identifier: str

    channels: tuple[str, ...] | None

    # UNIQUE FIELDS
    # Add fields to me!
