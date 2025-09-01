import { BetzaParser } from '../src/betza_parser';
import { Move } from '../src/types';

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

        it('should parse an Alibaba (J -> AD)', () => {
            const moves = parser.parse('J');
            expect(moves.length).toBe(8);
            expect(moves).toContainEqual(expect.objectContaining({ atom: 'A' }));
            expect(moves).toContainEqual(expect.objectContaining({ atom: 'D' }));
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
    });

    describe('Advanced Betza Modifier Rules', () => {
        let parser: BetzaParser;

        beforeEach(() => {
            parser = new BetzaParser();
        });

        it('should correctly handle quadrant modifiers like flN', () => {
            const moves = parser.parse('flN');
            const expected = new Set(['-1,2', '-2,1']);
            expect(toCoordSet(moves)).toEqual(expected);
        });

        it('should correctly handle doubled forward modifiers like ffN (Shogi Knight)', () => {
            const moves = parser.parse('ffN');
            const expected = new Set(['-1,2', '1,2']);
            expect(toCoordSet(moves)).toEqual(expected);
        });

        it('should correctly handle doubled sideways modifiers like srrC', () => {
            const moves = parser.parse('srrC');
            const expected = new Set(['3,1', '3,-1', '-3,1', '-3,-1']);
            expect(toCoordSet(moves)).toEqual(expected);
        });

        it('should correctly handle combined doubled and quadrant modifiers like fflN', () => {
            const moves = parser.parse('fflN');
            const expected = new Set(['-1,2']);
            expect(toCoordSet(moves)).toEqual(expected);
        });

        // --- NEW TESTS FOR n AND j MODIFIERS ---
        it('should correctly handle the non-jumping "n" modifier', () => {
            const moves = parser.parse('nN');
            expect(moves.length).toBe(8);
            expect(moves.every(m => m.jumpType === 'non-jumping')).toBe(true);
        });

        it('should correctly handle the jumping "j" modifier', () => {
            const moves = parser.parse('jD');
            expect(moves.length).toBe(4);
            expect(moves.every(m => m.jumpType === 'jumping')).toBe(true);
        });
    });
});
