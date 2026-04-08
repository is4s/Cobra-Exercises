from pntos.api import (
    LoggingLevel,
    Mediator,
    Preprocessor,
    PreprocessorPlugin,
)
from ZuptConfig import ZuptConfig  # noqa: F401


class ZuptPreprocessorPlugin(PreprocessorPlugin):
    mediator: Mediator | None

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        self.preprocessor_identifiers = []

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator
        if self.mediator is None:
            print('Error: mediator cannot be None')
            return None
        # REMOVE THE MESSAGE BELOW AFTER IMPLEMENTING
        self.mediator.log_message(
            LoggingLevel.WARN,
            'ExercisePreprocessorPlugin has not been setup to provide any preprocessors.',
        )

    def shutdown_plugin(self) -> None:
        pass

    def new_preprocessor(
        self,
        preprocessor_index: int,
        config_group: str | None = None,
    ) -> Preprocessor | None:
        # Implement me!

        return None
