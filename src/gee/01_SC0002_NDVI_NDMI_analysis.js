// SC0002 NDVI / NDMI Case Study — FIXED UTM GRID + RASTER QA VERSION
// ====================================================================
//
// STEP 1B reproducibility fix:
//   - Exact archived AOI geometry is embedded; no private asset ID is required.
//   - Analysis grid is explicitly EPSG:32651 on a globally anchored 10 m grid.
//   - Every reduceRegion uses the same CRS + crsTransform.
//   - Export raster is clipped to AOI.
//   - Outside-AOI / invalid pixels are explicitly written as 255 NoData.
//   - Raster loss-pixel QA counts are computed from the same clipped raster core
//     over the same rectangular export region, so QGIS counts can be checked.
//   - The exact AOI used by Earth Engine is exported as GeoJSON.
//   - CSV schemas are explicit.
//
// AOI reconstruction reference:
//   chosen parcel points        : 93
//   source builder planar area  : 63.304526 ha (EPSG:3826; feature property)
//   previous GEE geodesic area  : ~63.456375 ha
//   computed cluster centroid   : 120.414439044, 22.713945147
//
// IMPORTANT:
//   Formal published area uses ee.Image.pixelArea() inside the AOI.
//   The raster QA count is a count of full 10 m raster cells whose rasterized
//   footprint is retained after clip(AOI). Boundary cells can therefore make
//   raster_count * 0.01 ha differ slightly from the vector-weighted area.
//
// Output terminology:
//   "spectral vegetation loss" — NOT "tree loss".

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

// Fixed analysis grid.
// Explicit crsTransform avoids any ambiguity about grid alignment.
var ANALYSIS_CRS = 'EPSG:32651';
var ANALYSIS_SCALE_M = 10;
var ANALYSIS_TRANSFORM = [10, 0, 0, 0, -10, 0];

var DRIVE_FOLDER = 'SC0002_GEE_UTM51N_v4';

// ---------------------------------------------------------------
// 1. SC0002 AOI
// ---------------------------------------------------------------
var AOI_FC = SC0002_FC;
var AOI = SC0002_AOI;
var ANALYSIS_PROJ = ee.Projection(ANALYSIS_CRS);

// Rectangular export region in the analysis projection.
// The AOI itself is still used for all formal vector-weighted area reductions.
var EXPORT_REGION = AOI
  .transform(ANALYSIS_PROJ, 1)
  .bounds(1, ANALYSIS_PROJ);

print('SC0002 AOI source:', 'embedded archived V4 geometry');
print('Analysis CRS:', ANALYSIS_CRS);
print('Analysis transform:', ANALYSIS_TRANSFORM);
print('Analysis scale (m):', ANALYSIS_SCALE_M);
print('SC0002 AOI feature count:', AOI_FC.size());
print('SC0002 AOI geodesic area (ha):', AOI.area(1).divide(10000));
print('SC0002 builder planar area property (ha):',
      ee.Feature(AOI_FC.first()).get('area_ha'));

// ---------------------------------------------------------------
// 2. Analysis configuration
// ---------------------------------------------------------------
var YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026];
var START_MONTH = 3;
var END_MONTH = 7;

var BASELINE_NDVI = 0.55;
var BASELINE_NDMI = 0.10;
var NDVI_DROP_THRESHOLD = 0.20;
var NDMI_DROP_THRESHOLD = 0.10;

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

// ---------------------------------------------------------------
// 4. Annual March–July P70 composites
// ---------------------------------------------------------------
function annualComposite(year) {
  var start = ee.Date.fromYMD(year, START_MONTH, 1);
  var end = ee.Date.fromYMD(year, END_MONTH + 1, 1);

  var col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(AOI)
    .filterDate(start, end)
    .map(maskAndAddIndices);

  var p70 = col.reduce(ee.Reducer.percentile([70]))
    .rename(['NDVI_P70', 'NDMI_P70']);

  var count = col.select('NDVI').count().rename('valid_obs');

  return p70.addBands(count)
    .set('year', year)
    .set('scene_count', col.size());
}

var composites = {};
YEARS.forEach(function(year) {
  composites[year] = annualComposite(year);
});

