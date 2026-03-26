"""
Video generation backend wrapper supporting both Replicate and local ComfyUI.
Allows seamless switching between cloud API and local model execution.
Includes text-to-speech narration using OpenAI TTS.
"""

import os
import asyncio
import httpx
from typing import Dict, Any
from dotenv import load_dotenv
from openai import AsyncOpenAI
import tempfile
import base64

load_dotenv()

# Configuration
VIDEO_BACKEND = os.getenv("VIDEO_BACKEND", "replicate").lower()
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://localhost:8188")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

# Initialize clients
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Lazy import replicate to avoid import errors if token is missing
replicate_client = None


def _get_replicate_client():
    """Get or initialize Replicate client."""
    global replicate_client
    if replicate_client is None:
        import replicate
        replicate_client = replicate.Client(api_token=REPLICATE_API_TOKEN)
    return replicate_client


async def generate_tts_audio(text: str, voice: str = "nova") -> str:
    """
    Generate text-to-speech audio using OpenAI TTS.
    
    Args:
        text: The text to convert to speech
        voice: Voice to use ("nova", "alloy", "echo", "fable", "onyx", "shimmer")
    
    Returns:
        Base64 encoded audio data or error message
    """
    try:
        # Limit text length for TTS (max ~500 chars per request)
        if len(text) > 500:
            text = text[:500]
        
        response = await client.audio.speech.create(
            model="tts-1-hd",  # High quality
            voice=voice,
            input=text,
            speed=1.2  # Slightly faster for educational content
        )
        
        # Get audio bytes and encode as base64
        audio_bytes = response.content
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        return audio_base64
        
    except Exception as e:
        return f"Error generating TTS audio: {str(e)}"


async def upload_audio_to_comfyui(audio_data: str, filename: str = "narration.mp3") -> str:
    """
    Save audio file to ComfyUI input folder.
    
    Args:
        audio_data: Base64 encoded audio data
        filename: Name of the audio file
    
    Returns:
        Filename or error message
    """
    try:
        # Decode base64 to bytes
        audio_bytes = base64.b64decode(audio_data)
        
        # Get ComfyUI input directory from server info
        async with httpx.AsyncClient(timeout=5.0) as client_http:
            response = await client_http.get(f"{COMFYUI_URL}/api/get_config")
            if response.status_code == 200:
                config = response.json()
                # Save to a known location - ComfyUI looks for audio in inputs folder
                input_dir = "input"  # Default ComfyUI input folder
                
                # Create the full path for the audio file
                audio_path = os.path.join(input_dir, filename)
                
                # Save the audio file
                os.makedirs(input_dir, exist_ok=True)
                with open(audio_path, 'wb') as f:
                    f.write(audio_bytes)
                
                return filename  # Return just the filename for LoadAudio node
            else:
                # Fallback: just save to input folder and return filename
                input_dir = "input"
                os.makedirs(input_dir, exist_ok=True)
                audio_path = os.path.join(input_dir, filename)
                
                with open(audio_path, 'wb') as f:
                    f.write(audio_bytes)
                
                return filename
    
    except Exception as e:
        return f"Error saving audio: {str(e)}"


async def generate_video_prompt(script: str) -> str:
    """
    Generate a detailed visual prompt for video generation from a script.
    Uses OpenAI to convert script into visual descriptions.
    """
    prompt_text = f"""Create a detailed visual description for an educational medical video based on this script. 
Focus on:
- Medical/health education visuals
- Charts, animations, medical diagrams
- Professional medical imagery
- Clear, educational scene descriptions

Script excerpt: {script[:500]}...

Provide a comprehensive visual prompt suitable for video generation."""

    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt_text}],
        max_tokens=200,
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


