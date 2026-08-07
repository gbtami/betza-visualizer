import { BetzaParser } from '../../src/betza_parser';
import { Move } from '../../src/types';

// Helper to convert a set of moves to a set of coordinate strings for easy comparison
const toCoordSet = (moves: Move[]): Set<string> => {
    return new Set(moves.map(m => `${m.x},${m.y}`));
};

describe('BetzaParser', () => {
    let parser: BetzaParser;

    beforeEach(() => {
        parser = new BetzaParser();
    });

    describe('Original Porting and Regression Tests', () => {
        it('should correctly parse a simple piece with a suffix', () => {
            const moves = parser.parse('W3');
            expect(moves.length).toBe(12);
        });

        it('should correctly parse an abbreviation with a suffix (B3)', () => {
            const moves = parser.parse('B3');
            expect(moves.length).toBe(12);
        });

        it('should correctly parse a compound abbreviation with a suffix (Q2)', () => {
            const moves = parser.parse('Q2');
            expect(moves.length).toBe(16);
        });

        it('should handle stateful modifiers on compound pieces (mRcN)', () => {
            const moves = parser.parse('mRcN');
            const rookMove = moves.find(m => m.x === 0 && m.y === 5);
            const knightMove = moves.find(m => m.x === 2 && m.y === 1);
            expect(rookMove?.moveType).toBe('move');
            expect(knightMove?.moveType).toBe('capture');
        });
    });

    describe('Fairy-Stockfish Piece Definitions', () => {
        it('should parse a Pawn (fmWfceF)', () => {
            const moves = parser.parse('fmWfceF');
            expect(moves.length).toBe(3);
        });

        it('should parse a Knight (N)', () => {
            expect(parser.parse('N').length).toBe(8);
        });

        it('should parse a Bishop (B)', () => {
            expect(parser.parse('B').length).toBe(4 * parser.infinityCap);
        });

        it('should parse a Rook (R)', () => {
            expect(parser.parse('R').length).toBe(4 * parser.infinityCap);
        });

        it('should parse a Queen (Q)', () => {
            expect(parser.parse('Q').length).toBe(8 * parser.infinityCap);
        });

        it('should parse a King (K)', () => {
            expect(parser.parse('K').length).toBe(8);
        });

        it('should parse an Archbishop (BN)', () => {
            const moves = parser.parse('BN');
            expect(moves.length).toBe((4 * parser.infinityCap) + 8);
        });

        it('should parse an Empress (E)', () => {
            const moves = parser.parse('E');
            expect(moves.length).toBe((4 * parser.infinityCap) + 8);
        });

        it('should parse a Ferz (F)', () => {
            const expected = new Set(['1,1', '1,-1', '-1,1', '-1,-1']);
            expect(toCoordSet(parser.parse('F'))).toEqual(expected);
        });

        it('should parse a Wazir (W)', () => {
            const expected = new Set(['1,0', '-1,0', '0,1', '0,-1']);
            expect(toCoordSet(parser.parse('W'))).toEqual(expected);
        });

        it('should parse a Camel (C)', () => {
            expect(parser.parse('C').length).toBe(8);
        });

        it('should parse a Zebra (Z)', () => {
            expect(parser.parse('Z').length).toBe(8);
        });

        it('should parse a Tripper (G)', () => {
            expect(parser.parse('G').length).toBe(4);
        });

        it('should parse the original Zebra alias (J)', () => {
            expect(toCoordSet(parser.parse('J'))).toEqual(toCoordSet(parser.parse('Z')));
        });

        it('should parse the original Camel alias (L)', () => {
            expect(toCoordSet(parser.parse('L'))).toEqual(toCoordSet(parser.parse('C')));
        });

        it('should parse a Berolina Pawn (fmFfceW)', () => {
            expect(parser.parse('fmFfceW').length).toBe(3);
        });

        it('should parse a Spider Pawn (mFmcW)', () => {
            expect(parser.parse('mFmcW').length).toBe(8);
        });

        it('should parse a Champion (WAD)', () => {
            const moves = parser.parse('WAD');
            expect(moves.length).toBe(12);
        });

        it('should parse a Wizard (M -> FC)', () => {
            const moves = parser.parse('M');
            expect(moves.length).toBe(12);
        });

        it('should parse a Nightrider shorthand (NN)', () => {
            const moves = parser.parse('NN');
            expect(moves.length).toBe(8 * parser.infinityCap);
            const moveCoords = toCoordSet(moves);
            expect(moveCoords).toContain('4,2');
            expect(moveCoords).toContain('-4,-2');
        });
    });

    describe('Advanced Betza Modifier Rules', () => {
        let parser: BetzaParser;

        beforeEach(() => {
            parser = new BetzaParser();
        });

        it('should correctly handle quadrant modifiers like flN', () => {
            const moves = parser.parse('flN');
            const expected = new Set(['-2,1']);
            expect(toCoordSet(moves)).toEqual(expected);
        });

        it("should correctly parse 'fN' as a Shogi Knight", () => {
            const moves = parser.parse('fN');
            const expected = new Set(['-1,2', '1,2']);
            expect(toCoordSet(moves)).toEqual(expected);
        });

        it("should parse 'ffN' as equivalent to 'fN' for compatibility", () => {
            const moves_fN = parser.parse('fN');
            const moves_ffN = parser.parse('ffN');
            expect(toCoordSet(moves_fN)).toEqual(toCoordSet(moves_ffN));
        });

        it("should handle the 'h' modifier to get all forward moves for a Knight", () => {
            const moves = parser.parse('fhN');
            const expected = new Set(['-1,2', '1,2', '-2,1', '2,1']);
            expect(toCoordSet(moves)).toEqual(expected);
        });

        it("should handle union of doubled modifiers like 'ffrrN'", () => {
            const moves = parser.parse('ffrrN');
            const expected = new Set(['-1,2', '1,2', '2,1', '2,-1']);
            expect(toCoordSet(moves)).toEqual(expected);
        });

        it('should correctly handle doubled sideways modifiers like srrC', () => {
            const moves = parser.parse('srrC');
            const expected = new Set(['3,1', '3,-1', '-3,1', '-3,-1']);
            expect(toCoordSet(moves)).toEqual(expected);
        });

        it('should correctly handle combined doubled and quadrant modifiers like fflN', () => {
            const moves = parser.parse('fflN');
            const expected = new Set(['-2,-1', '-2,1', '-1,2', '1,2']);
            expect(toCoordSet(moves)).toEqual(expected);
        });

        // --- NON-JUMPING MODIFIER AND UNSUPPORTED j DIAGNOSTIC ---
        it('should correctly handle the non-jumping "n" modifier', () => {
            const moves = parser.parse('nN');
            expect(moves.length).toBe(8);
            expect(moves.every(m => m.jumpType === 'non-jumping')).toBe(true);
        });

        it('should report the unsupported "j" modifier and ignore it', () => {
            const parsed = parser.parseDetailed('jR');
            expect(parsed.warnings).toContainEqual({
                message: 'Unsupported Betza modifier "j" was ignored',
                index: 0,
                token: 'j',
            });
            const moves = parser.parse('jR');
            expect(moves.length).toBeGreaterThan(0);
            expect(moves.every(m => m.jumpType === 'non-jumping')).toBe(true);
        });

        it('should default to "jumping" for a leaper without modifiers', () => {
            const moves = parser.parse('N');
            expect(moves.length).toBe(8);
            expect(moves.every(m => m.jumpType === 'jumping')).toBe(true);
        });

        it('should default to "non-jumping" for a sliding rider', () => {
            const moves = parser.parse('R'); // R is an alias for W0
            expect(moves.length).toBeGreaterThan(0);
            expect(moves.every(m => m.jumpType === 'non-jumping')).toBe(true);
        });

        it('should default to "jumping" for a jumping rider', () => {
            const moves = parser.parse('NN'); // NN is an alias for N0
            expect(moves.length).toBeGreaterThan(0);
            expect(moves.every(m => m.jumpType === 'jumping')).toBe(true);
        });

        it('should correctly handle the pawn "p" modifier on a rider', () => {
            const moves = parser.parse('pNN');
            expect(moves.length).toBeGreaterThan(0);
            expect(moves.every(m => m.moveType === 'move_capture')).toBe(true);
            expect(moves.every(m => m.hopType === 'p')).toBe(true);
        });
    });

    describe('Directional Shorthand Modifiers', () => {
        it("should correctly handle 'vN' for a hippogonal piece", () => {
            const moves = parser.parse('vN');
            const expected = new Set(['-1,2', '1,2', '-1,-2', '1,-2']);
            expect(toCoordSet(moves)).toEqual(expected);
        });

        it("should correctly handle 'sN' for a hippogonal piece", () => {
            const moves = parser.parse('sN');
            const expected = new Set(['-2,1', '2,1', '-2,-1', '2,-1']);
            expect(toCoordSet(moves)).toEqual(expected);
        });

        it("should correctly handle the vertical 'v' modifier on a Rook", () => {
            const moves = parser.parse('vR');
            const moveCoords = toCoordSet(moves);
            const expectedCoords = new Set<string>();
            for (let i = 1; i <= parser.infinityCap; i++) {
                expectedCoords.add(`0,${i}`);
                expectedCoords.add(`0,${-i}`);
            }
            expect(moveCoords).toEqual(expectedCoords);
        });

        it("should correctly handle the sideways 's' modifier on a Rook", () => {
            const moves = parser.parse('sR');
            const moveCoords = toCoordSet(moves);
            const expectedCoords = new Set<string>();
            for (let i = 1; i <= parser.infinityCap; i++) {
                expectedCoords.add(`${i},0`);
                expectedCoords.add(`${-i},0`);
            }
            expect(moveCoords).toEqual(expectedCoords);
        });
    });

    describe('Multi-Directional Modifiers', () => {
        it("should correctly parse the Janggi pawn 'sfW'", () => {
            const moves = parser.parse('sfW');
            const moveCoords = toCoordSet(moves);
            const expected = new Set(['0,1', '-1,0', '1,0']);
            expect(moveCoords).toEqual(expected);
        });

        it("should correctly parse 'frlR' (forward and sideways Rook)", () => {
            const moves = parser.parse('frlR');
            const moveCoords = toCoordSet(moves);
            const expected = new Set<string>();
            for (let i = 1; i <= parser.infinityCap; i++) {
                expected.add(`0,${i}`);   // Forward
                expected.add(`${i},0`);   // Right
                expected.add(`${-i},0`);  // Left
            }
            expect(moveCoords).toEqual(expected);
        });

        it("should correctly parse 'rlbK' (sideways and backward King)", () => {
            const moves = parser.parse('rlbK');
            const moveCoords = toCoordSet(moves);
            const expected = new Set([
                '-1,-1', '0,-1', '1,-1', '1,0', '1,1'
            ]);
            expect(moveCoords).toEqual(expected);
        });

        it("should correctly parse the Fibnif 'fbNF'", () => {
            const moves = parser.parse('fbNF');
            const moveCoords = toCoordSet(moves);
            const expected = new Set([
                // Ferz moves
                '1,1', '1,-1', '-1,1', '-1,-1',
                // Fairy-Stockfish's fbN directions
                '1,2', '-1,2', '1,-2', '-1,-2'
            ]);
            expect(moveCoords.size).toBe(8);
            expect(moveCoords).toEqual(expected);
        });
    });

  describe('Modifier Scope', () => {
    test('modifier does not leak to the next atom', () => {
      const moves = parser.parse('fBW');
      const moveCoords = new Set(moves.map((m) => `${m.x},${m.y}`));

      // Check Wazir moves
      expect(moveCoords).toContain('0,-1'); // backward
      expect(moveCoords).toContain('1,0'); // sideways
      expect(moveCoords).toContain('-1,0'); // sideways

      // Check Bishop moves
      expect(moveCoords).not.toContain('1,-1'); // backward
    });

    test('modifiers apply to all parts of a compound piece', () => {
      const moves = parser.parse('fK');
      const moveCoords = new Set(moves.map((m) => `${m.x},${m.y}`));
      const expected = new Set(['0,1', '1,1', '-1,1']);
      expect(moveCoords).toEqual(expected);
    });
  });

  describe('Initial Modifier', () => {
    it('should correctly handle the initial "i" modifier', () => {
        const moves = parser.parse('iW');
        expect(moves.length).toBe(4);
        expect(moves.every(m => m.initialOnly === true)).toBe(true);
    });

    it('should not have the initialOnly flag for a normal piece', () => {
        const moves = parser.parse('W');
        expect(moves.length).toBe(4);
        expect(moves.every(m => m.initialOnly === undefined)).toBe(true);
    });
  });
  describe('Diagnostics', () => {
    it('reports unsupported punctuation while preserving supported moves', () => {
      const parsed = parser.parseDetailed('W?N');
      expect(parsed.warnings).toContainEqual({
        message: 'Unsupported Betza character "?" was ignored',
        index: 1,
        token: '?',
      });
      expect(toCoordSet(parser.parse('W?N'))).toEqual(toCoordSet(parser.parse('WN')));
    });
  });

  describe('Fairy-Stockfish supported Betza subset conformance', () => {
    const infinityCap = new BetzaParser().infinityCap;
    const coordinates = (notation: string): Set<string> =>
      toCoordSet(parser.parse(notation));

    test.each([
      ['W', 4],
      ['F', 4],
      ['D', 4],
      ['N', 8],
      ['A', 4],
      ['H', 4],
      ['L', 8],
      ['C', 8],
      ['J', 8],
      ['Z', 8],
      ['G', 4],
      ['K', 8],
      ['R', 4 * infinityCap],
      ['B', 4 * infinityCap],
      ['Q', 8 * infinityCap],
    ])('supports the FSF base atom %s', (notation, count) => {
      expect(parser.parse(notation).length).toBe(count);
    });

    const fsfDirectionCases: readonly [string, Set<string>][] = [
      ['fW', new Set(['0,1'])],
      ['bW', new Set(['0,-1'])],
      ['lW', new Set(['-1,0'])],
      ['rW', new Set(['1,0'])],
      ['vW', new Set(['0,1', '0,-1'])],
      ['sW', new Set(['-1,0', '1,0'])],
      ['fsW', new Set(['-1,0', '0,1', '1,0'])],
      ['bsW', new Set(['-1,0', '0,-1', '1,0'])],
      ['ffN', new Set(['-1,2', '1,2'])],
      ['bbN', new Set(['-1,-2', '1,-2'])],
      ['rrN', new Set(['2,-1', '2,1'])],
      ['llN', new Set(['-2,-1', '-2,1'])],
      ['vvN', new Set(['-1,-2', '-1,2', '1,-2', '1,2'])],
      ['ssN', new Set(['-2,-1', '-2,1', '2,-1', '2,1'])],
      ['rfN', new Set(['1,2'])],
      ['rvN', new Set(['1,-2', '1,2'])],
      ['fhN', new Set(['-2,1', '-1,2', '1,2', '2,1'])],
      ['rhN', new Set(['1,-2', '1,2', '2,-1', '2,1'])],
      ['hrN', new Set(['-2,1', '-1,-2', '1,2', '2,-1'])],
      ['lbN', new Set(['-1,-2'])],
      ['lvN', new Set(['-1,-2', '-1,2'])],
      ['bhN', new Set(['-2,-1', '-1,-2', '1,-2', '2,-1'])],
      ['lhN', new Set(['-2,-1', '-1,-2', '-1,2', '-2,1'])],
      ['brN', new Set(['2,-1'])],
      ['bsN', new Set(['-2,-1', '2,-1'])],
      ['flN', new Set(['-2,1'])],
      ['fsN', new Set(['-2,1', '2,1'])],
      ['frN', new Set(['2,1'])],
      ['hlN', new Set(['-2,-1', '-1,2', '1,-2', '2,1'])],
      ['blN', new Set(['-2,-1'])],
      ['rbN', new Set(['1,-2'])],
      ['lfN', new Set(['-1,2'])],
    ];

    test.each(fsfDirectionCases)(
      'matches FSF directional semantics for %s',
      (notation, expected) => {
        expect(coordinates(notation)).toEqual(expected);
      }
    );

    it('supports limited W/R, F/B and N riders', () => {
      expect(coordinates('W2')).toEqual(
        new Set(['1,0', '-1,0', '0,1', '0,-1', '2,0', '-2,0', '0,2', '0,-2'])
      );
      expect(parser.parse('F3').length).toBe(12);
      expect(parser.parse('N2').length).toBe(16);
      expect(coordinates('R2')).toEqual(coordinates('W2'));
      expect(coordinates('B3')).toEqual(coordinates('F3'));
    });

    it('supports unlimited W/R, F/B and N riders', () => {
      expect(coordinates('WW')).toEqual(coordinates('R'));
      expect(coordinates('FF')).toEqual(coordinates('B'));
      expect(coordinates('NN')).toEqual(coordinates('N0'));
    });

    test.each(['pR', 'pB', 'gR', 'gB'])(
      'marks the supported FSF hopper form %s',
      notation => {
        const expectedType = notation.startsWith('p') ? 'p' : 'g';
        const moves = parser.parse(notation);
        expect(moves.length).toBeGreaterThan(0);
        expect(moves.every(move => move.hopType === expectedType)).toBe(true);
      }
    );

    test.each(['nN', 'nA', 'nZ', 'nD'])(
      'marks the supported FSF lame-leaper form %s',
      notation => {
        const moves = parser.parse(notation);
        expect(moves.length).toBeGreaterThan(0);
        expect(moves.every(move => move.jumpType === 'non-jumping')).toBe(true);
      }
    );

    it('preserves FSF move and capture modalities', () => {
      expect(parser.parse('mW').every(move => move.moveType === 'move')).toBe(true);
      expect(parser.parse('cW').every(move => move.moveType === 'capture')).toBe(true);
      expect(parser.parse('mcW').every(move => move.moveType === 'move_capture')).toBe(true);
      expect(parser.parse('cmW').every(move => move.moveType === 'move_capture')).toBe(true);
    });

    it('preserves the FSF initial-only modifier', () => {
      expect(parser.parse('iW').every(move => move.initialOnly)).toBe(true);
    });

    it('keeps pending modifiers across an unsupported atom', () => {
      const moves = parser.parse('mXR');
      expect(moves.length).toBe(4 * parser.infinityCap);
      expect(moves.every(move => move.moveType === 'move')).toBe(true);
    });
  });

});
