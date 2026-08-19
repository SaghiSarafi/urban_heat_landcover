/**
 * 03_boundary_covariates_ghsl_compactness.js
 *
 * Computes two covariates requested by Reviewer 1 to address administrative
 * boundary sensitivity, without re-running the full analysis pipeline on new
 * boundary definitions:
 *
 *   1. AREA RATIO: our existing city boundary's area, divided by the area of
 *      the larger, population/built-up-defined "Urban Centre" from the GHSL
 *      Urban Centre Database (GHS-SMOD, Degree of Urbanisation method). This
 *      captures how much of a city's full extent our boundary represents,
 *      ignoring political/administrative definitions entirely -- cities where
 *      our boundary captures a small fraction of the larger urban extent
 *      likely oversample the densest core.
 *
 *   2. COMPACTNESS (perimeter-area ratio): a simple shape-compactness metric
 *      for our existing boundary. Included primarily because Reviewer 1
 *      explicitly suggested it, even though a priori we don't expect it to
 *      explain much -- boundary jaggedness doesn't obviously relate to how
 *      representative a boundary is of the whole city.
 *
 * Output: one row per city, with both covariates, exported as a CSV table
 * (not raster data) -- small, fast to download, no reprocessing needed.
 *
 * Inputs required:
 *   - City boundary FeatureCollection (existing asset; see city_list.csv
 *     "gee_asset_id" column for per-city asset paths, or a single merged
 *     FeatureCollection if one already exists from the original pipeline).
 *   - GHS-SMOD (Degree of Urbanisation), available directly in the Earth
 *     Engine Data Catalog.
 *
 * Outputs:
 *   - CSV exported to Google Drive: city, year, own_area_km2,
 *     ghsl_urban_centre_area_km2, area_ratio, perimeter_area_ratio
 */

// ---------------------------------------------------------------------------
// CONFIGURATION -- update these to match your actual asset paths
// ---------------------------------------------------------------------------

// MANUAL COORDINATE OVERRIDES -- for the 10 cities where the automated
// lat/lon-based centroid (and, for most, the 20km fallback search) did not
// find a valid Urban Centre pixel during testing. Coordinates below are
// independently verified dense-urban-core points (city centers, CBDs, or
// -- for planned capitals -- the most built-up administrative core), not
// just a city's symbolic "center" marker. Some of these may still fail
// even with a verified good point (particularly Fianarantsoa, Blantyre,
// and Dili, which are comparatively small cities that may genuinely fall
// below GHS-SMOD's population/density threshold for the "Urban Centre"
// tier) -- if so, that is an honest, real limitation to report as a data
// caveat for those specific cities, not a bug to keep chasing further.
// Note: city names inside .map() are server-side Earth Engine values, not
// plain JavaScript strings, so a plain JS object lookup
// (dictionary[cityName]) won't work here -- using ee.Dictionary with
// .contains()/.get() (both server-side operations) instead.
var MANUAL_CENTROID_OVERRIDES = ee.Dictionary({
  'Istanbul': [28.9784, 41.0082],           // Sultanahmet/historic peninsula (dense core, not the strait)
  'Amman': [35.9328, 31.9497],               // city center
  'Astana': [71.449074, 51.169392],          // government/administrative core
  'Brasília': [-47.882778, -15.793889],      // Rodoviária/central bus terminal, densest point of the Plano Piloto
  'Riyadh': [46.68112, 24.69567],            // Al-Olaya business district (dense, built-up CBD)
  'Dili': [125.560310, -8.556856],           // city center; result is unreliable even with this point (see reliability flag below)
  'Blantyre': [35.0058, -15.7861],           // city center; may still fail (small city, below density threshold)
  'Fianarantsoa': [47.0854, -21.4536],       // city center; may still fail (small city, below density threshold)
  'National Capital District': [147.14944, -9.47889],  // Port Moresby, PNG -- official Wikipedia coordinates
  'Phnom Penh': [104.92111, 11.56944],       // near Wat Phnom/Royal Palace, dense urban core
});

