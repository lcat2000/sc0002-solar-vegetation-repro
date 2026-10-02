// SC0002 NDVI / NDMI Threshold Sensitivity — UTM GRID + RASTER QA V4
// ====================================================================
//
// Uses the same AOI, EPSG:32651 CRS, globally anchored 10 m grid,
// rectangular export region, clipping logic, and 255 NoData convention as
// SC0002_NDVI_NDMI_analysis.js.
//
// Thresholds:
//   Loose    : NDVI drop >= 0.15, NDMI drop >= 0.08
//   Standard : NDVI drop >= 0.20, NDMI drop >= 0.10
//   Strict   : NDVI drop >= 0.25, NDMI drop >= 0.12
//
// Baseline vegetation:
//   2022 NDVI_P70 >= 0.55 AND NDMI_P70 >= 0.10

// ---------------------------------------------------------------
// 0. REPRODUCIBLE CONFIGURATION
// The archived AOI is embedded below; no private asset path is required.
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

var DRIVE_FOLDER = 'SC0002_GEE_UTM51N_v4';

// ---------------------------------------------------------------
// 1. AOI
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
print('Analysis scale (m):', ANALYSIS_SCALE_M);
print('SC0002 AOI geodesic area (ha):', AOI.area(1).divide(10000));

// ---------------------------------------------------------------
// 2. Configuration
// ---------------------------------------------------------------
var START_MONTH = 3;
var END_MONTH = 7;

var BASELINE_NDVI = 0.55;
var BASELINE_NDMI = 0.10;

var THRESHOLDS = [
  {name: 'Loose', ndvi_drop: 0.15, ndmi_drop: 0.08},
  {name: 'Standard', ndvi_drop: 0.20, ndmi_drop: 0.10},
  {name: 'Strict', ndvi_drop: 0.25, ndmi_drop: 0.12}
];

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

  return sr.addBands([ndvi, ndmi])
    .select(['NDVI', 'NDMI'])
    .copyProperties(img, img.propertyNames());
}

function annualComposite(year) {
  var start = ee.Date.fromYMD(year, START_MONTH, 1);
  var end = ee.Date.fromYMD(year, END_MONTH + 1, 1);

  var col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(AOI)
    .filterDate(start, end)
    .map(maskAndAddIndices);

  return col.reduce(ee.Reducer.percentile([70]))
    .rename(['NDVI_P70', 'NDMI_P70'])
    .set('year', year)
    .set('scene_count', col.size());
}

// ---------------------------------------------------------------
// 4. Baseline and target
// ---------------------------------------------------------------
var baseline2022 = annualComposite(2022);
var target2026 = annualComposite(2026);

var baselineVegetation = baseline2022.select('NDVI_P70')
  .gte(BASELINE_NDVI)
  .and(baseline2022.select('NDMI_P70').gte(BASELINE_NDMI))
  .rename('baseline_vegetation');

var ndviDrop = baseline2022.select('NDVI_P70')
  .subtract(target2026.select('NDVI_P70'));

var ndmiDrop = baseline2022.select('NDMI_P70')
  .subtract(target2026.select('NDMI_P70'));

var validPair2022_2026 = baseline2022.select('NDVI_P70').mask()
  .and(baseline2022.select('NDMI_P70').mask())
  .and(target2026.select('NDVI_P70').mask())
  .and(target2026.select('NDMI_P70').mask());

// ---------------------------------------------------------------
// 5. Helpers
// ---------------------------------------------------------------
function maskedAreaHa(mask) {
  var dict = ee.Image.pixelArea()
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

  return ee.Number(ee.Algorithms.If(dict.get('ha'), dict.get('ha'), 0));
}

function makeLossMask(ndviT, ndmiT) {
  return baselineVegetation
    .and(ndviDrop.gte(ndviT))
    .and(ndmiDrop.gte(ndmiT))
    .selfMask();
}

function makeRasterCore(mask, name) {
  return mask
    .unmask(0)
    .updateMask(validPair2022_2026)
    .clip(AOI)
    .rename(name)
    .toByte();
}

function rasterLossPixelCount(mask) {
  var core = makeRasterCore(mask, 'v');

  var dict = core.reduceRegion({
    reducer: ee.Reducer.sum().unweighted(),
    geometry: EXPORT_REGION,
    crs: ANALYSIS_CRS,
    crsTransform: ANALYSIS_TRANSFORM,
    maxPixels: 1e9,
    tileScale: 4
  });

  return ee.Number(ee.Algorithms.If(dict.get('v'), dict.get('v'), 0));
}


