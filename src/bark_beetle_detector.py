from src.sentinel_query import SentinelQuery
import keras
import datetime
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import numpy as np
import logging
from multiprocessing import Manager
from multiprocessing import Pool
from typing import Dict


class BarkBeetleDetector:
    # Length of the sequence of satellite data
    satellite_len = 31

    image_side = 100

    def __init__(self):
        self.sentinel_query = SentinelQuery()
        self.model = keras.saving.load_model("../model_75.keras")
        self.manager = Manager()

    @staticmethod
    def predict_time_series(column: pd.Series, column_id: int, results_dict: Dict, start_date: datetime, end_date: datetime):
        area_measures = ExponentialSmoothing(column).fit()
            
        # Get the prediction for the current dimension
        area_prediction = area_measures.predict(start=start_date, end=end_date)
        
        results_dict[column_id] = area_prediction

    def scan (self, latitude: float, longitude: float):
        satellite_data, unique_acquisitions, true_color_img = self.sentinel_query.collect_satellite_data((latitude, longitude))

        if len(satellite_data) - BarkBeetleDetector.satellite_len > 0:
            satellite_data = satellite_data[-BarkBeetleDetector.satellite_len:,:,:] # No comment please
            unique_acquisitions = unique_acquisitions[-BarkBeetleDetector.satellite_len:] # No comment please

        dates = pd.to_datetime(unique_acquisitions, format="%Y/%m/%d")
        dates = list(set(dates.normalize()))

        collected_data = pd.DataFrame(data=satellite_data.reshape(satellite_data.shape[0], -1), index=dates)

        today = datetime.datetime.now()
        today = today.replace(tzinfo=datetime.timezone.utc)

        collected_data = collected_data.resample('1W').mean().ffill()

        three_weeks = datetime.timedelta(days=21)
        three_weeks_from_now = today + three_weeks

        predictions = self.manager.dict()
        pool = Pool(6)
        n_weeks = 4
        for column in collected_data:
            pool.apply_async(self.predict_time_series, args=(collected_data[column], column, predictions, today, three_weeks_from_now))
        pool.close()
        pool.join()

        predictions = np.array(list(predictions.values())).reshape((n_weeks, BarkBeetleDetector.image_side, BarkBeetleDetector.image_side))

        future_predictions = []

        # Predict the bark bettle attack presence, using our model, for the weeks we just predicted
        for i in range(0, n_weeks):
            
            # Since the model accepts sequences of a certain lengthm we have to pad them
            weeks_to_pad = BarkBeetleDetector.satellite_len - i - 1

            pads = np.zeros((weeks_to_pad, predictions.shape[1], predictions.shape[2]))

            future_data = np.concatenate((pads,predictions[:i + 1]), axis=0)

            # Get the prediction
            #current_zone_prediction = self.model.predict(np.array([future_data]))
            current_zone_prediction = 1
            # Append it to the ones we are storing
            future_predictions.append(current_zone_prediction)

        return np.array(future_predictions), predictions, true_color_img