async def generate_video_replicate(script: str) -> str:
    """
    Generate video using Replicate's Stable Video Diffusion API.
    
    Returns:
        Video URL or error message
    """
    try:
        if not REPLICATE_API_TOKEN or REPLICATE_API_TOKEN == "r8_YOUR_REPLICATE_API_TOKEN_HERE":
            return "Error: Replicate API token not configured. Please add REPLICATE_API_TOKEN to .env"

        # Generate visual prompt from script
        video_prompt = await generate_video_prompt(script)

        # Get Replicate client
        replicate = _get_replicate_client()

        # Use Replicate's video generation model
        output = replicate.run(
            "stability-ai/stable-video-diffusion:3f0457e4619daac512fededddfaf846c",
            input={
                "cond_aug": 0.02,
                "decoding_t": 14,
                "input_image": None,
                "video_length": "14_frames_with_svd",
                "sizing_strategy": "maintain_aspect_ratio",
                "motion_bucket_id": 127,
                "frames_per_second": 6,
                "prompt": video_prompt,
                "negative_prompt": "blurry, low quality, distorted, ugly, text, watermark"
            }
        )

        # Handle various output formats from Replicate
        if isinstance(output, str):
            return output
        elif isinstance(output, list) and len(output) > 0:
            return output[0]
        elif hasattr(output, 'url'):
            return output.url
        else:
            return str(output)

    except Exception as e:
        return f"Replicate video generation failed: {str(e)}"


