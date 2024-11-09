import os
from PIL import Image
from fastapi import FastAPI
import base64
from io import BytesIO
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

app = FastAPI()

# Middleware to add CSP headers
class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        # Set the Content-Security-Policy header
        response.headers["Content-Security-Policy"] = "default-src *"
        return response

# Add middleware to FastAPI app
app.add_middleware(CSPMiddleware)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
def read_root():
    return {"message": "Pong"}

@app.get("/scan/{x_pos}/{y_pos}")
def read_item(x_pos: float, y_pos:float):
    # image = Image.fromarray(array)
    images = [ "caoria1.png", "caoria2.png", "caoria3.png"]
    encoded_images = []
    for image in images:
        images = Image.open(os.path.join("resources", image))

        # Convert PIL Image to base64
        buffered = BytesIO()
        images.save(buffered, format="PNG")  # Save image as PNG in a buffer
        encoded_images.append(base64.b64encode(buffered.getvalue()).decode("utf-8"))

    return JSONResponse({"status": "success", "content": encoded_images})
