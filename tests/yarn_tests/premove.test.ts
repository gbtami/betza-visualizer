import {
  betzaPremoveDestinations,
  createBetzaPremove,
  parseBetza,
  parseBetzaStrict,
} from '../../src/index';

const toCoordSet = (positions: readonly (readonly [number, number])[]) =>
  new Set(positions.map(([x, y]) => `${x},${y}`));

describe('Fairy-Stockfish-compatible Betza parsing', () => {
  it('ignores unknown characters without resetting pending modifiers', () => {
    const parsed = parseBetza('mXN');
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;

    expect(parsed.value.terms).toHaveLength(1);
    expect(parsed.value.terms[0].moveType).toBe('move');
    expect(parsed.warnings.map((warning) => warning.token)).toContain('X');
  });

  it('returns the movement Fairy-Stockfish understands together with warnings', () => {
    const parsed = parseBetza('W?N');
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;

    expect(parsed.value.terms.map((term) => term.atom)).toEqual(['W', 'N']);
    expect(parsed.warnings.map((warning) => warning.token)).toContain('?');
  });

  it('allows strict authoring tools to reject ignored fragments', () => {
    const parsed = parseBetzaStrict('W?N');
    expect(parsed.ok).toBe(false);
    if (parsed.ok) return;
    expect(parsed.errors.map((error) => error.token)).toContain('?');
  });

  it('uses Fairy-Stockfish atoms rather than visualizer-only aliases', () => {
    const j = parseBetza('J');
    const e = parseBetza('E');
    expect(j.ok).toBe(true);
    expect(e.ok).toBe(true);
    if (!j.ok || !e.ok) return;

    expect(j.value.terms[0].atomCoords).toEqual({ x: 2, y: 3 });
    expect(e.value.terms).toHaveLength(0);
    expect(e.warnings.map((warning) => warning.token)).toContain('E');
  });

  it('preserves Fairy-Stockfish repeated-atom rider behavior', () => {
    const parsed = parseBetza('mNN');
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;

    expect(parsed.value.terms).toHaveLength(2);
    expect(parsed.value.terms[0]).toMatchObject({
      maxSteps: 'unbounded',
      moveType: 'move',
    });
    expect(parsed.value.terms[1]).toMatchObject({
      maxSteps: 1,
      moveType: 'move_capture',
    });
  });
});

describe('Betza premove movement envelopes', () => {
  it('ignores blockers by depending only on geometry', () => {
    const parsed = parseBetza('R');
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;

    const destinations = betzaPremoveDestinations(parsed.value, {
      origin: [3, 3],
      color: 'white',
      board: { width: 8, height: 8 },
    });

    expect(toCoordSet(destinations)).toEqual(
      new Set([
        '0,3',
        '1,3',
        '2,3',
        '4,3',
        '5,3',
        '6,3',
        '7,3',
        '3,0',
        '3,1',
        '3,2',
        '3,4',
        '3,5',
        '3,6',
        '3,7',
      ])
    );
  });

  it.each(['R', 'mR', 'cR', 'pR', 'gR'])(
    '%s has the same conservative rook premove envelope',
    (notation: string) => {
      const compiled = createBetzaPremove(notation);
      expect(compiled.ok).toBe(true);
      if (!compiled.ok) return;

      const destinations = compiled.value({
        origin: [0, 0],
        color: 'white',
        board: { width: 4, height: 4 },
      });
      expect(toCoordSet(destinations)).toEqual(
        new Set(['1,0', '2,0', '3,0', '0,1', '0,2', '0,3'])
      );
    }
  );

  it('uses Fairy-Stockfish directional pairs and rotates them for black', () => {
    const compiled = createBetzaPremove('flN');
    expect(compiled.ok).toBe(true);
    if (!compiled.ok) return;

    const white = compiled.value({
      origin: [3, 3],
      color: 'white',
      board: { width: 8, height: 8 },
    });
    const black = compiled.value({
      origin: [3, 3],
      color: 'black',
      board: { width: 8, height: 8 },
    });

    expect(toCoordSet(white)).toEqual(new Set(['1,4']));
    expect(toCoordSet(black)).toEqual(new Set(['5,2']));
  });

  it('uses the actual rectangular board edge for unbounded riders', () => {
    const compiled = createBetzaPremove('fR');
    expect(compiled.ok).toBe(true);
    if (!compiled.ok) return;

    const destinations = compiled.value({
      origin: [1, 1],
      color: 'white',
      board: { width: 3, height: 16 },
    });
    expect(destinations).toHaveLength(14);
    expect(toCoordSet(destinations)).toContain('1,15');
  });

  it('uses the understood movement even when Fairy-Stockfish ignores syntax', () => {
    const compiled = createBetzaPremove('mXR');
    expect(compiled.ok).toBe(true);
    if (!compiled.ok) return;

    expect(compiled.warnings.map((warning) => warning.token)).toContain('X');
    expect(
      toCoordSet(
        compiled.value({
          origin: [0, 0],
          color: 'white',
          board: { width: 3, height: 3 },
        })
      )
    ).toEqual(new Set(['1,0', '2,0', '0,1', '0,2']));
  });

  it('treats unknown-only or empty notation as an immobile piece', () => {
    for (const notation of ['X', '']) {
      const compiled = createBetzaPremove(notation);
      expect(compiled.ok).toBe(true);
      if (!compiled.ok) continue;
      expect(
        compiled.value({
          origin: [1, 1],
          color: 'white',
          board: { width: 3, height: 3 },
        })
      ).toEqual([]);
    }
  });
});
