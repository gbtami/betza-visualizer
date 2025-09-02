import { BetzaParser } from './betza_parser.js';
import { Move } from './types.js';

const parser = new BetzaParser();
const inputEl = document.getElementById('betzaInput') as HTMLInputElement;
const boardContainer = document.getElementById('board-container')!;
const boardSizeSelect = document.getElementById(
  'boardSizeSelect'
) as HTMLSelectElement;

let boardSize = Number(boardSizeSelect.value);
const CELL_SIZE = 40;
const SVG_NS = 'http://www.w3.org/2000/svg';

const COLORS = {
  standard: '#4169E1',
  move: '#FFD700',
  capture: '#DC143C',
  hop: '#32CD32',
  blocker: '#606060',
};

const sign = (n: number): number => Math.sign(n);
const blockers = new Set<string>();

function renderBoard(moves: Move[], blockers: Set<string>) {
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('width', '100%');
  svg.setAttribute('height', '100%');
  svg.setAttribute(
    'viewBox',
    `0 0 ${boardSize * CELL_SIZE} ${boardSize * CELL_SIZE}`
  );

  const center = Math.floor(boardSize / 2);

  for (let r = 0; r < boardSize; r++) {
    for (let c = 0; c < boardSize; c++) {
      const rect = document.createElementNS(SVG_NS, 'rect');
      rect.setAttribute('x', String(c * CELL_SIZE));
      rect.setAttribute('y', String(r * CELL_SIZE));
      rect.setAttribute('width', String(CELL_SIZE));
      rect.setAttribute('height', String(CELL_SIZE));
      rect.setAttribute('fill', (r + c) % 2 === 0 ? '#769656' : '#eeeed2');
      svg.appendChild(rect);
    }
  }

  svg.addEventListener('click', (event) => {
    const svgPoint = svg.createSVGPoint();
    svgPoint.x = event.clientX;
    svgPoint.y = event.clientY;
    const { x, y } = svgPoint.matrixTransform(
      (svg.getScreenCTM() as SVGMatrix).inverse()
    );

    const c = Math.floor(x / CELL_SIZE);
    const r = Math.floor(y / CELL_SIZE);

    const blockerX = c - center;
    const blockerY = center - r;

    if (blockerX === 0 && blockerY === 0) return;

    const blockerCoord = `${blockerX},${blockerY}`;
    if (blockers.has(blockerCoord)) {
      blockers.delete(blockerCoord);
    } else {
      blockers.add(blockerCoord);
    }
    updateBoard();
  });

  blockers.forEach((b) => {
    const [bx, by] = b.split(',').map(Number);
    const cx = (center + bx) * CELL_SIZE + CELL_SIZE / 2;
    const cy = (center - by) * CELL_SIZE + CELL_SIZE / 2;
    const blocker = document.createElementNS(SVG_NS, 'text');
    blocker.textContent = '♟️';
    blocker.setAttribute('x', String(cx));
    blocker.setAttribute('y', String(cy));
    blocker.setAttribute('font-size', String(CELL_SIZE * 0.7));
    blocker.setAttribute('text-anchor', 'middle');
    blocker.setAttribute('dominant-baseline', 'central');
    blocker.setAttribute('fill', COLORS.blocker);
    blocker.setAttribute('opacity', '0.8');
    svg.appendChild(blocker);
  });

  moves.forEach((move) => {
    const { x, y, moveType, hopType, jumpType } = move;
    const cx = (center + x) * CELL_SIZE + CELL_SIZE / 2;
    const cy = (center - y) * CELL_SIZE + CELL_SIZE / 2;
    let isValid: boolean;

    if (hopType) {
      // Hoppers (e.g., Cannon 'p', Grasshopper 'g')
      isValid = false;
      const path: string[] = [];
      const dx = sign(x);
      const dy = sign(y);
      for (let i = 1; i < Math.max(Math.abs(x), Math.abs(y)); i++) {
        path.push(`${i * dx},${i * dy}`);
      }
      const blockersOnPath = path.filter((p) => blockers.has(p));
      if (blockersOnPath.length === 1) {
        if (hopType === 'p') {
          isValid = true;
        } else if (hopType === 'g') {
          const [hx, hy] = blockersOnPath[0].split(',').map(Number);
          if (x === hx + dx && y === hy + dy) {
            isValid = true;
          }
        }
      }
    } else if (jumpType === 'jumping') {
      // Leapers that MUST jump over a piece (e.g., jN)
      isValid = false;
      let blockX = 0,
        blockY = 0;
      if (Math.abs(x) > Math.abs(y)) blockX = sign(x);
      else if (Math.abs(y) > Math.abs(x)) blockY = sign(y);
      if (blockers.has(`${blockX},${blockY}`)) {
        isValid = true;
      }
    } else if (jumpType === 'non-jumping') {
      // Leapers that CANNOT jump over a piece (e.g., nN)
      isValid = true;
      let blockX = 0,
        blockY = 0;
      if (Math.abs(x) > Math.abs(y)) blockX = sign(x);
      else if (Math.abs(y) > Math.abs(x)) blockY = sign(y);
      if (blockers.has(`${blockX},${blockY}`)) {
        isValid = false;
      }
    } else {
      // Normal leapers (e.g., N) and sliders (e.g., R, B)
      isValid = true;
      const path: string[] = [];
      const dx = sign(x);
      const dy = sign(y);
      for (let i = 1; i < Math.max(Math.abs(x), Math.abs(y)); i++) {
        path.push(`${i * dx},${i * dy}`);
      }
      if (path.some((p) => blockers.has(p))) {
        isValid = false;
      }
    }

    // Final check for all move types: cannot land on a blocker if it's a 'move' only.
    if (isValid && blockers.has(`${x},${y}`) && moveType === 'move') {
      isValid = false;
    }

    if (!isValid) return;

    const r = CELL_SIZE * 0.3;
    const isSpecialMove = hopType || jumpType === 'jumping';
    const strokeWidth = '4';
    const opacity = '0.9';

    if (moveType === 'move') {
      const circle = document.createElementNS(SVG_NS, 'circle');
      circle.setAttribute('cx', String(cx));
      circle.setAttribute('cy', String(cy));
      circle.setAttribute('r', String(r));
      circle.setAttribute('stroke', COLORS.move);
      circle.setAttribute('stroke-width', strokeWidth);
      circle.setAttribute('fill', 'none');
      circle.setAttribute('opacity', opacity);
      svg.appendChild(circle);
    } else if (moveType === 'capture') {
      const circle = document.createElementNS(SVG_NS, 'circle');
      circle.setAttribute('cx', String(cx));
      circle.setAttribute('cy', String(cy));
      circle.setAttribute('r', String(r));
      circle.setAttribute('stroke', COLORS.capture);
      circle.setAttribute('stroke-width', strokeWidth);
      circle.setAttribute('fill', 'none');
      circle.setAttribute('opacity', opacity);
      svg.appendChild(circle);
    } else if (moveType === 'move_capture') {
      if (isSpecialMove) {
        const circle = document.createElementNS(SVG_NS, 'circle');
        circle.setAttribute('cx', String(cx));
        circle.setAttribute('cy', String(cy));
        circle.setAttribute('r', String(r));
        circle.setAttribute('stroke', COLORS.hop);
        circle.setAttribute('stroke-width', strokeWidth);
        circle.setAttribute('fill', 'none');
        circle.setAttribute('opacity', opacity);
        svg.appendChild(circle);
      } else {
        const moveIndicatorGroup = document.createElementNS(SVG_NS, 'g');
        moveIndicatorGroup.setAttribute('transform', `translate(${cx}, ${cy})`);
        moveIndicatorGroup.setAttribute('opacity', opacity);

        const path1 = document.createElementNS(SVG_NS, 'path');
        path1.setAttribute('d', `M 0,${-r} A ${r},${r} 0 0 0 0,${r}`);
        path1.setAttribute('stroke', COLORS.move);
        path1.setAttribute('stroke-width', strokeWidth);
        path1.setAttribute('fill', 'none');
        moveIndicatorGroup.appendChild(path1);

        const path2 = document.createElementNS(SVG_NS, 'path');
        path2.setAttribute('d', `M 0,${-r} A ${r},${r} 0 0 1 0,${r}`);
        path2.setAttribute('stroke', COLORS.capture);
        path2.setAttribute('stroke-width', strokeWidth);
        path2.setAttribute('fill', 'none');
        moveIndicatorGroup.appendChild(path2);

        svg.appendChild(moveIndicatorGroup);
      }
    }
  });

  const piece = document.createElementNS(SVG_NS, 'text');
  piece.textContent = '🧚';
  piece.setAttribute('x', String(center * CELL_SIZE + CELL_SIZE / 2));
  piece.setAttribute('y', String(center * CELL_SIZE + CELL_SIZE / 2));
  piece.setAttribute('font-size', String(CELL_SIZE * 0.8));
  piece.setAttribute('text-anchor', 'middle');
  piece.setAttribute('dominant-baseline', 'central');
  piece.setAttribute('fill', '#000000');
  svg.appendChild(piece);

  boardContainer.innerHTML = '';
  boardContainer.appendChild(svg);
}

