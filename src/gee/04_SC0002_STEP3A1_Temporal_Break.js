// SC0002 Step 3A.1 — Monthly / Bimonthly Temporal-Break Analysis
// =================================================================
//
// GOAL
// ----
// Refine the 2023 timing analysis without treating 2023-05-05 as an onset date.
//
// Main design:
//   1) Export monthly Sentinel-2 NDVI/NDMI P70 statistics for 2022-2024.
//   2) Compare the SAME calendar month in 2022 vs 2023 and 2022 vs 2024.
//   3) Repeat with fixed two-month periods:
//        Jan-Feb, Mar-Apr, May-Jun, Jul-Aug, Sep-Oct, Nov-Dec.
//   4) Keep the original 2022 Mar-Jul baseline only as a supplemental
//      descriptive comparison, not as the primary change-point test.
//
// Why same-calendar-period comparisons?
//   Comparing Jan-May with May-Jul mixes land-cover change with seasonality.
//   Matching the same month / same bimonth across years reduces that problem.
//
// IMPORTANT
// ---------
// - P70 composites still depend on observation density and cloud/SCL filtering.
// - Monthly composites can be sparse; always inspect scene_count and
//   mean_valid_obs before interpreting a period.
// - This is spectral vegetation change, NOT tree-loss classification.
// - The historical-image date 2023-05-05 is an observation date only.
//
// =================================================================


// ---------------------------------------------------------------
// 0. REPRODUCIBLE CONFIGURATION
// ---------------------------------------------------------------
// Self-contained archived AOI configuration.
// No private Earth Engine asset or Cloud project ID is referenced by this script.
// Geometry is copied from data/aoi/SC0002_Envelope_USED_BY_GEE_V4.geojson.
var SC0002_AOI_COORDINATES = [[[120.41211564021411,22.717804469199915],[120.41232077001267,22.711106846035747],[120.41232077001266,22.71108458995391],[120.41258832630717,22.708007807372148],[120.41259272256107,22.707967694856094],[120.41260169091858,22.70792752667832],[120.41261505552865,22.70788742142408],[120.41263290431486,22.707847278892753],[120.41265514935043,22.707811617766584],[120.41311446891253,22.70710708333978],[120.41314119802512,22.707066884803325],[120.41317241129106,22.707031231107745],[120.41320810870707,22.707000040426678],[120.41324380611323,22.706973268209993],[120.41328389973988,22.706950977378593],[120.41332847750759,22.706928731091],[120.41337314318442,22.70691080305374],[120.413422117147,22.706897456588212],[120.41346678279146,22.70689302936371],[120.41351575671851,22.706888601599385],[120.41356481855141,22.706888573887905],[120.41361388036569,22.70689304642687],[120.41366294216132,22.70690193738842],[120.41370751979822,22.706919784327773],[120.41455027163619,22.707223014799744],[120.41459493689054,22.707240842815086],[120.41463951420576,22.707263107596944],[120.41467960739922,22.70728990992395],[120.41471530439871,22.707321067774117],[120.41530834793437,22.70786066965158],[120.41534404476008,22.70789632724092],[120.41537525749368,22.707931940366006],[120.41539750205695,22.70797212845658],[120.41650339492251,22.70988063985978],[120.41652572721387,22.70992072689341],[120.41653909141786,22.70996530725309],[120.4165524556205,22.71000546925007],[120.41656133578068,22.710050087088497],[120.41713661059954,22.715432185196963],[120.41714100669867,22.715481258463793],[120.41713661059954,22.715525788374038],[120.41704736975555,22.716324041533536],[120.41673524612153,22.718981656496705],[120.41672636597332,22.719026224414478],[120.4167173979022,22.719066392382203],[120.41669963760266,22.7191065173488],[120.41668178937843,22.719146578890545],[120.41665945711404,22.719182259892],[120.41663272872955,22.719217960309578],[120.41660151629986,22.719249198364057],[120.41635621271665,22.719481082899982],[120.4163071519441,22.71952120868904],[120.41595941779788,22.719775334791052],[120.4159237211423,22.719802110547974],[120.41587914427032,22.71982436148562],[120.41583456738294,22.719842194049594],[120.41578990255731,22.719855626624415],[120.41574532563914,22.719864540606576],[120.41271317985996,22.720368407171726],[120.41266860187999,22.72037290191241],[120.41261953970668,22.720372852206538],[120.41257496169439,22.720372846618503],[120.41252589948552,22.720363959921308],[120.41248132144091,22.720355035516086],[120.41243665545568,22.72033721069302],[120.41239656156606,22.72031932977734],[120.41235646766403,22.720297030355937],[120.41232077001266,22.720270293138633],[120.41228507235145,22.720243555896996],[120.41225385887113,22.720207862167335],[120.41222264538327,22.720176668723692],[120.41220040027322,22.720136562954185],[120.41218255142724,22.720096437891804],[120.41216470257878,22.720056312816315],[120.41215133792215,22.72001615006892],[120.41214685372782,22.71997159371924],[120.41214236953337,22.71992695554246],[120.41211115601857,22.717826762888397],[120.41211564021411,22.717804469199915]]];
var SC0002_AOI = ee.Geometry.Polygon(SC0002_AOI_COORDINATES, null, false);
var SC0002_FC = ee.FeatureCollection([
  ee.Feature(SC0002_AOI, {
    case_id: 'SC0002',
    area_ha: 63.304526019347165,
    located_points: 93,
    all_located_points: 106,
    cluster_count: 3,
    buffer_m: 50,
    max_gap_m: 300,
    method: 'convex_hull_plus_50m'
  })
]);

