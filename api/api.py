from typing import Annotated, List

from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os.path
import asyncio
import aiofiles
app = FastAPI()
templates = Jinja2Templates(directory="templates")
RAW_FILES = '../data/raw_appliances/'
MON_FILES = '../data/mon_appliances/'

async def file_handler(files, path):
    for file in files:
        out_file_path = os.path.join(path, str(file.filename))
        async with aiofiles.open(out_file_path, 'wb') as out_file:
            content = await file.read()
            result = await out_file.write(content)
    
@app.post("/submit")
async def submit(
    user_id: str = Form(...),
    class_id: int = Form(...),
    time_stamp: int = Form(...),
    files: List[UploadFile] = File(...),
):
    
    await file_handler(files, RAW_FILES)

    submitted = {
        "JSON Payload ": {"user_id": user_id, "class_id": class_id, "time_stamp": time_stamp, "files_size":[file.size for file in files]},
        "Filenames": [file.filename for file in files],
    }
    return submitted

@app.post("/mon")
async def monitor(
    user_id: str = Form(...),
    class_id: int = Form(...),
    time_stamp: int = Form(...),
    files: List[UploadFile] = File(...),
):
    await file_handler(files, MON_FILES)
    
    submitted = {
        "JSON Payload ": {"user_id": user_id, "class_id": class_id, "time_stamp": time_stamp, "files_size":[file.size for file in files]},
        "Filenames": [file.filename for file in files],
    }
    return submitted

@app.get("/", response_class=HTMLResponse)
def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})