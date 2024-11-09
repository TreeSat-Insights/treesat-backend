from sentinelhub import SHConfig, BBox, CRS
#import utils
config = SHConfig()
config.sh_client_id = "848a9ae0-b57d-4ad1-98ee-2d72b3882737"
config.sh_client_secret = "TIMjaUmWqncdtvXt1wtBIY4b7HXXn16G"

if not config.sh_client_id or not config.sh_client_secret:
    print("Warning! To use Process API, please provide the credentials (OAuth client ID and client secret).")

import matplotlib.pyplot as plt
import numpy as np

import datetime
from dateutil.relativedelta import relativedelta


from sentinelhub import (
    CRS,
    SentinelHubCatalog,
    filter_times,
    BBox,
    DataCollection,
    DownloadRequest,
    MimeType,
    MosaickingOrder,
    SentinelHubDownloadClient,
    bbox_to_dimensions,
    SentinelHubRequest,
    bbox_to_dimensions,
)

betsiboka_coords_wgs84 = (46.16, -16.15, 46.51, -15.58)
resolution = 10

bounding_box = BBox(bbox=[11.319652,46.502942, 11.348405,46.51892], crs=CRS.WGS84)
betsiboka_size = bbox_to_dimensions(bounding_box, resolution=resolution)


print(betsiboka_size)
# exit(0)

forest_stress = """
//VERSION=3
const moistureRamps = [
    [-0.8, 0x800000],
    [-0.24, 0xff0000],
    [-0.032, 0xffff00],
    [0.032, 0x00ffff],
    [0.24, 0x0000ff],
    [0.8, 0x000080]
  ];

//const viz = new ColorRampVisualizer(moistureRamps);

function setup() {
  return {
    input: ["B8A", "B11", "SCL", "dataMask"],
    output: [
      { id: "default", bands: 1 },
      { id: "index", bands: 1, sampleType: "FLOAT32" },
      { id: "eobrowserStats", bands: 2, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1 },
    ],
  };
}

function evaluatePixel(samples) {
  let val = index(samples.B8A, samples.B11);
  // The library for tiffs works well only if there is only one channel returned.
  // So we encode the "no data" as NaN here and ignore NaNs on frontend.
  const indexVal = samples.dataMask === 1 ? val : NaN;
  return {
    default: [val],
    index: [indexVal],
    eobrowserStats: [val, isCloud(samples.SCL) ? 1 : 0],
    dataMask: [samples.dataMask],
  };
}

function isCloud(scl) {
  if (scl == 3) {
    // SC_CLOUD_SHADOW
    return false;
  } else if (scl == 9) {
    // SC_CLOUD_HIGH_PROBA
    return true;
  } else if (scl == 8) {
    // SC_CLOUD_MEDIUM_PROBA
    return true;
  } else if (scl == 7) {
    // SC_CLOUD_LOW_PROBA
    return false;
  } else if (scl == 10) {
    // SC_THIN_CIRRUS
    return true;
  } else if (scl == 11) {
    // SC_SNOW_ICE
    return false;
  } else if (scl == 1) {
    // SC_SATURATED_DEFECTIVE
    return false;
  } else if (scl == 2) {
    // SC_DARK_FEATURE_SHADOW
    return false;
  }
  return false;
}

"""

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
        evalscript=forest_stress,
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

# Prediction

from statsforecast.models import HoltWinters