// ---------------------------------------------------------------
// 5. Annual statistics
// ---------------------------------------------------------------
function annualStatsFeature(year) {
  var img = composites[year];

  var stats = img.reduceRegion({
    reducer: ee.Reducer.mean()
      .combine(ee.Reducer.median(), '', true),
    geometry: AOI,
    crs: ANALYSIS_CRS,
    crsTransform: ANALYSIS_TRANSFORM,
    maxPixels: 1e9,
    tileScale: 4
  });

  return ee.Feature(null, {
    year: year,
    scene_count: img.get('scene_count'),
    mean_NDVI_P70: stats.get('NDVI_P70_mean'),
    median_NDVI_P70: stats.get('NDVI_P70_median'),
    mean_NDMI_P70: stats.get('NDMI_P70_mean'),
    median_NDMI_P70: stats.get('NDMI_P70_median'),
    mean_valid_obs: stats.get('valid_obs_mean'),
    analysis_crs: ANALYSIS_CRS,
    analysis_scale_m: ANALYSIS_SCALE_M,
    grid_transform: ANALYSIS_TRANSFORM.join(',')
  });
}

var annualStats = ee.FeatureCollection(
  YEARS.map(function(year) {
    return annualStatsFeature(year);
  })
);

print('SC0002 annual NDVI/NDMI stats:', annualStats);

// ---------------------------------------------------------------
// 6. 2022 -> 2026 spectral change
// ---------------------------------------------------------------
var baseline2022 = composites[2022];
var target2026 = composites[2026];

var baselineVegetation = baseline2022.select('NDVI_P70').gte(BASELINE_NDVI)
  .and(baseline2022.select('NDMI_P70').gte(BASELINE_NDMI))
  .rename('baseline_vegetation');

var ndviDrop = baseline2022.select('NDVI_P70')
  .subtract(target2026.select('NDVI_P70'))
  .rename('NDVI_drop_2022_2026');

var ndmiDrop = baseline2022.select('NDMI_P70')
  .subtract(target2026.select('NDMI_P70'))
  .rename('NDMI_drop_2022_2026');

var spectralLoss = baselineVegetation
  .and(ndviDrop.gte(NDVI_DROP_THRESHOLD))
  .and(ndmiDrop.gte(NDMI_DROP_THRESHOLD))
  .selfMask()
  .rename('spectral_vegetation_loss');

var validPair2022_2026 = baseline2022.select('NDVI_P70').mask()
  .and(baseline2022.select('NDMI_P70').mask())
  .and(target2026.select('NDVI_P70').mask())
  .and(target2026.select('NDMI_P70').mask())
  .rename('valid_pair_2022_2026');

// ---------------------------------------------------------------
// 7. Area + raster-QA helpers
// ---------------------------------------------------------------
function maskedAreaHa(mask) {
  var areaImage = ee.Image.pixelArea()
    .divide(10000)
    .updateMask(mask)
    .rename('ha');

  var dict = areaImage.reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: AOI,
    crs: ANALYSIS_CRS,
    crsTransform: ANALYSIS_TRANSFORM,
    maxPixels: 1e9,
    tileScale: 4
  });

  return ee.Number(ee.Algorithms.If(dict.get('ha'), dict.get('ha'), 0));
}

// This is the exact raster core that is exported before masked cells are
// converted to the numeric NoData value 255.
function makeRasterCore(mask, name) {
  return mask
    .unmask(0)
    .updateMask(validPair2022_2026)
    .clip(AOI)
    .rename(name)
    .toByte();
}

// Count raster cells from the SAME clipped raster core and SAME rectangular
// export region used by Export.image.toDrive. This is for raster QA only.
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


var aoiGeodesicHa = ee.Number(AOI.area(1)).divide(10000);
var builderPlanarHa = ee.Number(ee.Feature(AOI_FC.first()).get('area_ha'));
var baselineVegHa = maskedAreaHa(baselineVegetation.selfMask());
var spectralLossHa = maskedAreaHa(spectralLoss);

var spectralLossPixelCount = rasterLossPixelCount(spectralLoss);
var spectralLossNominalRasterHa = spectralLossPixelCount
  .multiply(ANALYSIS_SCALE_M * ANALYSIS_SCALE_M)
  .divide(10000);

