// SC0002 Step 3B.1 — Pre-treatment Matched-Control Candidate Generation
// =======================================================================
//
// PURPOSE
// -------
// Generate control-area candidates WITHOUT using 2023-2026 outcome data.
//
// Candidate match_score uses exactly nine pre-treatment variables:
//   - Sentinel-2 March-July P70 NDVI / NDMI in 2020, 2021, 2022 (6 terms)
//   - 2022 baseline spectral-vegetation fraction (1 term)
//   - SRTM elevation and slope (2 terms)
//
// Valid observations are a HARD SCREEN (>=10 in each of 2020/2021/2022),
// not a match_score term. Geographic distance defines the deterministic
// 2-12 km candidate-search ring and is not a match_score term.
//
// The script deliberately does NOT use:
//   - 2023-2026 NDVI / NDMI
//   - future spectral-loss results
//   - Google Earth post-development appearance
//
// After ranking, the top candidates MUST be screened separately for:
//   - overlap with known solar-development records
//   - visible solar / major land-use conversion
//   - obvious non-comparability
//
// That screening is Step 3B.2 and must be documented independently.
//
// Candidate geometry:
//   Equal-area square sampling units, area ~= SC0002 GEE geodesic area
//   (~63.456 ha), centered on a deterministic UTM grid.
//
// =======================================================================


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

var DRIVE_FOLDER = 'SC0002_STEP3B1_CONTROL_CANDIDATES';


// ---------------------------------------------------------------
// 1. Candidate-grid design
// ---------------------------------------------------------------
//
// SC0002 computed centroid, transformed to EPSG:32651:
//   lon/lat : 120.414439044, 22.713945147
//   UTM 51N : approximately 234409.013, 2514169.146
//
// The square side is chosen to approximate the SC0002 GEE geodesic area.
// sqrt(63.456375405 ha * 10,000) ~= 796.595 m.
//
// Search design:
//   grid spacing : 1000 m
//   min distance : 2000 m
//   max distance : 12000 m
//
// These are fixed before outcome analysis.
//
var CENTER_X = 234409.013;
var CENTER_Y = 2514169.146;

var CONTROL_SIDE_M = 796.5951;
var HALF_SIDE_M = CONTROL_SIDE_M / 2;

var GRID_SPACING_M = 1000;
var SEARCH_RADIUS_M = 12000;
var EXCLUSION_RADIUS_M = 2000;


// ---------------------------------------------------------------
// 2. Pre-treatment matching thresholds / score scales
// ---------------------------------------------------------------
//
// Hard screening uses only pre-treatment covariates.
// Ranking score is a normalized squared-distance score: lower = better.
//
var MIN_BASEVEG_FRAC_2022 = 0.75;
var MIN_MEAN_VALID_OBS = 10;

// Hard upper bounds relative to SC0002 reference.
var MAX_ABS_NDVI_DIFF_2022 = 0.10;
var MAX_ABS_NDMI_DIFF_2022 = 0.10;
var MAX_ABS_ELEV_DIFF_M = 120;
var MAX_ABS_SLOPE_DIFF_DEG = 6;
var MAX_ABS_BASEVEG_FRAC_DIFF = 0.15;

// Score normalization scales.
var SCORE_NDVI_SCALE = 0.08;
var SCORE_NDMI_SCALE = 0.08;
var SCORE_BASEVEG_SCALE = 0.10;
var SCORE_ELEV_SCALE_M = 75;
var SCORE_SLOPE_SCALE_DEG = 4;


// ---------------------------------------------------------------
// 3. SC0002 AOI
// ---------------------------------------------------------------
var AOI_FC = SC0002_FC;
var AOI = SC0002_AOI;

print('SC0002 AOI source:', 'embedded archived V4 geometry');
print('Analysis CRS:', ANALYSIS_CRS);
print('Analysis scale:', ANALYSIS_SCALE_M);
print('SC0002 AOI geodesic area (ha):', AOI.area(1).divide(10000));


// ---------------------------------------------------------------
// 4. Sentinel-2 preprocessing
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