var baselineVegHa = maskedAreaHa(baselineVegetation.selfMask());

// ---------------------------------------------------------------
// 6. Sensitivity table
// ---------------------------------------------------------------
function makeSensitivityFeature(cfg) {
  var lossMask = makeLossMask(cfg.ndvi_drop, cfg.ndmi_drop);
  var lossHa = maskedAreaHa(lossMask);
  var pixelCount = rasterLossPixelCount(lossMask);
  var nominalRasterHa = pixelCount
    .multiply(ANALYSIS_SCALE_M * ANALYSIS_SCALE_M)
    .divide(10000);

  return ee.Feature(null, {
    threshold_name: cfg.name,
    baseline_ndvi: BASELINE_NDVI,
    baseline_ndmi: BASELINE_NDMI,
    ndvi_drop_threshold: cfg.ndvi_drop,
    ndmi_drop_threshold: cfg.ndmi_drop,
    baseline_vegetation_ha: baselineVegHa,
    spectral_loss_ha: lossHa,
    loss_fraction_of_2022_baseline: ee.Algorithms.If(
      baselineVegHa.gt(0),
      lossHa.divide(baselineVegHa),
      null
    ),
    export_raster_loss_pixel_count: pixelCount,
    export_raster_nominal_loss_area_ha: nominalRasterHa,
    analysis_crs: ANALYSIS_CRS,
    analysis_scale_m: ANALYSIS_SCALE_M,
    grid_transform: ANALYSIS_TRANSFORM.join(',')
  });
}

var sensitivityFC = ee.FeatureCollection(
  THRESHOLDS.map(function(cfg) {
    return makeSensitivityFeature(cfg);
  })
);

print('SC0002 threshold sensitivity:', sensitivityFC);

var lossLoose = makeLossMask(0.15, 0.08);
var lossStandard = makeLossMask(0.20, 0.10);
var lossStrict = makeLossMask(0.25, 0.12);

// ---------------------------------------------------------------
// 7. Map layers
// ---------------------------------------------------------------
Map.centerObject(AOI_FC, 15);
Map.addLayer(
  AOI_FC.style({color: 'FFFF00', fillColor: '00000000', width: 2}),
  {},
  'SC0002 AOI',
  true
);
Map.addLayer(lossLoose, {palette: ['FFA500']}, 'Loose 0.15 / 0.08', false);
Map.addLayer(lossStandard, {palette: ['FF0000']}, 'Standard 0.20 / 0.10', true);
Map.addLayer(lossStrict, {palette: ['800080']}, 'Strict 0.25 / 0.12', false);

// ---------------------------------------------------------------
// 8. CSV export
// ---------------------------------------------------------------
Export.table.toDrive({
  collection: sensitivityFC,
  description: 'SC0002_Threshold_Sensitivity_UTM51N_V4',
  fileNamePrefix: 'SC0002_Threshold_Sensitivity_UTM51N_V4',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV',
  selectors: [
    'threshold_name',
    'baseline_ndvi', 'baseline_ndmi',
    'ndvi_drop_threshold', 'ndmi_drop_threshold',
    'baseline_vegetation_ha',
    'spectral_loss_ha',
    'loss_fraction_of_2022_baseline',
    'export_raster_loss_pixel_count',
    'export_raster_nominal_loss_area_ha',
    'analysis_crs', 'analysis_scale_m', 'grid_transform'
  ]
});

// ---------------------------------------------------------------
// 9. Multi-band GeoTIFF
// ---------------------------------------------------------------
function exportBand(mask, name) {
  return makeRasterCore(mask, name)
    .unmask(255, false)
    .toByte();
}

var sensitivityRaster = ee.Image.cat([
  exportBand(lossLoose, 'loss_loose'),
  exportBand(lossStandard, 'loss_standard'),
  exportBand(lossStrict, 'loss_strict')
]);

Export.image.toDrive({
  image: sensitivityRaster,
  description: 'SC0002_Threshold_Sensitivity_Masks_UTM51N_V4',
  fileNamePrefix: 'SC0002_Threshold_Sensitivity_Masks_UTM51N_V4',
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
