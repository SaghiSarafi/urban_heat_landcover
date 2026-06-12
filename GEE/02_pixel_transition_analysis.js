/**************************************************************
 * Pixel-Level LC Transition & LST Analysis (2000 → 2020)
 *
 * Author: Saghi Sarafi
 * Date: 2026
 *
 * Description:
 *   For each city, this script identifies every pixel that changed
 *   land cover class between 2000 and 2020. For each transition
 *   (both off-diagonal and stable), it computes:
 *     - Percentage of city area occupied by that transition
 *     - Mean, max, and top-10% LST in 2000 and 2020
 *     - ΔLST, ΔmaxLST, Δtop10LST (2020 - 2000)
 *
 * Inputs (user must replace asset IDs):
 *   - City boundaries: FeatureCollection with a 'name' property.
 *   - GLAD LC datasets (public): 'projects/glad/GLCLU2020/v2/LCLUC_yyyy'
 *   - Landsat LST module: 'users/sofiaermida/landsat_smw_lst:modules/Landsat_LST.js'
 *
 * Outputs:
 *   - One CSV file per batch, exported to Google Drive.
 *   - After merging all batches, rename to 'pixel_transitions_thermal_2000_2020.csv'.
 *
 * Notes:
 *   - Summer window: Northern = Jun–Aug; Southern = Nov–Mar (previous/current year).
 *   - Top-10% LST is approximated as (p90 + p100) / 2.
 *   - City boundaries are simplified (500 m) to avoid memory errors.
 *   - Batch size = 1 is safe for testing; increase to 5-10 for production.
 **************************************************************/

// === CONFIGURATION (USER MODIFIABLE) ===
var BASELINE_YEAR = 2000;
var FINAL_YEAR = 2020;
var batchSize = 1;

// !!! REPLACE WITH YOUR OWN CITY BOUNDARIES FEATURE COLLECTION !!!
// The asset must contain a 'name' property for each city.
var allCities = ee.FeatureCollection("projects/ee-saghisarafi/assets/Global_UHI_City_Boundaries");

// === END USER CONFIGURATION ===

var totalCities = allCities.size();
print('Total cities:', totalCities);

var landmask = ee.Image("projects/glad/OceanMask").lte(1);
var LandsatLST = require('users/sofiaermida/landsat_smw_lst:modules/Landsat_LST.js');

// LC class codes after reclassification
var lcClasses = [1, 2, 3, 4, 5]; // 1=Imp, 2=Veg, 3=Crop, 4=Water, 5=Bare
var classNames = {
  1: 'imp',
  2: 'veg',
  3: 'crop',
  4: 'wat',
  5: 'bare'
};

// Simplify geometries to reduce vertex count and avoid memory errors
var simplifiedCities = allCities.map(function(city) {
  return city.setGeometry(city.geometry().simplify(500));
});

// Reclassify GLAD LC to our 5-class scheme
function reclassifyLC(image) {
  return image
    .remap(
      [250, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 244, 200, 201, 202, 203, 204, 205, 206, 207, 254, 241, 100, 101, 102, 103, 0, 1, 2, 3],
      [1,   2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 4, 4, 4, 4, 4, 4, 4, 4, 5, 4, 5, 5, 5, 5, 5, 5, 5, 5]
    )
    .rename('remapped')
    .updateMask(landmask);
}

// Hemisphere-aware summer window
function getSummerDates(year, lat) {
  year = ee.Number(year);
  return ee.Algorithms.If(
    ee.Number(lat).gte(0),
    ee.Dictionary({
      'start': year.format().cat('-06-01'),
      'end': year.format().cat('-08-31')
    }),
    ee.Dictionary({
      'start': year.subtract(1).format().cat('-11-01'),
      'end': year.format().cat('-03-31')
    })
  );
}

// Sensor selection by year
function getSensor(year) {
  return (year <= 2011) ? 'L5' : (year === 2012 ? 'L7' : 'L8');
}

