// Detects anomalies in the moisture of the biomass
const moistureRamps = [
    [-0.8, 0x800000],
    [-0.24, 0xff0000],
    [-0.032, 0xffff00],
    [0.032, 0x00ffff],
    [0.24, 0x0000ff],
    [0.8, 0x000080]
  ];

function setup() {
  return {
    input: ["B8A", "B11", "SCL", "dataMask", "B03", "B08"],
    output: [
      { id: "default", bands: 1 },
      { id: "index", bands: 1, sampleType: "FLOAT32" },
      { id: "eobrowserStats", bands: 2, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1 },
    ],
  };
}

function evaluatePixel(samples) {
  let moisture = index(samples.B8A, samples.B11);
  let NVDI_index = index(samples.B03, samples.B08);

  // if it's not biomass mark it as non relevant by manipulating the moisture value
  if (NVDI_index > -0.8){
    moisture = 0.8
  }


  // The library for tiffs works well only if there is only one channel returned.
  // So we encode the "no data" as NaN here and ignore NaNs on frontend.
  const indexVal = samples.dataMask === 1 ? moisture : NaN;
  return {
    default: [moisture],
    index: [indexVal],
    eobrowserStats: [moisture, isCloud(samples.SCL) ? 1 : 0],
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