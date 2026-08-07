import {
  betzaPremoveDestinations,
  createBetzaPremove,
} from '../../src/premove';
import { parseBetza } from '../../src/betza_parser';

const board = { width: 8, height: 8 };

const keys = (destinations: readonly (readonly [number, number])[]): Set<string> =>
  new Set(destinations.map(([x, y]) => `${x},${y}`));

describe('Betza premove envelopes', () => {
  it('uses the same full parser as the visualizer', () => {
    const movement = parseBetza('fRffN');
    const destinations = betzaPremoveDestinations(movement, {
      origin: [3, 3],
      color: 'white',
      board,
    });

    expect(keys(destinations)).toEqual(
      new Set(['3,4', '3,5', '3,6', '3,7', '2,5', '4,5'])
    );
  });

  it('rotates player-relative directions by 180 degrees for black', () => {
    const premove = createBetzaPremove('flN');
    expect(
      keys(
        premove({
          origin: [3, 3],
          color: 'black',
          board,
        })
      )
    ).toEqual(new Set(['5,2']));
  });

  it('ignores current-position blocker rules by widening riders to board edges', () => {
    const premove = createBetzaPremove('R');
    expect(
      keys(premove({ origin: [3, 3], color: 'white', board }))
    ).toEqual(
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

  it('uses full Betza geometry even when Fairy-Stockfish may ignore a feature', () => {
    const premove = createBetzaPremove('jD');
    expect(keys(premove({ origin: [3, 3], color: 'white', board }))).toEqual(
      new Set(['1,3', '5,3', '3,1', '3,5'])
    );
  });

  it('returns no targets for an unknown-only expression', () => {
    const premove = createBetzaPremove('X');
    expect(premove({ origin: [3, 3], color: 'white', board })).toEqual([]);
  });

  it('deduplicates compound destinations', () => {
    const premove = createBetzaPremove('WK');
    const destinations = premove({ origin: [3, 3], color: 'white', board });
    expect(destinations).toHaveLength(keys(destinations).size);
  });

  it('uses rectangular board boundaries instead of the visualizer infinity cap', () => {
    const premove = createBetzaPremove('R');
    const destinations = keys(
      premove({
        origin: [0, 0],
        color: 'white',
        board: { width: 16, height: 4 },
      })
    );
    expect(destinations).toContain('15,0');
    expect(destinations).toContain('0,3');
    expect(destinations).not.toContain('0,4');
  });
});
