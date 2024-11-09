// Simple filter NDVI based that excludes everything which is not biomass
function setup() {
  return {
    input: ["B03", "B08"],
    output: { bands: 3 }
  }
}
function evaluatePixel(samples) {
   const val = index(samples.B03, samples.B08);

  // If it's not biomass filter it out
  if (val > -0.8){
     return [0];
  }else{
    return [1];
  }}