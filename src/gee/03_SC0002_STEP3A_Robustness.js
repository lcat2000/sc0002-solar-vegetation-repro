// SC0002 Step 3A — Methodological Robustness Tests
// ================================================================
//
// PURPOSE
// -------
// Address the main methodological questions that remain after the V4
// reproducibility fixes:
//
//   A. Baseline-year sensitivity:
//      2020, 2021, and 2022 -> 2026
//
//   B. Index ablation:
//      NDVI-only vs NDMI-only vs NDVI+NDMI
//
//   C. Pre-development "null" comparisons:
//      2019->2020, 2020->2021, 2021->2022
//      These help show how often the same thresholds can fire before the
//      documented SC0002 development transition.
//
//   D. Event-window analysis around the 2023-05-05 historical-image date:
//      2023 Jan 1-May 5 vs 2023 May 6-Jul 31,
//      both compared against the fixed 2022 Mar-Jul baseline.
//
// IMPORTANT
// ---------
// This script does NOT select or analyze a control area. A control area should
// be chosen with explicit matching criteria in Step 3B, not ad hoc.
//
// Output terminology:
//   "spectral vegetation loss" — NOT "tree loss".
//
// ================================================================


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

var DRIVE_FOLDER = 'SC0002_STEP3A_ROBUSTNESS';


// ---------------------------------------------------------------
// 1. Fixed method parameters
// ---------------------------------------------------------------
var START_MONTH = 3;
var END_MONTH = 7;

var BASELINE_NDVI = 0.55;
var BASELINE_NDMI = 0.10;

var NDVI_DROP_THRESHOLD = 0.20;
var NDMI_DROP_THRESHOLD = 0.10;


// ---------------------------------------------------------------
// 2. AOI
// ---------------------------------------------------------------
var AOI_FC = SC0002_FC;
var AOI = SC0002_AOI;
var ANALYSIS_PROJ = ee.Projection(ANALYSIS_CRS);

var EXPORT_REGION = AOI
  .transform(ANALYSIS_PROJ, 1)
  .bounds(1, ANALYSIS_PROJ);

print('SC0002 AOI source:', 'embedded archived V4 geometry');
print('Analysis CRS:', ANALYSIS_CRS);
print('Analysis transform:', ANALYSIS_TRANSFORM);
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


function annualComposite(year) {
  var start = ee.Date.fromYMD(year, START_MONTH, 1);
  var end = ee.Date.fromYMD(year, END_MONTH + 1, 1);

  return compositeBetween(
    start,
    end,
    String(year) + '_Mar-Jul'
  ).set('year', year);
}


// ---------------------------------------------------------------
// 4. Shared helpers
// ---------------------------------------------------------------
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


function meanStats(img) {
  return img.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: AOI,
    crs: ANALYSIS_CRS,
    crsTransform: ANALYSIS_TRANSFORM,
    maxPixels: 1e9,
    tileScale: 4
  });
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


function comparisonMasks(base, target) {
  var baseVeg = baselineVegetation(base);

  var ndviDrop = base.select('NDVI_P70')
    .subtract(target.select('NDVI_P70'));

  var ndmiDrop = base.select('NDMI_P70')
    .subtract(target.select('NDMI_P70'));

  var ndviOnly = baseVeg
    .and(ndviDrop.gte(NDVI_DROP_THRESHOLD))
    .selfMask()
    .rename('ndvi_only');

  var ndmiOnly = baseVeg
    .and(ndmiDrop.gte(NDMI_DROP_THRESHOLD))
    .selfMask()
    .rename('ndmi_only');

  var combined = baseVeg
    .and(ndviDrop.gte(NDVI_DROP_THRESHOLD))
    .and(ndmiDrop.gte(NDMI_DROP_THRESHOLD))
    .selfMask()
    .rename('combined');

  return {
    baseVeg: baseVeg,
    ndviDrop: ndviDrop,
    ndmiDrop: ndmiDrop,
    ndviOnly: ndviOnly,
    ndmiOnly: ndmiOnly,
    combined: combined,
    validPair: validPair(base, target)
  };
}