var ANALYSIS_CRS = 'EPSG:32651';
var ANALYSIS_SCALE_M = 10;
var ANALYSIS_TRANSFORM = [10, 0, 0, 0, -10, 0];

var DRIVE_FOLDER = 'SC0002_STEP3A1_TEMPORAL_BREAK';


// ---------------------------------------------------------------
// 1. Fixed thresholds
// ---------------------------------------------------------------
var BASELINE_NDVI = 0.55;
var BASELINE_NDMI = 0.10;

var NDVI_DROP_THRESHOLD = 0.20;
var NDMI_DROP_THRESHOLD = 0.10;


// ---------------------------------------------------------------
// 2. AOI
// ---------------------------------------------------------------
var AOI_FC = SC0002_FC;
var AOI = SC0002_AOI;

print('SC0002 AOI source:', 'embedded archived V4 geometry');
print('Analysis CRS:', ANALYSIS_CRS);
print('Analysis scale:', ANALYSIS_SCALE_M);
print('AOI geodesic area (ha):', AOI.area(1).divide(10000));


// ---------------------------------------------------------------
// 3. Sentinel-2 preprocessing
// ---------------------------------------------------------------
function maskAndAddIndices(img) {
  var scl = img.select('SCL');

  var good = scl.neq(0)
    .and(scl.neq(1))
    .and(scl.neq(3))
    .and(scl.neq(7))
    .and(scl.neq(8))
    .and(scl.neq(9))
    .and(scl.neq(10))
    .and(scl.neq(11));

  var sr = img.updateMask(good);

  var ndvi = sr.normalizedDifference(['B8', 'B4']).rename('NDVI');
  var ndmi = sr.normalizedDifference(['B8', 'B11']).rename('NDMI');

  return sr
    .addBands([ndvi, ndmi])
    .select(['NDVI', 'NDMI'])
    .copyProperties(img, img.propertyNames());
}


function compositeBetween(startDate, endDateExclusive, label) {
  var col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(AOI)
    .filterDate(startDate, endDateExclusive)
    .map(maskAndAddIndices);

  var p70 = col
    .reduce(ee.Reducer.percentile([70]))
    .rename(['NDVI_P70', 'NDMI_P70']);

  var validObs = col
    .select('NDVI')
    .count()
    .rename('valid_obs');

  return p70
    .addBands(validObs)
    .set('label', label)
    .set('scene_count', col.size())
    .set('start_date', startDate)
    .set('end_date_exclusive', endDateExclusive);
}


// ---------------------------------------------------------------
// 4. Shared helpers
// ---------------------------------------------------------------
function reduceMeans(img) {
  return img.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: AOI,
    crs: ANALYSIS_CRS,
    crsTransform: ANALYSIS_TRANSFORM,
    maxPixels: 1e9,
    tileScale: 4
  });
}


function areaHa(mask) {
  var d = ee.Image.pixelArea()
    .divide(10000)
    .updateMask(mask)
    .rename('ha')
    .reduceRegion({
      reducer: ee.Reducer.sum(),
      geometry: AOI,
      crs: ANALYSIS_CRS,
      crsTransform: ANALYSIS_TRANSFORM,
      maxPixels: 1e9,
      tileScale: 4
    });

  return ee.Number(
    ee.Algorithms.If(d.get('ha'), d.get('ha'), 0)
  );
}


