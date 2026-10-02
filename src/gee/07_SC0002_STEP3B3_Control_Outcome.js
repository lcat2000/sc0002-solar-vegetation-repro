// SC0002 Step 3B.3 — Treatment vs Frozen Matched Controls
// ============================================================================
//
// PURPOSE
// -------
// This is the FIRST outcome analysis after the matched-control set was frozen.
//
// Frozen controls from Step 3B.2:
//   C162, C172, C176, C222, C129
//
// Selection used only PRE-TREATMENT covariates plus outcome-blind treatment
// status screening. This script now computes 2022->2023/2024/2025/2026
// Sentinel-2 NDVI/NDMI outcomes for SC0002 and those frozen controls.
//
// IMPORTANT
// ---------
// Do not use the results from this script to change the control set.
// If a control result looks surprising, investigate it as a sensitivity or
// diagnostic analysis, not by replacing the control post hoc.
//
// Same analytical rule as SC0002 V4:
//   Sentinel-2 SR Harmonized
//   March-July
//   SCL exclude 0,1,3,7,8,9,10,11
//   annual P70 NDVI / NDMI
//   2022 baseline vegetation:
//       NDVI_P70 >= 0.55 AND NDMI_P70 >= 0.10
//   standard spectral vegetation loss:
//       baseline vegetation
//       AND 2022 NDVI - target-year NDVI >= 0.20
//       AND 2022 NDMI - target-year NDMI >= 0.10
//
// Projection:
//   EPSG:32651
//   10 m fixed grid
//   transform [10,0,0,0,-10,0]
//
// ============================================================================


// ---------------------------------------------------------------------------
// 0. CONFIG
// ---------------------------------------------------------------------------
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

var DRIVE_FOLDER = 'SC0002_STEP3B3_CONTROL_OUTCOME';

var CRS = 'EPSG:32651';
var SCALE_M = 10;
var TRANSFORM = [10, 0, 0, 0, -10, 0];

var START_MONTH_DAY = '-03-01';
var END_MONTH_DAY_EXCLUSIVE = '-08-01';

var BASELINE_YEAR = 2022;
var YEARS = [2022, 2023, 2024, 2025, 2026];

var BASE_NDVI_MIN = 0.55;
var BASE_NDMI_MIN = 0.10;
var NDVI_DROP_MIN = 0.20;
var NDMI_DROP_MIN = 0.10;

// Same nominal square geometry as Step 3B.1.
var CONTROL_SIDE_M = 796.5951;
var HALF_SIDE_M = CONTROL_SIDE_M / 2;


// ---------------------------------------------------------------------------
// 1. FROZEN controls — DO NOT CHANGE AFTER SEEING OUTCOMES
// ---------------------------------------------------------------------------
var FROZEN_CONTROLS = [
  {id: 'C162', order: 1, score: 0.251794610, x: 231409.013, y: 2525169.146},
  {id: 'C172', order: 2, score: 0.517142889, x: 232409.013, y: 2512169.146},
  {id: 'C176', order: 3, score: 0.536305349, x: 232409.013, y: 2516169.146},
  {id: 'C222', order: 4, score: 0.674966065, x: 234409.013, y: 2521169.146},
  {id: 'C129', order: 5, score: 0.741549727, x: 230409.013, y: 2515169.146}
];

print('FROZEN controls:', FROZEN_CONTROLS);


// ---------------------------------------------------------------------------
// 2. Site geometry
// ---------------------------------------------------------------------------
var sc0002Fc = SC0002_FC;

function controlFeature(c) {
  var rect = ee.Geometry.Rectangle(
    [
      c.x - HALF_SIDE_M,
      c.y - HALF_SIDE_M,
      c.x + HALF_SIDE_M,
      c.y + HALF_SIDE_M
    ],
    CRS,
    false
  );

  return ee.Feature(rect, {
    site_id: c.id,
    site_type: 'control',
    selected_control_order: c.order,
    pre_treatment_match_score: c.score,
    selection_frozen_before_outcome: 'YES'
  });
}