function annualComposite(year) {
  var start = ee.Date.fromYMD(year, 3, 1);
  var end = ee.Date.fromYMD(year, 8, 1);

  var col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(
      ee.Geometry.Point(
        [CENTER_X, CENTER_Y],
        ANALYSIS_CRS
      ).buffer(SEARCH_RADIUS_M + 1500)
    )
    .filterDate(start, end)
    .map(maskAndAddIndices);

  var p70 = col
    .reduce(ee.Reducer.percentile([70]))
    .rename([
      'NDVI_' + String(year),
      'NDMI_' + String(year)
    ]);

  var validObs = col
    .select('NDVI')
    .count()
    .rename('VALID_' + String(year));

  return p70
    .addBands(validObs)
    .set('year', year)
    .set('scene_count', col.size());
}


var c2020 = annualComposite(2020);
var c2021 = annualComposite(2021);
var c2022 = annualComposite(2022);


// ---------------------------------------------------------------
// 5. Terrain + 2022 baseline vegetation
// ---------------------------------------------------------------
var baseVeg2022 = c2022.select('NDVI_2022').gte(0.55)
  .and(c2022.select('NDMI_2022').gte(0.10))
  .rename('BASEVEG_2022');

var dem = ee.Image('USGS/SRTMGL1_003')
  .select('elevation')
  .rename('ELEV_M');

var slope = ee.Terrain.slope(dem)
  .rename('SLOPE_DEG');

var covariateStack = ee.Image.cat([
  c2020,
  c2021,
  c2022,
  baseVeg2022,
  dem,
  slope
]);


// ---------------------------------------------------------------
// 6. Deterministic equal-area square candidate grid
// ---------------------------------------------------------------
var candidates = [];
var candidateCounter = 1;

for (var dx = -SEARCH_RADIUS_M;
     dx <= SEARCH_RADIUS_M;
     dx += GRID_SPACING_M) {

  for (var dy = -SEARCH_RADIUS_M;
       dy <= SEARCH_RADIUS_M;
       dy += GRID_SPACING_M) {

    var distanceM = Math.sqrt(dx * dx + dy * dy);

    if (distanceM < EXCLUSION_RADIUS_M ||
        distanceM > SEARCH_RADIUS_M) {
      continue;
    }

    var cx = CENTER_X + dx;
    var cy = CENTER_Y + dy;

    var rect = ee.Geometry.Rectangle(
      [
        cx - HALF_SIDE_M,
        cy - HALF_SIDE_M,
        cx + HALF_SIDE_M,
        cy + HALF_SIDE_M
      ],
      ANALYSIS_CRS,
      false
    );

    var id = 'C' + String(candidateCounter).padStart(3, '0');

    candidates.push(
      ee.Feature(rect, {
        candidate_id: id,
        center_x_utm51n: cx,
        center_y_utm51n: cy,
        dx_m: dx,
        dy_m: dy,
        distance_from_sc0002_m: distanceM,
        nominal_square_area_ha:
          CONTROL_SIDE_M * CONTROL_SIDE_M / 10000
      })
    );

    candidateCounter++;
  }
}

var candidateFC = ee.FeatureCollection(candidates);

print('Raw candidate count:', candidateFC.size());


// ---------------------------------------------------------------
// 7. Reduce PRE-TREATMENT covariates for all candidates
// ---------------------------------------------------------------
var candidateCovariates = covariateStack.reduceRegions({
  collection: candidateFC,
  reducer: ee.Reducer.mean(),
  crs: ANALYSIS_CRS,
  crsTransform: ANALYSIS_TRANSFORM,
  tileScale: 4
});


// ---------------------------------------------------------------
// 8. Compute SC0002 PRE-TREATMENT reference covariates
// ---------------------------------------------------------------
var scRef = covariateStack.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: AOI,
  crs: ANALYSIS_CRS,
  crsTransform: ANALYSIS_TRANSFORM,
  maxPixels: 1e9,
  tileScale: 4
});

var refFeature = ee.Feature(null, {
  site_id: 'SC0002',
  NDVI_2020: scRef.get('NDVI_2020'),
  NDMI_2020: scRef.get('NDMI_2020'),
  VALID_2020: scRef.get('VALID_2020'),

  NDVI_2021: scRef.get('NDVI_2021'),
  NDMI_2021: scRef.get('NDMI_2021'),
  VALID_2021: scRef.get('VALID_2021'),

  NDVI_2022: scRef.get('NDVI_2022'),
  NDMI_2022: scRef.get('NDMI_2022'),
  VALID_2022: scRef.get('VALID_2022'),

  BASEVEG_2022: scRef.get('BASEVEG_2022'),
  ELEV_M: scRef.get('ELEV_M'),
  SLOPE_DEG: scRef.get('SLOPE_DEG'),

  note:
    'Reference covariates use only 2020-2022 Sentinel-2 plus SRTM terrain'
});

