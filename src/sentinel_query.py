from sentinelhub import SHConfig, BBox, CRS, SentinelHubCatalog, filter_times, SentinelHubRequest, WmsRequest, DataCollection, \
    SentinelHubDownloadClient, bbox_to_dimensions, MimeType
import os
import math
import datetime
from dateutil.relativedelta import  relativedelta
import numpy as np
import logging
from src.utils import plot_image

class SentinelQuery:
    # Satellite image target size
    size = (100,100)

    # Earth radius in meters, used for conversion
    R = 6378137.0

    @staticmethod
    def load_crendentials():
        config = SHConfig()
        config.sh_client_id = os.environ.get("SENTINEL_CLIENT_ID")
        config.sh_client_secret = os.environ.get("SENTINEL_CLIENT_SECRET")
        return config

    @staticmethod
    def load_eval_script(script_name: str):
        with open(os.path.join("../eval_functions", f"{script_name}.js"), "r") as f:
            return f.read()

    def __init__(self):
        self.config = SentinelQuery.load_crendentials()
        self.catalog = SentinelHubCatalog(config=self.config)
        self.tree_strees_script = self.load_eval_script(script_name="tree_stress")
        self.load_true_color_script = self.load_eval_script(script_name="true_color")

    def get_bounding_box_from_center(self, bounding_boxes_left_corner: (float, float), bounding_box_side_size_in_metres=100):

        half_side = bounding_box_side_size_in_metres / 2

        lat_offset = half_side / SentinelQuery.R * (180 / math.pi)

        lon_offset = half_side / (SentinelQuery.R * math.cos(math.radians(bounding_boxes_left_corner[1]))) * (180 / math.pi)

        top_left = [bounding_boxes_left_corner[1] + lat_offset, bounding_boxes_left_corner[0] - lon_offset]
        bottom_right = [bounding_boxes_left_corner[1] - lat_offset, bounding_boxes_left_corner[0] + lon_offset]

        return BBox(bbox=top_left + bottom_right, crs=CRS.WGS84)

    def collect_satellite_data(self, bounding_box_center: (float, float)):
        today = datetime.date.today()

        six_months_ago = today - relativedelta(months=6)

        time_interval = six_months_ago, today

        bounding_box = self.get_bounding_box_from_center(bounding_box_center)

        search_iterator = self.catalog.search(
            DataCollection.SENTINEL2_L2A,
            bbox=bounding_box,
            time=time_interval,
            filter="eo:cloud_cover < 30",
            fields={"include": ["id", "properties.datetime"], "exclude": []},
        )

        all_timestamps = search_iterator.get_timestamps()

        time_difference = datetime.timedelta(hours=1)

        unique_acquisitions = filter_times(all_timestamps, time_difference)

        process_requests = []

        for timestamp in unique_acquisitions:
            request = SentinelHubRequest(
                evalscript=self.tree_strees_script,
                input_data=[
                    SentinelHubRequest.input_data(
                        data_collection=DataCollection.SENTINEL2_L2A,
                        time_interval=(timestamp - time_difference, timestamp + time_difference),
                    )
                ],
                responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
                bbox=bounding_box,
                size=(100,100),
                config=self.config,
            )
            process_requests.append(request)

        client = SentinelHubDownloadClient(config=self.config)

        download_requests = [request.download_list[0] for request in process_requests]

        data = np.array(client.download(download_requests))

        # Retrieve also the true colors image, updated to today

        today = datetime.datetime.now()
        today = today.replace(tzinfo=datetime.timezone.utc)

        betsiboka_coords_wgs84 = (46.16, -16.15, 46.51, -15.58)
        betsiboka_bbox = BBox(bbox=betsiboka_coords_wgs84, crs=CRS.WGS84)
        betsiboka_size = bbox_to_dimensions(betsiboka_bbox, resolution=60)

        evalscript_true_color = """
            //VERSION=3

            function setup() {
                return {
                    input: [{
                        bands: ["B02", "B03", "B04"]
                    }],
                    output: {
                        bands: 3
                    }
                };
            }

            function evaluatePixel(sample) {
                return [sample.B04, sample.B03, sample.B02];
            }
        """

        request_true_color = SentinelHubRequest(
            evalscript=evalscript_true_color,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L1C,
                    time_interval=("2020-06-12", "2020-06-13"),
                )
            ],
            responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
            bbox=bounding_box,
            size=(100,100),
            config=self.config,
        )

        true_color_imgs = request_true_color.get_data()
        true_color_img = true_color_imgs[0]

        plot_image(true_color_img, factor=3.5 / 255, clip_range=(0, 1))

        return data, np.array(unique_acquisitions), np.clip(true_color_img * 3.5 / 255, 0, 1)




