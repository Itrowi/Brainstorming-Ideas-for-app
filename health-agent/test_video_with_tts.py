import asyncio
from openai_helper import get_video_explanation
from video_backend import generate_video

async def test_full_flow():
    """Test complete flow: script → video with narration"""
    
    # Example health abstract
    abstract = """
    Diabetes is a chronic disease characterized by elevated blood glucose levels.
    Type 2 diabetes accounts for 90-95% of all diabetes cases.
    Management includes lifestyle changes, medication, and regular monitoring.
    Early intervention significantly improves outcomes and reduces complications.
    """
    
    print("=== STEP 1: Generate Video Script ===")
    script = await get_video_explanation(abstract, 'beginner')
    print(f"Script generated ({len(script)} characters):\n{script[:200]}...\n")
    
    print("=== STEP 2: Generate Video with TTS Narration ===")
    result = await generate_video(script, backend='comfyui')
    print(result)
    
    print("\n=== CHECKING OUTPUT ===")
    import os
    if os.path.exists('input/narration.mp3'):
        size = os.path.getsize('input/narration.mp3')
        print(f"✅ Audio narration created: {size} bytes")
    
    print("\nCheck http://localhost:8188 for video generation progress!")

asyncio.run(test_full_flow())