var siteList = [
  ee.Feature(sc0002Fc.geometry(), {
    site_id: 'SC0002',
    site_type: 'treatment',
    selected_control_order: 0,
    pre_treatment_match_score: null,
    selection_frozen_before_outcome: 'YES'
  })
];

FROZEN_CONTROLS.forEach(function(c) {
  siteList.push(controlFeature(c));
});

var sites = ee.FeatureCollection(siteList);

print('Site count (expect 6):', sites.size());
print('Sites:', sites);


// ---------------------------------------------------------------------------
// 3. Sentinel-2 preprocessing
// ---------------------------------------------------------------------------
function prepS2(img) {
  var scl = img.select('SCL');

  var good = scl.neq(0)
    .and(scl.neq(1))
    .and(scl.neq(3))
    .and(scl.neq(7))
    .and(scl.neq(8))
    .and(scl.neq(9))
    .and(scl.neq(10))
    .and(scl.neq(11));

  var masked = img.updateMask(good);

  var ndvi = masked
    .normalizedDifference(['B8', 'B4'])
    .rename('NDVI');

  var ndmi = masked
    .normalizedDifference(['B8', 'B11'])
    .rename('NDMI');

  var valid = ee.Image.constant(1)
    .updateMask(good)
    .rename('VALID')
    .toByte();

  return ee.Image.cat([ndvi, ndmi, valid])
    .copyProperties(img, ['system:time_start']);
}


function annualComposite(year, geom) {
  year = Number(year);

  var start = String(year) + START_MONTH_DAY;
  var end = String(year) + END_MONTH_DAY_EXCLUSIVE;

  var col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(geom)
    .filterDate(start, end)
    .map(prepS2);

  var ndvi = col
    .select('NDVI')
    .reduce(ee.Reducer.percentile([70]))
    .rename('NDVI_P70');

  var ndmi = col
    .select('NDMI')
    .reduce(ee.Reducer.percentile([70]))
    .rename('NDMI_P70');

  var validObs = col
    .select('VALID')
    .count()
    .rename('VALID_OBS');

  return ee.Image.cat([ndvi, ndmi, validObs])
    .set({
      year: year,
      scene_count: col.size(),
      window_start: start,
      window_end_exclusive: end
    });
}


// ---------------------------------------------------------------------------
// 4. Fixed-grid reducers
// ---------------------------------------------------------------------------
function reduceOne(img, reducer, geom) {
  return img.reduceRegion({
    reducer: reducer,
    geometry: geom,
    crs: CRS,
    crsTransform: TRANSFORM,
    maxPixels: 1e8
  });
}

function areaHa(maskImage, geom) {
  var area = ee.Image.pixelArea()
    .divide(10000)
    .rename('area_ha')
    .updateMask(maskImage.selfMask());

  var d = reduceOne(
    area,
    ee.Reducer.sum(),
    geom
  );

  return ee.Number(
    ee.Algorithms.If(
      d.contains('area_ha'),
      d.get('area_ha'),
      0
    )
  );
}

function siteAreaHa(geom) {
  var area = ee.Image.pixelArea()
    .divide(10000)
    .rename('area_ha');

  var d = reduceOne(
    area,
    ee.Reducer.sum(),
    geom
  );

  return ee.Number(d.get('area_ha'));
}

function bandMean(img, band, geom) {
  var d = reduceOne(
    img.select(band),
    ee.Reducer.mean(),
    geom
  );

  return d.get(band);
}

function bandMedian(img, band, geom) {
  var d = reduceOne(
    img.select(band),
    ee.Reducer.median(),
    geom
  );

  return d.get(band);
}


// ---------------------------------------------------------------------------
// 5. Outcome table
// ---------------------------------------------------------------------------
var outcomeFeatures = [];

