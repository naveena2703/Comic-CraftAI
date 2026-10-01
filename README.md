# ComicCraft

ComicCraft is an AI-powered web application that converts a user story idea into a five-panel comic.

## Technologies

- Python
- FastAPI
- Jinja2
- Gemini
- Hugging Face
- Diffusers
- Pillow
- FPDF2
- Pydantic

## Application Pipeline

User
    |
    v
Frontend
    |
    v
FastAPI
    |
    +----> Gemini Outline
    |
    +----> Gemini Story
    |
    +----> Image Generator
    |
    v
Comic Layout
    |
    v
PDF Export
    |
    v
User


## Windows Installation

Create a virtual environment:

```powershell
py -3.11 -m venv .venv