var lossFraction = ee.Algorithms.If(
  baselineVegHa.gt(0),
  spectralLossHa.divide(baselineVegHa),
  null
);

var summary = ee.FeatureCollection([
  ee.Feature(null, {
    metric: 'AOI_builder_planar_area_ha',
    value: builderPlanarHa,
    note: 'Source AOI feature property from local EPSG:3826 builder',
    rule: 'feature property area_ha',
    analysis_crs: ANALYSIS_CRS,
    analysis_scale_m: ANALYSIS_SCALE_M,
    grid_transform: ANALYSIS_TRANSFORM.join(',')
  }),
  ee.Feature(null, {
    metric: 'AOI_geodesic_area_ha',
    value: aoiGeodesicHa,
    note: 'Earth Engine geodesic vector area; not raster-cell area',
    rule: 'AOI.geometry().area(1)/10000',
    analysis_crs: ANALYSIS_CRS,
    analysis_scale_m: ANALYSIS_SCALE_M,
    grid_transform: ANALYSIS_TRANSFORM.join(',')
  }),
  ee.Feature(null, {
    metric: '2022_baseline_spectral_vegetation_ha',
    value: baselineVegHa,
    note: '2022 March-July Sentinel-2 P70 baseline',
    rule: 'NDVI_P70>=0.55 AND NDMI_P70>=0.10',
    analysis_crs: ANALYSIS_CRS,
    analysis_scale_m: ANALYSIS_SCALE_M,
    grid_transform: ANALYSIS_TRANSFORM.join(',')
  }),
  ee.Feature(null, {
    metric: '2022_to_2026_spectral_vegetation_loss_ha',
    value: spectralLossHa,
    note: 'pixelArea-based area inside AOI; threshold-defined; not tree loss',
    rule: 'baseline vegetation AND NDVI_2022-NDVI_2026>=0.20 AND NDMI_2022-NDMI_2026>=0.10',
    analysis_crs: ANALYSIS_CRS,
    analysis_scale_m: ANALYSIS_SCALE_M,
    grid_transform: ANALYSIS_TRANSFORM.join(',')
  }),
  ee.Feature(null, {
    metric: 'loss_fraction_of_2022_baseline',
    value: lossFraction,
    note: 'spectral_loss_ha / 2022_baseline_spectral_vegetation_ha',
    rule: 'loss_fraction = spectral_loss_ha / baseline_vegetation_ha',
    analysis_crs: ANALYSIS_CRS,
    analysis_scale_m: ANALYSIS_SCALE_M,
    grid_transform: ANALYSIS_TRANSFORM.join(',')
  }),
  ee.Feature(null, {
    metric: '2022_to_2026_export_raster_loss_pixel_count',
    value: spectralLossPixelCount,
    note: 'QA count from same clipped raster core and export rectangle',
    rule: 'sum(loss raster core), unweighted',
    analysis_crs: ANALYSIS_CRS,
    analysis_scale_m: ANALYSIS_SCALE_M,
    grid_transform: ANALYSIS_TRANSFORM.join(',')
  }),
  ee.Feature(null, {
    metric: '2022_to_2026_export_raster_nominal_loss_area_ha',
    value: spectralLossNominalRasterHa,
    note: 'QA only: full-cell count * 100 m2 / 10000; boundary cells are full raster cells',
    rule: 'export_raster_loss_pixel_count * 0.01 ha',
    analysis_crs: ANALYSIS_CRS,
    analysis_scale_m: ANALYSIS_SCALE_M,
    grid_transform: ANALYSIS_TRANSFORM.join(',')
  })
]);

print('SC0002 spectral-change summary:', summary);