print('SC0002 pre-treatment reference:', refFeature);


// ---------------------------------------------------------------
// 9. Score candidates using only PRE-TREATMENT variables
// ---------------------------------------------------------------
var requiredProps = [
  'NDVI_2020', 'NDMI_2020', 'VALID_2020',
  'NDVI_2021', 'NDMI_2021', 'VALID_2021',
  'NDVI_2022', 'NDMI_2022', 'VALID_2022',
  'BASEVEG_2022', 'ELEV_M', 'SLOPE_DEG'
];

var completeCandidates = candidateCovariates
  .filter(ee.Filter.notNull(requiredProps));


function sqNormDiff(value, refValue, scale) {
  return ee.Number(value)
    .subtract(ee.Number(refValue))
    .divide(scale)
    .pow(2);
}


var scoredCandidates = completeCandidates.map(function(f) {

  var dNDVI20 = ee.Number(f.get('NDVI_2020'))
    .subtract(ee.Number(scRef.get('NDVI_2020'))).abs();

  var dNDMI20 = ee.Number(f.get('NDMI_2020'))
    .subtract(ee.Number(scRef.get('NDMI_2020'))).abs();

  var dNDVI21 = ee.Number(f.get('NDVI_2021'))
    .subtract(ee.Number(scRef.get('NDVI_2021'))).abs();

  var dNDMI21 = ee.Number(f.get('NDMI_2021'))
    .subtract(ee.Number(scRef.get('NDMI_2021'))).abs();

  var dNDVI22 = ee.Number(f.get('NDVI_2022'))
    .subtract(ee.Number(scRef.get('NDVI_2022'))).abs();

  var dNDMI22 = ee.Number(f.get('NDMI_2022'))
    .subtract(ee.Number(scRef.get('NDMI_2022'))).abs();

  var dBaseVeg = ee.Number(f.get('BASEVEG_2022'))
    .subtract(ee.Number(scRef.get('BASEVEG_2022'))).abs();

  var dElev = ee.Number(f.get('ELEV_M'))
    .subtract(ee.Number(scRef.get('ELEV_M'))).abs();

  var dSlope = ee.Number(f.get('SLOPE_DEG'))
    .subtract(ee.Number(scRef.get('SLOPE_DEG'))).abs();

  var score = sqNormDiff(
      f.get('NDVI_2020'), scRef.get('NDVI_2020'), SCORE_NDVI_SCALE)
    .add(sqNormDiff(
      f.get('NDMI_2020'), scRef.get('NDMI_2020'), SCORE_NDMI_SCALE))
    .add(sqNormDiff(
      f.get('NDVI_2021'), scRef.get('NDVI_2021'), SCORE_NDVI_SCALE))
    .add(sqNormDiff(
      f.get('NDMI_2021'), scRef.get('NDMI_2021'), SCORE_NDMI_SCALE))
    .add(sqNormDiff(
      f.get('NDVI_2022'), scRef.get('NDVI_2022'), SCORE_NDVI_SCALE))
    .add(sqNormDiff(
      f.get('NDMI_2022'), scRef.get('NDMI_2022'), SCORE_NDMI_SCALE))
    .add(sqNormDiff(
      f.get('BASEVEG_2022'), scRef.get('BASEVEG_2022'), SCORE_BASEVEG_SCALE))
    .add(sqNormDiff(
      f.get('ELEV_M'), scRef.get('ELEV_M'), SCORE_ELEV_SCALE_M))
    .add(sqNormDiff(
      f.get('SLOPE_DEG'), scRef.get('SLOPE_DEG'), SCORE_SLOPE_SCALE_DEG));

  var validObsPass = ee.Number(f.get('VALID_2020')).gte(MIN_MEAN_VALID_OBS)
    .and(ee.Number(f.get('VALID_2021')).gte(MIN_MEAN_VALID_OBS))
    .and(ee.Number(f.get('VALID_2022')).gte(MIN_MEAN_VALID_OBS));

  var hardPass = validObsPass
    .and(ee.Number(f.get('BASEVEG_2022')).gte(MIN_BASEVEG_FRAC_2022))
    .and(dNDVI22.lte(MAX_ABS_NDVI_DIFF_2022))
    .and(dNDMI22.lte(MAX_ABS_NDMI_DIFF_2022))
    .and(dBaseVeg.lte(MAX_ABS_BASEVEG_FRAC_DIFF))
    .and(dElev.lte(MAX_ABS_ELEV_DIFF_M))
    .and(dSlope.lte(MAX_ABS_SLOPE_DIFF_DEG));

  var center = ee.Geometry.Point(
    [
      ee.Number(f.get('center_x_utm51n')),
      ee.Number(f.get('center_y_utm51n'))
    ],
    ANALYSIS_CRS
  ).transform('EPSG:4326', 1);

  var lonLat = center.coordinates();

  return f.set({
    center_lon: lonLat.get(0),
    center_lat: lonLat.get(1),

    abs_diff_NDVI_2020: dNDVI20,
    abs_diff_NDMI_2020: dNDMI20,

    abs_diff_NDVI_2021: dNDVI21,
    abs_diff_NDMI_2021: dNDMI21,

    abs_diff_NDVI_2022: dNDVI22,
    abs_diff_NDMI_2022: dNDMI22,

    abs_diff_BASEVEG_2022: dBaseVeg,
    abs_diff_ELEV_M: dElev,
    abs_diff_SLOPE_DEG: dSlope,

    match_score: score,
    match_pass: ee.Number(ee.Algorithms.If(hardPass, 1, 0)),

    selection_data_end: '2022-12-31',
    outcome_data_used_for_ranking: 'NO'
  });
});