function updateBoard() {
  const moves = parser.parse(inputEl.value);
  renderBoard(moves, blockers);
}

function createLegendItem(
  content: string,
  description: string,
  isEmoji = false
): HTMLElement {
  const item = document.createElement('div');
  item.classList.add('legend-item');

  const icon = document.createElement('span');
  icon.classList.add('legend-icon');
  if (isEmoji) {
    icon.classList.add('legend-icon-emoji');
    icon.textContent = content;
  } else {
    icon.innerHTML = content;
  }

  const text = document.createElement('span');
  text.textContent = description;

  item.appendChild(icon);
  item.appendChild(text);
  return item;
}

function renderLegend() {
  const legendContainer = document.getElementById('legend-container')!;
  const r = CELL_SIZE * 0.3;
  const strokeWidth = '4';

  const moveIcon = `<svg width="30" height="30" viewBox="0 0 30 30"><circle cx="15" cy="15" r="${
    r * 0.75
  }" stroke="${
    COLORS.move
  }" stroke-width="${strokeWidth}" fill="none" /></svg>`;
  const captureIcon = `<svg width="30" height="30" viewBox="0 0 30 30"><circle cx="15" cy="15" r="${
    r * 0.75
  }" stroke="${
    COLORS.capture
  }" stroke-width="${strokeWidth}" fill="none" /></svg>`;
  const moveCaptureIcon = `<svg width="30" height="30" viewBox="0 0 30 30">
        <path d="M 15,${15 - r * 0.75} A ${r * 0.75},${r * 0.75} 0 0 0 15,${
          15 + r * 0.75
        }" stroke="${COLORS.move}" stroke-width="${strokeWidth}" fill="none" />
        <path d="M 15,${15 - r * 0.75} A ${r * 0.75},${r * 0.75} 0 0 1 15,${
          15 + r * 0.75
        }" stroke="${
          COLORS.capture
        }" stroke-width="${strokeWidth}" fill="none" />
    </svg>`;
  const hopIcon = `<svg width="30" height="30" viewBox="0 0 30 30"><circle cx="15" cy="15" r="${
    r * 0.75
  }" stroke="${COLORS.hop}" stroke-width="${strokeWidth}" fill="none" /></svg>`;

  legendContainer.appendChild(createLegendItem('🧚', 'Piece', true));
  legendContainer.appendChild(createLegendItem('♟️', 'Blocker', true));
  legendContainer.appendChild(createLegendItem(moveIcon, 'Move'));
  legendContainer.appendChild(createLegendItem(captureIcon, 'Capture'));
  legendContainer.appendChild(
    createLegendItem(moveCaptureIcon, 'Move or Capture')
  );
  legendContainer.appendChild(createLegendItem(hopIcon, 'Special Move / Hop'));
}

