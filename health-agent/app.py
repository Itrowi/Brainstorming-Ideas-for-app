from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import httpx
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai_helper import get_professional_explanation, get_beginner_explanation, get_video_explanation, get_disease_overview, generate_video_from_script
import re


load_dotenv()

app = FastAPI()

# Add session middleware
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Users database (username: password)
USERS = {
    "admin": "admin",
    "manager": "manager",
    "doctor": "doctor",
    "student": "student",
    "user": "user",
}

# User roles
USER_ROLES = {
    "admin": "admin",
    "manager": "manager",
    "doctor": "professional",
    "student": "beginner",
    "user": "beginner",
}

NCBI_API_KEY = os.getenv("NCBI_API_KEY")

PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


async def search_pubmed(term: str, retmax: int = 5):
    params = {
        "db": "pubmed",
        "term": term,
        "retmode": "json",
        "retmax": str(retmax),
    }
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(PUBMED_SEARCH_URL, params=params)
        r.raise_for_status()
        data = r.json()
        ids = data.get("esearchresult", {}).get("idlist", [])
        return ids


async def fetch_abstract(pmid: str):
    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml",
    }
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(PUBMED_FETCH_URL, params=params)
        r.raise_for_status()
        xml = r.text
        soup = BeautifulSoup(xml, "xml")
        abstract_text = ""
        for abst in soup.find_all("AbstractText"):
            abstract_text += abst.get_text() + " "
        title = soup.find("ArticleTitle").get_text() if soup.find("ArticleTitle") else ""
        return {"pmid": pmid, "title": title, "abstract": abstract_text.strip()}


def get_pubmed_url(pmid: str) -> str:
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"


def simplify_text(text: str) -> str:
    replacements = {
        "randomized": "randomly assigned",
        "placebo": "inactive treatment",
        "cohort": "group of people",
        "mortality": "death rate",
        "morbidity": "illness",
    }

    text = re.sub(r"\([^)]*\)", "", text)
    for k, v in replacements.items():
        text = re.sub(rf"\b{k}\b", v, text, flags=re.IGNORECASE)

    sentences = re.split(r"(?<=[.!?]) +", text)
    short = []
    for s in sentences:
        if len(s) > 300:
            parts = [s[i:i+200] for i in range(0, len(s), 200)]
            short.extend(parts)
        else:
            short.append(s)
    return " ".join(short)


def is_authenticated(request: Request) -> bool:
    return "user" in request.session


def get_user_role(request: Request) -> str:
    username = request.session.get("user")
    return USER_ROLES.get(username, "beginner")


# ============ LOGIN ROUTES ============

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if is_authenticated(request):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    template = templates.env.get_template("login.html")
    html_content = template.render(request=request)
    return HTMLResponse(content=html_content)


@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username in USERS and USERS[username] == password:
        request.session["user"] = username
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    else:
        template = templates.env.get_template("login.html")
        html_content = template.render(request=request, error="Invalid username or password")
        return HTMLResponse(content=html_content)


@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    username = request.session.get("user")
    role = get_user_role(request)
    
    template = templates.env.get_template("dashboard.html")
    html_content = template.render(request=request, username=username, role=role)
    return HTMLResponse(content=html_content)


# ============ EXPLANATION ROUTES ============

@app.post("/explain", response_class=HTMLResponse)
async def explain(request: Request, topic: str = Form(...), output_type: str = Form(default="text")):
    if not is_authenticated(request):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    username = request.session.get("user")
    role = get_user_role(request)
    
    # Generate disease overview
    if role == "professional":
        disease_overview = await get_disease_overview(topic, "professional")
    elif role == "beginner":
        disease_overview = await get_disease_overview(topic, "beginner")
    elif role == "admin" or role == "manager":
        disease_overview = await get_disease_overview(topic, "professional")
    else:
        disease_overview = await get_disease_overview(topic, "beginner")
    
    ids = await search_pubmed(topic, retmax=5)
    results = []
    
    for pmid in ids:
        item = await fetch_abstract(pmid)
        abstract = item.get("abstract", "")
        
        if abstract:
            # Generate role-based explanation
            if role == "professional":
                explanation = await get_professional_explanation(abstract)
            elif role == "beginner":
                explanation = await get_beginner_explanation(abstract)
            elif role == "admin" or role == "manager":
                # Managers get professional explanations
                explanation = await get_professional_explanation(abstract)
            else:
                explanation = simplify_text(abstract)
        else:
            explanation = "No abstract available."
        
        results.append({
            "pmid": pmid,
            "title": item.get("title"),
            "explanation": explanation,
            "pubmed_url": get_pubmed_url(pmid),
            "output_type": output_type,
        })
    
    context = {
        "request": request,
        "topic": topic,
        "disease_overview": disease_overview,
        "results": results,
        "username": username,
        "role": role,
        "output_type": output_type,
    }
    
    template = templates.env.get_template("results.html")
    html_content = template.render(**context)
    return HTMLResponse(content=html_content)


@app.post("/video-explanation", response_class=HTMLResponse)
async def video_explanation(request: Request, topic: str = Form(...), generate_video: str = Form(default="false")):
    if not is_authenticated(request):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    username = request.session.get("user")
    role = get_user_role(request)
    
    # Get search results first
    ids = await search_pubmed(topic, retmax=3)
    results = []
    
    for pmid in ids:
        item = await fetch_abstract(pmid)
        abstract = item.get("abstract", "")
        
        if abstract:
            # Generate video script based on role
            if role == "professional":
                video_script = await get_video_explanation(abstract, "professional")
            elif role == "beginner":
                video_script = await get_video_explanation(abstract, "beginner")
            elif role == "admin" or role == "manager":
                video_script = await get_video_explanation(abstract, "professional")
            else:
                video_script = await get_video_explanation(abstract, "beginner")
            
            # Generate actual video if requested
            video_url = None
            if generate_video == "true":
                try:
                    video_url = await generate_video_from_script(video_script, role)
                except Exception as e:
                    video_url = f"Video generation failed: {str(e)}"
        else:
            video_script = "No content available for video generation."
            video_url = None
        
        results.append({
            "pmid": pmid,
            "title": item.get("title"),
            "video_script": video_script,
            "video_url": video_url,
            "pubmed_url": get_pubmed_url(pmid),
        })
    
    context = {
        "request": request,
        "topic": topic,
        "results": results,
        "username": username,
        "role": role,
        "generate_video": generate_video == "true",
    }
    
    template = templates.env.get_template("video_results.html")
    html_content = template.render(**context)
    return HTMLResponse(content=html_content)
