// SC0002 Step 3B.2 — Outcome-blind visual treatment-status review exporter
// ============================================================================
//
// WHAT THIS DOES
// --------------
// Exports one multiband GeoTIFF for SC0002 and one for each of the 20
// pre-treatment-ranked control candidates.
//
// Each GeoTIFF contains annual cloud/SCL-masked Sentinel-2 RGB median imagery:
//   2020, 2021, 2022, 2023, 2024, 2025, 2026
//
// Band order:
//   Y2020_R, Y2020_G, Y2020_B,
//   ...
//   Y2026_R, Y2026_G, Y2026_B
//
// IMPORTANT METHODOLOGICAL RULE
// -----------------------------
// These post-2022 true-colour images may be used ONLY to determine whether a
// candidate itself was treated / developed / otherwise made unsuitable as a
// control. They must NOT be used to select candidates because their
// post-treatment NDVI/NDMI outcome "looks good".
//
// This script exports RGB reflectance only. It does not calculate NDVI, NDMI,
// spectral-loss area, or any 2023-2026 outcome score.
//
// Review composites are visual-screening products and are separate from the
// formal March-July P70 analytical composites.
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

var CRS = 'EPSG:32651';
var SCALE_M = 10;
var TRANSFORM = [10, 0, 0, 0, -10, 0];

var DRIVE_FOLDER = 'SC0002_STEP3B2_REVIEW_IMAGES';

// Use fixed dates for reproducibility.
// 2026 is intentionally partial-year through 2026-09-28 inclusive.
var REVIEW_WINDOWS = [
  {year: 2020, start: '2020-01-01', end: '2021-01-01'},
  {year: 2021, start: '2021-01-01', end: '2022-01-01'},
  {year: 2022, start: '2022-01-01', end: '2023-01-01'},
  {year: 2023, start: '2023-01-01', end: '2024-01-01'},
  {year: 2024, start: '2024-01-01', end: '2025-01-01'},
  {year: 2025, start: '2025-01-01', end: '2026-01-01'},
  {year: 2026, start: '2026-01-01', end: '2026-09-29'}
];

// Candidate square area matches Step 3B.1.
var CONTROL_SIDE_M = 796.5951;
var HALF_SIDE_M = CONTROL_SIDE_M / 2;

// Set to e.g. ['C162'] for a one-candidate test.
// Leave empty to export all Top20.
var TEST_ONLY_IDS = [];


// ---------------------------------------------------------------------------
// 1. Top20 frozen from Step 3B.1 pre-treatment ranking
// ---------------------------------------------------------------------------
var TOP20 = [
  {id: 'C162', rank: 1, x: 231409.013, y: 2525169.146, score: 0.251794610},
  {id: 'C185', rank: 2, x: 232409.013, y: 2525169.146, score: 0.465231596},
  {id: 'C172', rank: 3, x: 232409.013, y: 2512169.146, score: 0.517142889},
  {id: 'C176', rank: 4, x: 232409.013, y: 2516169.146, score: 0.536305349},
  {id: 'C222', rank: 5, x: 234409.013, y: 2521169.146, score: 0.674966065},
  {id: 'C129', rank: 6, x: 230409.013, y: 2515169.146, score: 0.741549727},
  {id: 'C221', rank: 7, x: 234409.013, y: 2520169.146, score: 0.747979839},
  {id: 'C177', rank: 8, x: 232409.013, y: 2517169.146, score: 0.866789262},
  {id: 'C290', rank: 9, x: 237409.013, y: 2522169.146, score: 1.022337966},
  {id: 'C264', rank: 10, x: 236409.013, y: 2519169.146, score: 1.050633422},
  {id: 'C268', rank: 11, x: 236409.013, y: 2523169.146, score: 1.164754016},
  {id: 'C269', rank: 12, x: 236409.013, y: 2524169.146, score: 1.166624051},
  {id: 'C152', rank: 13, x: 231409.013, y: 2515169.146, score: 1.180770504},
  {id: 'C146', rank: 14, x: 231409.013, y: 2509169.146, score: 1.181036251},
  {id: 'C241', rank: 15, x: 235409.013, y: 2519169.146, score: 1.187231292},
  {id: 'C171', rank: 16, x: 232409.013, y: 2511169.146, score: 1.218218867},
  {id: 'C291', rank: 17, x: 237409.013, y: 2523169.146, score: 1.266276465},
  {id: 'C179', rank: 18, x: 232409.013, y: 2519169.146, score: 1.314914496},
  {id: 'C153', rank: 19, x: 231409.013, y: 2516169.146, score: 1.465066369},
  {id: 'C313', rank: 20, x: 238409.013, y: 2522169.146, score: 1.502263514}
];


// ---------------------------------------------------------------------------
// 2. Geometry construction
// ---------------------------------------------------------------------------
var sc0002 = SC0002_FC;

function candidateFeature(c) {
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
    rank: c.rank,
    pre_treatment_match_score: c.score,
    outcome_used_for_ranking: 'NO'
  });
}