async function renderPieceCatalog() {
  const catalogContainer = document.getElementById('piece-catalog-container')!;
  try {
    const response = await fetch('/piece_catalog.json');
    const pieceCatalog = await response.json();

    pieceCatalog.forEach((piece: { name: string; variant: string; betza: string }) => {
      const item = document.createElement('div');
      item.classList.add('piece-catalog-item');
      item.dataset.betza = piece.betza;

      const nameEl = document.createElement('div');
      nameEl.classList.add('name');
      nameEl.textContent = piece.name;

      const variantEl = document.createElement('div');
      variantEl.classList.add('variant');
      variantEl.textContent = piece.variant;

      item.appendChild(nameEl);
      item.appendChild(variantEl);
      catalogContainer.appendChild(item);
    });
  } catch (error) {
    console.error('Error loading piece catalog:', error);
    catalogContainer.textContent = 'Error loading piece catalog.';
  }
}

renderBoard([], blockers);
renderLegend();
renderPieceCatalog();

inputEl.addEventListener('input', updateBoard);
boardSizeSelect.addEventListener('change', () => {
  boardSize = Number(boardSizeSelect.value);
  blockers.clear();
  updateBoard();
});

document
  .getElementById('piece-catalog-container')!
  .addEventListener('click', (event) => {
    const target = event.target as HTMLElement;
    const item = target.closest('.piece-catalog-item') as HTMLElement | null;
    if (item && item.dataset.betza) {
      inputEl.value = item.dataset.betza;
      // Manually trigger the input event to update the board
      inputEl.dispatchEvent(new Event('input'));
    }
  });
