export const bivariateColors = {
  1: '#EDF8FB',
  2: '#8FD18F',
  3: '#1E8F4E',
  4: '#C6C4E8',
  5: '#7A7FD1',
  6: '#5A5AA6',
  7: '#2F6BFF',
  8: '#4B5BC0',
  9: '#2E2E7F'
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