function safeFraction(n, d) {
  return ee.Algorithms.If(
    ee.Number(d).gt(0),
    ee.Number(n).divide(d),
    null
  );
}


function baselineVegetation(img) {
  return img.select('NDVI_P70').gte(BASELINE_NDVI)
    .and(img.select('NDMI_P70').gte(BASELINE_NDMI))
    .rename('baseline_vegetation');
}


function validPair(base, target) {
  return base.select('NDVI_P70').mask()
    .and(base.select('NDMI_P70').mask())
    .and(target.select('NDVI_P70').mask())
    .and(target.select('NDMI_P70').mask())
    .rename('valid_pair');
}


function comparisonMetrics(base, target) {
  var baseVeg = baselineVegetation(base);

  var ndviDrop = base.select('NDVI_P70')
    .subtract(target.select('NDVI_P70'));

  var ndmiDrop = base.select('NDMI_P70')
    .subtract(target.select('NDMI_P70'));

  var combined = baseVeg
    .and(ndviDrop.gte(NDVI_DROP_THRESHOLD))
    .and(ndmiDrop.gte(NDMI_DROP_THRESHOLD))
    .selfMask();

  var pairMask = validPair(base, target);

  var fullBaseHa = areaHa(baseVeg.selfMask());

  var comparableBaseHa = areaHa(
    baseVeg
      .and(pairMask)
      .selfMask()
  );

  var lossHa = areaHa(combined);

  return {
    fullBaseHa: fullBaseHa,
    comparableBaseHa: comparableBaseHa,
    lossHa: lossHa,
    lossFractionFull: safeFraction(lossHa, fullBaseHa),
    lossFractionComparable: safeFraction(lossHa, comparableBaseHa)
  };
}


// ---------------------------------------------------------------
// 5. Period definitions
// ---------------------------------------------------------------
var YEARS = [2022, 2023, 2024];

var MONTH_NAMES = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
];

var BIMONTHS = [
  {id: 'Jan-Feb', startMonth: 1, endMonthExclusive: 3},
  {id: 'Mar-Apr', startMonth: 3, endMonthExclusive: 5},
  {id: 'May-Jun', startMonth: 5, endMonthExclusive: 7},
  {id: 'Jul-Aug', startMonth: 7, endMonthExclusive: 9},
  {id: 'Sep-Oct', startMonth: 9, endMonthExclusive: 11},
  {id: 'Nov-Dec', startMonth: 11, endMonthExclusive: 13}
];


function monthComposite(year, month) {
  var start = ee.Date.fromYMD(year, month, 1);
  var end = start.advance(1, 'month');
  var label = String(year) + '-' + String(month).padStart(2, '0');

  return compositeBetween(start, end, label)
    .set('year', year)
    .set('month', month)
    .set('period_id', MONTH_NAMES[month - 1]);
}


function bimonthComposite(year, cfg) {
  var start = ee.Date.fromYMD(year, cfg.startMonth, 1);
  var end;

  if (cfg.endMonthExclusive <= 12) {
    end = ee.Date.fromYMD(year, cfg.endMonthExclusive, 1);
  } else {
    end = ee.Date.fromYMD(year + 1, 1, 1);
  }

  return compositeBetween(
    start,
    end,
    String(year) + '_' + cfg.id
  )
    .set('year', year)
    .set('period_id', cfg.id);
}


// ---------------------------------------------------------------
// 6. A — Monthly descriptive statistics, 2022-2024
// ---------------------------------------------------------------
var monthlyFeatures = [];

YEARS.forEach(function(year) {
  for (var month = 1; month <= 12; month++) {
    var img = monthComposite(year, month);
    var stats = reduceMeans(img);

    monthlyFeatures.push(
      ee.Feature(null, {
        year: year,
        month: month,
        month_name: MONTH_NAMES[month - 1],

        scene_count: img.get('scene_count'),
        mean_NDVI_P70: stats.get('NDVI_P70'),
        mean_NDMI_P70: stats.get('NDMI_P70'),
        mean_valid_obs: stats.get('valid_obs'),

        analysis_crs: ANALYSIS_CRS,
        analysis_scale_m: ANALYSIS_SCALE_M
      })
    );
  }
});

var monthlyStatsFC = ee.FeatureCollection(monthlyFeatures);