function safeFraction(n, d) {
  return ee.Algorithms.If(
    ee.Number(d).gt(0),
    ee.Number(n).divide(d),
    null
  );
}


// ---------------------------------------------------------------
// 5. A — Baseline-year sensitivity
// ---------------------------------------------------------------
var target2026 = annualComposite(2026);

function baselineSensitivityFeature(year) {
  var base = annualComposite(year);
  var m = comparisonMasks(base, target2026);

  var baselineHa = areaHa(m.baseVeg.selfMask());

  var comparableBaseHa = areaHa(
    m.baseVeg
      .and(m.validPair)
      .selfMask()
  );

  var combinedHa = areaHa(m.combined);
  var ndviOnlyHa = areaHa(m.ndviOnly);
  var ndmiOnlyHa = areaHa(m.ndmiOnly);

  return ee.Feature(null, {
    baseline_year: year,
    target_year: 2026,

    baseline_vegetation_ha: baselineHa,
    comparable_baseline_vegetation_ha: comparableBaseHa,

    ndvi_only_loss_ha: ndviOnlyHa,
    ndmi_only_loss_ha: ndmiOnlyHa,
    combined_loss_ha: combinedHa,

    combined_fraction_of_full_baseline:
      safeFraction(combinedHa, baselineHa),

    combined_fraction_of_comparable_baseline:
      safeFraction(combinedHa, comparableBaseHa),

    baseline_ndvi_threshold: BASELINE_NDVI,
    baseline_ndmi_threshold: BASELINE_NDMI,
    ndvi_drop_threshold: NDVI_DROP_THRESHOLD,
    ndmi_drop_threshold: NDMI_DROP_THRESHOLD,

    analysis_crs: ANALYSIS_CRS,
    analysis_scale_m: ANALYSIS_SCALE_M,
    grid_transform: ANALYSIS_TRANSFORM.join(',')
  });
}

var baselineSensitivity = ee.FeatureCollection(
  [2020, 2021, 2022].map(function(year) {
    return baselineSensitivityFeature(year);
  })
);

print('A. Baseline-year sensitivity:', baselineSensitivity);


// ---------------------------------------------------------------
// 6. B — 2022->2026 index ablation
// ---------------------------------------------------------------
var base2022 = annualComposite(2022);
var masks2022_2026 = comparisonMasks(base2022, target2026);

var baseline2022Ha = areaHa(
  masks2022_2026.baseVeg.selfMask()
);

var comparable2022Ha = areaHa(
  masks2022_2026.baseVeg
    .and(masks2022_2026.validPair)
    .selfMask()
);

function ablationFeature(name, mask) {
  var lossHa = areaHa(mask);

  return ee.Feature(null, {
    comparison: '2022_to_2026',
    criterion: name,
    loss_area_ha: lossHa,
    fraction_of_full_2022_baseline:
      safeFraction(lossHa, baseline2022Ha),
    fraction_of_comparable_2022_baseline:
      safeFraction(lossHa, comparable2022Ha),
    baseline_vegetation_ha: baseline2022Ha,
    comparable_baseline_vegetation_ha: comparable2022Ha,
    analysis_crs: ANALYSIS_CRS,
    analysis_scale_m: ANALYSIS_SCALE_M
  });
}

var ablation2022_2026 = ee.FeatureCollection([
  ablationFeature('NDVI_only_drop_ge_0.20',
                  masks2022_2026.ndviOnly),
  ablationFeature('NDMI_only_drop_ge_0.10',
                  masks2022_2026.ndmiOnly),
  ablationFeature('NDVI_and_NDMI_combined',
                  masks2022_2026.combined)
]);

print('B. 2022->2026 ablation:', ablation2022_2026);


// ---------------------------------------------------------------
// 7. C — Pre-development null comparisons
// ---------------------------------------------------------------
var NULL_PAIRS = [
  [2019, 2020],
  [2020, 2021],
  [2021, 2022]
];