var passingCandidates = scoredCandidates
  .filter(ee.Filter.eq('match_pass', 1))
  .sort('match_score');

var top20 = passingCandidates.limit(20);

print('Complete candidate count:', completeCandidates.size());
print('Hard-match passing candidate count:', passingCandidates.size());
print('Top 20 PRE-TREATMENT matched candidates:', top20);


// ---------------------------------------------------------------
// 10. Map — top candidates only
// ---------------------------------------------------------------
Map.centerObject(AOI_FC, 12);

Map.addLayer(
  AOI_FC.style({
    color: 'FFFF00',
    fillColor: '00000000',
    width: 3
  }),
  {},
  'SC0002',
  true
);

Map.addLayer(
  top20.style({
    color: '00FFFF',
    fillColor: '00000000',
    width: 2
  }),
  {},
  'Top 20 pre-treatment matched control candidates',
  true
);


// ---------------------------------------------------------------
// 11. Exports
// ---------------------------------------------------------------

// Reference covariates.
Export.table.toDrive({
  collection: ee.FeatureCollection([refFeature]),
  description: 'SC0002_STEP3B1_SC0002_Reference_Covariates',
  fileNamePrefix: 'SC0002_STEP3B1_SC0002_Reference_Covariates',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV'
});

// All scored candidates, including failures.
Export.table.toDrive({
  collection: scoredCandidates.sort('match_score'),
  description: 'SC0002_STEP3B1_All_Control_Candidates',
  fileNamePrefix: 'SC0002_STEP3B1_All_Control_Candidates',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV'
});

// Top 20 table.
Export.table.toDrive({
  collection: top20,
  description: 'SC0002_STEP3B1_Top20_Control_Candidates',
  fileNamePrefix: 'SC0002_STEP3B1_Top20_Control_Candidates',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV'
});

// Top 20 geometry for GIS / archival review.
Export.table.toDrive({
  collection: top20,
  description: 'SC0002_STEP3B1_Top20_Control_Candidates_GeoJSON',
  fileNamePrefix: 'SC0002_STEP3B1_Top20_Control_Candidates',
  folder: DRIVE_FOLDER,
  fileFormat: 'GeoJSON'
});

// KML for convenient manual screening in Google Earth.
// Screening must only decide treatment/non-comparability status;
// do not rank candidates using their 2023-2026 vegetation outcomes.
Export.table.toDrive({
  collection: top20,
  description: 'SC0002_STEP3B1_Top20_Control_Candidates_KML',
  fileNamePrefix: 'SC0002_STEP3B1_Top20_Control_Candidates',
  folder: DRIVE_FOLDER,
  fileFormat: 'KML'
});