print('A. Monthly stats 2022-2024:', monthlyStatsFC);


// ---------------------------------------------------------------
// 7. B — Same-month matched comparisons
// ---------------------------------------------------------------
//
// Compare:
//   2022 same month -> 2023 same month
//   2022 same month -> 2024 same month
//
// This is the primary temporal-break table.
// ---------------------------------------------------------------
var sameMonthFeatures = [];

[2023, 2024].forEach(function(targetYear) {
  for (var month = 1; month <= 12; month++) {
    var base = monthComposite(2022, month);
    var target = monthComposite(targetYear, month);

    var metrics = comparisonMetrics(base, target);

    var baseStats = reduceMeans(base);
    var targetStats = reduceMeans(target);

    sameMonthFeatures.push(
      ee.Feature(null, {
        baseline_year: 2022,
        target_year: targetYear,

        month: month,
        month_name: MONTH_NAMES[month - 1],

        baseline_scene_count: base.get('scene_count'),
        target_scene_count: target.get('scene_count'),

        baseline_mean_valid_obs: baseStats.get('valid_obs'),
        target_mean_valid_obs: targetStats.get('valid_obs'),

        baseline_mean_NDVI_P70: baseStats.get('NDVI_P70'),
        target_mean_NDVI_P70: targetStats.get('NDVI_P70'),

        baseline_mean_NDMI_P70: baseStats.get('NDMI_P70'),
        target_mean_NDMI_P70: targetStats.get('NDMI_P70'),

        baseline_vegetation_ha: metrics.fullBaseHa,
        comparable_baseline_vegetation_ha: metrics.comparableBaseHa,
        combined_loss_ha: metrics.lossHa,

        loss_fraction_full_baseline: metrics.lossFractionFull,
        loss_fraction_comparable_baseline: metrics.lossFractionComparable,

        baseline_ndvi_threshold: BASELINE_NDVI,
        baseline_ndmi_threshold: BASELINE_NDMI,
        ndvi_drop_threshold: NDVI_DROP_THRESHOLD,
        ndmi_drop_threshold: NDMI_DROP_THRESHOLD,

        analysis_crs: ANALYSIS_CRS,
        analysis_scale_m: ANALYSIS_SCALE_M
      })
    );
  }
});

var sameMonthFC = ee.FeatureCollection(sameMonthFeatures);

print('B. Same-month matched comparisons:', sameMonthFC);


// ---------------------------------------------------------------
// 8. C — Bimonthly descriptive statistics
// ---------------------------------------------------------------
var bimonthStatsFeatures = [];

YEARS.forEach(function(year) {
  BIMONTHS.forEach(function(cfg) {
    var img = bimonthComposite(year, cfg);
    var stats = reduceMeans(img);

    bimonthStatsFeatures.push(
      ee.Feature(null, {
        year: year,
        period_id: cfg.id,

        scene_count: img.get('scene_count'),
        mean_NDVI_P70: stats.get('NDVI_P70'),
        mean_NDMI_P70: stats.get('NDMI_P70'),
        mean_valid_obs: stats.get('valid_obs'),

        analysis_crs: ANALYSIS_CRS,
        analysis_scale_m: ANALYSIS_SCALE_M
      })
    );
  });
});

var bimonthStatsFC = ee.FeatureCollection(bimonthStatsFeatures);

print('C. Bimonthly stats 2022-2024:', bimonthStatsFC);


// ---------------------------------------------------------------
// 9. D — Same-bimonth matched comparisons
// ---------------------------------------------------------------
var sameBimonthFeatures = [];

