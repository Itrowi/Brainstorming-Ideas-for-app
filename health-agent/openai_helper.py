import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from video_backend import generate_video, get_backend_status

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def get_professional_explanation(text: str) -> str:
    """
    Generate a professional-level explanation for doctors and managers.
    - Longer, detailed explanations (400-600 words)
    - Uses appropriate medical terminology
    - Includes clinical implications
    """
    prompt = (
        "You are a medical expert writing for healthcare professionals (doctors, managers). "
        "Provide a detailed, professional explanation of the following research abstract. "
        "Include clinical implications and key findings. Use appropriate medical terminology. "
        "Keep the explanation between 400-600 words.\n\n" + text
    )
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()


async def get_beginner_explanation(text: str) -> str:
    """
    Generate a beginner-friendly explanation for students and general users.
    - Shorter, simpler explanations (150-250 words)
    - Avoids medical jargon or explains it simply
    - Written for a 12-year-old reading level
    """
    prompt = (
        "You are a friendly health educator writing for students and general public. "
        "Explain the following medical research in the simplest way possible. "
        "Use short sentences and avoid medical jargon. If you must use medical terms, explain them simply. "
        "Think of it like explaining to a curious teenager. Keep it between 150-250 words.\n\n" + text
    )
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.6,
    )
    return response.choices[0].message.content.strip()


async def get_video_explanation(text: str, level: str = "beginner") -> str:
    """
    Generate a video script based on the research abstract.
    - Professional level: 3-4 minute script (professional tone)
    - Beginner level: 2-3 minute script (conversational tone)
    """
    if level == "professional":
        prompt = (
            "You are a medical educator creating a video script for healthcare professionals. "
            "Write a 3-4 minute video script (approximately 600-800 words) based on this research abstract. "
            "Include an engaging introduction, key findings, clinical implications, and conclusion. "
            "Use professional medical language suitable for doctors and managers.\n\n" + text
        )
        max_tokens = 1000
    else:
        prompt = (
            "You are a friendly health educator creating a short educational video for students and the general public. "
            "Write a 2-3 minute video script (approximately 300-400 words) based on this research abstract. "
            "Start with a catchy hook, explain the research simply, and end with practical takeaways. "
            "Use conversational language that anyone can understand.\n\n" + text
        )
        max_tokens = 600

    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


async def generate_video_from_script(script: str, level: str = "beginner") -> str:
    """
    Generate a video from a script using the configured backend.
    
    Supports two backends:
    - Replicate: Cloud-based video generation (requires API token)
    - ComfyUI: Local video generation (requires ComfyUI server running)
    
    Returns the video URL, local path, or a status/error message.
    """
    return await generate_video(script)


async def get_disease_overview(topic: str, level: str = "beginner") -> str:
    """
    Generate a brief overview/summary of a disease or health topic.
    - Beginner level: Simple explanation of what the disease is (150-200 words)
    - Professional level: Medical definition and overview (200-250 words)
    """
    if level == "professional":
        prompt = (
            f"You are a medical expert. Provide a brief professional medical overview of {topic}. "
            "Include what it is, who it affects, causes, and general symptoms. "
            "Use medical terminology. Keep it between 200-250 words and structured with clear key points."
        )
        max_tokens = 400
    else:
        prompt = (
            f"You are a friendly health educator. Provide a brief, simple explanation of {topic}. "
            "Explain what it is, who can get it, what causes it, and common symptoms. "
            "Use simple language that anyone can understand. Keep it between 150-200 words."
        )
        max_tokens = 300

    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()
