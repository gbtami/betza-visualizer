import { Piece } from './types.js';

export class VariantIniParser {
  private readonly config: Map<string, Map<string, string>> = new Map();

  private readonly predefinedPieces: Map<string, string> = new Map([
    ['pawn', 'fmWfceF'], ['knight', 'N'], ['bishop', 'B'], ['rook', 'R'],
    ['queen', 'Q'], ['fers', 'F'], ['alfil', 'A'], ['fersAlfil', 'FA'],
    ['silver', 'FfW'], ['aiwok', 'RNF'], ['bers', 'RF'], ['archbishop', 'BN'],
    ['chancellor', 'RN'], ['amazon', 'QN'], ['knibis', 'mNcB'], ['biskni', 'mBcN'],
    ['kniroo', 'mNcR'], ['rookni', 'mRcN'], ['shogiPawn', 'fW'], ['lance', 'fR'],
    ['shogiKnight', 'fN'], ['gold', 'WfF'], ['dragonHorse', 'BW'], ['clobber', 'cW'],
    ['breakthrough', 'fmWfF'], ['immobile', ''], ['cannon', 'mRcpR'],
    ['janggiCannon', 'pR'], ['soldier', 'fsW'], ['horse', 'nN'], ['elephant', 'nA'],
    ['janggiElephant', 'nZ'], ['banner', 'RcpRnN'], ['wazir', 'W'], ['commoner', 'K'],
    ['centaur', 'KN'], ['king', 'K'],
  ]);

  private readonly pieceKeys: Set<string> = new Set([
    'pawn', 'knight', 'bishop', 'rook', 'queen', 'king', 'fers', 'alfil',
    'fersAlfil', 'silver', 'aiwok', 'bers', 'archbishop', 'chancellor',
    'amazon', 'knibis', 'biskni', 'kniroo', 'rookni', 'shogiPawn', 'lance',
    'shogiKnight', 'gold', 'dragonHorse', 'clobber', 'breakthrough',
    'immobile', 'cannon', 'janggiCannon', 'soldier', 'horse', 'elephant',
    'janggiElephant', 'banner', 'wazir', 'commoner', 'centaur',
    ...Array.from({ length: 25 }, (_, i) => `customPiece${i + 1}`),
  ]);

  constructor(iniContent: string) {
    this.parseIni(iniContent);
  }

  private parseIni(iniContent: string): void {
    const lines = iniContent.split(/\r?\n/);
    let currentSection = '';

    for (const line of lines) {
      const trimmedLine = line.trim();
      if (trimmedLine.startsWith('[') && trimmedLine.endsWith(']')) {
        currentSection = trimmedLine.substring(1, trimmedLine.length - 1);
        if (!this.config.has(currentSection)) {
          this.config.set(currentSection, new Map());
        }
      } else if (currentSection && trimmedLine.includes('=')) {
        const [key, value] = trimmedLine.split('=', 2);
        this.config.get(currentSection)!.set(key.trim(), value.trim());
      }
    }
  }

  private getAllVariantSettings(variantSectionName: string): Map<string, string> {
    const memo: Map<string, Map<string, string>> = new Map();

    const resolve = (sectionName: string): Map<string, string> => {
      if (memo.has(sectionName)) {
        return memo.get(sectionName)!;
      }

      let settings = new Map<string, string>();
      if (sectionName.includes(':')) {
        const [, parent] = sectionName.split(':', 2);
        const parentFullSection = Array.from(this.config.keys()).find(
          (s) => s.startsWith(parent) && (s.length === parent.length || s[parent.length] === ':')
        );
        if (parentFullSection) {
          settings = new Map(resolve(parentFullSection));
        }
      }

      if (this.config.has(sectionName)) {
        const currentSettings = this.config.get(sectionName)!;
        for (const [key, value] of currentSettings.entries()) {
          settings.set(key, value);
        }
      }

      memo.set(sectionName, settings);
      return settings;
    };

    return resolve(variantSectionName);
  }

  public parse(): Piece[] {
    const allPieces: Piece[] = [];
    const processedVariants = new Set<string>();

    for (const sectionName of this.config.keys()) {
      const variantName = sectionName.split(':', 1)[0];

      if (processedVariants.has(variantName)) {
        continue;
      }

      const settings = this.getAllVariantSettings(sectionName);
      const variantPieces: Map<string, Piece> = new Map();

      // First, apply parent pieces to the map
      if (sectionName.includes(':')) {
          const [, parent] = sectionName.split(':', 2);
          const parentFullSection = Array.from(this.config.keys()).find(s => s.startsWith(parent));
          if (parentFullSection) {
              const parentSettings = this.getAllVariantSettings(parentFullSection);
              for (const [key, value] of parentSettings.entries()) {
                  this.addPiece(key, value, variantName, variantPieces);
              }
          }
      }

      // Then, add/override with current variant's pieces
      for (const [key, value] of settings.entries()) {
        this.addPiece(key, value, variantName, variantPieces);
      }

      allPieces.push(...Array.from(variantPieces.values()));
      processedVariants.add(variantName);
    }

    const uniquePieces: Piece[] = [];
    const seen = new Set<string>();
    for (let i = allPieces.length - 1; i >= 0; i--) {
        const piece = allPieces[i];
        const identifier = `${piece.name}|${piece.variant}`;
        if (!seen.has(identifier)) {
            uniquePieces.unshift(piece);
            seen.add(identifier);
        }
    }

    return uniquePieces;
  }

  private addPiece(key: string, value: string, variantName: string, pieceMap: Map<string, Piece>): void {
    if (this.pieceKeys.has(key)) {
        let pieceName = key.charAt(0).toUpperCase() + key.slice(1);
        if (key.startsWith('customPiece')) {
          pieceName = `Custom Piece ${key.replace('customPiece', '')}`;
        }

        if (value.trim() === '-') {
          if (pieceMap.has(pieceName)) {
            pieceMap.delete(pieceName);
          }
          return;
        }

        let betza = '';
        if (value.includes(':')) {
          [, betza] = value.split(':', 2);
        } else {
          if (this.predefinedPieces.has(key)) {
            betza = this.predefinedPieces.get(key)!;
          }
        }

        if (betza) {
          pieceMap.set(pieceName, {
            name: pieceName,
            variant: variantName,
            betza: betza,
          });
        }
      }
  }
}
