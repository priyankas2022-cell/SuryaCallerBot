#
# Copyright (c) 2024-2026, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Audio utility functions for Pipecat.

This module provides common audio processing utilities including mixing,
format conversion, volume calculation, and codec transformations for
various audio formats used in Pipecat pipelines.
"""

import audioop

import numpy as np
import pyloudnorm as pyln
from loguru import logger

from pipecat.audio.resamplers.base_audio_resampler import BaseAudioResampler
from pipecat.audio.resamplers.soxr_resampler import SOXRAudioResampler
from pipecat.audio.resamplers.soxr_stream_resampler import SOXRStreamAudioResampler

# Normal speech usually results in many samples between ±500 to ±5000, depending on loudness and mic gain.
# So we are using a threshold that is well below what real speech produces.
SPEAKING_THRESHOLD = 20


def create_default_resampler(**kwargs) -> BaseAudioResampler:
    """Create a default audio resampler instance.

    .. deprecated:: 0.0.74
        This function is deprecated and will be removed in a future version.
        Use `create_stream_resampler` for real-time processing scenarios or
        `create_file_resampler` for batch processing of complete audio files.

    Args:
        **kwargs: Additional keyword arguments passed to the resampler constructor.

    Returns:
        A configured SOXRAudioResampler instance.
    """
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("always")
        warnings.warn(
            "`create_default_resampler` is deprecated. "
            "Use `create_stream_resampler` for real-time processing scenarios or "
            "`create_file_resampler` for batch processing of complete audio files.",
            DeprecationWarning,
            stacklevel=2,
        )
    return SOXRAudioResampler(**kwargs)


def create_file_resampler(**kwargs) -> BaseAudioResampler:
    """Create an audio resampler instance for batch processing of complete audio files.

    Args:
        **kwargs: Additional keyword arguments passed to the resampler constructor.

    Returns:
        A configured SOXRAudioResampler instance.
    """
    return SOXRAudioResampler(**kwargs)


def create_stream_resampler(**kwargs) -> BaseAudioResampler:
    """Create a stream audio resampler instance.

    Args:
        **kwargs: Additional keyword arguments passed to the resampler constructor.

    Returns:
        A configured SOXRStreamAudioResampler instance.
    """
    return SOXRStreamAudioResampler(**kwargs)


def parse_wav_header(audio: bytes) -> tuple[bytes, int | None]:
    """Robustly parse and strip a WAV header, returning structural sample rate.
    
    Checks if the bytes start with RIFF/WAVE, securely parses 'fmt ' and 'data' chunks
    to extract actual sample rate, and calculates exact data offset.
    
    Args:
        audio: Raw audio byte string.
    
    Returns:
        Tuple of (stripped_audio_bytes, actual_sample_rate).
        If no valid header is found, returns (audio, None).
    """
    if len(audio) < 44 or not audio.startswith(b"RIFF"):
        return audio, None
        
    try:
        # RIFF chunks must have "WAVE" at byte 8
        if audio[8:12] != b"WAVE":
            return audio, None
            
        offset = 12
        sample_rate = None
        data_offset = None
        
        # Traverse chunks securely up to 512 bytes avoiding infinite loops
        while offset + 8 <= len(audio) and offset < 512:
            chunk_id = audio[offset:offset+4]
            chunk_size = int.from_bytes(audio[offset+4:offset+8], "little")
            
            if chunk_id == b"fmt ":
                # Format chunk: offset+8 is format_tag, offset+10 is channels
                # offset+12 to +16 is sample_rate
                channels = int.from_bytes(audio[offset+10:offset+12], "little")
                sample_rate = int.from_bytes(audio[offset+12:offset+16], "little")
                bits_per_sample = int.from_bytes(audio[offset+22:offset+24], "little")
                logger.debug(f"[Audio Pipeline] parse_wav_header: Found 'fmt ' chunk: {sample_rate}Hz, {channels}ch, {bits_per_sample}bps")
            elif chunk_id == b"data":
                # Data chunk header takes 8 bytes (id + size), raw audio immediately follows
                data_offset = offset + 8
                break
                
            offset += 8 + chunk_size
            
        if data_offset is not None:
            logger.debug(f"[Audio Pipeline] parse_wav_header: Successfully parsed WAV. Slicing at offset {data_offset}. True rate: {sample_rate}Hz")
            return audio[data_offset:], sample_rate
            
        logger.warning("[Audio Pipeline] parse_wav_header: Found 'RIFF' but missed 'data' chunk! Returning safe fallback.")
        return audio, sample_rate
        
    except Exception as e:
        logger.error(f"[Audio Pipeline] parse_wav_header: Structural parse failure: {e}. Defaulting to 44-byte slice.")
        return audio[44:], None

def validate_audio_chunk(audio: bytes, expected_rate: int = 8000, is_mulaw: bool = True) -> bool:
    """Validate Twilio audio chunk payload before sending over Transport.
    
    We prefer sending ~20ms chunks to Twilio.
    For 8kHz mulaw, this is exactly 160 bytes.
    """
    if not audio:
        logger.warning("[Audio Pipeline] validate_audio_chunk: Chunk is completely empty (0 bytes). Dropping.")
        return False
        
    expected_chunk_size = int((expected_rate * 20) / 1000)
    if not is_mulaw:
        expected_chunk_size *= 2  # 16-bit is 2 bytes per sample
        
    if len(audio) != expected_chunk_size:
        logger.debug(f"[Audio Pipeline] validate_audio_chunk: Expected {expected_chunk_size} bytes (20ms), got {len(audio)} bytes. Proceeding anyway.")
        if len(audio) == 0:
            return False
            
    header_check = audio.startswith(b"RIFF")
    if header_check:
        logger.error("[Audio Pipeline] validate_audio_chunk: FATAL: Chunk still contains WAV header! Rejecting.")
        return False
        
    return True


def mix_audio(audio1: bytes, audio2: bytes) -> bytes:
    """Mix two audio streams together by adding their samples.

    Both audio streams are assumed to be 16-bit signed integer PCM data.
    If the streams have different lengths, the shorter one is zero-padded
    to match the longer stream.

    Args:
        audio1: First audio stream as raw bytes (16-bit signed integers).
        audio2: Second audio stream as raw bytes (16-bit signed integers).

    Returns:
        Mixed audio data as raw bytes with samples clipped to 16-bit range.
    """
    data1 = np.frombuffer(audio1, dtype=np.int16)
    data2 = np.frombuffer(audio2, dtype=np.int16)

    # Max length
    max_length = max(len(data1), len(data2))

    # Zero-pad the arrays to the same length
    padded1 = np.pad(data1, (0, max_length - len(data1)), mode="constant")
    padded2 = np.pad(data2, (0, max_length - len(data2)), mode="constant")

    # Mix the arrays
    mixed_audio = padded1.astype(np.int32) + padded2.astype(np.int32)
    mixed_audio = np.clip(mixed_audio, -32768, 32767).astype(np.int16)

    return mixed_audio.astype(np.int16).tobytes()


def interleave_stereo_audio(left_audio: bytes, right_audio: bytes) -> bytes:
    """Interleave left and right mono audio channels into stereo audio.

    Takes two mono audio streams and combines them into a single stereo
    stream by interleaving the samples (L, R, L, R, ...). If the channels
    have different lengths, both are truncated to the shorter length.

    Args:
        left_audio: Left channel audio as raw bytes (16-bit signed integers).
        right_audio: Right channel audio as raw bytes (16-bit signed integers).

    Returns:
        Interleaved stereo audio data as raw bytes.
    """
    left = np.frombuffer(left_audio, dtype=np.int16)
    right = np.frombuffer(right_audio, dtype=np.int16)

    min_length = min(len(left), len(right))
    left = left[:min_length]
    right = right[:min_length]

    stereo = np.column_stack((left, right))

    return stereo.astype(np.int16).tobytes()


def normalize_value(value, min_value, max_value):
    """Normalize a value to the range [0, 1] and clamp it to bounds.

    Args:
        value: The value to normalize.
        min_value: The minimum value of the input range.
        max_value: The maximum value of the input range.

    Returns:
        Normalized value clamped to the range [0, 1].
    """
    normalized = (value - min_value) / (max_value - min_value)
    normalized_clamped = max(0, min(1, normalized))
    return normalized_clamped


def calculate_audio_volume(audio: bytes, sample_rate: int) -> float:
    """Calculate the loudness level of audio data using EBU R128 standard.

    Uses the pyloudnorm library to calculate integrated loudness according
    to the EBU R128 recommendation, then normalizes the result to [0, 1].

    Args:
        audio: Audio data as raw bytes (16-bit signed integers).
        sample_rate: Sample rate of the audio in Hz.

    Returns:
        Normalized loudness value between 0 (quiet) and 1 (loud).
    """
    audio_np = np.frombuffer(audio, dtype=np.int16)
    audio_float = audio_np.astype(np.float64)

    block_size = audio_np.size / sample_rate
    meter = pyln.Meter(sample_rate, block_size=block_size)
    loudness = meter.integrated_loudness(audio_float)

    # Loudness goes from -20 to 80 (more or less), where -20 is quiet and 80 is
    # loud.
    loudness = normalize_value(loudness, -20, 80)

    return loudness


def exp_smoothing(value: float, prev_value: float, factor: float) -> float:
    """Apply exponential smoothing to a value.

    Exponential smoothing is used to reduce noise in time-series data by
    giving more weight to recent values while still considering historical data.

    Args:
        value: The new value to incorporate.
        prev_value: The previous smoothed value.
        factor: Smoothing factor between 0 and 1. Higher values give more
                weight to the new value.

    Returns:
        The exponentially smoothed value.
    """
    return prev_value + factor * (value - prev_value)


async def ulaw_to_pcm(
    ulaw_bytes: bytes, in_rate: int, out_rate: int, resampler: BaseAudioResampler
):
    """Convert μ-law encoded audio to PCM and optionally resample.

    Args:
        ulaw_bytes: μ-law encoded audio data as raw bytes.
        in_rate: Original sample rate of the μ-law audio in Hz.
        out_rate: Desired output sample rate in Hz.
        resampler: Audio resampler instance for rate conversion.

    Returns:
        PCM audio data as raw bytes at the specified output rate.
    """
    # Convert μ-law to PCM
    in_pcm_bytes = audioop.ulaw2lin(ulaw_bytes, 2)

    # Resample
    out_pcm_bytes = await resampler.resample(in_pcm_bytes, in_rate, out_rate)

    return out_pcm_bytes


async def pcm_to_ulaw(pcm_bytes: bytes, in_rate: int, out_rate: int, resampler: BaseAudioResampler):
    """Convert PCM audio to μ-law encoding and optionally resample.

    Args:
        pcm_bytes: PCM audio data as raw bytes (16-bit signed integers).
        in_rate: Original sample rate of the PCM audio in Hz.
        out_rate: Desired output sample rate in Hz.
        resampler: Audio resampler instance for rate conversion.

    Returns:
        μ-law encoded audio data as raw bytes at the specified output rate.
    """
    # Resample
    in_pcm_bytes = await resampler.resample(pcm_bytes, in_rate, out_rate)

    # Convert PCM to μ-law
    out_ulaw_bytes = audioop.lin2ulaw(in_pcm_bytes, 2)

    return out_ulaw_bytes


async def pcm16_to_mulaw(pcm_bytes: bytes, in_rate: int, out_rate: int, resampler: BaseAudioResampler) -> bytes:
    """Convert PCM16 audio to μ-law and safely resample (with explicit logging)."""
    original_size = len(pcm_bytes)
    first_16_hex = pcm_bytes[:16].hex() if original_size >= 16 else pcm_bytes.hex()
    
    if original_size == 0:
        return b""
        
    # Resample
    in_pcm_bytes = await resampler.resample(pcm_bytes, in_rate, out_rate)
    resampler_len = len(in_pcm_bytes)
    
    # Backup resampler condition natively handled inside try/except block upstream
    # Convert PCM to μ-law
    out_ulaw_bytes = audioop.lin2ulaw(in_pcm_bytes, 2)
    final_size = len(out_ulaw_bytes)
    
    logger.debug(
        f"[Audio Pipeline] pcm16_to_mulaw: size_in={original_size}B, "
        f"hex_start={first_16_hex}, rate_in={in_rate}Hz, rate_out={out_rate}Hz, "
        f"channels=1, codec_out=mulaw, resampled_len={resampler_len}B, size_out={final_size}B"
    )
    return out_ulaw_bytes

async def mulaw_to_pcm16(ulaw_bytes: bytes, in_rate: int, out_rate: int, resampler: BaseAudioResampler) -> bytes:
    """Convert μ-law to PCM16 audio and safely resample (with explicit logging)."""
    original_size = len(ulaw_bytes)
    first_16_hex = ulaw_bytes[:16].hex() if original_size >= 16 else ulaw_bytes.hex()
    
    if original_size == 0:
        return b""
        
    in_pcm_bytes = audioop.ulaw2lin(ulaw_bytes, 2)
    unencoded_len = len(in_pcm_bytes)
    
    out_pcm_bytes = await resampler.resample(in_pcm_bytes, in_rate, out_rate)
    final_size = len(out_pcm_bytes)
    
    logger.debug(
        f"[Audio Pipeline] mulaw_to_pcm16: size_in={original_size}B, "
        f"hex_start={first_16_hex}, rate_in={in_rate}Hz, rate_out={out_rate}Hz, "
        f"channels=1, codec_out=pcm16, unencoded_len={unencoded_len}B, size_out={final_size}B"
    )
    return out_pcm_bytes


async def alaw_to_pcm(
    alaw_bytes: bytes, in_rate: int, out_rate: int, resampler: BaseAudioResampler
) -> bytes:
    """Convert A-law encoded audio to PCM and optionally resample.

    Args:
        alaw_bytes: A-law encoded audio data as raw bytes.
        in_rate: Original sample rate of the A-law audio in Hz.
        out_rate: Desired output sample rate in Hz.
        resampler: Audio resampler instance for rate conversion.

    Returns:
        PCM audio data as raw bytes at the specified output rate.
    """
    # Convert a-law to PCM
    in_pcm_bytes = audioop.alaw2lin(alaw_bytes, 2)

    # Resample
    out_pcm_bytes = await resampler.resample(in_pcm_bytes, in_rate, out_rate)

    return out_pcm_bytes


async def pcm_to_alaw(pcm_bytes: bytes, in_rate: int, out_rate: int, resampler: BaseAudioResampler):
    """Convert PCM audio to A-law encoding and optionally resample.

    Args:
        pcm_bytes: PCM audio data as raw bytes (16-bit signed integers).
        in_rate: Original sample rate of the PCM audio in Hz.
        out_rate: Desired output sample rate in Hz.
        resampler: Audio resampler instance for rate conversion.

    Returns:
        A-law encoded audio data as raw bytes at the specified output rate.
    """
    # Resample
    in_pcm_bytes = await resampler.resample(pcm_bytes, in_rate, out_rate)

    # Convert PCM to μ-law
    out_alaw_bytes = audioop.lin2alaw(in_pcm_bytes, 2)

    return out_alaw_bytes


def is_silence(pcm_bytes: bytes) -> bool:
    """Determine if an audio sample contains silence by checking amplitude levels.

    This function analyzes raw PCM audio data to detect silence by comparing
    the maximum absolute amplitude against a predefined threshold. The audio
    is expected to be clean speech or complete silence without background noise.

    Args:
        pcm_bytes: Raw PCM audio data as bytes (16-bit signed integers).

    Returns:
        bool: True if the audio sample is considered silence (below threshold),
              False otherwise.

    Note:
        Normal speech typically produces amplitude values between ±500 to ±5000,
        depending on factors like loudness and microphone gain. The threshold
        (SPEAKING_THRESHOLD) is set well below typical speech levels to
        reliably detect silence vs. speech.
    """
    # Convert raw audio bytes to a NumPy array of int16 samples
    audio_data = np.frombuffer(pcm_bytes, dtype=np.int16)

    # Check the maximum absolute amplitude in the frame
    max_value = np.abs(audio_data).max()

    # If max value is lower than SPEAKING_THRESHOLD, consider it as silence
    return max_value <= SPEAKING_THRESHOLD