[2023, 2024].forEach(function(targetYear) {
  BIMONTHS.forEach(function(cfg) {
    var base = bimonthComposite(2022, cfg);
    var target = bimonthComposite(targetYear, cfg);

    var metrics = comparisonMetrics(base, target);

    var baseStats = reduceMeans(base);
    var targetStats = reduceMeans(target);

    sameBimonthFeatures.push(
      ee.Feature(null, {
        baseline_year: 2022,
        target_year: targetYear,
        period_id: cfg.id,

        baseline_scene_count: base.get('scene_count'),
        target_scene_count: target.get('scene_count'),

        baseline_mean_valid_obs: baseStats.get('valid_obs'),
        target_mean_valid_obs: targetStats.get('valid_obs'),

        baseline_mean_NDVI_P70: baseStats.get('NDVI_P70'),
        target_mean_NDVI_P70: targetStats.get('NDVI_P70'),

        baseline_mean_NDMI_P70: baseStats.get('NDMI_P70'),
        target_mean_NDMI_P70: targetStats.get('NDMI_P70'),

        baseline_vegetation_ha: metrics.fullBaseHa,
        comparable_baseline_vegetation_ha: metrics.comparableBaseHa,
        combined_loss_ha: metrics.lossHa,

        loss_fraction_full_baseline: metrics.lossFractionFull,
        loss_fraction_comparable_baseline: metrics.lossFractionComparable,

        baseline_ndvi_threshold: BASELINE_NDVI,
        baseline_ndmi_threshold: BASELINE_NDMI,
        ndvi_drop_threshold: NDVI_DROP_THRESHOLD,
        ndmi_drop_threshold: NDMI_DROP_THRESHOLD,

        analysis_crs: ANALYSIS_CRS,
        analysis_scale_m: ANALYSIS_SCALE_M
      })
    );
  });
});

var sameBimonthFC = ee.FeatureCollection(sameBimonthFeatures);

print('D. Same-bimonth matched comparisons:', sameBimonthFC);


// ---------------------------------------------------------------
// 10. E — Supplemental fixed-baseline comparison
// ---------------------------------------------------------------
//
// Keep the original 2022 Mar-Jul P70 baseline, but compare it to each
// 2023/2024 bimonth only as a SUPPLEMENTAL descriptive table.
// This must NOT be used as the main change-point test because seasons differ.
// ---------------------------------------------------------------
var fixedBaseline2022 = compositeBetween(
  '2022-03-01',
  '2022-08-01',
  '2022_Mar-Jul_baseline'
);

var fixedBaselineHa = areaHa(
  baselineVegetation(fixedBaseline2022).selfMask()
);

var fixedBaselineFeatures = [];

[2023, 2024].forEach(function(targetYear) {
  BIMONTHS.forEach(function(cfg) {
    var target = bimonthComposite(targetYear, cfg);
    var metrics = comparisonMetrics(
      fixedBaseline2022,
      target
    );

    fixedBaselineFeatures.push(
      ee.Feature(null, {
        baseline_window: '2022_Mar-Jul_P70',
        target_year: targetYear,
        target_period: cfg.id,

        baseline_vegetation_ha: fixedBaselineHa,
        comparable_baseline_vegetation_ha: metrics.comparableBaseHa,

        combined_loss_ha: metrics.lossHa,
        loss_fraction_full_baseline: metrics.lossFractionFull,
        loss_fraction_comparable_baseline: metrics.lossFractionComparable,

        warning:
          'SUPPLEMENTAL ONLY: seasonal windows differ; do not use as a controlled onset test'
      })
    );
  });
});

var fixedBaselineFC = ee.FeatureCollection(
  fixedBaselineFeatures
);

print('E. Supplemental fixed-baseline comparison:', fixedBaselineFC);


// ---------------------------------------------------------------
// 11. Exports
// ---------------------------------------------------------------
Export.table.toDrive({
  collection: monthlyStatsFC,
  description: 'SC0002_STEP3A1_Monthly_Stats_2022_2024',
  fileNamePrefix: 'SC0002_STEP3A1_Monthly_Stats_2022_2024',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: sameMonthFC,
  description: 'SC0002_STEP3A1_Same_Month_Comparisons',
  fileNamePrefix: 'SC0002_STEP3A1_Same_Month_Comparisons',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: bimonthStatsFC,
  description: 'SC0002_STEP3A1_Bimonthly_Stats_2022_2024',
  fileNamePrefix: 'SC0002_STEP3A1_Bimonthly_Stats_2022_2024',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: sameBimonthFC,
  description: 'SC0002_STEP3A1_Same_Bimonth_Comparisons',
  fileNamePrefix: 'SC0002_STEP3A1_Same_Bimonth_Comparisons',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: fixedBaselineFC,
  description: 'SC0002_STEP3A1_Fixed_2022_Baseline_Supplemental',
  fileNamePrefix: 'SC0002_STEP3A1_Fixed_2022_Baseline_Supplemental',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV'
});


// ---------------------------------------------------------------
// 12. Map
// ---------------------------------------------------------------
Map.centerObject(AOI_FC, 15);

Map.addLayer(
  AOI_FC.style({
    color: 'FFFF00',
    fillColor: '00000000',
    width: 2
  }),
  {},
  'SC0002 AOI',
  true
);
