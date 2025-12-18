export const bivariateColors = {
  1: '#e8e8e8',
  2: '#ace4e4',
  3: '#5ac8c8',
  4: '#dfb0d6',
  5: '#a5add3',
  6: '#5698b9',
  7: '#be64ac',
  8: '#8c62aa',
  9: '#3b4994'
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