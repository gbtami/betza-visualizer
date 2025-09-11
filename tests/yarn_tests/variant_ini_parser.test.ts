import { VariantIniParser } from '../../src/variant_ini_parser';
import { Piece } from '../../src/types';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

describe('VariantIniParser', () => {
  const __dirname = path.dirname(fileURLToPath(import.meta.url));
  let fsfCatalog: Piece[];
  let fsfVariantProperties: any;
  let variantsIni: string;

  beforeAll(() => {
    const catalogPath = path.join(__dirname, '../../fsf_built_in_variants_catalog.json');
    fsfCatalog = JSON.parse(fs.readFileSync(catalogPath, 'utf-8'));

    const propertiesPath = path.join(__dirname, '../../fsf_built_in_variant_properties.json');
    fsfVariantProperties = JSON.parse(fs.readFileSync(propertiesPath, 'utf-8'));

    const iniPath = path.join(__dirname, '../variants.ini');
    variantsIni = fs.readFileSync(iniPath, 'utf-8');
  });

  it('should parse variants.ini with the FSF catalog', () => {
    const parser = new VariantIniParser(variantsIni, fsfCatalog, fsfVariantProperties);
    const pieces = parser.parse();

    expect(pieces.length).toBeGreaterThan(0);

    // Test allwayspawns variant which inherits from chess
    const allwaysPawn = pieces.find(p => p.name === 'Allwayspawns-p' && p.variant === 'allwayspawns');
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
    const variantProperties = {
        "chess": {"double_step": true}
    };

    const parser = new VariantIniParser(iniContent, pieceCatalog, variantProperties);
    const pieces = parser.parse();

    const allwaysKing = pieces.find(p => p.name === 'King' && p.variant === 'allwayspawns');
    expect(allwaysKing).toBeDefined();
    expect(allwaysKing?.betza).toBe('K');

    const allwaysPawn = pieces.find(p => p.name === 'Allwayspawns-p' && p.variant === 'allwayspawns');
    expect(allwaysPawn).toBeDefined();
    expect(allwaysPawn?.betza).toBe('mWfceFifmnD');
  });

  it('should override the king\'s betza string', () => {
    const iniContent = `
[centaurking:chess]
king = k:KN
`;
    const pieceCatalog = [
      { name: 'King', variant: 'chess', betza: 'K' },
      { name: 'Pawn', variant: 'chess', betza: 'fmWfceF' },
    ];
    const variantProperties = {
        "chess": {"double_step": true}
    };
    const parser = new VariantIniParser(iniContent, pieceCatalog, variantProperties);
    const pieces = parser.parse();

    const centaurKing = pieces.find(p => p.name === 'King' && p.variant === 'centaurking');
    expect(centaurKing).toBeDefined();
    expect(centaurKing?.betza).toBe('KN');
  });

  it('should handle king override inheritance', () => {
    const iniContent = `
[basevariant]
king = k:N

[childvariant:basevariant]
pawn = p:fW
`;
    const pieceCatalog: Piece[] = [];
    const variantProperties = {};
    const parser = new VariantIniParser(iniContent, pieceCatalog, variantProperties);
    const pieces = parser.parse();

    const childKing = pieces.find(p => p.name === 'King' && p.variant === 'childvariant');
    expect(childKing).toBeDefined();
    expect(childKing?.betza).toBe('N');
  });

  it('should handle double step logic', () => {
    const iniContent = `
[withdoublestep:chess]
king = k:K

[withoutdoublestep:chess]
doubleStep = false
`;
    const pieceCatalog = [
        { name: 'Pawn', variant: 'chess', betza: 'fmWfceF' }
    ];
    const variantProperties = {
        "chess": {"double_step": true}
    };
    const parser = new VariantIniParser(iniContent, pieceCatalog, variantProperties);
    const pieces = parser.parse();

    const pawn1 = pieces.find(p => p.variant === 'withdoublestep' && p.name === 'Pawn');
    expect(pawn1).toBeDefined();
    expect(pawn1?.betza).toContain('ifmnD');

    const pawn2 = pieces.find(p => p.variant === 'withoutdoublestep' && p.name === 'Pawn');
    expect(pawn2).toBeDefined();
    expect(pawn2?.betza).not.toContain('ifmnD');
  });
});
