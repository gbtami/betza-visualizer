import { createMoveIndicator, COLORS, CELL_SIZE } from '../../src/svg_utils.js';

describe('createMoveIndicator', () => {
  it('should create a full circle for a "move" type', () => {
    const indicator = createMoveIndicator('move', false, false);
    expect(indicator.tagName).toBe('g');
    expect(indicator.childNodes.length).toBe(1);

    const path = indicator.childNodes[0] as SVGPathElement;
    expect(path.tagName).toBe('path');
    expect(path.getAttribute('stroke')).toBe(COLORS.move);

    const r = CELL_SIZE * 0.3;
    const expectedD = `M 0,${-r} A ${r},${r} 0 1 1 0,${r} A ${r},${r} 0 1 1 0,${-r}`;
    expect(path.getAttribute('d')).toBe(expectedD);
  });

  it('should create a move indicator for a "capture" type', () => {
    const indicator = createMoveIndicator('capture', false, false);
    expect(indicator.tagName).toBe('g');
    expect(indicator.childNodes.length).toBe(1);

    const path = indicator.childNodes[0] as SVGPathElement;
    expect(path.tagName).toBe('path');
    expect(path.getAttribute('stroke')).toBe(COLORS.capture);
  });

  it('should create a move indicator for a "move_capture" type', () => {
    const indicator = createMoveIndicator('move_capture', false, false);
    expect(indicator.tagName).toBe('g');
    expect(indicator.childNodes.length).toBe(2);

    const path1 = indicator.childNodes[0] as SVGPathElement;
    expect(path1.tagName).toBe('path');
    expect(path1.getAttribute('stroke')).toBe(COLORS.move);

    const path2 = indicator.childNodes[1] as SVGPathElement;
    expect(path2.tagName).toBe('path');
    expect(path2.getAttribute('stroke')).toBe(COLORS.capture);
  });

  it('should create a move indicator for a special move', () => {
    const indicator = createMoveIndicator('move_capture', true, false);
    expect(indicator.tagName).toBe('g');
    expect(indicator.childNodes.length).toBe(1);

    const path = indicator.childNodes[0] as SVGPathElement;
    expect(path.tagName).toBe('path');
    expect(path.getAttribute('stroke')).toBe(COLORS.hop);
  });

  it('should add the initial-move class for an initial move', () => {
    const indicator = createMoveIndicator('move', false, true);
    expect(indicator.classList.contains('initial-move')).toBe(true);
  });
});
