from loguru import logger

from pipecat.frames.frames import Frame, TranscriptionFrame, TTSUpdateSettingsFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.transcriptions.language import Language

# Primary: Hindi, Secondary: Odia — any other detected language falls back to Hindi
_SARVAM_LANGUAGE_MAP = {
    Language.HI: "hi-IN",
    Language.HI_IN: "hi-IN",
    Language.OR: "od-IN",
    Language.OR_IN: "od-IN",
}


class LanguageSwitchProcessor(FrameProcessor):
    """Detects the language from incoming TranscriptionFrames and updates TTS language.

    Primary language: Hindi (hi-IN)
    Secondary language: Odia (od-IN)
    Any other Sarvam-detected language defaults back to Hindi.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._current_tts_language = "hi-IN"

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame) and direction == FrameDirection.DOWNSTREAM:
            detected = frame.language
            target = _SARVAM_LANGUAGE_MAP.get(detected, "hi-IN")

            if target != self._current_tts_language:
                self._current_tts_language = target
                logger.info(
                    f"Language switch: STT detected [{detected}] → TTS switching to [{target}]"
                )
                await self.push_frame(
                    TTSUpdateSettingsFrame(settings={"target_language_code": target}),
                    FrameDirection.DOWNSTREAM,
                )

        await self.push_frame(frame, direction)
