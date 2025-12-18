import { bivariateFillExpression, createBivariateLegend } from './bivariate.js';


const map = new maplibregl.Map({
  container: 'map',
  style: {
    version: 8,
    sources: {
      osm: {
        type: 'raster',
        tiles: [
          'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
          'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
          'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
        ],
        tileSize: 256,
        attribution: '© OpenStreetMap contributors'
      }
    },
    layers: [
      {
        id: 'osm',
        type: 'raster',
        source: 'osm',
        paint: {
          'raster-opacity': 0.9
        }
      }
    ]
  },
  center: [1.2100, 46.7561],
  zoom: 10
});

map.on('load', async () => {

  const response = await fetch('data/etangs_temporal_2018.geojson');
  const geojson = await response.json();

  // Dates uniques triées
  const dates = [...new Set(
    geojson.features.map(f => f.properties.date)
  )].sort();

  // Slider
  const slider = document.getElementById('timeSlider');
  const label = document.getElementById('dateLabel');

  slider.min = 0;
  slider.max = dates.length - 1;
  slider.value = 0;

  label.textContent = dates[0];

  map.addSource('etangs', {
    type: 'geojson',
    data: geojson
  });

    map.addLayer({
      id: 'etangs',
      type: 'fill',
      source: 'etangs',
      paint: {
        'fill-color': bivariateFillExpression(),
        'fill-opacity': 0.9
      },
      filter: ['==', ['get', 'date'], dates[0]]
    });


    function updateMap(date) {
    map.setFilter('etangs', [
      '==',
      ['get', 'date'],
      date
    ]);
    label.textContent = date;
  }

    slider.addEventListener('input', (e) => {
      updateMap(dates[e.target.value]);
    });
  
  createBivariateLegend();

});
