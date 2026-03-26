# Video Generation Backend Guide

Your health-agent now supports dual video generation backends! Switch between Replicate (cloud) and ComfyUI (local) seamlessly.

## Current Configuration

Check `.env` file for:
```
VIDEO_BACKEND=replicate  # or "comfyui"
COMFYUI_URL=http://localhost:8188
REPLICATE_API_TOKEN=your_token_here
```

## Backend Comparison

| Feature | Replicate | ComfyUI |
|---------|-----------|---------|
| **Cost** | Pay per generation | Free (one-time setup) |
| **Speed** | Fast (~1-2 min) | Variable (2-10 min) |
| **Internet** | Required | Not needed after setup |
| **Setup** | 1. Get API token | 1. Download & install |
| **Hardware** | Cloud-based | Needs GPU (~8GB+ VRAM) |
| **Quality** | High | Very high (more control) |

## Quick Setup

### Option 1: Use Replicate (Recommended for quick start)

1. Go to [replicate.com](https://replicate.com)
2. Sign up for free account
3. Get your API token from dashboard
4. Add to `.env`:
   ```
   REPLICATE_API_TOKEN=r8_YOUR_TOKEN_HERE
   VIDEO_BACKEND=replicate
   ```

### Option 2: Use ComfyUI (Recommended for power users)

1. Download ComfyUI from [github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
2. Install on your machine (requires Python 3.10+, NVIDIA GPU recommended)
3. Download required models (Stable Video Diffusion ~5GB)
4. Start ComfyUI server:
   ```bash
   python main.py
   ```
   Server runs at `http://localhost:8188`

5. Update `.env`:
   ```
   VIDEO_BACKEND=comfyui
   COMFYUI_URL=http://localhost:8188
   ```

6. Restart health-agent and it will auto-detect ComfyUI

## Check Backend Status

In your Python code, check which backends are available:

```python
from video_backend import get_backend_status
import asyncio

async def check():
    status = await get_backend_status()
    print(status)

asyncio.run(check())
```

## Override Backend Per Request

Generate video with specific backend:

```python
from video_backend import generate_video
import asyncio

async def example():
    # Use ComfyUI specifically
    result = await generate_video(script_text, backend="comfyui")
    
    # Or use Replicate
    result = await generate_video(script_text, backend="replicate")

asyncio.run(example())
```

## Switching Backends

Simply change `VIDEO_BACKEND` in `.env` and restart the server:

```bash
# Switch to ComfyUI
# Edit: VIDEO_BACKEND=comfyui
cd health-agent
python app.py
```

The system will automatically use the configured backend!

## Troubleshooting

**"Cannot connect to ComfyUI"**
- Make sure ComfyUI server is running on `http://localhost:8188`
- Check `COMFYUI_URL` in `.env`

**"Replicate API token not set"**
- Get token from [replicate.com](https://replicate.com)
- Add to `.env` as `REPLICATE_API_TOKEN=...`

**"Video generation failed"**
- Check which backend is configured
- Ensure backend is available (see Backend Status)
- Check API quota/credits