function nullPairFeatures(pair) {
  var y0 = pair[0];
  var y1 = pair[1];

  var base = annualComposite(y0);
  var target = annualComposite(y1);
  var m = comparisonMasks(base, target);

  var baselineHa = areaHa(m.baseVeg.selfMask());
  var comparableHa = areaHa(
    m.baseVeg
      .and(m.validPair)
      .selfMask()
  );

  var ndviHa = areaHa(m.ndviOnly);
  var ndmiHa = areaHa(m.ndmiOnly);
  var combinedHa = areaHa(m.combined);

  return [
    ee.Feature(null, {
      baseline_year: y0,
      target_year: y1,
      criterion: 'NDVI_only_drop_ge_0.20',
      loss_area_ha: ndviHa,
      fraction_of_full_baseline:
        safeFraction(ndviHa, baselineHa),
      fraction_of_comparable_baseline:
        safeFraction(ndviHa, comparableHa),
      baseline_vegetation_ha: baselineHa,
      comparable_baseline_vegetation_ha: comparableHa
    }),

    ee.Feature(null, {
      baseline_year: y0,
      target_year: y1,
      criterion: 'NDMI_only_drop_ge_0.10',
      loss_area_ha: ndmiHa,
      fraction_of_full_baseline:
        safeFraction(ndmiHa, baselineHa),
      fraction_of_comparable_baseline:
        safeFraction(ndmiHa, comparableHa),
      baseline_vegetation_ha: baselineHa,
      comparable_baseline_vegetation_ha: comparableHa
    }),

    ee.Feature(null, {
      baseline_year: y0,
      target_year: y1,
      criterion: 'NDVI_and_NDMI_combined',
      loss_area_ha: combinedHa,
      fraction_of_full_baseline:
        safeFraction(combinedHa, baselineHa),
      fraction_of_comparable_baseline:
        safeFraction(combinedHa, comparableHa),
      baseline_vegetation_ha: baselineHa,
      comparable_baseline_vegetation_ha: comparableHa
    })
  ];
}

var nullFeatureList = [];
NULL_PAIRS.forEach(function(pair) {
  nullFeatureList = nullFeatureList.concat(
    nullPairFeatures(pair)
  );
});

var nullComparisons = ee.FeatureCollection(nullFeatureList);

print('C. Pre-development null comparisons:', nullComparisons);


// ---------------------------------------------------------------
// 8. D — 2023 event-window analysis
// ---------------------------------------------------------------
//
// Historical-image review date: 2023-05-05.
//
// Important:
// The labels "pre-May-5" and "post-May-5" are temporal labels only.
// They do NOT assert that clearing began exactly on 2023-05-05.
//
// Baseline is fixed to 2022 Mar-Jul P70.
// ---------------------------------------------------------------

var eventWindows = [
  {
    id: '2022_MarJul_baseline',
    start: '2022-03-01',
    end: '2022-08-01',
    end_inclusive: '2022-07-31'
  },
  {
    id: '2023_Jan01_May05',
    start: '2023-01-01',
    end: '2023-05-06',
    end_inclusive: '2023-05-05'
  },
  {
    id: '2023_May06_Jul31',
    start: '2023-05-06',
    end: '2023-08-01',
    end_inclusive: '2023-07-31'
  },
  {
    id: '2023_MarJul_full',
    start: '2023-03-01',
    end: '2023-08-01',
    end_inclusive: '2023-07-31'
  },
  {
    id: '2024_MarJul',
    start: '2024-03-01',
    end: '2024-08-01',
    end_inclusive: '2024-07-31'
  }
];

