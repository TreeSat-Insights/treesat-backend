import logging

from PIL import Image
from fastapi import FastAPI
import base64
from io import BytesIO
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
from src.utils import plot_image
import numpy as np
import io
import matplotlib.pyplot as plt

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
    future_predictions, predictions, true_color_img = bark_beetle_detector.scan(latitude, longitude)

    if all(future_predictions <= 0.5):
        return JSONResponse({"status": "success", "content": []})

    encoded_images = []
    for prediction_idx in range(0, len(predictions)):
        prediction = predictions[prediction_idx]

        fig, ax = plt.subplots(figsize=(6, 6))  # Opzionale, imposta la dimensione del grafico
        ax.imshow(prediction, cmap='Blues')
        ax.axis('off')  # Rimuove gli assi

        # Salva l'immagine in un oggetto BytesIO
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches='tight', pad_inches=0)
        buf.seek(0)
        

        # Converte l'immagine in formato Base64
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()

        encoded_images.append({"image": img_base64, "beetle_attacked": bool(future_predictions[prediction_idx] > 0.5)})

    return JSONResponse({"status": "success", "content": encoded_images})