// Get multi-band LST image (mean, max, p90, p100) for a city-year
function getLSTMetrics(city, year) {
  var geom = city.geometry();
  var lat = geom.centroid().coordinates().get(1);
  var dates = ee.Dictionary(getSummerDates(year, lat));
  var start = ee.Date(dates.get('start'));
  var end = ee.Date(dates.get('end'));
  var sensor = getSensor(year);

  var coll = LandsatLST.collection(sensor, start, end, geom.buffer(5000), true);

  var emptyImage = ee.Image.constant([0, 0, 0, 0])
    .rename(['LST_mean', 'LST_max', 'LST_p90', 'LST_p100'])
    .selfMask();

  var metricImage = ee.Image(ee.Algorithms.If(
    coll.size().gt(0),
    coll.select('LST').mean().rename('LST_mean')
      .addBands(coll.select('LST').max().rename('LST_max'))
      .addBands(
        coll.select('LST')
          .reduce(ee.Reducer.percentile([90, 100]))
          .rename(['LST_p90', 'LST_p100'])
      ),
    emptyImage
  ));

  return ee.Dictionary({
    image: metricImage,
    n_images: coll.size(),
    sensor: sensor
  });
}

// Build feature for one transition mask
function buildTransitionFeature(cityName, geom, transMask, transCount, totalPixels,
                                metricsBase, metricsFinal,
                                transitionName, transitionCode) {
  var baseImg = ee.Image(metricsBase.get('image')).clip(geom);
  var finalImg = ee.Image(metricsFinal.get('image')).clip(geom);

  var baseMasked = baseImg.updateMask(transMask);
  var finalMasked = finalImg.updateMask(transMask);

  var baseStats = baseMasked.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: geom,
    scale: 30,
    bestEffort: true,
    maxPixels: 1e12
  });

  var finalStats = finalMasked.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: geom,
    scale: 30,
    bestEffort: true,
    maxPixels: 1e12
  });

  var meanBase = baseStats.get('LST_mean');
  var maxBase = baseStats.get('LST_max');
  var p90Base = baseStats.get('LST_p90');
  var p100Base = baseStats.get('LST_p100');

  var meanFinal = finalStats.get('LST_mean');
  var maxFinal = finalStats.get('LST_max');
  var p90Final = finalStats.get('LST_p90');
  var p100Final = finalStats.get('LST_p100');

  var top10Base = ee.Algorithms.If(
    ee.Algorithms.IsEqual(p90Base, null),
    null,
    ee.Number(p90Base).add(ee.Number(p100Base)).divide(2)
  );

  var top10Final = ee.Algorithms.If(
    ee.Algorithms.IsEqual(p90Final, null),
    null,
    ee.Number(p90Final).add(ee.Number(p100Final)).divide(2)
  );

  var transPct = ee.Number(transCount).divide(ee.Number(totalPixels)).multiply(100);

  return ee.Feature(null, {
    city: cityName,
    transition: transitionName,
    transition_code: transitionCode,
    transition_area_pct: transPct,
    n_pixels: transCount,
    baseline_year: BASELINE_YEAR,
    final_year: FINAL_YEAR,

    mean_LST_2000: meanBase,
    mean_LST_2020: meanFinal,
    delta_LST: ee.Algorithms.If(
      ee.Algorithms.IsEqual(meanBase, null),
      null,
      ee.Number(meanFinal).subtract(ee.Number(meanBase))
    ),

    max_LST_2000: maxBase,
    max_LST_2020: maxFinal,
    delta_max_LST: ee.Algorithms.If(
      ee.Algorithms.IsEqual(maxBase, null),
      null,
      ee.Number(maxFinal).subtract(ee.Number(maxBase))
    ),

    top10_LST_2000: top10Base,
    top10_LST_2020: top10Final,
    delta_top10_LST: ee.Algorithms.If(
      ee.Algorithms.IsEqual(top10Base, null),
      null,
      ee.Number(top10Final).subtract(ee.Number(top10Base))
    ),

    n_images_2000: metricsBase.get('n_images'),
    n_images_2020: metricsFinal.get('n_images'),
    sensor_2000: metricsBase.get('sensor'),
    sensor_2020: metricsFinal.get('sensor')
  });
}

// === MAIN PROCESSING ===
var lcBase = reclassifyLC(ee.Image('projects/glad/GLCLU2020/v2/LCLUC_' + BASELINE_YEAR));
var lcFinal = reclassifyLC(ee.Image('projects/glad/GLCLU2020/v2/LCLUC_' + FINAL_YEAR));

// Transition code = from*100 + to
var transitionCode = lcBase.multiply(100).add(lcFinal).rename('transition');