// ---------------------------------------------------------------
// 8. Year-by-year loss against 2022 baseline
// ---------------------------------------------------------------
function lossVs2022Feature(year) {
  var target = composites[year];

  var yearNdviDrop = baseline2022.select('NDVI_P70')
    .subtract(target.select('NDVI_P70'));

  var yearNdmiDrop = baseline2022.select('NDMI_P70')
    .subtract(target.select('NDMI_P70'));

  var yearLoss = baselineVegetation
    .and(yearNdviDrop.gte(NDVI_DROP_THRESHOLD))
    .and(yearNdmiDrop.gte(NDMI_DROP_THRESHOLD))
    .selfMask();

  var yearLossHa = maskedAreaHa(yearLoss);

  return ee.Feature(null, {
    baseline_year: 2022,
    target_year: year,
    spectral_loss_ha: yearLossHa,
    loss_fraction_of_2022_baseline: ee.Algorithms.If(
      baselineVegHa.gt(0),
      yearLossHa.divide(baselineVegHa),
      null
    ),
    analysis_crs: ANALYSIS_CRS,
    analysis_scale_m: ANALYSIS_SCALE_M,
    grid_transform: ANALYSIS_TRANSFORM.join(',')
  });
}

var lossTimeSeries = ee.FeatureCollection(
  [2023, 2024, 2025, 2026].map(function(year) {
    return lossVs2022Feature(year);
  })
);

print('SC0002 loss time series vs 2022:', lossTimeSeries);

// ---------------------------------------------------------------
// 9. Map layers
// ---------------------------------------------------------------
Map.centerObject(AOI_FC, 15);

Map.addLayer(
  AOI_FC.style({color: 'FFFF00', fillColor: '00000000', width: 2}),
  {},
  'SC0002 government-derived AOI',
  true
);

Map.addLayer(
  baseline2022.select('NDVI_P70'),
  {min: 0, max: 0.9, palette: ['white', 'yellow', 'green']},
  '2022 NDVI P70',
  false
);

Map.addLayer(
  target2026.select('NDVI_P70'),
  {min: 0, max: 0.9, palette: ['white', 'yellow', 'green']},
  '2026 NDVI P70',
  false
);

Map.addLayer(
  spectralLoss,
  {palette: ['FF0000']},
  'SC0002 spectral vegetation loss',
  true
);

// ---------------------------------------------------------------
// 10. Exports
// ---------------------------------------------------------------
Export.table.toDrive({
  collection: annualStats,
  description: 'SC0002_Annual_NDVI_NDMI_2018_2026_UTM51N_V4',
  fileNamePrefix: 'SC0002_Annual_NDVI_NDMI_2018_2026_UTM51N_V4',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV',
  selectors: [
    'year', 'scene_count',
    'mean_NDVI_P70', 'median_NDVI_P70',
    'mean_NDMI_P70', 'median_NDMI_P70',
    'mean_valid_obs',
    'analysis_crs', 'analysis_scale_m', 'grid_transform'
  ]
});

Export.table.toDrive({
  collection: summary,
  description: 'SC0002_Spectral_Change_Summary_UTM51N_V4',
  fileNamePrefix: 'SC0002_Spectral_Change_Summary_UTM51N_V4',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV',
  selectors: [
    'metric', 'value', 'note', 'rule',
    'analysis_crs', 'analysis_scale_m', 'grid_transform'
  ]
});

Export.table.toDrive({
  collection: lossTimeSeries,
  description: 'SC0002_Loss_TimeSeries_2022_2026_UTM51N_V4',
  fileNamePrefix: 'SC0002_Loss_TimeSeries_2022_2026_UTM51N_V4',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV',
  selectors: [
    'baseline_year', 'target_year',
    'spectral_loss_ha', 'loss_fraction_of_2022_baseline',
    'analysis_crs', 'analysis_scale_m', 'grid_transform'
  ]
});

Export.table.toDrive({
  collection: AOI_FC,
  description: 'SC0002_Envelope_USED_BY_GEE_V4',
  fileNamePrefix: 'SC0002_Envelope_USED_BY_GEE_V4',
  folder: DRIVE_FOLDER,
  fileFormat: 'GeoJSON'
});

// Fill all masked cells AFTER clip with 255 and extend the footprint so
// outside-AOI pixels in the rectangular GeoTIFF are explicitly NoData.
var spectralLossExport = makeRasterCore(
    spectralLoss,
    'spectral_vegetation_loss'
  )
  .unmask(255, false)
  .toByte();

Export.image.toDrive({
  image: spectralLossExport,
  description: 'SC0002_Spectral_Vegetation_Loss_2022_2026_UTM51N_V4',
  fileNamePrefix: 'SC0002_Spectral_Vegetation_Loss_2022_2026_UTM51N_V4',
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