// SINGLE-PIXEL RESULT THRESHOLD -- results this small are known, from
// repeated testing, to reflect one isolated Urban Centre pixel rather than
// a city's real extent (confirmed for Dili, Hobart, National Capital
// District, and Honiara). An earlier hand-maintained city list missed 3 of
// these 4 cases, so this is instead an automatic rule: at our 2km working
// resolution, one pixel = 4 km2, so any result at or below that is flagged
// unreliable regardless of which city it is.
var SINGLE_PIXEL_THRESHOLD_KM2 = 4;

function getManualOverride(cityName) {
  var hasOverride = MANUAL_CENTROID_OVERRIDES.contains(cityName);
  return ee.Algorithms.If(
    hasOverride,
    ee.Geometry.Point(ee.List(MANUAL_CENTROID_OVERRIDES.get(cityName, ee.List([0, 0])))),
    null
  );
}

// City boundaries FeatureCollection (all 100 study cities).
// Source features use 'name' for city identification, not 'city' --
// confirmed via Inspector on the Athens feature. Output CSV still uses
// 'city' as the column header for consistency with the rest of the
// repo's tables.
//
// KNOWN DATA-QUALITY EXCLUSION: Baku City is excluded here. Its boundary
// polygon in this asset (11,480 km2) is roughly 3.5x larger than even the
// broadest real administrative definition of the Baku region (Absheron
// Economic Region, 3,290 km2), and includes a large area of open Caspian
// Sea. Confirmed via the core city_year_lst_lc.csv dataset: Baku shows
// ~81% "Water" land cover across all 5 study years, which is not
// plausible for a city of ~2.3 million people (for comparison, Athens
// shows >97% Impervious). This is likely because the ocean mask used in
// 01_extract_city_lst_lc_per_year.js (projects/glad/OceanMask) does not
// treat the Caspian Sea -- an enclosed inland sea, not connected to the
// global ocean -- as "ocean," so Baku never got the same protection that
// saved Tokyo from an analogous oversized-boundary problem. Excluding
// Baku changes Level 1 regression R^2 from 0.186 to 0.196 and all RTI
// values by less than 0.0003 -- no material effect on any headline
// result, so exclusion is a clean, low-risk fix.
var cityBoundaries = ee.FeatureCollection('projects/ee-saghisarafi/assets/Global_UHI_City_Boundaries')
  .filter(ee.Filter.neq('name', 'Baku City'));

// Study years -- must match the years used throughout the rest of the pipeline.
var studyYears = [2000, 2005, 2010, 2015, 2020];

// Ocean mask, identical to the one used in 01_extract_city_lst_lc_per_year.js.
// Applied here for the same reason: some boundary geometries (e.g., Tokyo,
// pulled from OSM as the full Tokyo Metropolis prefecture) include large
// areas of open ocean far beyond the actual urban area (remote islands,
// etc.). The original pipeline already solves this for land-cover percentages
// by masking ocean before computing anything -- this applies the same fix
// here so the area-ratio covariate is computed on land area only, consistent
// with the rest of the analysis, not raw (and potentially ocean-inflated)
// polygon geometry.
var landmask = ee.Image("projects/glad/OceanMask").lte(1).rename('land');

// GHS-SMOD (Degree of Urbanisation) images are accessed directly by year --
// see getSmodImage() below. Confirmed via Inspector: P2023A covers
// 1975-2030 at 5-year intervals, single band 'smod_code', class values
// [10,11,12,13,21,22,23,30]. Class 30 is "Urban Centre" under the standard
// GHS-SMOD Level 2 Degree of Urbanisation scheme.
var URBAN_CENTRE_CLASS = 30;

// ---------------------------------------------------------------------------
// HELPER: get the GHS-SMOD image for a given study year.
// GHS-SMOD P2023A contains exactly 12 images at 5-year intervals from
// 1975-2030, indexed by exact year (e.g., image ID ".../GHS_SMOD_V2-0/2000").
// All five of our study years (2000, 2005, 2010, 2015, 2020) match this
// schedule exactly -- no nearest-year approximation needed.
// ---------------------------------------------------------------------------
function getSmodImage(year) {
  return ee.Image('JRC/GHSL/P2023A/GHS_SMOD_V2-0/' + year).select('smod_code');
}