var numBatches = totalCities.divide(batchSize).ceil();
var batchIndices = ee.List.sequence(0, numBatches.subtract(1));

batchIndices.evaluate(function(indices) {
  indices.forEach(function(i) {
    var cities = ee.FeatureCollection(simplifiedCities.toList(batchSize, i * batchSize));

    var results = cities.map(function(city) {
      var geom = city.geometry();
      var cityName = city.get('name');

      var metricsBase = getLSTMetrics(city, BASELINE_YEAR);
      var metricsFinal = getLSTMetrics(city, FINAL_YEAR);

      var baseImg = ee.Image(metricsBase.get('image'));
      var finalImg = ee.Image(metricsFinal.get('image'));

      var hasBase = baseImg.select('LST_mean').mask().reduceRegion({
        reducer: ee.Reducer.mean(),
        geometry: geom,
        scale: 30,
        maxPixels: 1e12
      }).get('LST_mean');

      var hasFinal = finalImg.select('LST_mean').mask().reduceRegion({
        reducer: ee.Reducer.mean(),
        geometry: geom,
        scale: 30,
        maxPixels: 1e12
      }).get('LST_mean');

      var hasBaseNum = ee.Number(ee.Algorithms.If(hasBase, 1, 0));
      var hasFinalNum = ee.Number(ee.Algorithms.If(hasFinal, 1, 0));

      return ee.Algorithms.If(
        hasBaseNum.and(hasFinalNum),
        (function() {
          var cityTransition = transitionCode.clip(geom);

          var totalPixels = cityTransition.reduceRegion({
            reducer: ee.Reducer.count(),
            geometry: geom,
            scale: 30,
            maxPixels: 1e12,
            bestEffort: true
          }).get('transition');

          var transitionFeatures = [];

          // Off-diagonal transitions
          for (var ii = 0; ii < lcClasses.length; ii++) {
            for (var jj = 0; jj < lcClasses.length; jj++) {
              if (ii === jj) continue;

              var fromClass = lcClasses[ii];
              var toClass = lcClasses[jj];
              var tCode = fromClass * 100 + toClass;
              var tName = classNames[fromClass] + '→' + classNames[toClass];

              var transMask = cityTransition.eq(tCode).selfMask();

              var transCount = transMask.reduceRegion({
                reducer: ee.Reducer.count(),
                geometry: geom,
                scale: 30,
                maxPixels: 1e12,
                bestEffort: true
              }).get('transition');

              var feature = ee.Algorithms.If(
                ee.Number(transCount).gt(0),
                buildTransitionFeature(
                  cityName, geom, transMask, transCount, totalPixels,
                  metricsBase, metricsFinal, tName, tCode
                ),
                null
              );

              if (feature) transitionFeatures.push(feature);
            }
          }

          // Stable transitions
          for (var kk = 0; kk < lcClasses.length; kk++) {
            var stableClass = lcClasses[kk];
            var stableCode = stableClass * 100 + stableClass;
            var stableName = classNames[stableClass] + '→' + classNames[stableClass];

            var stableMask = cityTransition.eq(stableCode).selfMask();

            var stableCount = stableMask.reduceRegion({
              reducer: ee.Reducer.count(),
              geometry: geom,
              scale: 30,
              maxPixels: 1e12,
              bestEffort: true
            }).get('transition');

            var stableFeature = ee.Algorithms.If(
              ee.Number(stableCount).gt(0),
              buildTransitionFeature(
                cityName, geom, stableMask, stableCount, totalPixels,
                metricsBase, metricsFinal, stableName, stableCode
              ),
              null
            );

            if (stableFeature) transitionFeatures.push(stableFeature);
          }

          return ee.FeatureCollection(
            transitionFeatures.filter(function(f) { return f !== null; })
          );
        })(),
        ee.FeatureCollection([ee.Feature(null, {
          city: cityName,
          transition: 'NO_DATA',
          error: 'Insufficient LST imagery'
        })])
      );
    }, true).flatten();

    Export.table.toDrive({
      collection: results,
      description: 'Pixel_Transitions_LSTMetrics_' + BASELINE_YEAR + '_' + FINAL_YEAR + '_Batch' + (i + 1),
      folder: 'LC_Pixel_Transitions_2000_2020',
      fileFormat: 'CSV'
    });

    print('Exporting batch:', i + 1);
  });
});

print('Script finished. Check the Console for export status.');