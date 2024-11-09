import logging

from PIL import Image
from fastapi import FastAPI
import base64
from io import BytesIO
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

import src.bark_beetle_detector as bbd

app = FastAPI()

bark_beetle_detector = bbd.BarkBeetleDetector()


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

@app.get("/scan/{latitude}/{longitude}")
def read_item(latitude: float, longitude:float):
    future_predictions, predictions = bark_beetle_detector.scan(latitude, longitude)

    encoded_images = []
    for prediction in predictions:
        image = Image.fromarray(prediction)
        logging.error(prediction.shape)
        if image.mode != 'RGB':
            image = image.convert("RGB")

        # Convert PIL Image to base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")  # Save image as PNG in a buffer
        encoded_images.append(base64.b64encode(buffered.getvalue()).decode("utf-8"))

    return JSONResponse({"status": "success", "content": encoded_images})