// ---------------------------------------------------------------------------
// HELPER: compute the connected "Urban Centre" patch area containing a
// given city's centroid, for a given year
// ---------------------------------------------------------------------------
// Computes LAND-ONLY area within a geometry (ocean pixels excluded),
// matching the masking approach in the original extraction pipeline.
function landOnlyAreaKm2(geometry) {
  // 100m scale here refers to the OceanMask/pixelArea computation for the
  // city's OWN boundary polygon -- unrelated to GHS-SMOD's resolution.
  // Chosen for a reasonable balance of precision and speed for this ratio
  // covariate; some study cities (e.g., Tokyo, whose OSM boundary spans
  // mainland + remote islands) have large enough geometries to time out
  // interactively at finer scales like 30m.
  var pixelAreaImage = ee.Image.pixelArea().rename('land');
  var landAreaImage = landmask.multiply(pixelAreaImage);
  var areaM2 = landAreaImage.reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: geometry,
    scale: 100,
    maxPixels: 1e12,
    tileScale: 8,
    bestEffort: true,
  }).get('land');
  return ee.Number(areaM2).divide(1e6);
}

// Finds a reliable seed point for locating each city's GHS-SMOD Urban
// Centre patch. Prefers the curated 'lat'/'lon' properties already present
// on most features (Nominatim/OSM's own designated representative point
// for the named place), since these are far more reliable than a computed
// geometric centroid for boundaries with disconnected multi-part geometry
// (e.g., Tokyo's OSM boundary spans mainland + a huge maritime corridor
// out to the remote Izu/Ogasawara islands; the "largest polygon piece by
// area" can actually be that mostly-ocean maritime piece, since it spans
// such enormous distance, even though it contains almost no land).
// Falls back to a largest-polygon-piece geometric centroid only when
// lat/lon are missing (e.g., the GADM-sourced Athens/Riyadh replacements).
function getBestCentroid(cityFeature) {
  var cityName = cityFeature.get('name');
  var manualOverride = getManualOverride(cityName);
  var overrideIsNull = ee.Algorithms.IsEqual(manualOverride, null);

  var lat = cityFeature.get('lat');
  var lon = cityFeature.get('lon');

  var geometry = cityFeature.geometry();
  var isMulti = ee.String(geometry.type()).equals('MultiPolygon');
  var polygons = ee.List(ee.Algorithms.If(
    isMulti,
    geometry.geometries(),
    ee.List([geometry])
  ));
  var areas = polygons.map(function(g) {
    return ee.Geometry(g).area(1);
  });
  var maxArea = areas.reduce(ee.Reducer.max());
  var maxIndex = areas.indexOf(maxArea);
  var largestPolygon = ee.Geometry(polygons.get(maxIndex));
  var fallbackCentroid = largestPolygon.centroid(30);

  // Nested If (rather than chaining .not()/.and() on IsEqual's output,
  // which Earth Engine's client-side type inference doesn't support
  // directly) to check both lat and lon are present before using them.
  var latMissing = ee.Algorithms.IsEqual(lat, null);
  var lonMissing = ee.Algorithms.IsEqual(lon, null);

  var latLonOrFallback = ee.Algorithms.If(
    latMissing,
    fallbackCentroid,
    ee.Algorithms.If(
      lonMissing,
      fallbackCentroid,
      ee.Geometry.Point([lon, lat])
    )
  );

  // Manual override (verified dense-urban-core coordinate) takes priority
  // over both lat/lon and the geometric fallback, for the specific cities
  // where those methods were confirmed to fail during testing.
  return ee.Geometry(ee.Algorithms.If(
    overrideIsNull,
    latLonOrFallback,
    manualOverride
  ));
}

