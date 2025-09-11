import { Piece } from './types.js';

// A simple INI parser that is sufficient for the variants.ini format.
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

type VariantProperties = {
    double_step: boolean;
};

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
  private variantProperties: Record<string, VariantProperties>;
  private parsedVariantsCache: Record<string, [Piece[], VariantProperties]> = {};

  constructor(iniContent: string, pieceCatalog: Piece[], variantProperties: Record<string, VariantProperties>) {
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
    this.variantProperties = variantProperties;
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

  private parseVariant(sectionName: string): [Piece[], VariantProperties] {
    if (this.parsedVariantsCache[sectionName]) {
        return this.parsedVariantsCache[sectionName];
    }

    const [variantName, parentName] = sectionName.split(':', 2);

    let parentPieces: Piece[] = [];
    let parentProps: VariantProperties = { double_step: false };

    if (parentName) {
        let parentSectionName: string | null = null;
        for (const section in this.config) {
            if (section.split(':', 1)[0] === parentName) {
                parentSectionName = section;
                break;
            }
        }

        if (parentSectionName) {
            [parentPieces, parentProps] = this.parseVariant(parentSectionName);
        } else {
            parentPieces = this.catalogByVariant[parentName] || [];
            parentProps = this.variantProperties[parentName] || { double_step: false };
        }
    } else {
        parentPieces = this.catalogByVariant[variantName] || [];
        parentProps = this.variantProperties[variantName] || { double_step: false };
    }

    let pieces: Piece[] = parentPieces.map(p => ({ ...p, variant: variantName }));
    let props: VariantProperties = { ...parentProps };

    if (this.config[sectionName]) {
        const settings = this.config[sectionName];

        if (settings['doubleStep']) {
            props.double_step = settings['doubleStep'].toLowerCase() === 'true';
        }

        const removals = new Set<string>();
        for (const key in settings) {
            if (settings[key]?.trim() === '-') {
                removals.add(key.toLowerCase().replace(/ /g, ''));
            }
        }
        pieces = pieces.filter(p => !removals.has(p.name.toLowerCase().replace(/ /g, '')));

        for (const key in settings) {
            const value = settings[key];
            if (!value || value.trim() === '-' || ['promotedpiecetype', 'doublestep'].includes(key.toLowerCase())) {
                continue;
            }

            if (value.includes(':')) {
                const [pieceChar, betza] = value.split(':', 2);
                const pieceNameKey = key.toLowerCase().replace(/ /g, '');
                const isCustom = key.startsWith('customPiece');
                const variantNameTitle = variantName.charAt(0).toUpperCase() + variantName.slice(1);
                const pieceName = isCustom ? `${variantNameTitle}-${pieceChar}` : titleCase(key);

                let found = false;
                for (const piece of pieces) {
                    if (piece.name.toLowerCase().replace(/ /g, '') === pieceNameKey) {
                        piece.betza = betza;
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    pieces.push({ name: pieceName, variant: variantName, betza: betza });
                }
            } else {
                const pieceChar = value.trim();
                if (pieceChar in VariantIniParser.PREDEFINED_PIECES) {
                    const [officialName, betza] = VariantIniParser.PREDEFINED_PIECES[pieceChar];
                    let found = false;
                    for (const piece of pieces) {
                        if (piece.name.toLowerCase().replace(/ /g, '') === officialName.toLowerCase()) {
                            piece.betza = betza;
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        pieces.push({ name: officialName, variant: variantName, betza: betza });
                    }
                }
            }
        }
    }

    if (props.double_step) {
        for (const piece of pieces) {
            if (piece.name.toLowerCase() === 'pawn' && !piece.betza.includes('imfnA')) {
                piece.betza += 'imfnA';
            }
        }
    }

    this.parsedVariantsCache[sectionName] = [pieces, props];
    return [pieces, props];
  }

  public parse(): Piece[] {
    let allPieces: Piece[] = [];
    for (const sectionName in this.config) {
      const [pieces, ] = this.parseVariant(sectionName);
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

    return uniquePieces.reverse().sort((a, b) => {
        if (a.variant < b.variant) return -1;
        if (a.variant > b.variant) return 1;
        if (a.name < b.name) return -1;
        if (a.name > b.name) return 1;
        return 0;
    });
  }
}
