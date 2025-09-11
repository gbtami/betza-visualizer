import { Move } from './types.js';

export const CELL_SIZE = 40;
export const SVG_NS = 'http://www.w3.org/2000/svg';

export const COLORS = {
  standard: '#4169E1',
  move: '#FFD700',
  capture: '#DC143C',
  hop: '#32CD32',
  initial: '#87CEEB', // Sky Blue
  blocker: '#606060',
};

function createPath(d: string, color: string, strokeWidth: string): SVGPathElement {
  const path = document.createElementNS(SVG_NS, 'path');
  path.setAttribute('d', d);
  path.setAttribute('stroke', color);
  path.setAttribute('stroke-width', strokeWidth);
  path.setAttribute('fill', 'none');
  return path;
}

/**
 * Creates an SVG group element containing the move indicator path(s).
 * This approach ensures that all move indicators have a consistent DOM structure.
 * @param moveType - The type of move ('move', 'capture', 'move_capture').
 * @param isSpecialMove - Flag for special moves like hops, which get a different color.
 * @returns An SVGElement representing the move indicator.
 */
export function createMoveIndicator(
  moveType: Move['moveType'],
  isSpecialMove: boolean,
  isInitial: boolean
): SVGElement {
  const r = CELL_SIZE * 0.3;
  const strokeWidth = '4';
  const opacity = '0.9';

  const moveIndicatorGroup = document.createElementNS(SVG_NS, 'g');
  moveIndicatorGroup.setAttribute('opacity', opacity);

  if (isInitial) {
    moveIndicatorGroup.classList.add('initial-move');
  }

  const fullCircleD = `M 0,${-r} A ${r},${r} 0 1 1 0,${r} A ${r},${r} 0 1 1 0,${-r}`;
  const leftSemiCircleD = `M 0,${-r} A ${r},${r} 0 0 0 0,${r}`;
  const rightSemiCircleD = `M 0,${-r} A ${r},${r} 0 0 1 0,${r}`;

  const moveColor = isInitial ? COLORS.initial : COLORS.move;

  if (isSpecialMove) {
    moveIndicatorGroup.appendChild(createPath(fullCircleD, COLORS.hop, strokeWidth));
  } else {
    if (moveType === 'move') {
      moveIndicatorGroup.appendChild(createPath(fullCircleD, moveColor, strokeWidth));
    } else if (moveType === 'capture') {
      const captureColor = isInitial ? COLORS.initial : COLORS.capture;
      moveIndicatorGroup.appendChild(createPath(fullCircleD, captureColor, strokeWidth));
    } else if (moveType === 'move_capture') {
      const captureColor = isInitial ? COLORS.initial : COLORS.capture;
      moveIndicatorGroup.appendChild(createPath(leftSemiCircleD, moveColor, strokeWidth));
      moveIndicatorGroup.appendChild(createPath(rightSemiCircleD, captureColor, strokeWidth));
    }
  }

  return moveIndicatorGroup;
}
