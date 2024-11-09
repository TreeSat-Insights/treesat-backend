from src.sentinel_query import SentinelQuery
import keras
import datetime
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import numpy as np
import logging


class BarkBeetleDetector:
    # Length of the sequence of satellite data
    satellite_len = 31

    def __init__(self):
        self.sentinel_query = SentinelQuery()
        self.model = keras.saving.load_model("../model.keras")

    def scan (self, latitude: float, longitude: float):
        satellite_data, unique_acquisitions = self.sentinel_query.collect_satellite_data((latitude, longitude))

        if len(satellite_data) - BarkBeetleDetector.satellite_len > 0:
            satellite_data = satellite_data[-BarkBeetleDetector.satellite_len:,:,:] # No comment please
            unique_acquisitions = unique_acquisitions[-BarkBeetleDetector.satellite_len:] # No comment please

        # SBDA: La fixo dopo, va bene
        dates = pd.to_datetime(unique_acquisitions, format="%Y/%m/%d")
        dates = list(set(dates.normalize()))

        collected_data = pd.DataFrame(data=satellite_data.reshape(satellite_data.shape[0], -1), index=dates)
        min_date = collected_data.index.min()
        dt = datetime.datetime.now()
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        collected_data = collected_data.resample('1W').mean().ffill()

        three_weeks = datetime.timedelta(days=21)
        three_weeks_from_now = dt + three_weeks
        max_date = collected_data.index.max()

        predictions = []
        n_weeks = 0

        for column in collected_data:
            area_measures = ExponentialSmoothing(collected_data[column]).fit()
            area_prediction = area_measures.predict(start=max_date, end=three_weeks_from_now)
            n_weeks = len(area_prediction)
            predictions.append(area_prediction)

        predictions = np.array(predictions).reshape((n_weeks, 14, 10)) # TODO SBDA dice 14 ottobre

        logging.error(predictions.shape)



        future_predictions = []

        for i in range(0, n_weeks):

            logging.error(f"Predicting week {i}")

            weeks_to_pad = BarkBeetleDetector.satellite_len - i - 1

            logging.error(f"Weeks to pad {weeks_to_pad}")

            pads = np.zeros((weeks_to_pad, predictions.shape[1], predictions.shape[2]))
            logging.error(f"Pads shape {pads.shape}")
            future_data = np.concatenate((pads,predictions[:i + 1]), axis=0)
            logging.error(f"Future data shape {future_data.shape}")
            current_zone_prediction = self.model.predict(np.array([future_data]))
            logging.error(f"Prediction {current_zone_prediction}")

            future_predictions.append(current_zone_prediction[0][0])

        return np.array(future_predictions), predictions

