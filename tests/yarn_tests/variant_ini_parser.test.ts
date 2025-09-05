import { VariantIniParser } from '../../src/variant_ini_parser';
import { Piece } from '../../src/types';

describe('VariantIniParser', () => {
    it('should parse a variants.ini file content correctly', () => {
        const iniContent = `
[test_variant]
pawn = p
knight = n:N
customPiece1 = x:mybetza

[test_variant2:test_variant]
knight = n:anotherbetza
customPiece2 = y:anotherbetza2
`;
        const parser = new VariantIniParser(iniContent);
        const pieces: Piece[] = parser.parse();

        expect(pieces.length).toBe(7);

        // test_variant pieces
        const pawn = pieces.find(p => p.name === "Pawn" && p.variant === "test_variant");
        expect(pawn).toBeDefined();
        expect(pawn?.betza).toBe("fmWfceF");

        const knight1 = pieces.find(p => p.name === "Knight" && p.variant === "test_variant");
        expect(knight1).toBeDefined();
        expect(knight1?.betza).toBe("N");

        const custom1 = pieces.find(p => p.name === "Custom Piece 1" && p.variant === "test_variant");
        expect(custom1).toBeDefined();
        expect(custom1?.betza).toBe("mybetza");

        // test_variant2 pieces (should inherit and override)
        const pawn2 = pieces.find(p => p.name === "Pawn" && p.variant === "test_variant2");
        expect(pawn2).toBeDefined();
        expect(pawn2?.betza).toBe("fmWfceF");

        const knight2 = pieces.find(p => p.name === "Knight" && p.variant === "test_variant2");
        expect(knight2).toBeDefined();
        expect(knight2?.betza).toBe("anotherbetza");

        const custom1_inherited = pieces.find(p => p.name === "Custom Piece 1" && p.variant === "test_variant2");
        expect(custom1_inherited).toBeDefined();
        expect(custom1_inherited?.betza).toBe("mybetza");

        const custom2 = pieces.find(p => p.name === "Custom Piece 2" && p.variant === "test_variant2");
        expect(custom2).toBeDefined();
        expect(custom2?.betza).toBe("anotherbetza2");
    });
});
