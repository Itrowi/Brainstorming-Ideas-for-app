# Health Explainer Agent 🏥

A role-based health information system that provides AI-powered explanations of medical research. Each user type receives explanations tailored to their expertise level.

## Features

### 🔐 Authentication System
- 5 pre-configured user roles with role-based access control
- Session-based authentication using FastAPI middleware
- Secure login page with credential protection

### 👥 User Roles

| Role | Username | Password | Explanation Level | Access |
|------|----------|----------|-------------------|---------|
| **Admin** | admin | admin | Professional | Full access to all features |
| **Manager** | manager | manager | Professional | Professional-level explanations |
| **Doctor** | doctor | doctor | Professional | Professional medical terminology |
| **Student** | student | student | Beginner | Simplified explanations |
| **User** | user | user | Beginner | Beginner-friendly format |

### 📝 Text Generation
- Search PubMed research database
- AI-powered explanations tailored to user expertise level
- Professional-level for doctors/managers (400-600 words, technical terminology)
- Beginner-level for students/users (150-250 words, simple language)
- Direct links to original research papers

### 🎬 Video Generation
- Generate AI-powered video scripts based on research abstracts
- Professional scripts (3-4 minutes) for healthcare professionals
- Beginner scripts (2-3 minutes) for general audience
- Download capability for editing and production

### 🔗 Source Attribution
- Every explanation includes a link to the original PubMed article
- Full citation information available
- Research transparency and educational integrity

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- OpenAI API key
- NCBI API key (PubMed access)

### Setup

1. **Clone or navigate to the health-agent folder**
```bash
cd health-agent
```

2. **Create a virtual environment** (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Create a `.env` file** with your API keys
```
OPENAI_API_KEY=your_openai_api_key_here
NCBI_API_KEY=your_ncbi_api_key_here
SECRET_KEY=your-secret-key-for-sessions
```

5. **Run the application**
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

6. **Access the application**
Open your browser and navigate to:
```
http://localhost:8000
```

## Usage

### Login
1. Visit the login page at `http://localhost:8000`
2. Enter credentials for one of the available users
3. You'll be redirected to your personalized dashboard

### Search for Health Topics
1. On the dashboard, enter a health topic in the text generation form
   - Examples: "type 2 diabetes", "cardiovascular disease", "anxiety disorders"
2. Click "Search & Explain"
3. The system will:
   - Search PubMed for relevant research
   - Generate explanations tailored to your role
   - Display results with source links

### Generate Video Scripts
1. On the dashboard, enter a topic in the video generation form
2. Click "Generate Script"
3. The system will generate a tailored video script
4. Copy or download the script for use in video creation

### Viewing Results
- **Professional Users** (Doctor, Manager, Admin):
  - Get detailed, technical explanations
  - Longer content with clinical implications
  - Professional medical terminology preserved

- **Beginner Users** (Student, User):
  - Get simplified, easy-to-understand explanations
  - Shorter content (2-3 minutes of reading)
  - Medical terms explained in simple language

## API Endpoints

### Authentication
- `GET /` - Login page
- `POST /login` - Process login credentials
- `GET /logout` - Logout and clear session
- `GET /dashboard` - User dashboard (requires authentication)

### Content Generation
- `POST /explain` - Generate text-based explanation
- `POST /video-explanation` - Generate video script

## Project Structure

```
health-agent/
├── app.py                 # Main FastAPI application
├── openai_helper.py       # OpenAI integration functions
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── static/
│   ├── style.css         # Global styles
│   ├── login.css         # Login page styles
│   ├── dashboard.css     # Dashboard styles
│   └── results.css       # Results page styles
└── templates/
    ├── login.html        # Login page
    ├── dashboard.html    # User dashboard
    ├── results.html      # Text results page
    └── video_results.html # Video script results page
```

## Technical Stack

- **Backend**: FastAPI (Python web framework)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **AI**: OpenAI GPT-3.5-turbo for explanations
- **Research Data**: PubMed API (NCBI)
- **Authentication**: Starlette Sessions
- **Web Scraping**: BeautifulSoup4

## Configuration

### Environment Variables

```
OPENAI_API_KEY        # Your OpenAI API key for GPT responses
NCBI_API_KEY          # Your NCBI API key for PubMed access
SECRET_KEY            # Session encryption key (change in production!)
```

## Important Notes

⚠️ **Disclaimer**: This application is for educational purposes only. The information provided is NOT a substitute for professional medical advice. Always consult a qualified healthcare provider for medical concerns.

### Production Deployment

Before deploying to production:
1. Change the `SECRET_KEY` in your `.env` file
2. Use environment variables for all sensitive data
3. Enable HTTPS
4. Set `DEBUG=False` in production
5. Use a production-grade ASGI server (e.g., Gunicorn)
6. Implement proper rate limiting and request validation
7. Add database storage for user sessions instead of in-memory

## Troubleshooting

### "Invalid API Key" Error
- Verify your OpenAI and NCBI API keys are correct
- Check that they're properly set in the `.env` file

### "No Results Found"
- Try a different search term
- Ensure your internet connection is working
- Check that NCBI API is accessible

### Login Issues
- Make sure you're using the correct username/password
- Clear your browser cache and try again
- Check that sessions middleware is properly configured

## Future Enhancements

- [ ] User registration and custom authentication
- [ ] Database integration for storing searches and favorites
- [ ] Multi-language support
- [ ] Email delivery of explanations
- [ ] PDF export functionality
- [ ] User preference customization
- [ ] Advanced search filters
- [ ] Integration with medical knowledge bases
- [ ] Text-to-speech for explanations
- [ ] Real-time streaming of AI-generated content

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review your API key configuration
3. Check the application logs for error details

## License

This project is provided as-is for educational and research purposes.

---

**Last Updated**: March 2026
**Version**: 1.0
**Status**: Active Development
