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

  const response = await fetch('data/etangs_mensuel_2018.geojson');
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
      id: 'etangs-fill',
      type: 'fill',
      source: 'etangs',
      paint: {
        'fill-color': bivariateFillExpression(),
        'fill-opacity': 0.9
      },
      filter: ['==', ['get', 'date'], dates[0]]
    });

    map.addLayer({
      id: 'etangs-assec-outline',
      type: 'line',
      source: 'etangs',
      paint: {
        'line-color': '#FFD700',
        'line-width': 3,
        'line-opacity': 1
      },
      filter: [
        'all',

        // même date que le slider
        ['==', ['get', 'date'], dates[0]],

        // étang en assec
        ['==', ['get', 'assec'], true],

        // mois >= mars
        ['>=', ['to-number', ['slice', ['get', 'date'], 5, 7]], 3],

        // mois <= octobre
        ['<=', ['to-number', ['slice', ['get', 'date'], 5, 7]], 10]
      ]
    });


    function updateMap(date) {

      map.setFilter('etangs-fill', [
        '==',
        ['get', 'date'],
        date
      ]);

      map.setFilter('etangs-assec-outline', [
        'all',
        ['==', ['get', 'date'], date],
        ['==', ['get', 'assec'], true],
        ['>=', ['to-number', ['slice', ['get', 'date'], 5, 7]], 3],
        ['<=', ['to-number', ['slice', ['get', 'date'], 5, 7]], 10]
      ]);

      label.textContent = date;
    }

    slider.addEventListener('input', (e) => {
      updateMap(dates[e.target.value]);
    });
  
  createBivariateLegend();

});
