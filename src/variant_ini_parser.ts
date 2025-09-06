import { Piece } from './types';

// A simple INI parser that is sufficient for the variants.ini format.
// It supports sections, key-value pairs, and comments starting with # or ;.
// It does not support multi-line values or other advanced INI features.
const parseIni = (data: string): Record<string, Record<string, string>> => {
  const result: Record<string, Record<string, string>> = {};
  let currentSection: string | null = null;

  for (const line of data.split(/[\r\n]+/)) {
    const trimmedLine = line.trim();
    if (!trimmedLine || trimmedLine.startsWith('#') || trimmedLine.startsWith(';')) {
      continue;
    }

    const sectionMatch = trimmedLine.match(/^\[(.+)\]$/);
    if (sectionMatch) {
      currentSection = sectionMatch[1];
      result[currentSection] = {};
    } else if (currentSection) {
      const keyValueMatch = trimmedLine.match(/^([^=]+)=(.*)$/);
      if (keyValueMatch) {
        const key = keyValueMatch[1].trim();
        const value = keyValueMatch[2].trim();
        result[currentSection][key] = value;
      }
    }
  }

  return result;
};

const titleCase = (s: string) =>
  s.replace(/^_*(.)|_+(.)/g, (s, c, d) => c ? c.toUpperCase() : ' ' + d.toUpperCase());

export class VariantIniParser {
  private static PREDEFINED_PIECES: Record<string, [string, string]> = {
        'p': ["Pawn", "fmWfceF"], 'n': ["Knight", "N"], 'b': ["Bishop", "B"], 'r': ["Rook", "R"],
        'q': ["Queen", "Q"], 'f': ["Fers", "F"], 'a': ["Alfil", "A"], 'h': ["Horse", "nN"],
        'e': ["Elephant", "nA"], 'w': ["Wazir", "W"], 'd': ["Dragon", "RF"], 'c': ["Cannon", "mRcpR"],
        'k': ["King", "K"], 'g': ["Gold", "WfF"], 's': ["Silver", "FfW"], 'l': ["Lance", "fR"],
        'z': ["Janggi Elephant", "nZ"], 'u': ["Janggi Cannon", "pR"], 't': ["Soldier", "fsW"],
        'v': ["Archbishop", "BN"], 'm': ["Chancellor", "RN"]
    };

  private config: Record<string, Record<string, string>>;
  private catalogByVariant: Record<string, Piece[]>;

  constructor(iniContent: string, pieceCatalog: Piece[]) {
    const cleanedContent = this._cleanIniContent(iniContent);
    this.config = parseIni(cleanedContent);

    this.catalogByVariant = {};
    for (const piece of pieceCatalog) {
      const variant = piece.variant;
      if (!this.catalogByVariant[variant]) {
        this.catalogByVariant[variant] = [];
      }
      this.catalogByVariant[variant].push(piece);
    }
  }

  private _cleanIniContent(iniContent: string): string {
    const lines = iniContent.split('\n');
    let firstSectionIndex = -1;
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].trim().startsWith('[') && lines[i].trim().endsWith(']')) {
        firstSectionIndex = i;
        break;
      }
    }

    if (firstSectionIndex === -1) {
      return "";
    }

    return lines.slice(firstSectionIndex).join('\n');
  }

  private _getInheritedPieces(parentVariantName: string): Piece[] {
    let parentSectionName: string | null = null;
    for (const section in this.config) {
      if (section.split(':', 1)[0] === parentVariantName) {
        parentSectionName = section;
        break;
      }
    }

    if (parentSectionName) {
      return this.parseVariant(parentSectionName);
    }

    return this.catalogByVariant[parentVariantName] || [];
  }

  private parseVariant(sectionName: string): Piece[] {
    const [variantName, parentName] = sectionName.split(':', 2);

    let pieces: Piece[] = [];
    if (parentName) {
      pieces = this._getInheritedPieces(parentName);
    } else if (this.catalogByVariant[variantName]) {
      pieces = this.catalogByVariant[variantName];
    }

    // Make a copy to avoid modifying the catalog
    pieces = pieces.map(p => ({ ...p, variant: variantName }));

    if (this.config[sectionName]) {
      const settings = this.config[sectionName];

      const removals = new Set<string>();
      for (const key in settings) {
        if (settings[key]?.trim() === '-') {
          removals.add(key.toLowerCase().replace(/ /g, ''));
        }
      }
      pieces = pieces.filter(p => !removals.has(p.name.toLowerCase().replace(/ /g, '')));

      for (const key in settings) {
        const value = settings[key];
        if (!value || value.trim() === '-') {
          continue;
        }

        if (value.includes(':')) {
          const [, betza] = value.split(':', 2);
          const pieceNameKey = key.toLowerCase().replace(/ /g, '');

          const isCustom = key.startsWith('customPiece');
          const pieceName = isCustom ? `Custom Piece ${key.replace('customPiece', '')}` : key;

          let found = false;
          for (const piece of pieces) {
            if (piece.name.toLowerCase().replace(/ /g, '') === pieceNameKey) {
              piece.betza = betza;
              found = true;
              break;
            }
          }

          if (!found) {
            pieces.push({
              name: pieceName,
              variant: variantName,
              betza: betza,
            });
          }
        } else {
            const pieceChar = value.trim();
            if (pieceChar in VariantIniParser.PREDEFINED_PIECES) {
                const [officialName, betza] = VariantIniParser.PREDEFINED_PIECES[pieceChar];
                const pieceName = officialName;

                let found = false;
                for (const piece of pieces) {
                    if (piece.name.toLowerCase().replace(/ /g, '') === pieceName.toLowerCase().replace(/ /g, '')) {
                        piece.betza = betza;
                        found = true;
                        break;
                    }
                }

                if (!found) {
                    pieces.push({
                        name: pieceName,
                        variant: variantName,
                        betza: betza,
                    });
                }
            }
        }
      }
    }

    return pieces;
  }

  public parse(): Piece[] {
    let allPieces: Piece[] = [];
    for (const sectionName in this.config) {
      const pieces = this.parseVariant(sectionName);
      allPieces.push(...pieces);
    }

    const uniquePieces: Piece[] = [];
    const seen = new Set<string>();
    for (let i = allPieces.length - 1; i >= 0; i--) {
      const piece = allPieces[i];
      const identifier = `${piece.name}|${piece.variant}`;
      if (!seen.has(identifier)) {
        uniquePieces.push(piece);
        seen.add(identifier);
      }
    }

    return uniquePieces.reverse();
  }
}
