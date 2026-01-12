import { bivariateFillExpression, createBivariateLegend, bivariateColors } from './bivariate.js';


const map = new maplibregl.Map({
  container: 'map',
  style: {
    version: 8,
    sources: {
      osm: {  //Définition de la source raster OSM Dark
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
    layers: [ //Fond de carte OSM Dark
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
  center: [1.2100, 46.7561],  //Centrage sur les étangs de la Brenne
  zoom: 10
});

map.on('load', async () => {

  const response = await fetch('data/etangs_mensuel_2018.geojson');
  const geojson = await response.json();

  // Organiser les données par étang
  const pondData = {};
  geojson.features.forEach(feature => {
    const pond_id = feature.properties.pond_id;
    if (!pondData[pond_id]) pondData[pond_id] = [];
    pondData[pond_id].push({
      date: feature.properties.date,
      ndvi: feature.properties.ndvi,
      freq_eau: feature.properties.freq_eau
    });
  });
  // Trier les données par date pour chaque étang
  Object.values(pondData).forEach(data => data.sort((a, b) => new Date(a.date) - new Date(b.date)));

  // Dates uniques triées
  const dates = [...new Set(
    geojson.features.map(f => f.properties.date)
  )].sort();

  // Pré-calculer les counts par date et classe
  const countsByDate = {};
  dates.forEach(date => {
    const featuresForDate = geojson.features.filter(f => f.properties.date === date);
    const counts = {};
    for (let i = 1; i <= 9; i++) {
      counts[i] = 0;
    }
    featuresForDate.forEach(f => {
      const cls = f.properties.bivar_class;
      if (cls >= 1 && cls <= 9) {
        counts[cls]++;
      }
    });
    countsByDate[date] = counts;
  });

  function formatYearMonth(dateString) {
    return new Date(dateString).toISOString().slice(0, 7);
  }
  
  // Slider
  const slider = document.getElementById('timeSlider');
  const label = document.getElementById('dateLabel');


  slider.min = 0;
  slider.max = dates.length - 1;
  slider.value = 0;

  label.textContent = formatYearMonth(dates[0]);

  map.addSource('etangs', {
    type: 'geojson',
    data: geojson
  });

    map.addLayer({  //Ajout couche des étangs
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

    const toggleAssec = document.getElementById('toggleAssec');

    toggleAssec.addEventListener('change', (e) => {
      map.setLayoutProperty(
        'etangs-assec-outline',
        'visibility',
        e.target.checked ? 'visible' : 'none'
      );
    });

    // Ajouter le curseur pointer sur les étangs
    map.on('mouseenter', 'etangs-fill', () => {
      map.getCanvas().style.cursor = 'pointer';
    });
    map.on('mouseleave', 'etangs-fill', () => {
      map.getCanvas().style.cursor = '';
    });

    // Événement de clic sur les étangs
    map.on('click', 'etangs-fill', (e) => {
      const feature = e.features[0];
      const pond_id = feature.properties.pond_id;
      const data = pondData[pond_id];
      if (!data) return;

      const uniqueId = `pond-${pond_id}-${Date.now()}`;
      const popupContent = `
        <div style="width: 400px; font-family: Roboto, sans-serif;">
          <h3>Étang ${pond_id}</h3>
          <div style="margin-bottom: 10px;">
            <canvas id="ndviChart-${uniqueId}" width="350" height="200"></canvas>
          </div>
          <div>
            <canvas id="mndwiChart-${uniqueId}" width="350" height="200"></canvas>
          </div>
        </div>
      `;

      new maplibregl.Popup()
        .setLngLat(e.lngLat)
        .setHTML(popupContent)
        .addTo(map);

      // Créer les graphiques
      const ndviCanvas = document.getElementById(`ndviChart-${uniqueId}`);
      const ndviCtx = ndviCanvas.getContext('2d');
      new Chart(ndviCtx, {
        type: 'line',
        data: {
          labels: data.map(d => d.date),
          datasets: [{
            label: 'NDVI',
            data: data.map(d => d.ndvi),
            borderColor: 'green',
            backgroundColor: 'rgba(0, 128, 0, 0.1)',
            fill: false
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              type: 'category',
              title: {
                display: true,
                text: 'Date'
              }
            },
            y: {
              title: {
                display: true,
                text: 'NDVI'
              }
            }
          },
          plugins: {
            legend: {
              display: false
            }
          }
        }
      });

      const mndwiCanvas = document.getElementById(`mndwiChart-${uniqueId}`);
      const mndwiCtx = mndwiCanvas.getContext('2d');
      new Chart(mndwiCtx, {
        type: 'line',
        data: {
          labels: data.map(d => d.date),
          datasets: [{
            label: 'MNDWI',
            data: data.map(d => d.freq_eau),
            borderColor: 'blue',
            backgroundColor: 'rgba(0, 0, 255, 0.1)',
            fill: false
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              type: 'category',
              title: {
                display: true,
                text: 'Date'
              }
            },
            y: {
              title: {
                display: true,
                text: 'MNDWI'
              }
            }
          },
          plugins: {
            legend: {
              display: false
            }
          }
        }
      });
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

      createBivariateChart(date);
    }

    slider.addEventListener('input', (e) => {
      updateMap(dates[e.target.value]);
    });
  
  createBivariateLegend();

  // Créer le chart
  let bivariateChart;
  function createBivariateChart(date) {
    const counts = countsByDate[date];
    const labels = Object.keys(counts).map(cls => `Classe ${cls}`);
    const data = Object.values(counts);
    const backgroundColors = Object.keys(counts).map(cls => bivariateColors[parseInt(cls)]);

    const ctx = document.getElementById('bivariateChart').getContext('2d');
    if (bivariateChart) {
      bivariateChart.destroy();
    }
    bivariateChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Nombre d\'étangs',
          data: data,
          backgroundColor: backgroundColors,
          borderColor: backgroundColors.map(color => color),
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 1
            }
          },
          x: {
            ticks: {
              autoSkip: false
            }
          }
        },
        plugins: {
          legend: {
            display: false
          }
        }
      }
    });
  }

  createBivariateChart(dates[0]);

});