siteList.forEach(function(site) {
  site = ee.Feature(site);

  var geom = site.geometry();
  var siteId = site.get('site_id');
  var siteType = site.get('site_type');
  var order = site.get('selected_control_order');
  var score = site.get('pre_treatment_match_score');

  var baseline = annualComposite(BASELINE_YEAR, geom);

  var baselineVeg = baseline.select('NDVI_P70')
    .gte(BASE_NDVI_MIN)
    .and(
      baseline.select('NDMI_P70')
        .gte(BASE_NDMI_MIN)
    )
    .rename('BASELINE_VEG');

  var siteArea = siteAreaHa(geom);
  var baselineArea = areaHa(baselineVeg, geom);
  var baselineFraction = baselineArea.divide(siteArea);

  YEARS.forEach(function(year) {
    var annual = annualComposite(year, geom);

    var ndviDrop = baseline.select('NDVI_P70')
      .subtract(annual.select('NDVI_P70'));

    var ndmiDrop = baseline.select('NDMI_P70')
      .subtract(annual.select('NDMI_P70'));

    var loss = baselineVeg
      .and(ndviDrop.gte(NDVI_DROP_MIN))
      .and(ndmiDrop.gte(NDMI_DROP_MIN))
      .rename('LOSS');

    // Pixels where both target-year indices are available.
    var annualValid = annual
      .select(['NDVI_P70', 'NDMI_P70'])
      .mask()
      .reduce(ee.Reducer.min())
      .gt(0);

    var baselineVegValidThisYear = baselineVeg
      .updateMask(annualValid)
      .rename('BASELINE_VEG_VALID_THIS_YEAR');

    var lossArea = areaHa(loss, geom);
    var baselineValidArea = areaHa(
      baselineVegValidThisYear,
      geom
    );

    var lossFractionBaseline = ee.Algorithms.If(
      baselineArea.gt(0),
      lossArea.divide(baselineArea),
      null
    );

    var lossFractionValidBaseline = ee.Algorithms.If(
      baselineValidArea.gt(0),
      lossArea.divide(baselineValidArea),
      null
    );

    var baselineCoverageThisYear = ee.Algorithms.If(
      baselineArea.gt(0),
      ee.Number(baselineValidArea.divide(baselineArea)).max(0).min(1),
      null
    );

    outcomeFeatures.push(
      ee.Feature(null, {
        site_id: siteId,
        site_type: siteType,
        selected_control_order: order,
        pre_treatment_match_score: score,
        selection_frozen_before_outcome: 'YES',

        year: year,
        window: 'Mar-Jul',
        scene_count: annual.get('scene_count'),

        site_area_ha_fixed_grid: siteArea,
        baseline_year: BASELINE_YEAR,
        baseline_veg_area_ha: baselineArea,
        baseline_veg_fraction_of_site: baselineFraction,

        baseline_veg_valid_this_year_ha: baselineValidArea,
        baseline_veg_valid_fraction_this_year: baselineCoverageThisYear,

        loss_area_ha: lossArea,
        loss_fraction_of_2022_baseline: lossFractionBaseline,
        loss_fraction_of_valid_2022_baseline: lossFractionValidBaseline,

        mean_ndvi_p70: bandMean(
          annual, 'NDVI_P70', geom
        ),
        median_ndvi_p70: bandMedian(
          annual, 'NDVI_P70', geom
        ),
        mean_ndmi_p70: bandMean(
          annual, 'NDMI_P70', geom
        ),
        median_ndmi_p70: bandMedian(
          annual, 'NDMI_P70', geom
        ),
        mean_valid_obs: bandMean(
          annual, 'VALID_OBS', geom
        ),

        base_ndvi_min: BASE_NDVI_MIN,
        base_ndmi_min: BASE_NDMI_MIN,
        ndvi_drop_min: NDVI_DROP_MIN,
        ndmi_drop_min: NDMI_DROP_MIN,

        outcome_data_used_for_control_selection: 'NO'
      })
    );
  });
});

