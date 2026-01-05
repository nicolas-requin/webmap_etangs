export const bivariateColors = {
  1: '#e8e8e8',
  2: '#b5c0da',
  3: '#6c83b5',
  4: '#b8d6be',
  5: '#90b2b3',
  6: '#567994',
  7: '#73ae80',
  8: '#5a9178',
  9: '#2a5a5b'
};

export function bivariateFillExpression() {
  return [
    'match',
    ['get', 'bivar_class'],
    1, bivariateColors[1],
    2, bivariateColors[2],
    3, bivariateColors[3],
    4, bivariateColors[4],
    5, bivariateColors[5],
    6, bivariateColors[6],
    7, bivariateColors[7],
    8, bivariateColors[8],
    9, bivariateColors[9],
    '#cccccc'
  ];
}

export function createBivariateLegend() {
  const grid = document.querySelector('.legend-grid');
  grid.innerHTML = '';

  // ordre visuel : ligne du haut = eau forte
  for (let y = 2; y >= 0; y--) {
    for (let x = 0; x < 3; x++) {
      const cls = y * 3 + x + 1;
      const cell = document.createElement('div');
      cell.style.backgroundColor = bivariateColors[cls];
      grid.appendChild(cell);
    }
  }
}