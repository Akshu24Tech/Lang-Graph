import os
import tempfile
import requests
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

class VoiceIntegration:
    """Simple Deepgram voice integration using HTTP requests."""
    
    def __init__(self):
        """Initialize Deepgram integration."""
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        self.base_url = "https://api.deepgram.com/v1"
        
    def is_available(self) -> bool:
        """Check if voice features are available."""
        return self.api_key is not None
    
    def text_to_speech(self, text: str, voice: str = "aura-asteria-en") -> Optional[bytes]:
        """
        Convert text to speech using Deepgram Aura API.
        
        Args:
            text: Text to convert to speech
            voice: Voice model to use
            
        Returns:
            Audio bytes or None if failed
        """
        if not self.api_key:
            print("❌ No Deepgram API key available")
            return None
        
        try:
            # Use the correct Deepgram Aura endpoint
            url = "https://api.deepgram.com/v1/speak"
            
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Correct payload format for Deepgram Aura
            payload = {
                "text": text
            }
            
            # Add query parameters for voice settings
            params = {
                "model": voice,
                "encoding": "mp3"
            }
            
            print(f"🔊 Making TTS request to Deepgram...")
            print(f"   Text length: {len(text)} chars")
            print(f"   Voice: {voice}")
            print(f"   URL: {url}")
            print(f"   Params: {params}")
            
            response = requests.post(url, json=payload, headers=headers, params=params, timeout=30)
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                audio_data = response.content
                print(f"✅ TTS Success! Generated {len(audio_data)} bytes")
                return audio_data
            else:
                print(f"❌ TTS Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ TTS Exception: {e}")
            return None
    
    def speech_to_text(self, audio_bytes: bytes, mimetype: str = "audio/wav") -> Optional[str]:
        """
        Convert speech to text using Deepgram API.
        
        Args:
            audio_bytes: Audio data to transcribe
            mimetype: MIME type of audio data
            
        Returns:
            Transcribed text or None if failed
        """
        if not self.api_key:
            return None
        
        try:
            url = f"{self.base_url}/listen"
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": mimetype
            }
            
            params = {
                "model": "nova-2",
                "smart_format": "true",
                "punctuate": "true"
            }
            
            response = requests.post(
                url, 
                headers=headers, 
                params=params, 
                data=audio_bytes,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("results") and result["results"].get("channels"):
                    transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
                    return transcript.strip()
            else:
                print(f"STT Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"STT Error: {e}")
            return None
    
    def process_voice_command(self, transcript: str) -> Dict[str, any]:
        """
        Process voice command transcript and return action.
        
        Args:
            transcript: Transcribed voice command
            
        Returns:
            Dictionary with action and parameters
        """
        if not transcript:
            return {"action": "unknown", "confidence": "low", "transcript": ""}
            
        transcript = transcript.lower().strip()
        
        # Define command patterns
        approve_patterns = ["approve", "yes", "accept", "good", "send it", "looks good"]
        reject_patterns = ["reject", "no", "decline", "bad", "try again", "regenerate"]
        edit_patterns = ["edit", "modify", "change", "update", "revise"]
        read_patterns = ["read", "play", "listen", "hear", "speak"]
        
        # Check for commands
        if any(pattern in transcript for pattern in approve_patterns):
            return {"action": "approve", "confidence": "high"}
        
        elif any(pattern in transcript for pattern in reject_patterns):
            return {"action": "reject", "confidence": "high"}
        
        elif any(pattern in transcript for pattern in edit_patterns):
            return {"action": "edit", "confidence": "medium"}
        
        elif any(pattern in transcript for pattern in read_patterns):
            return {"action": "read", "confidence": "high"}
        
        else:
            return {"action": "unknown", "confidence": "low", "transcript": transcript}

# Global voice integration instance
voice_integration = VoiceIntegration()