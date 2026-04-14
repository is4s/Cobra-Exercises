import numpy as np
from pntos.api.plugins.common import LoggingLevel, Mediator
from pntos.api.plugins.fusion import StandardFusionEngine
from pntos.api.plugins.state_modeling import (
    StandardStateModelProvider,
    StateModelingPlugin,
    StateModelProviderType,
    StandardMeasurementProcessor
)
from pntos.cobra.config import (
    SensorMeasurementProcessorConfig,
    config_from_registry,
)


class DirectionModelProvider(StandardStateModelProvider):

    _mediator: Mediator

    def __init__(self, mediator: Mediator) -> None:
        self._mediator = mediator
        self.processor_identifiers: list[str] = []
        self.block_identifiers: list[str] = []
        self.virtual_block_identifiers: list[str] = []

    def new_processor(
        self,
        processor_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        state_block_labels: list[str],
        config_group: str | None,
    ) -> (
        StandardMeasurementProcessor | None
    ):
        raise NotImplementedError("This StateModelProvider should supply at least one MeasurementProcessor.")

    def new_block(
        self,
        block_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        config_group: str | None,
    ) -> None:
        return None

    def new_virtual_block(
        self,
        virtual_block_index: int,
        source_label: str,
        target_label: str,
        config_group: str | None,
    ) -> None:
        return None


class DirectionPlugin(StateModelingPlugin):
    _mediator: Mediator

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        if mediator is not None:
            self._mediator = mediator

    def shutdown_plugin(self) -> None:
        pass

    def new_state_model_provider(
        self, type: type[StateModelProviderType]
    ) -> StateModelProviderType | None:
        raise NotImplementedError("This plugin currently does not produce any StateModelProviders.")

    def is_fusion_type_supported(self, type: StateModelProviderType) -> bool:
        return type is StandardStateModelProvider