// If the exact centroid point doesn't fall on an Urban Centre pixel, search
// a 20km radius around the point for some valid Urban Centre pixel instead
// of failing outright. It does not need to be the mathematically nearest
// one -- any pixel within the true contiguous patch works equally well as
// a seed for connectedComponents(), which will still capture the whole
// patch regardless of which pixel within it we start from. Returns null
// (not an error) if no Urban Centre pixel is found even within 20km --
// this is a real, honest signal the city may fall below GHS-SMOD's Urban
// Centre density threshold entirely (plausible for smaller cities like
// Fianarantsoa, Blantyre, Dili), not a bug to force past.
function findFallbackSeedPoint(point, smodImage) {
  var mask = smodImage.eq(URBAN_CENTRE_CLASS).selfMask();
  var searchArea = point.buffer(20000);

  // Note: .addBands() does not carry a mask from one band to another --
  // each band can have an independent mask in Earth Engine, so the
  // coordinate image is explicitly masked here (.updateMask(mask)) to
  // ensure only true Urban Centre pixels can contribute a coordinate.
  var coords = ee.Image.pixelLonLat().updateMask(mask);

  var pixelInfo = coords.reduceRegion({
    reducer: ee.Reducer.first(),
    geometry: searchArea,
    scale: 100,
    bestEffort: true,
  });

  var lon = pixelInfo.get('longitude');
  var latVal = pixelInfo.get('latitude');
  var lonMissing = ee.Algorithms.IsEqual(lon, null);

  return ee.Algorithms.If(
    lonMissing,
    null,
    ee.Geometry.Point([lon, latVal])
  );
}

