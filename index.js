function getToken() {
  return "<MAPBOX_ACCESS_TOKEN>";
}

function getMap() {
  return map;
}

function updateCorners(jsonData) {
  let data = JSON.parse(jsonData);
  for (let i = 0; i < data.features.length; i++) {
    let screenCoords = data.features[i].geometry.coordinates;
    let point = new mapboxgl.Point(screenCoords[0], screenCoords[1]);
    let geoCoords = map.unproject(point);
    data.features[i].geometry.coordinates = [geoCoords.lng, geoCoords.lat];
  }
  map.getSource("corners").setData(data);
}

function updateImage(src) {
  let bounds = map.getBounds();
  map.getSource("edges").updateImage({
    url: src,
    coordinates: [
      [bounds._sw.lng, bounds._ne.lat],
      [bounds._ne.lng, bounds._ne.lat],
      [bounds._ne.lng, bounds._sw.lat],
      [bounds._sw.lng, bounds._sw.lat],
    ],
  });
}

mapboxgl.accessToken = getToken();
const map = new mapboxgl.Map({
  container: "map",
  style: "mapbox://styles/mapbox/satellite-streets-v9",
  center: [-123, 45],
  zoom: 10,
});

map.on("load", () => {
  const layers = map.getStyle().layers;
  // Find the index of the first symbol layer in the map style.
  let firstSymbolId;
  for (const layer of layers) {
    if (layer.type === "symbol") {
      firstSymbolId = layer.id;
      break;
    }
  }

  map.addSource("corners", {
    type: "geojson",
    data: {
      type: "FeatureCollection",
      features: [],
    },
  });
  map.addLayer(
    {
      id: "corners",
      type: "circle",
      source: "corners",
      paint: {
        "circle-radius": 4,
        "circle-color": "#ffaa00",
      },
    },
    firstSymbolId
  );

  map.addSource("edges", {
    type: "image",
    url: "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==",
    coordinates: [
      [-80.425, 46.437],
      [-71.516, 46.437],
      [-71.516, 37.936],
      [-80.425, 37.936],
    ],
  });
  map.addLayer(
    {
      id: "edges",
      type: "raster",
      source: "edges",
      paint: {
        "raster-fade-duration": 1000,
      },
    },
    "corners"
  );
});
