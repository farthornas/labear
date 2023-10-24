from typing import Annotated, List

from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.post("/submit")
def submit(
    user_id: str = Form(...),
    class_id: int = Form(...),
    time_stamp: int = Form(...),
    files: List[UploadFile] = File(...),
):
    return {
        "JSON Payload ": {"user_id": user_id, "class_id": class_id, "time_stamp": time_stamp},
        "Filenames": [file.filename for file in files],
    }

@app.get("/", response_class=HTMLResponse)
def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})