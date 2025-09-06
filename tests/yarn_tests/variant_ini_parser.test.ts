import { VariantIniParser } from '../../src/variant_ini_parser';
import { Piece } from '../../src/types';
import * as fs from 'fs';
import * as path from 'path';

describe('VariantIniParser', () => {
    it('should parse the real variants.ini file content correctly', () => {
        const iniContent = fs.readFileSync(path.join(__dirname, '..', 'variants.ini'), 'utf-8');
        const pieceCatalog: Piece[] = JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'piece_catalog.json'), 'utf-8'));

        const parser = new VariantIniParser(iniContent, pieceCatalog);
        const pieces: Piece[] = parser.parse();

        expect(pieces.length).toBeGreaterThan(0);

        // Test allwayspawns variant which inherits from chess
        // and has a custom pawn
        const allways_pawn = pieces.find(p => p.name === "Custom Piece 1" && p.variant === "allwayspawns");
        expect(allways_pawn).toBeDefined();
        expect(allways_pawn?.betza).toBe("mWfceFifmnD");

        // It should inherit the king from chess
        const allways_king = pieces.find(p => p.name === "King" && p.variant === "allwayspawns");
        expect(allways_king).toBeDefined();
        expect(allways_king?.betza).toBe("K");

        // Test gothhouse which inherits from capablanca
        const gothhouse_knight = pieces.find(p => p.name === "Knight" && p.variant === "gothhouse");
        expect(gothhouse_knight).toBeDefined();

        const capablanca_knight = pieceCatalog.find(p => p.name === "Knight" && p.variant === "capablanca");
        expect(capablanca_knight).toBeDefined();
        expect(gothhouse_knight?.betza).toBe(capablanca_knight?.betza);

        // and it should also have the chancellor from capablanca
        const gothhouse_chancellor = pieces.find(p => p.name === "Chancellor" && p.variant === "gothhouse");
        expect(gothhouse_chancellor).toBeDefined();
        const capablanca_chancellor = pieceCatalog.find(p => p.name === "Chancellor" && p.variant === "capablanca");
        expect(capablanca_chancellor).toBeDefined();
        expect(gothhouse_chancellor?.betza).toBe(capablanca_chancellor?.betza);
    });
});