function eventWindowFeature(cfg) {
  var img = compositeBetween(
    cfg.start,
    cfg.end,
    cfg.id
  );

  var stats = meanStats(img);

  var m = comparisonMasks(base2022, img);
  var combinedHa = areaHa(m.combined);
  var comparableHa = areaHa(
    m.baseVeg
      .and(m.validPair)
      .selfMask()
  );

  return ee.Feature(null, {
    window_id: cfg.id,
    start_date: cfg.start,
    end_date_inclusive: cfg.end_inclusive,

    scene_count: img.get('scene_count'),

    mean_NDVI_P70: stats.get('NDVI_P70'),
    mean_NDMI_P70: stats.get('NDMI_P70'),
    mean_valid_obs: stats.get('valid_obs'),

    combined_loss_vs_2022_ha: combinedHa,
    loss_fraction_of_full_2022_baseline:
      safeFraction(combinedHa, baseline2022Ha),
    loss_fraction_of_comparable_2022_baseline:
      safeFraction(combinedHa, comparableHa),

    comparable_2022_baseline_ha: comparableHa,

    analysis_crs: ANALYSIS_CRS,
    analysis_scale_m: ANALYSIS_SCALE_M
  });
}

var eventWindowFC = ee.FeatureCollection(
  eventWindows.map(function(cfg) {
    return eventWindowFeature(cfg);
  })
);

print('D. Event-window analysis:', eventWindowFC);


// ---------------------------------------------------------------
// 9. Optional spatial ablation raster
// ---------------------------------------------------------------
//
// 0   = valid comparison pixel that does not satisfy this criterion
// 1   = satisfies criterion
// 255 = outside AOI / invalid comparison pixel
//
// Three bands:
//   loss_ndvi_only
//   loss_ndmi_only
//   loss_combined
// ---------------------------------------------------------------

function exportBand(mask, name) {
  return mask
    .unmask(0)
    .updateMask(masks2022_2026.validPair)
    .clip(AOI)
    .rename(name)
    .toByte()
    .unmask(255, false)
    .toByte();
}

var ablationRaster = ee.Image.cat([
  exportBand(
    masks2022_2026.ndviOnly,
    'loss_ndvi_only'
  ),
  exportBand(
    masks2022_2026.ndmiOnly,
    'loss_ndmi_only'
  ),
  exportBand(
    masks2022_2026.combined,
    'loss_combined'
  )
]);


// ---------------------------------------------------------------
// 10. Exports
// ---------------------------------------------------------------

Export.table.toDrive({
  collection: baselineSensitivity,
  description: 'SC0002_STEP3A_Baseline_Year_Sensitivity',
  fileNamePrefix: 'SC0002_STEP3A_Baseline_Year_Sensitivity',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: ablation2022_2026,
  description: 'SC0002_STEP3A_2022_2026_Index_Ablation',
  fileNamePrefix: 'SC0002_STEP3A_2022_2026_Index_Ablation',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: nullComparisons,
  description: 'SC0002_STEP3A_PreDevelopment_Null_Comparisons',
  fileNamePrefix: 'SC0002_STEP3A_PreDevelopment_Null_Comparisons',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: eventWindowFC,
  description: 'SC0002_STEP3A_2023_Event_Window',
  fileNamePrefix: 'SC0002_STEP3A_2023_Event_Window',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV'
});

Export.image.toDrive({
  image: ablationRaster,
  description: 'SC0002_STEP3A_2022_2026_Ablation_Masks',
  fileNamePrefix: 'SC0002_STEP3A_2022_2026_Ablation_Masks',
  folder: DRIVE_FOLDER,
  region: EXPORT_REGION,
  crs: ANALYSIS_CRS,
  crsTransform: ANALYSIS_TRANSFORM,
  maxPixels: 1e9,
  fileFormat: 'GeoTIFF',
  formatOptions: {
    cloudOptimized: true,
    noData: 255
  }
});


// ---------------------------------------------------------------
// 11. Map layers
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

Map.addLayer(
  masks2022_2026.ndviOnly,
  {palette: ['FF8C00']},
  '2022->2026 NDVI-only',
  false
);

Map.addLayer(
  masks2022_2026.ndmiOnly,
  {palette: ['4169E1']},
  '2022->2026 NDMI-only',
  false
);

Map.addLayer(
  masks2022_2026.combined,
  {palette: ['FF0000']},
  '2022->2026 combined',
  true
);
