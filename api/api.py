from typing import List

from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os.path, os
from eartools.eartools import RAW_FILES, MON_FILES, LEARN, MONITOR
from eartools.eartools import Metrics
import aiofiles

app = FastAPI()
templates = Jinja2Templates(directory="templates")
metrics = Metrics()


async def file_handler(files, path):
    for file in files:
        out_file_path = os.path.join(path, str(file.filename))
        async with aiofiles.open(out_file_path, 'wb') as out_file:
            content = await file.read()
            result = await out_file.write(content)
    return result
    

@app.post(LEARN)
async def submit(
    user_id: str = Form(...),
    class_id: int = Form(...),
    time_stamp: int = Form(...),
    files: List[UploadFile] = File(...),
):
    
    await file_handler(files, RAW_FILES)

    submitted = {
        "Payload": {"user_id": user_id, "class_id": class_id, "time_stamp": time_stamp, "files_size":[file.size for file in files],
        "Filenames": [file.filename for file in files],}
    }
    metr = {"user_id": user_id, "class_id": class_id, "time_stamp": time_stamp, "files": len(files)}
    metrics.post(metr, LEARN)
    return submitted

@app.post(MONITOR)
async def monitor(
    user_id: str = Form(...),
    class_id: int = Form(...),
    time_stamp: int = Form(...),
    files: List[UploadFile] = File(...),
):
    await file_handler(files, MON_FILES)
    
    submitted = {
        "Payload": {"user_id": user_id, "class_id": class_id, "time_stamp": time_stamp, "files_size":[file.size for file in files],
        "Filenames": [file.filename for file in files],}
    }
    metr = {"user_id": user_id, "class_id": class_id, "time_stamp": time_stamp, "files": len(files)}
    metrics.post(metr, MONITOR)
    
    return submitted

@app.get("/", response_class=HTMLResponse)
def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})