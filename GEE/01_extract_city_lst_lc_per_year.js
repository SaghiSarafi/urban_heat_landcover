/**************************************************************
 * Title: Mean Summer Land Surface Temperature (LST) Extraction for Global Cities
 *
 * Authors: Saghi Sarafi
 * Date: 2026
 *
 * Sources:
 *   - LST module: Ermida et al. (2020) Remote Sensing of Environment
 *     https://code.earthengine.google.com/?scriptPath=users/sofiaermida/landsat_smw_lst
 *   - LC data: Potapov et al. (2022) Global Land Cover and Land Use Change
 *     https://glad.umd.edu/dataset/GLCLUC2020
 *
 * Purpose:
 *   For each city and each analysis year (2000,2005,2010,2015,2020):
 *     - Compute percentage of each LC class (impervious, vegetation, cropland, water, bare)
 *     - Extract mean, max, and top-10% summer LST (Kelvin) for each LC class
 *     - Report number of images and sensor used
 *
 * Outputs:
 *   One CSV file per batch per year (exported to Google Drive).
 *   After merging, rename to 'city_year_lst_lc.csv'.
 *
 * Notes:
 *   - Summer window: Northern = Jun–Aug; Southern = Nov–Mar (previous/current year)
 *   - Top-10% LST = (90th percentile + 100th percentile) / 2
 *   - City boundaries are simplified (500 m) to reduce memory usage.
 *   - Batch size 20 works for most cities; reduce if timeouts occur.
 **************************************************************/

// === CONFIGURATION (USER MODIFIABLE) ===
var years = [2000, 2005, 2010, 2015, 2020];
var batchSize = 20;   // Reduce to 10 or 5 if memory/timeout errors occur

// !!! REPLACE WITH YOUR OWN CITY BOUNDARIES FEATURE COLLECTION !!!
// The asset must contain a 'name' property for each city.
var allCities = ee.FeatureCollection("projects/ee-saghisarafi/assets/Global_UHI_City_Boundaries");

// === END USER CONFIGURATION ===

var totalCities = allCities.size();
print('Total cities:', totalCities);

var landmask = ee.Image("projects/glad/OceanMask").lte(1);
var LandsatLST = require('users/sofiaermida/landsat_smw_lst:modules/Landsat_LST.js');

var lcClasses = [1, 2, 3, 4, 5]; // 1=Imp, 2=Veg, 3=Crop, 4=Water, 5=Bare

// Simplify geometries to reduce vertex count and avoid memory errors
var simplifiedCities = allCities.map(function(city) {
  return city.setGeometry(city.geometry().simplify(500));
});

// Reclassify GLAD LC to 5‑class scheme
function reclassifyLC(image) {
  return image
    .remap(
      [250, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 244, 200, 201, 202, 203, 204, 205, 206, 207, 254, 241, 100, 101, 102, 103, 0, 1, 2, 3],
      [1,   2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 4, 4, 4, 4, 4, 4, 4, 4, 5, 4, 5, 5, 5, 5, 5, 5, 5, 5]
    )
    .rename('remapped')
    .updateMask(landmask);
}

// Hemisphere‑aware summer window
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

// === Loop over years ===
years.forEach(function(year) {
  var lcAsset = 'projects/glad/GLCLU2020/v2/LCLUC_' + year;
  var satellite = (year <= 2011) ? 'L5' : (year === 2012 ? 'L7' : 'L8');
  var use_ndvi = true;

  var lcImage = reclassifyLC(ee.Image(lcAsset));
  var numBatches = totalCities.divide(batchSize).ceil();
  var batchIndices = ee.List.sequence(0, numBatches.subtract(1));

  batchIndices.evaluate(function(indices) {
    indices.forEach(function(i) {
      var cities = ee.FeatureCollection(simplifiedCities.toList(batchSize, i * batchSize));

      var results = cities.map(function(city) {
        var geom = city.geometry();
        var cityName = city.get('name');
        var lat = geom.centroid().coordinates().get(1);
        var dates = ee.Dictionary(getSummerDates(year, lat));
        var start = ee.Date(dates.get('start'));
        var end   = ee.Date(dates.get('end'));

        var lcCity = lcImage;

        // LC percentage histogram
        var lcStats = lcCity.reduceRegion({
          reducer: ee.Reducer.frequencyHistogram(),
          geometry: geom,
          scale: 30,
          maxPixels: 1e12,
          tileScale: 8
        });
        
        var hist = ee.Dictionary(lcStats.get('remapped'));
        var total = ee.Number(hist.values().reduce(ee.Reducer.sum()));
        var lcPercents = ee.Dictionary.fromLists(
          hist.keys(),
          hist.values().map(function(val) {
            return ee.Number(val).divide(total).multiply(100);
          })
        );

        // LST collection
        var coll = LandsatLST.collection(satellite, start, end, geom.buffer(5000), use_ndvi);
        var lstMean = coll.select('LST').mean().rename('LST_mean');
        var lstMax  = coll.select('LST').max().rename('LST_max');
        var lstPerc = coll.select('LST')
                          .reduce(ee.Reducer.percentile([90, 100]))
                          .rename(['LST_p90', 'LST_p100']);
        var lstImage = lstMean.addBands([lstMax, lstPerc]);

        return ee.Algorithms.If(
          coll.size().gt(0),
          ee.FeatureCollection(lcClasses.map(function(cls) {
            var classKey = ee.Number(cls).format();
            var classPercent = ee.Number(
              ee.Algorithms.If(hist.contains(classKey), lcPercents.get(classKey), 0)
            );

            return ee.Algorithms.If(
              classPercent.gt(0),
              (function() {
                var mask = lcCity.eq(cls);
                var masked = lstImage.updateMask(mask);
                var stats = masked.reduceRegion({
                  reducer: ee.Reducer.mean(),
                  geometry: geom,
                  scale: 30,
                  bestEffort: true,
                  maxPixels: 1e12
                });

                return ee.Feature(null, {
                  city: cityName,
                  year: year,
                  LC_class: cls,
                  mean_LST: stats.get('LST_mean'),
                  max_LST:  stats.get('LST_max'),
                  mean_top10_LST: ee.Algorithms.If(
                    stats.get('LST_p90'),
                    ee.Number(stats.get('LST_p90')).add(ee.Number(stats.get('LST_p100'))).divide(2),
                    null
                  ),
                  LC_percent: classPercent,
                  n_images: coll.size(),
                  sensor: satellite
                });
              })(),
              null
            );
          }, true)),
          null
        );
      }, true).flatten().filter(ee.Filter.notNull(['mean_LST', 'max_LST', 'mean_top10_LST']));

      Export.table.toDrive({
        collection: results,
        description: 'LST_LC_Metrics_' + year + '_Batch' + (i + 1),
        folder: 'LST_LC_Extractions',   // <- generic folder name
        fileFormat: 'CSV'
      });

      print('Exporting year:', year, 'batch:', i + 1);
    });
  });
});

print('Script finished. Check Console for export status.');