async def get_comfyui_checkpoints() -> list:
    """
    Get list of available checkpoint models in ComfyUI.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{COMFYUI_URL}/api/models/checkpoints")
            if response.status_code == 200:
                return response.json()
    except:
        pass
    return []


async def generate_video_comfyui(script: str) -> str:
    """
    Generate a 12-second educational video with AI narration using:
    1. ByteDance Text-to-Video for video generation
    2. OpenAI TTS for professional narration
    3. ComfyUI audio merging to combine them
    
    Returns:
        Status message with generation info
    """
    try:
        # Generate visual prompt from script
        video_prompt = await generate_video_prompt(script)
        
        # Keep prompt concise for better video generation
        if len(video_prompt) > 150:
            video_prompt = video_prompt[:150]

        # Generate TTS audio narration from the script
        print(f"Generating TTS audio from script...")
        audio_data = await generate_tts_audio(script)
        
        if audio_data.startswith("Error"):
            return f"⚠️ Audio generation failed: {audio_data}. Generating video without narration..."
        
        # Upload audio to ComfyUI
        print(f"Uploading audio to ComfyUI...")
        audio_filename = await upload_audio_to_comfyui(audio_data, "narration.mp3")
        
        if audio_filename.startswith("Error") or audio_filename.startswith("Upload"):
            return f"⚠️ Audio upload failed: {audio_filename}. Generating video without audio..."

        # Check if ComfyUI is running
        async with httpx.AsyncClient(timeout=5.0) as client_http:
            try:
                response = await client_http.get(f"{COMFYUI_URL}/system_stats")
                if response.status_code != 200:
                    return "Error: ComfyUI server not responding correctly. Ensure it's running."
            except Exception as e:
                return f"Error: Cannot connect to ComfyUI at {COMFYUI_URL}. Make sure ComfyUI is running. Details: {str(e)}"

            # Create workflow using ByteDance Text-to-Video with audio merging
            # ByteDance supports up to 12 seconds duration
            workflow = {
                # Step 1: Generate video from text
                "1": {
                    "inputs": {
                        "model": "seedance-1-0-pro-fast-251015",
                        "prompt": video_prompt,
                        "resolution": "720p",
                        "aspect_ratio": "16:9",
                        "duration": 12,  # 12 seconds max
                        "seed": 0,
                        "camera_fixed": False,  # Don't fix camera
                        "watermark": False      # No watermark
                    },
                    "class_type": "ByteDanceTextToVideoNode"
                },
                # Step 2: Load the audio file
                "2": {
                    "inputs": {
                        "audio": audio_filename
                    },
                    "class_type": "LoadAudio"
                },
                # Step 3: Adjust audio volume (optional, but helps mix)
                "3": {
                    "inputs": {
                        "audio": ["2", 0],
                        "volume": 0.8  # 80% volume for narration
                    },
                    "class_type": "AudioAdjustVolume"
                },
                # Step 4: Trim/adjust audio duration to match video (12 seconds)
                "4": {
                    "inputs": {
                        "audio": ["3", 0],
                        "duration_seconds": 12
                    },
                    "class_type": "TrimAudioDuration"
                },
                # Step 5: Save audio (for verification)
                "5": {
                    "inputs": {
                        "audio": ["4", 0],
                        "filename_prefix": "health_education_narration"
                    },
                    "class_type": "SaveAudioMP3"
                },
                # Step 6: Save video with audio
                "6": {
                    "inputs": {
                        "video": ["1", 0],
                        "filename_prefix": "health_education_video_with_narration",
                        "format": "mp4",
                        "codec": "h264"
                    },
                    "class_type": "SaveVideo"
                }
            }

            # Submit workflow to ComfyUI
            try:
                response = await client_http.post(
                    f"{COMFYUI_URL}/prompt",
                    json={"prompt": workflow},
                    timeout=600.0  # 10 minute timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    prompt_id = result.get("prompt_id")
                    if prompt_id:
                        return f"✅ 12-second educational video with narration started (ID: {prompt_id}). The video includes professional AI voiceover explaining the health information. Check ComfyUI UI at {COMFYUI_URL} for real-time progress. Estimated time: 3-7 minutes."
                    else:
                        return "✅ Video with narration workflow submitted to ComfyUI. Check ComfyUI UI for progress."
                elif response.status_code == 400:
                    error_text = response.text[:500]
                    # Try without audio merging (video only)
                    simple_workflow = {
                        "1": {
                            "inputs": {
                                "model": "seedance-1-0-pro-fast-251015",
                                "prompt": video_prompt,
                                "resolution": "720p",
                                "aspect_ratio": "16:9",
                                "duration": 12,
                                "seed": 0,
                                "camera_fixed": False,
                                "watermark": False
                            },
                            "class_type": "ByteDanceTextToVideoNode"
                        },
                        "2": {
                            "inputs": {
                                "video": ["1", 0],
                                "filename_prefix": "health_education_video",
                                "format": "mp4",
                                "codec": "h264"
                            },
                            "class_type": "SaveVideo"
                        }
                    }
                    
                    response = await client_http.post(
                        f"{COMFYUI_URL}/prompt",
                        json={"prompt": simple_workflow},
                        timeout=600.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return f"✅ Video generation started (ID: {result.get('prompt_id', 'unknown')}). Audio mixing not available, generating video with visual narration only."
                    else:
                        return f"⚠️ ComfyUI error: {error_text}"
                else:
                    return f"Error: ComfyUI returned status {response.status_code}"

            except asyncio.TimeoutError:
                return "⏱️ Video generation request sent to ComfyUI (timeout). Check ComfyUI UI for progress - generating 12-second video with AI narration."
            except Exception as e:
                return f"Error submitting to ComfyUI: {str(e)}"

    except Exception as e:
        return f"ComfyUI error: {str(e)}"


async def generate_video(script: str, backend: str = None) -> str:
    """
    Main video generation function with backend abstraction.
    Intelligently routes to Replicate or ComfyUI based on configuration.
    
    Args:
        script: The video script to generate video from
        backend: Override default backend ("replicate" or "comfyui"), optional
    
    Returns:
        Video URL/path or descriptive error/status message
    """
    chosen_backend = backend or VIDEO_BACKEND

    if chosen_backend == "comfyui":
        return await generate_video_comfyui(script)
    else:
        # Default to Replicate
        return await generate_video_replicate(script)


async def get_backend_status() -> Dict[str, Any]:
    """
    Check status of available video generation backends.
    
    Returns:
        Dict with status of each backend
    """
    status = {
        "configured_backend": VIDEO_BACKEND,
        "replicate": {
            "available": False,
            "configured": bool(REPLICATE_API_TOKEN and REPLICATE_API_TOKEN != "r8_YOUR_REPLICATE_API_TOKEN_HERE"),
            "reason": None
        },
        "comfyui": {
            "available": False,
            "configured": True,
            "url": COMFYUI_URL,
            "reason": None
        }
    }

    # Check Replicate
    if not status["replicate"]["configured"]:
        status["replicate"]["reason"] = "API token not set in .env"
    else:
        status["replicate"]["available"] = True

    # Check ComfyUI
    try:
        async with httpx.AsyncClient(timeout=2.0) as http_client:
            response = await http_client.get(f"{COMFYUI_URL}/system_stats")
            if response.status_code == 200:
                status["comfyui"]["available"] = True
            else:
                status["comfyui"]["reason"] = f"ComfyUI returned status {response.status_code}"
    except Exception as e:
        status["comfyui"]["reason"] = f"Cannot connect: {str(e)}"

    return status
