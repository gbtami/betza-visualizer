import { BetzaParser } from './betza_parser.js';
import { VariantIniParser } from './variant_ini_parser.js';
import { Move, Piece } from './types.js';
import {
  CELL_SIZE,
  SVG_NS,
  COLORS,
  createMoveIndicator,
} from './svg_utils.js';

const parser = new BetzaParser();
const inputEl = document.getElementById('betzaInput') as HTMLInputElement;
const boardContainer = document.getElementById('board-container')!;
const boardSizeSelect = document.getElementById(
  'boardSizeSelect'
) as HTMLSelectElement;
const variantSelect = document.getElementById(
  'variant-select'
) as HTMLSelectElement;
const loadVariantsBtn = document.getElementById(
  'loadVariantsBtn'
) as HTMLButtonElement;
const variantsFileInput = document.getElementById(
  'variantsFileInput'
) as HTMLInputElement;

let boardSize = Number(boardSizeSelect.value);

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
      rect.dataset.x = String(c);
      rect.dataset.y = String(r);
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
    const { x, y, moveType, hopType, jumpType, atomCoords } = move;

    // Check if the move is within the board boundaries
    const boardX = center + x;
    const boardY = center - y;
    if (
      boardX < 0 ||
      boardX >= boardSize ||
      boardY < 0 ||
      boardY >= boardSize
    ) {
      return; // Skip rendering for off-board moves
    }

    const cx = (center + x) * CELL_SIZE + CELL_SIZE / 2;
    const cy = (center - y) * CELL_SIZE + CELL_SIZE / 2;
    let isValid: boolean;

    if (hopType) {
      // Hoppers (e.g., Cannon 'p', Grasshopper 'g')
      isValid = false;
      let dx: number, dy: number;
      const isLinearMove = x === 0 || y === 0 || Math.abs(x) === Math.abs(y);

      if (isLinearMove) {
        // This is a simplified gcd function for positive integers.
        const gcd = (a: number, b: number): number =>
          b === 0 ? a : gcd(b, a % b);
        const commonDivisor = gcd(Math.abs(x), Math.abs(y));
        dx = x === 0 ? 0 : x / commonDivisor;
        dy = y === 0 ? 0 : y / commonDivisor;
      } else {
        // For non-linear moves (e.g., Knight), the step is the atom itself.
        const { x: atomX, y: atomY } = atomCoords;
        const possibleSteps = [
          { dx: atomX, dy: atomY },
          { dx: -atomX, dy: atomY },
          { dx: atomX, dy: -atomY },
          { dx: -atomX, dy: -atomY },
          { dx: atomY, dy: atomX },
          { dx: -atomY, dy: atomX },
          { dx: atomY, dy: -atomX },
          { dx: -atomY, dy: -atomX },
        ];
        const step = possibleSteps.find(
          (s) => x % s.dx === 0 && y % s.dy === 0 && x / s.dx === y / s.dy
        );
        if (step) {
          dx = step.dx;
          dy = step.dy;
        } else {
          // Should not happen for valid Betza
          dx = 0;
          dy = 0;
        }
      }

      let path_len: number;
      if (dx === 0 && dy === 0) {
        path_len = 0;
      } else if (dx !== 0) {
        path_len = Math.abs(x / dx);
      } else {
        // dy !== 0
        path_len = Math.abs(y / dy);
      }

      const path: string[] = [];
      for (let i = 1; i < path_len; i++) {
        path.push(`${i * dx},${i * dy}`);
      }
      const blockersOnPath = path.filter((p) => blockers.has(p));

      if (hopType === 'p') {
        if (blockersOnPath.length === 1) {
          isValid = true;
        }
      } else if (hopType === 'g') {
        if (blockersOnPath.length === 1) {
          const [hx, hy] = blockersOnPath[0].split(',').map(Number);
          if (x === hx + dx && y === hy + dy) {
            isValid = true;
          }
        }
      }
    } else if (jumpType === 'jumping') {
      // Leapers are not blocked by pieces on their path.
      isValid = true;
    } else if (jumpType === 'non-jumping') {
      const isLinearMove = x === 0 || y === 0 || Math.abs(x) === Math.abs(y);
      if (isLinearMove) {
        // Path-checking for linear non-jumpers (e.g., nA, nD)
        isValid = true;
        const path: string[] = [];
        const dx = sign(x);
        const dy = sign(y);
        console.log(`Checking move (${x},${y}) with blockers:`, Array.from(blockers));
        for (let i = 1; i < Math.max(Math.abs(x), Math.abs(y)); i++) {
          path.push(`${i * dx},${i * dy}`);
        }
        console.log(`Path for (${x},${y}):`, path);
        if (path.some((p) => blockers.has(p))) {
          console.log(`Blocker found in path for (${x},${y})`);
          isValid = false;
        }
      } else {
        // Adjacent-checking for oblique non-jumpers (e.g., nN, nZ)
        isValid = true;
        let blockX = 0,
          blockY = 0;
        if (Math.abs(x) > Math.abs(y)) blockX = sign(x);
        else if (Math.abs(y) > Math.abs(x)) blockY = sign(y);
        if (blockers.has(`${blockX},${blockY}`)) {
          isValid = false;
        }
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

    const isSpecialMove = hopType !== null;
    const moveIndicator = createMoveIndicator(moveType, isSpecialMove);
    moveIndicator.setAttribute('transform', `translate(${cx}, ${cy})`);
    svg.appendChild(moveIndicator);
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
  const moves = parser.parse(inputEl.value, boardSize);
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
  legendContainer.appendChild(createLegendItem(hopIcon, 'Hop'));
}

function populateVariantFilter(
  pieceCatalog: Piece[]
) {
  const variants = [
    ...new Set(pieceCatalog.map((p) => p.variant).join(', ').split(', ')),
  ].sort();

  variantSelect.innerHTML = '';
  const allOption = document.createElement('option');
  allOption.value = 'All';
  allOption.textContent = 'All';
  variantSelect.appendChild(allOption);

  variants.forEach((variant) => {
    if (variant) {
      const option = document.createElement('option');
      option.value = variant;
      option.textContent = variant;
      variantSelect.appendChild(option);
    }
  });
}

function renderPieceCatalog(
  pieceCatalog: Piece[],
  filterVariant = 'All'
) {
  const catalogContainer = document.getElementById('piece-catalog-container')!;
  const catalogContent =
    document.getElementById('piece-catalog-content') ||
    document.createElement('div');
  catalogContent.id = 'piece-catalog-content';
  catalogContent.innerHTML = '';

  const filteredPieces =
    filterVariant === 'All'
      ? pieceCatalog
      : pieceCatalog.filter((p: { variant: string }) =>
          p.variant
            .split(', ')
            .map((v) => v.trim())
            .includes(filterVariant)
        );

  filteredPieces.forEach(
    (piece: { name: string; variant: string; betza: string }) => {
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
      catalogContent.appendChild(item);
    }
  );
  if (!document.getElementById('piece-catalog-content')) {
    catalogContainer.appendChild(catalogContent);
  }
}

async function initialize() {
  let pieceCatalog: Piece[] = [];
  renderBoard([], blockers);
  renderLegend();
  try {
    const response = await fetch('/fsf_built_in_variants_catalog.json');
    pieceCatalog = await response.json();
    populateVariantFilter(pieceCatalog);
    renderPieceCatalog(pieceCatalog);
  } catch (error) {
    console.error('Error loading piece catalog:', error);
  }

  inputEl.addEventListener('input', updateBoard);
  boardSizeSelect.addEventListener('change', () => {
    boardSize = Number(boardSizeSelect.value);
    blockers.clear();
    updateBoard();
  });

  variantSelect.addEventListener('change', () => {
    inputEl.value = '';
    blockers.clear();
    updateBoard();
    renderPieceCatalog(pieceCatalog, variantSelect.value);
  });

  loadVariantsBtn.addEventListener('click', () => {
    variantsFileInput.click();
  });

  variantsFileInput.addEventListener('change', (event) => {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      if (content) {
        try {
          const iniParser = new VariantIniParser(content, pieceCatalog);
          const newPieces = iniParser.parse();
          pieceCatalog.push(...newPieces);
          populateVariantFilter(pieceCatalog);
          renderPieceCatalog(pieceCatalog);
        } catch (error) {
          console.error('Error parsing variants.ini file:', error);
        }
      }
    };
    reader.readAsText(file);
  });

  document
    .getElementById('piece-catalog-container')!
    .addEventListener('click', (event) => {
      const target = event.target as HTMLElement;
      const item = target.closest('.piece-catalog-item') as HTMLElement | null;
      if (item && item.dataset.betza) {
        inputEl.value = item.dataset.betza;
        blockers.clear();
        inputEl.dispatchEvent(new Event('input'));
      }
    });
}

initialize();