var outcomeTable = ee.FeatureCollection(outcomeFeatures);

print(
  'Outcome rows (expect 30 = 6 sites x 5 years):',
  outcomeTable.size()
);

print(
  'SC0002 preview:',
  outcomeTable
    .filter(ee.Filter.eq('site_id', 'SC0002'))
    .sort('year')
);


// ---------------------------------------------------------------------------
// 6. Export main outcome table
// ---------------------------------------------------------------------------
Export.table.toDrive({
  collection: outcomeTable,
  description: 'SC0002_STEP3B3_Site_Outcome_2022_2026',
  fileNamePrefix: 'SC0002_STEP3B3_Site_Outcome_2022_2026',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV'
});


// ---------------------------------------------------------------------------
// 7. Export exact site geometries used
// ---------------------------------------------------------------------------
// RFC 7946 GeoJSON uses WGS84 longitude/latitude. The analysis controls are
// constructed in EPSG:32651, so explicitly transform every feature before
// GeoJSON export. Analysis/reduction geometry above remains unchanged.
var sitesWgs84 = sites.map(function(f) {
  f = ee.Feature(f);
  return ee.Feature(
    f.geometry().transform('EPSG:4326', 1),
    f.toDictionary()
  );
});

Export.table.toDrive({
  collection: sitesWgs84,
  description: 'SC0002_STEP3B3_Site_Geometries',
  fileNamePrefix: 'SC0002_STEP3B3_Site_Geometries',
  folder: DRIVE_FOLDER,
  fileFormat: 'GeoJSON'
});


// ---------------------------------------------------------------------------
// 8. Export 2022->2026 standard loss-mask QA rasters
// ---------------------------------------------------------------------------
siteList.forEach(function(site) {
  site = ee.Feature(site);

  var geom = site.geometry();
  var siteIdClient = site.get('site_id').getInfo();

  var baseline = annualComposite(2022, geom);
  var target = annualComposite(2026, geom);

  var baselineVeg = baseline.select('NDVI_P70')
    .gte(BASE_NDVI_MIN)
    .and(
      baseline.select('NDMI_P70')
        .gte(BASE_NDMI_MIN)
    );

  var loss = baselineVeg
    .and(
      baseline.select('NDVI_P70')
        .subtract(target.select('NDVI_P70'))
        .gte(NDVI_DROP_MIN)
    )
    .and(
      baseline.select('NDMI_P70')
        .subtract(target.select('NDMI_P70'))
        .gte(NDMI_DROP_MIN)
    );

  var raster = loss
    .unmask(0)
    .clip(geom)
    .toUint8();

  Export.image.toDrive({
    image: raster,
    description:
      'SC0002_STEP3B3_LOSS_2022_2026_' +
      siteIdClient,

    fileNamePrefix:
      'SC0002_STEP3B3_LOSS_2022_2026_' +
      siteIdClient,

    folder: DRIVE_FOLDER,
    region: geom.bounds(1, ee.Projection(CRS)),
    crs: CRS,
    crsTransform: TRANSFORM,
    maxPixels: 1e8,
    fileFormat: 'GeoTIFF',
    formatOptions: {
      cloudOptimized: true,
      noData: 255
    }
  });
});


// ---------------------------------------------------------------------------
// 9. Map preview only
// ---------------------------------------------------------------------------
Map.centerObject(sc0002Fc, 11);

Map.addLayer(
  sc0002Fc.style({
    color: 'FFFF00',
    fillColor: '00000000',
    width: 3
  }),
  {},
  'SC0002',
  true
);

Map.addLayer(
  ee.FeatureCollection(
    FROZEN_CONTROLS.map(controlFeature)
  ).style({
    color: '00FFFF',
    fillColor: '00000000',
    width: 2
  }),
  {},
  'Frozen controls',
  true
);

print(
  'Expected Tasks: 1 outcome CSV + 1 site-geometry GeoJSON + 6 loss-mask TIFFs = 8.'
);