var candidates = ee.FeatureCollection(
  TOP20.map(candidateFeature)
);

print('SC0002 AOI source:', 'embedded archived V4 geometry');
print('Top20 candidate count:', candidates.size());


// ---------------------------------------------------------------------------
// 3. Sentinel-2 true-colour review preprocessing
// ---------------------------------------------------------------------------
function maskS2(img) {
  var scl = img.select('SCL');

  var good = scl.neq(0)
    .and(scl.neq(1))
    .and(scl.neq(3))
    .and(scl.neq(7))
    .and(scl.neq(8))
    .and(scl.neq(9))
    .and(scl.neq(10))
    .and(scl.neq(11));

  return img
    .updateMask(good)
    .select(['B4', 'B3', 'B2']);
}


function annualRgbStack(geom) {
  var images = REVIEW_WINDOWS.map(function(w) {
    var col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(geom)
      .filterDate(w.start, w.end)
      .map(maskS2);

    var med = col.median()
      .rename([
        'Y' + String(w.year) + '_R',
        'Y' + String(w.year) + '_G',
        'Y' + String(w.year) + '_B'
      ]);

    return med;
  });

  return ee.Image.cat(images)
    .clip(geom)
    .toUint16();
}


// ---------------------------------------------------------------------------
// 4. Review metadata table: scene count by site/year
// ---------------------------------------------------------------------------
var metadataFeatures = [];

function appendMetadata(siteId, geom, rank, score) {
  REVIEW_WINDOWS.forEach(function(w) {
    var count = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(geom)
      .filterDate(w.start, w.end)
      .size();

    metadataFeatures.push(ee.Feature(null, {
      site_id: siteId,
      rank: rank,
      pre_treatment_match_score: score,
      year: w.year,
      start_date: w.start,
      end_date_exclusive: w.end,
      source_scene_count: count,
      review_product: 'annual RGB median; visual treatment-status screening only'
    }));
  });
}

appendMetadata('SC0002', sc0002.geometry(), 0, 0);

TOP20.forEach(function(c) {
  var f = candidateFeature(c);
  appendMetadata(c.id, f.geometry(), c.rank, c.score);
});

Export.table.toDrive({
  collection: ee.FeatureCollection(metadataFeatures),
  description: 'SC0002_STEP3B2_Review_Image_Metadata',
  fileNamePrefix: 'SC0002_STEP3B2_Review_Image_Metadata',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV'
});


// ---------------------------------------------------------------------------
// 5. Export SC0002 reference stack
// ---------------------------------------------------------------------------
var scStack = annualRgbStack(sc0002.geometry());

Export.image.toDrive({
  image: scStack,
  description: 'SC0002_STEP3B2_RGB_REVIEW_SC0002',
  fileNamePrefix: 'SC0002_STEP3B2_RGB_REVIEW_SC0002',
  folder: DRIVE_FOLDER,
  region: sc0002.geometry().bounds(1, ee.Projection(CRS)),
  crs: CRS,
  crsTransform: TRANSFORM,
  maxPixels: 1e8,
  fileFormat: 'GeoTIFF',
  formatOptions: {
    cloudOptimized: true,
    noData: 0
  }
});


// ---------------------------------------------------------------------------
// 6. Export Top20 candidate stacks
// ---------------------------------------------------------------------------
TOP20.forEach(function(c) {
  if (TEST_ONLY_IDS.length > 0 &&
      TEST_ONLY_IDS.indexOf(c.id) === -1) {
    return;
  }

  var f = candidateFeature(c);
  var stack = annualRgbStack(f.geometry());

  Export.image.toDrive({
    image: stack,
    description:
      'SC0002_STEP3B2_RGB_REVIEW_' +
      String(c.rank).padStart(2, '0') + '_' + c.id,

    fileNamePrefix:
      'SC0002_STEP3B2_RGB_REVIEW_' +
      String(c.rank).padStart(2, '0') + '_' + c.id,

    folder: DRIVE_FOLDER,
    region: f.geometry(),
    crs: CRS,
    crsTransform: TRANSFORM,
    maxPixels: 1e8,
    fileFormat: 'GeoTIFF',
    formatOptions: {
      cloudOptimized: true,
      noData: 0
    }
  });
});


// ---------------------------------------------------------------------------
// 7. Map preview
// ---------------------------------------------------------------------------
Map.centerObject(sc0002, 11);

Map.addLayer(
  sc0002.style({
    color: 'FFFF00',
    fillColor: '00000000',
    width: 3
  }),
  {},
  'SC0002',
  true
);

Map.addLayer(
  candidates.style({
    color: '00FFFF',
    fillColor: '00000000',
    width: 2
  }),
  {},
  'Top20 frozen candidates',
  true
);

print(
  'Tasks: 1 metadata CSV + 1 SC0002 TIFF + up to 20 candidate TIFFs.'
);
