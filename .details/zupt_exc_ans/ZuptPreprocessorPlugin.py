from ZuptConfig import ZuptConfig
from pntos.api import (
    LoggingLevel,
    Mediator,
    Preprocessor,
    PreprocessorPlugin,
)
from pntos.cobra.config import config_from_registry
from ZuptPreprocessor import ZuptPreprocessor


class ZuptPreprocessorPlugin(PreprocessorPlugin):
    mediator: Mediator | None

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        self.preprocessor_identifiers = ['zupt_generator']

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        if mediator is None:
            print('Error: mediator cannot be None')
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        pass

    def new_preprocessor(
        self,
        preprocessor_index: int,
        config_group: str | None = None,
    ) -> Preprocessor | None:
        if self.mediator is None:
            print(
                'Error: mediator is None. PreprocessorPlugin.init_plugin must be called'
                + ' and passed a valid mediator before new_preprocessor.'
            )
            return None
        if preprocessor_index == 0:
            if config_group is None:
                self.mediator.log_message(
                    LoggingLevel.ERROR,
                    'ZuptPreprocessorPlugin requires param config_group to be populated'
                    + ' to create a ZuptPreprocessor.',
                )
                return None
            conf = config_from_registry(ZuptConfig, self.mediator, config_group)
            if conf is None:
                self.mediator.log_message(
                    LoggingLevel.ERROR,
                    'Failed to populate ZuptConfig.',
                )
                return None

            return ZuptPreprocessor(
                mediator=self.mediator, stationary_times=conf.stationary_times
            )

        self.mediator.log_message(
            LoggingLevel.ERROR,
            'Invalid preprocessor index passed to ZuptPreprocessorPlugin.'
            + f' Received index: {preprocessor_index}',
        )
        return None
