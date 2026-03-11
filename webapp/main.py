"""
webapp/main.py
--------------
FastAPI server for the ResolvedPDF web app.
"""

from fastapi import FastAPI, File, UploadFile, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os

from convert_resolved import convert_to_pdf_bytes
from usage_tracker import can_convert, increment

BASE_DIR   = os.path.dirname(__file__)
templates  = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Mount static files to serve the logo
app = FastAPI(title="ResolvedPDF", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host or "unknown"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/convert")
async def convert(
    request: Request,
    file: UploadFile = File(...),
    license_key: str = Form(default=""),
):
    ip = get_client_ip(request)

    # Check rate limit
    allowed, message, remaining = can_convert(ip, license_key)
    if not allowed:
        raise HTTPException(status_code=429, detail=message)

    # Validate file
    if not file.filename.endswith(".resolved"):
        raise HTTPException(status_code=400, detail="Only .resolved files are accepted.")

    content = await file.read()
    try:
        md_text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text.")

    # Convert
    try:
        pdf_bytes = convert_to_pdf_bytes(md_text, filename=file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

    # Track usage (only after successful conversion)
    increment(ip)

    # Return PDF
    pdf_name = os.path.splitext(file.filename)[0] + ".pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pdf_name}"'},
    )


@app.get("/usage")
async def usage_info(request: Request):
    from usage_tracker import get_usage, FREE_DAILY_LIMIT
    ip = get_client_ip(request)
    used = get_usage(ip)
    return {
        "ip": ip,
        "used_today": used,
        "limit": FREE_DAILY_LIMIT,
        "remaining": max(0, FREE_DAILY_LIMIT - used),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
