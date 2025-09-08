import { VariantIniParser } from '../../src/variant_ini_parser';
import { Piece } from '../../src/types';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

describe('VariantIniParser', () => {
  const __dirname = path.dirname(fileURLToPath(import.meta.url));
  let fsfCatalog: Piece[];
  let variantsIni: string;

  beforeAll(() => {
    const catalogPath = path.join(__dirname, '../../fsf_built_in_variants_catalog.json');
    fsfCatalog = JSON.parse(fs.readFileSync(catalogPath, 'utf-8'));

    const iniPath = path.join(__dirname, '../variants.ini');
    variantsIni = fs.readFileSync(iniPath, 'utf-8');
  });

  it('should parse variants.ini with the FSF catalog', () => {
    const parser = new VariantIniParser(variantsIni, fsfCatalog);
    const pieces = parser.parse();

    expect(pieces.length).toBeGreaterThan(0);

    // Test allwayspawns variant which inherits from chess
    const allwaysPawn = pieces.find(p => p.name === 'Custom Piece 1' && p.variant === 'allwayspawns');
    expect(allwaysPawn).toBeDefined();
    expect(allwaysPawn?.betza).toBe('mWfceFifmnD');

    const allwaysKing = pieces.find(p => p.name === 'King' && p.variant === 'allwayspawns');
    expect(allwaysKing).toBeDefined();
    expect(allwaysKing?.betza).toBe('K');

    // Test 3check-crazyhouse which inherits from crazyhouse
    const crazyhouseKnight = fsfCatalog.find(p => p.name === 'Knight' && p.variant === 'crazyhouse');
    expect(crazyhouseKnight).toBeDefined();

    const threecheckKnight = pieces.find(p => p.name === 'Knight' && p.variant === '3check-crazyhouse');
    expect(threecheckKnight).toBeDefined();
    expect(threecheckKnight?.betza).toBe(crazyhouseKnight?.betza);

    // Test gothhouse:capablanca
    const gothhouseKnight = pieces.find(p => p.name === 'Knight' && p.variant === 'gothhouse');
    expect(gothhouseKnight).toBeDefined();

    const capablancaKnight = fsfCatalog.find(p => p.name === 'Knight' && p.variant === 'capablanca');
    expect(capablancaKnight).toBeDefined();
    expect(gothhouseKnight?.betza).toBe(capablancaKnight?.betza);

    const gothhouseChancellor = pieces.find(p => p.name === 'Chancellor' && p.variant === 'gothhouse');
    expect(gothhouseChancellor).toBeDefined();
    const capablancaChancellor = fsfCatalog.find(p => p.name === 'Chancellor' && p.variant === 'capablanca');
    expect(capablancaChancellor).toBeDefined();
    expect(gothhouseChancellor?.betza).toBe(capablancaChancellor?.betza);
  });

  it('should handle inheritance from a minimal catalog', () => {
    const iniContent = `
[allwayspawns:chess]
customPiece1 = p:mWfceFifmnD
`;
    const pieceCatalog = [
      { name: 'King', variant: 'chess', betza: 'K' },
      { name: 'Pawn', variant: 'chess', betza: 'fmWfceF' }
    ];

    const parser = new VariantIniParser(iniContent, pieceCatalog);
    const pieces = parser.parse();

    const allwaysKing = pieces.find(p => p.name === 'King' && p.variant === 'allwayspawns');
    expect(allwaysKing).toBeDefined();
    expect(allwaysKing?.betza).toBe('K');
  });
});
