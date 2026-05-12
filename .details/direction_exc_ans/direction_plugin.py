import numpy as np
from pntos.api.plugins.common import LoggingLevel, Mediator
from pntos.api.plugins.fusion import StandardFusionEngine
from pntos.api.plugins.state_modeling import (
    StandardStateModelProvider,
    StateModelingPlugin,
    StateModelProviderType,
)
from pntos.cobra.config import (
    Direction3dToPointsMPConfig,
    config_from_registry,
)

from direction_processor import DirectionMeasurementProcessor


class DirectionModelProvider(StandardStateModelProvider):
    _mediator: Mediator

    def __init__(self, mediator: Mediator) -> None:
        self._mediator = mediator
        self.processor_identifiers: list[str] = [
            'pinson_direction_processor',
        ]
        self.block_identifiers: list[str] = []
        self.virtual_block_identifiers: list[str] = []

    def new_processor(
        self,
        processor_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        state_block_labels: list[str],
        config_group: str | None,
    ) -> DirectionMeasurementProcessor | None:
        """
        Generates DirectionMeasurementProcessors.

        Args:
            processor_index: Index of entry in processor_identifiers to generate. If not 0,
                no processor will be produced.
            engine: Fusion engine this processor will be added to. Unused.
            label: The ID used for this processor instance.
            state_block_labels: The set of state blocks the processor will be used to update.
            config_group: Group identifier used to access the configuration for this processor in the registry.
        """
        match processor_index:
            case 0:
                if config_group is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        f'A config group is required for processor {self.processor_identifiers[processor_index]}',
                    )
                    return None
                sensor_mp_config = config_from_registry(
                    Direction3dToPointsMPConfig, self._mediator, config_group
                )
                if sensor_mp_config is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        'Could not get sensor config from registry.',
                    )
                    return None
                return DirectionMeasurementProcessor(
                    label,
                    state_block_labels,
                    self._mediator,
                    np.array(sensor_mp_config.lever_arm),
                    np.array(sensor_mp_config.orientation),
                )

        self._mediator.log_message(
            LoggingLevel.ERROR,
            f'Invalid processor index of {processor_index}. DirectionModelProvider provides {len(self.processor_identifiers)} processors.',
        )
        return None

    def new_block(
        self,
        block_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        config_group: str | None,
    ) -> None:
        """
        Does not produce any state blocks.
        """
        return None

    def new_virtual_block(
        self,
        virtual_block_index: int,
        source_label: str,
        target_label: str,
        config_group: str | None,
    ) -> None:
        """
        Does not produce any virtual state blocks.
        """
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
        if not self.is_fusion_type_supported(type):
            return None

        return DirectionModelProvider(self._mediator)

    def is_fusion_type_supported(self, type: StateModelProviderType) -> bool:
        return type is StandardStateModelProvider