function urbanCentreAreaForCity(cityFeature, year) {
  var smodImage = getSmodImage(year);
  var initialCentroid = getBestCentroid(cityFeature);

  // Check whether the initial centroid already lands on an Urban Centre
  // pixel; if not, fall back to searching nearby for a valid seed point.
  var classAtCentroid = smodImage.reduceRegion({
    reducer: ee.Reducer.first(),
    geometry: initialCentroid,
    scale: 100,
    maxPixels: 1e9,
  }).get('smod_code');
  var centroidIsUrbanCentre = ee.Algorithms.IsEqual(classAtCentroid, URBAN_CENTRE_CLASS);

  // findFallbackSeedPoint() can genuinely return null (e.g., Brasilia,
  // Fianarantsoa, Blantyre -- confirmed to have no Urban Centre pixel even
  // within a widened search). Checking validity here, before ever
  // constructing a geometry or calling .buffer()/.clip(), avoids passing
  // an invalid/empty geometry downstream, which would otherwise throw a
  // hard error rather than a clean null result.
  var fallbackResult = findFallbackSeedPoint(initialCentroid, smodImage);
  var fallbackIsNull = ee.Algorithms.IsEqual(fallbackResult, null);
  var hasValidCentroid = ee.Algorithms.If(
    centroidIsUrbanCentre,
    true,
    ee.Algorithms.If(fallbackIsNull, false, true)
  );

  // The search region is built around the verified CENTROID POINT, not the
  // city's original polygon. Basing it on the original polygon fails for
  // cities like Tokyo, whose OSM boundary already spans ~1000km (mainland
  // to the remote Ogasawara Islands) -- buffering an already-enormous
  // polygon by 100km barely bounds anything. A fixed-radius circle around
  // the clean centroid point is small and well-behaved regardless of how
  // sprawling or oddly-shaped the original boundary is.
  //
  // RADIUS TRADEOFF (tested against real cities, not a guess): a 50km
  // radius truncated Shanghai's true Urban Centre extent (returned only
  // 1,538 km2, implausibly small for one of the world's largest cities'
  // built-up core). 150km avoids this truncation for large megacities, but
  // introduces a different risk: if two cities' built-up areas are
  // physically touching (or nearly so), connectedComponents will merge
  // them into a single patch, and both cities would incorrectly get
  // credited with the combined area. There is no single radius that is
  // simultaneously correct for isolated small cities, megacities, and safe
  // against merging nearby cities -- 150km is a reasonable middle ground;
  // ghsl_search_radius_km is recorded in the output so unusually large
  // results can be manually reviewed after the full run.
  //
  // Everything below only runs if hasValidCentroid is true. If not (e.g.,
  // Brasilia, Fianarantsoa, Blantyre), this short-circuits directly to the
  // -1 sentinel without calling .buffer()/.clip() on an invalid geometry.
  return ee.Number(ee.Algorithms.If(
    hasValidCentroid,
    (function () {
      var centroid = ee.Geometry(ee.Algorithms.If(
        centroidIsUrbanCentre, initialCentroid, fallbackResult
      ));

      var searchRegion = centroid.buffer(150000); // 150km around the city centre

      // Mask to Urban Centre class only, clipped to a local search region
      // first -- without clipping before reprojecting, Earth Engine
      // attempts to reproject the entire global image before narrowing to
      // the area of interest, which fails ("Reprojection output too
      // large"). Clipping first bounds all downstream computation to a
      // local area around this one city.
      var urbanCentreMask = smodImage.eq(URBAN_CENTRE_CLASS).selfMask().clip(searchRegion);

      // GHS-SMOD's native resolution is 1km. Earth Engine's
      // connectedComponents() caps maxSize at 1024 pixels; at native 1km
      // resolution that covers only 1,024 km2, insufficient for large
      // cities (e.g., Tokyo's real Urban Centre extent is ~4,318 km2).
      // Aggregating to a coarser 2km working resolution raises this cap to
      // 4,096 km2.
      var coarseMask = urbanCentreMask
        .reduceResolution({reducer: ee.Reducer.max(), maxPixels: 1024})
        .reproject({crs: 'EPSG:4326', scale: 2000});

      var labeled = coarseMask.connectedComponents({
        connectedness: ee.Kernel.plus(1),
        maxSize: 1024,
      });

      var centroidLabel = labeled.select('labels').reduceRegion({
        reducer: ee.Reducer.first(),
        geometry: centroid,
        scale: 2000,
        maxPixels: 1e9,
      }).get('labels');

      var thisPatch = labeled.select('labels').eq(ee.Image.constant(centroidLabel));

      var areaImage = thisPatch.multiply(ee.Image.pixelArea());
      var areaM2 = areaImage.reduceRegion({
        reducer: ee.Reducer.sum(),
        geometry: searchRegion,
        scale: 2000,
        maxPixels: 1e9,
      }).get('labels');

      return ee.Number(areaM2).divide(1e6); // convert to km2
    })(),
    -1  // no valid centroid found at all (genuine data limitation) -- clean sentinel, no crash
  ));
}

// ---------------------------------------------------------------------------
// HELPER: compactness / perimeter-area ratio for the existing boundary
// ---------------------------------------------------------------------------
// KNOWN LIMITATION: this computes area and perimeter from the RAW city
// boundary geometry, while landOnlyAreaKm2() (used for the area-ratio
// covariate on the same city) computes a LAND-ONLY area. For the large
// majority of cities this makes no practical difference (their boundaries
// do not include significant open water), but for a city whose boundary
// spans a large ocean area -- Tokyo is the clearest case in this sample --
// the raw perimeter includes coastline around that ocean area, which a
// land-only version would exclude. Properly fixing this requires
// vectorizing the land-only raster mask (an expensive raster-to-vector
// conversion, not a simple pixel-sum like landOnlyAreaKm2 uses), which was
// not implemented given the scope of this sensitivity analysis. Baku, the
// other major ocean-inclusion case in this sample, is excluded from this
// analysis entirely (see exclusion filter above), which addresses the
// worst instance. Tokyo's compactness value should be treated as
// approximate.
function compactness(cityFeature) {
  var geom = cityFeature.geometry();
  var areaM2 = geom.area(1);
  var perimeterM = geom.perimeter(1);
  // Perimeter-area ratio: lower values = more compact (circle-like) shape.
  // Normalizing by sqrt(area) makes this scale-independent across cities
  // of very different sizes.
  return ee.Number(perimeterM).divide(areaM2.sqrt());
}

