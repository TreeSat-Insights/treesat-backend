from sentinelhub import SHConfig, BBox, CRS
config = SHConfig()

if not config.sh_client_id or not config.sh_client_secret:
    print("Warning! To use Process API, please provide the credentials (OAuth client ID and client secret).")

import numpy as np

import datetime
from dateutil.relativedelta import relativedelta


from sentinelhub import (
    CRS,
    SentinelHubCatalog,
    filter_times,
    BBox,
    DataCollection,
    MimeType,
    SentinelHubDownloadClient,
    SentinelHubRequest,
    bbox_to_dimensions,
)

betsiboka_coords_wgs84 = (46.16, -16.15, 46.51, -15.58)
resolution = 10

bounding_box = BBox(bbox=[11.319652,46.502942, 11.348405,46.51892], crs=CRS.WGS84)
betsiboka_size = bbox_to_dimensions(bounding_box, resolution=resolution)

with open("../eval_functions/tree_stress.js") as f:
    tree_stress = f.read()

today = datetime.date.today()

one_year_ago = today - relativedelta(years=1)

time_interval = one_year_ago, today

catalog = SentinelHubCatalog(config=config)

search_iterator = catalog.search(
    DataCollection.SENTINEL2_L2A,
    bbox=bounding_box,
    time=time_interval,
    filter="eo:cloud_cover < 30",
    fields={"include": ["id", "properties.datetime"], "exclude": []},
)

results = list(search_iterator)

all_timestamps = search_iterator.get_timestamps()

time_difference = datetime.timedelta(hours=1)

unique_acquisitions = filter_times(all_timestamps, time_difference)

process_requests = []

for timestamp in unique_acquisitions:
    request = SentinelHubRequest(
        evalscript=tree_stress,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=(timestamp - time_difference, timestamp + time_difference),
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
        bbox=bounding_box,
        size=betsiboka_size,
        config=config,
    )
    process_requests.append(request)


client = SentinelHubDownloadClient(config=config)

download_requests = [request.download_list[0] for request in process_requests]

data = client.download(download_requests)

images = np.array(data)

print(images.shape)
