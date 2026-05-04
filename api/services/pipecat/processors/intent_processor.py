import json
from typing import Any, Dict, Optional

from loguru import logger

from pipecat.frames.frames import Frame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class IntentDetectionProcessor(FrameProcessor):
    """
    A processor that extracts the user's intent from a TranscriptionFrame.
    It uses a fast LLM classification to categorize the utterance, helping 
    the main LLM stay on track and reduce hallucinations.
    """

    def __init__(self, engine, **kwargs):
        super().__init__(**kwargs)
        self._engine = engine
        self._intent_prompt = (
            "You are an intent classifier for a phone-based AI assistant. "
            "Given the user's utterance, categorize it into ONE of the following: "
            "GREETING, QUESTION, COMPLAINT, AFFIRMATIVE, NEGATIVE, IRRELEVANT, or REQUEST_INFO. "
            "Respond ONLY with the category name."
        )

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame):
            intent = await self._extract_intent(frame.text)
            logger.info(f"Detected Intent: {intent} for text: '{frame.text}'")
            
            # Store intent in engine's gathered context for the main LLM to use
            try:
                self._engine._gathered_context["current_user_intent"] = intent
                
                # Optionally prefix the text with intent for better LLM context
                # frame.text = f"[Intent: {intent}] {frame.text}"
            except Exception as e:
                logger.error(f"Failed to store intent in engine: {e}")

        await self.push_frame(frame, direction)

    async def _extract_intent(self, text: str) -> str:
        """Use the engine's LLM (or a dedicated one) to classify intent."""
        if not text or len(text.strip()) < 2:
            return "UNKNOWN"

        try:
            # We use a dedicated, simple message system for intent extraction
            # This is a synchronous-style call but uses the async LLM service
            messages = [
                {"role": "system", "content": self._intent_prompt},
                {"role": "user", "content": f"Utterance: \"{text}\""}
            ]
            
            # Use the engine's LLM service if available
            if self._engine and self._engine.llm:
                # We use a temporary non-streaming generation for intent
                # Note: Not all LLM services support easy non-streaming calls via pipecat easily
                # but we can simulate it or just use the system prompt logic.
                # For now, we'll implement a helper in PipecatEngine.
                return await self._engine.classify_intent(text)
            
            return "PEE" # Plain English Extraction? No, let's just return a default
        except Exception as e:
            logger.error(f"Error during intent extraction: {e}")
            return "ERROR"
