"""Speech-to-Text service supporting Whisper and GCP Speech-to-Text."""

import asyncio
import io
import tempfile
from typing import Optional, Dict, Any, List
import whisper
from api.utils.config import settings


class STTService:
    """Speech-to-Text service with multiple provider support."""
    
    def __init__(self):
        self.provider = settings.stt_provider
        self.whisper_model: Optional[whisper.Whisper] = None
        self.gcp_client = None
        
        # Whisper model configuration
        self.whisper_model_size = "base"  # tiny, base, small, medium, large
        self.whisper_language = "en"
        
    async def transcribe_audio(
        self, 
        audio_data: bytes, 
        format: str = "pcm",
        sample_rate: int = 16000,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio bytes
            format: Audio format (pcm, wav, mp3, etc.)
            sample_rate: Audio sample rate
            language: Language code (optional)
            
        Returns:
            Dictionary with transcription results
        """
        try:
            if self.provider == "whisper":
                return await self._transcribe_whisper(audio_data, format, sample_rate, language)
            elif self.provider == "gcp":
                return await self._transcribe_gcp(audio_data, format, sample_rate, language)
            else:
                raise ValueError(f"Unsupported STT provider: {self.provider}")
                
        except Exception as e:
            print(f"STT transcription error: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "language": language or "en",
                "error": str(e)
            }
    
    async def transcribe_stream(
        self, 
        audio_chunks: List[bytes],
        format: str = "pcm",
        sample_rate: int = 16000,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe a stream of audio chunks.
        
        Args:
            audio_chunks: List of audio data chunks
            format: Audio format
            sample_rate: Audio sample rate
            language: Language code
            
        Returns:
            Dictionary with transcription results
        """
        try:
            # Combine chunks into single audio data
            combined_audio = b"".join(audio_chunks)
            return await self.transcribe_audio(combined_audio, format, sample_rate, language)
            
        except Exception as e:
            print(f"Stream transcription error: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "language": language or "en",
                "error": str(e)
            }
    
    async def _transcribe_whisper(
        self, 
        audio_data: bytes, 
        format: str,
        sample_rate: int,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe using OpenAI Whisper."""
        try:
            # Ensure model is loaded
            await self._ensure_whisper_model()
            
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Run transcription in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self.whisper_model.transcribe(temp_file_path, language=language or self.whisper_language)
                )
                
                return {
                    "text": result["text"].strip(),
                    "confidence": result.get("confidence", 0.0),
                    "language": result.get("language", language or "en"),
                    "segments": result.get("segments", []),
                    "provider": "whisper"
                }
                
            finally:
                # Clean up temporary file
                import os
                os.unlink(temp_file_path)
                
        except Exception as e:
            print(f"Whisper transcription error: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "language": language or "en",
                "error": str(e),
                "provider": "whisper"
            }
    
    async def _transcribe_gcp(
        self, 
        audio_data: bytes, 
        format: str,
        sample_rate: int,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe using Google Cloud Speech-to-Text."""
        # This would implement GCP Speech-to-Text
        # For now, return placeholder
        return {
            "text": "",
            "confidence": 0.0,
            "language": language or "en",
            "error": "GCP Speech-to-Text not implemented yet",
            "provider": "gcp"
        }
    
    async def _ensure_whisper_model(self):
        """Ensure Whisper model is loaded."""
        if self.whisper_model is None:
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.whisper_model = await loop.run_in_executor(
                None,
                whisper.load_model,
                self.whisper_model_size
            )
    
    async def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats."""
        if self.provider == "whisper":
            return ["wav", "mp3", "m4a", "ogg", "flac"]
        elif self.provider == "gcp":
            return ["wav", "flac", "mp3", "m4a", "ogg"]
        else:
            return []
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        if self.provider == "whisper":
            # Whisper supports many languages
            return ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
        elif self.provider == "gcp":
            # GCP supports many languages
            return ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR", "ru-RU", "ja-JP", "ko-KR", "zh-CN"]
        else:
            return []
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the STT model."""
        if self.provider == "whisper":
            await self._ensure_whisper_model()
            return {
                "provider": "whisper",
                "model_size": self.whisper_model_size,
                "language": self.whisper_language,
                "model_loaded": self.whisper_model is not None
            }
        elif self.provider == "gcp":
            return {
                "provider": "gcp",
                "project_id": settings.gcp_project_id,
                "credentials_path": settings.gcp_credentials_path
            }
        else:
            return {"provider": "unknown"}
    
    async def close(self):
        """Clean up resources."""
        if self.whisper_model:
            # Clear model from memory
            del self.whisper_model
            self.whisper_model = None


# Global STT service instance
stt_service = STTService()