// ---------------------------------------------------------------------------
// MAIN: compute both covariates for every city x year combination
//
// Given how many distinct edge cases surfaced during testing (Tokyo's
// disconnected multi-part geometry, Istanbul's centroid landing on water,
// Shanghai's true extent exceeding a smaller search radius), each city's
// computation is wrapped so that failures produce a clearly flagged
// null/error row instead of stopping the whole batch. After export, filter
// the output CSV for missing ghsl_urban_centre_area_km2 values to find
// exactly which cities need manual follow-up.
// ---------------------------------------------------------------------------
var results = ee.FeatureCollection(
  cityBoundaries.map(function (city) {
    var cityName = city.get('name');
    var ownAreaKm2 = landOnlyAreaKm2(city.geometry());
    var compactnessRatio = compactness(city);

    var yearFeatures = studyYears.map(function (year) {
      var ghslAreaKm2 = ee.Number(urbanCentreAreaForCity(city, year));
      var failed = ghslAreaKm2.eq(-1);
      var areaRatio = ee.Number(ee.Algorithms.If(failed, -1, ownAreaKm2.divide(ghslAreaKm2)));

      // Automatic single-pixel detection, rather than a hand-maintained
      // city list (which missed 3 of 4 real cases when tried).
      var isSpuriousSinglePixel = ee.Algorithms.If(
        failed,
        false,  // -1 failures are handled separately, not double-flagged here
        ghslAreaKm2.lte(SINGLE_PIXEL_THRESHOLD_KM2)
      );
      var isReliable = ee.Algorithms.If(isSpuriousSinglePixel, false, true);

      return ee.Feature(null, {
        city: cityName,
        year: year,
        own_area_km2: ownAreaKm2,
        ghsl_urban_centre_area_km2: ghslAreaKm2,  // -1 means this city/year failed -- review manually
        area_ratio: areaRatio,                     // -1 means this city/year failed -- review manually
        perimeter_area_ratio: compactnessRatio,
        ghsl_search_radius_km: 150,
        reliable: isReliable,  // false for cities with a confirmed spurious result
      });
    });

    return ee.FeatureCollection(yearFeatures);
  })
).flatten();

// Quick console summary of how many city/year combinations failed, so you
// know immediately after running whether cleanup is needed and roughly how
// much, without having to open the exported CSV first.
var failedCount = results.filter(ee.Filter.eq('ghsl_urban_centre_area_km2', -1)).size();
print('City/year combinations that FAILED (value = -1, need manual review):', failedCount);
print('Failed cities:', results.filter(ee.Filter.eq('ghsl_urban_centre_area_km2', -1))
  .aggregate_array('city').distinct());
print('Known-unreliable cities (result exists but flagged reliable=false):',
  results.filter(ee.Filter.eq('reliable', false)).aggregate_array('city').distinct());

// ---------------------------------------------------------------------------
// EXPORT: CSV table only -- no raster data, small and fast to download.
// ---------------------------------------------------------------------------
Export.table.toDrive({
  collection: results,
  description: 'boundary_covariates_ghsl_compactness',
  fileFormat: 'CSV',
  selectors: ['city', 'year', 'own_area_km2', 'ghsl_urban_centre_area_km2',
              'area_ratio', 'perimeter_area_ratio', 'reliable'],
});

// ---------------------------------------------------------------------------
// SANITY CHECK -- run this on 2-3 known cities before running the full
// batch export above. Print results to the Console and eyeball whether the
// GHSL urban centre area looks physically reasonable (e.g., larger than or
// comparable to your own boundary, not wildly off).
// ---------------------------------------------------------------------------
var testCities = cityBoundaries.filter(
  ee.Filter.inList('name', ['Tokyo', 'Paris', 'Athens'])
);
print('Sanity check on test cities:', results.filter(
  ee.Filter.inList('city', ['Tokyo', 'Paris', 'Athens'])
));