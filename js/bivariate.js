export const bivariateColors = {
  1: '#e8e8e8',
  2: '#b8d6be',
  3: '#73ae80',
  4: '#b5c0da',
  5: '#90b2b3',
  6: '#5a9178',
  7: '#6c83b5',
  8: '#567994',
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

export function createBivariateLegend(counts = null) {
  const grid = document.querySelector('.legend-grid');
  grid.innerHTML = '';

  // ordre visuel : ligne du haut = eau forte
  const maxCount = counts ? Math.max(...Object.values(counts)) : 1;
  const minSize = 8;
  const maxSize = 32;

  for (let y = 2; y >= 0; y--) {
    for (let x = 0; x < 3; x++) {
      const cls = x * 3 + y + 1;
      const cell = document.createElement('div');
      cell.style.backgroundColor = bivariateColors[cls];
      cell.style.borderRadius = '6px';
      cell.style.border = '1px solid rgba(0,0,0,0.12)';

      if (counts) {
        const count = counts[cls] || 0;
        const size = minSize + (count / maxCount) * (maxSize - minSize);
        cell.style.width = size + 'px';
        cell.style.height = size + 'px';
      } else {
        cell.style.width = '32px';
        cell.style.height = '32px';
      }

      grid.appendChild(cell);
    }
  }
}