from dataclasses import dataclass
from pntos.cobra.config import PreprocessorConfig
from numpy.typing import NDArray
from numpy import float64


@dataclass
class ZuptConfig(PreprocessorConfig):
    # INHERITED FIELDS
    group: str

    identifier: str

    # UNIQUE FIELDS
    stationary_times: NDArray[float64]
