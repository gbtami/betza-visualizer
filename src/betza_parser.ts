import {
  BetzaDiagnostic,
  BetzaMovement,
  BetzaParseResult,
  BetzaTerm,
  Move,
} from './types.js';

export class BetzaParser {
  private readonly atoms: Map<string, { x: number; y: number }> = new Map([
    ['W', { x: 1, y: 0 }],
    ['F', { x: 1, y: 1 }],
    ['D', { x: 2, y: 0 }],
    ['N', { x: 2, y: 1 }],
    ['A', { x: 2, y: 2 }],
    ['H', { x: 3, y: 0 }],
    ['C', { x: 3, y: 1 }],
    ['Z', { x: 3, y: 2 }],
    ['G', { x: 3, y: 3 }],
  ]);

  private readonly compoundAliases: Map<string, string> = new Map([
    ['B', 'F0'],
    ['R', 'W0'],
    ['Q', 'W0F0'],
    ['K', 'W1F1'],
    ['E', 'RN'],
    ['J', 'AD'],
    ['M', 'FC'],
  ]);
  public readonly infinityCap = 12;

  public parseDetailed(notation: string): BetzaParseResult<BetzaMovement> {
    return parseBetza(notation);
  }
  private readonly jumpingAtoms: Set<string> = new Set(['N', 'C', 'Z']);

  public parse(notation: string, boardSize?: number): Move[] {
    const moves: Move[] = [];
    const tokenWorklist: string[] = notation.match(/[a-z]+|[A-Z]\d*/g) || [];
    let currentMods = '';

    while (tokenWorklist.length > 0) {
      const token = tokenWorklist.shift()!;
      if (token.toLowerCase() === token) {
        currentMods = token;
        continue;
      }
      const match = token.match(/([A-Z])(\d*)/);
      if (!match) continue;
      const [, letter, suffix] = match;

      // Nightrider shorthand: 'NN' -> treat as rider 'N0'
      if (suffix === '' && tokenWorklist[0] === letter) {
        tokenWorklist.shift(); // consume the second 'N'
        tokenWorklist.unshift(`${letter}0`); // push rider form
        continue;
      }

      if (this.compoundAliases.has(letter)) {
        let expansion = this.compoundAliases.get(letter)!;
        if (suffix) {
          expansion = expansion.replace(/([A-Z])\d*/g, `$1${suffix}`);
        }
        let newTokens: string[] = expansion.match(/[A-Z]\d*/g) || [];

        if (currentMods) {
          const prefixedTokens: string[] = [];
          for (const t of newTokens) {
            prefixedTokens.push(currentMods, t);
          }
          newTokens = prefixedTokens;
        }

        tokenWorklist.unshift(...newTokens);
        currentMods = '';
        continue;
      }

      if (!this.atoms.has(letter)) continue;

      const modsForThisAtom = currentMods;
      currentMods = '';

      const atom = letter;
      const countStr = suffix;

      let moveType: Move['moveType'] = 'move_capture';
      if (modsForThisAtom.includes('m') && !modsForThisAtom.includes('c'))
        moveType = 'move';
      else if (modsForThisAtom.includes('c') && !modsForThisAtom.includes('m'))
        moveType = 'capture';
      else if (modsForThisAtom.includes('m') && modsForThisAtom.includes('c')) {
        moveType =
          modsForThisAtom.lastIndexOf('c') > modsForThisAtom.lastIndexOf('m')
            ? 'capture'
            : 'move';
      }

      const hopType: Move['hopType'] = modsForThisAtom.includes('p')
        ? 'p'
        : modsForThisAtom.includes('g')
          ? 'g'
          : null;

      // Determine jump_type based on whether it's a rider or a leaper
      const isRider = countStr === '0';
      let jumpType: Move['jumpType'];
      if (isRider) {
        // Rider type depends on the base atom
        if (this.jumpingAtoms.has(atom)) {
          jumpType = 'jumping';
        } else {
          jumpType = 'non-jumping';
        }
      } else {
        // Leapers are jumping by default, unless they are lame (n)
        jumpType = 'jumping';
        if (modsForThisAtom.includes('n')) {
          jumpType = 'non-jumping';
        }
      }

      let maxSteps: number;
      if (countStr === '0') {
        maxSteps = boardSize ? Math.floor(boardSize / 2) : this.infinityCap;
      } else if (countStr === '') {
        maxSteps = 1;
      } else {
        maxSteps = parseInt(countStr);
      }
      const { x: atomX, y: atomY } = this.atoms.get(atom)!;

      const baseDirections = this._getDirections(atomX, atomY);
      const allowedDirections = this._filterDirections(
        baseDirections,
        modsForThisAtom,
        atom
      );

      const isInitialOnly = modsForThisAtom.includes('i');

      for (let i = 1; i <= maxSteps; i++) {
        for (const { dx, dy } of allowedDirections) {
          const move: Move = {
            x: dx * i,
            y: dy * i,
            moveType,
            hopType,
            jumpType,
            atom,
            atomCoords: { x: atomX, y: atomY },
          };
          if (isInitialOnly) {
            move.initialOnly = true;
          }
          moves.push(move);
        }
      }
    }
    return moves;
  }

  private _getDirections(
    x: number,
    y: number
  ): Set<{ dx: number; dy: number }> {
    const directions = new Set<string>();
    for (const sx of [-1, 1]) {
      for (const sy of [-1, 1]) {
        directions.add(`${x * sx},${y * sy}`);
        directions.add(`${y * sx},${x * sy}`);
      }
    }
    return new Set(
      Array.from(directions).map((s) => {
        const [dx, dy] = s.split(',').map(Number);
        return { dx, dy };
      })
    );
  }

  private _filterDirections(
    directions: Set<{ dx: number; dy: number }>,
    mods: string,
    atom: string
  ): Set<{ dx: number; dy: number }> {
    // 1. Handle union-style modifiers recursively.
    if (mods.includes('v')) {
      const otherMods = mods.replace('v', '');
      const fDirs = this._filterDirections(
        directions,
        'f' + otherMods,
        atom
      );
      const bDirs = this._filterDirections(
        directions,
        'b' + otherMods,
        atom
      );
      return new Set([...fDirs, ...bDirs]);
    }
    if (mods.includes('s')) {
      const otherMods = mods.replace('s', '');
      const lDirs = this._filterDirections(
        directions,
        'l' + otherMods,
        atom
      );
      const rDirs = this._filterDirections(
        directions,
        'r' + otherMods,
        atom
      );
      return new Set([...lDirs, ...rDirs]);
    }

    const doubledMods = mods.match(/ff|bb|ll|rr/g) || [];
    if (doubledMods.length > 1) {
      const totalDirs = new Set<{ dx: number; dy: number }>();
      for (const dMod of doubledMods) {
        const filtered = this._filterDirections(directions, dMod, atom);
        for (const dir of filtered) {
          totalDirs.add(dir);
        }
      }
      return totalDirs;
    }

    // 2. Base case: process a modifier string without union-style modifiers.
    const { x: atomX, y: atomY } = this.atoms.get(atom)!;
    const isHippogonal = atomX !== atomY && atomX * atomY !== 0;

    if (isHippogonal) {
      const dirModsOnly = mods.match(/[fblr]/g)?.join('') || '';
      if (dirModsOnly.length === 1) {
        mods = mods.replace(dirModsOnly, dirModsOnly.repeat(2));
      }
    }

    const has_h = mods.includes('h');
    if (has_h) {
      mods = mods.replace('h', '');
    }

    if (mods === 'fb' && atom === 'N') {
      const fDirs = this._filterDirections(directions, 'f', atom);
      const bDirs = this._filterDirections(directions, 'b', atom);
      return new Set([...fDirs, ...bDirs]);
    }

    const dirMods = mods
      .split('')
      .filter((c) => 'fblr'.includes(c))
      .join('');
    const isOrthogonal = atomX * atomY === 0;

    if (!dirMods) {
      return directions;
    }

    let filtered: Set<{ dx: number; dy: number }> = new Set();
    const hasVMod = dirMods.includes('f') || dirMods.includes('b');
    const hasHMod = dirMods.includes('l') || dirMods.includes('r');

    for (const { dx, dy } of directions) {
      const vValid =
        !hasVMod ||
        (dirMods.includes('f') && dy > 0) ||
        (dirMods.includes('b') && dy < 0);
      const hValid =
        !hasHMod ||
        (dirMods.includes('l') && dx < 0) ||
        (dirMods.includes('r') && dx > 0);

      const isUnion = isOrthogonal && hasVMod && hasHMod;
      if (isUnion) {
        if (vValid || hValid) {
          filtered.add({ dx, dy });
        }
      } else {
        if (vValid && hValid) {
          filtered.add({ dx, dy });
        }
      }
    }

    const constrainDoubleVertical =
      (mods.includes('ff') || mods.includes('bb')) && !has_h;
    const constrainDoubleHorizontal =
      (mods.includes('ll') || mods.includes('rr')) && !has_h;

    if (!constrainDoubleVertical && !constrainDoubleHorizontal) {
      return filtered;
    }

    const finalFiltered = new Set<{ dx: number; dy: number }>();
    for (const { dx, dy } of filtered) {
      let isValid = true;
      if (constrainDoubleVertical && Math.abs(dy) <= Math.abs(dx)) {
        isValid = false;
      }
      if (constrainDoubleHorizontal && Math.abs(dx) <= Math.abs(dy)) {
        isValid = false;
      }

      if (isValid) {
        finalFiltered.add({ dx, dy });
      }
    }

    return finalFiltered;
  }
}


type Direction = { dx: number; dy: number };
type FsfAtomVector = { forward: number; sideways: number };

const FSF_LEAPER_ATOMS: ReadonlyMap<string, readonly FsfAtomVector[]> = new Map([
  ['W', [{ forward: 1, sideways: 0 }]],
  ['F', [{ forward: 1, sideways: 1 }]],
  ['D', [{ forward: 2, sideways: 0 }]],
  ['N', [{ forward: 2, sideways: 1 }]],
  ['A', [{ forward: 2, sideways: 2 }]],
  ['H', [{ forward: 3, sideways: 0 }]],
  ['L', [{ forward: 3, sideways: 1 }]],
  ['C', [{ forward: 3, sideways: 1 }]],
  ['J', [{ forward: 3, sideways: 2 }]],
  ['Z', [{ forward: 3, sideways: 2 }]],
  ['G', [{ forward: 3, sideways: 3 }]],
  [
    'K',
    [
      { forward: 1, sideways: 0 },
      { forward: 1, sideways: 1 },
    ],
  ],
]);

const FSF_RIDER_ATOMS: ReadonlyMap<string, readonly FsfAtomVector[]> = new Map([
  ['R', [{ forward: 1, sideways: 0 }]],
  ['B', [{ forward: 1, sideways: 1 }]],
  [
    'Q',
    [
      { forward: 1, sideways: 0 },
      { forward: 1, sideways: 1 },
    ],
  ],
]);

const FSF_VERTICAL_MODIFIERS = 'fbvh';
const FSF_HORIZONTAL_MODIFIERS = 'rlsh';

function diagnostic(message: string, index: number, token?: string): BetzaDiagnostic {
  return { message, index, token };
}

function uniqueDirections(directions: Iterable<Direction>): Direction[] {
  const result: Direction[] = [];
  const seen = new Set<string>();
  for (const direction of directions) {
    const key = `${direction.dx},${direction.dy}`;
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(direction);
  }
  return result;
}

function fsfMoveType(modalities: readonly ('m' | 'c')[]): BetzaTerm['moveType'] {
  if (!modalities.length) return 'move_capture';
  const quiet = modalities.includes('m');
  const capture = modalities.includes('c');
  if (quiet && capture) return 'move_capture';
  return quiet ? 'move' : 'capture';
}

function fsfDirections(
  atom: FsfAtomVector,
  sourceDirections: readonly string[],
  splitOrthogonalDirections: boolean
): Direction[] {
  const directions = splitOrthogonalDirections
    ? sourceDirections.flatMap((value) =>
        value[0] !== value[1] ? [value[0].repeat(2), value[1].repeat(2)] : [value]
      )
    : [...sourceDirections];
  const hasDirection = (value: string): boolean => directions.includes(value);
  const unrestricted = directions.length === 0;
  const { forward, sideways } = atom;
  const result: Direction[] = [];

  if (
    unrestricted ||
    ['ff', 'vv', 'rf', 'rv', 'fh', 'rh', 'hr'].some(hasDirection)
  ) {
    result.push({ dx: sideways, dy: forward });
  }
  if (
    unrestricted ||
    ['bb', 'vv', 'lb', 'lv', 'bh', 'lh', 'hr'].some(hasDirection)
  ) {
    result.push({ dx: -sideways, dy: -forward });
  }
  if (
    unrestricted ||
    ['rr', 'ss', 'br', 'bs', 'bh', 'rh', 'hr'].some(hasDirection)
  ) {
    result.push({ dx: forward, dy: -sideways });
  }
  if (
    unrestricted ||
    ['ll', 'ss', 'fl', 'fs', 'fh', 'lh', 'hr'].some(hasDirection)
  ) {
    result.push({ dx: -forward, dy: sideways });
  }
  if (
    unrestricted ||
    ['rr', 'ss', 'fr', 'fs', 'fh', 'rh', 'hl'].some(hasDirection)
  ) {
    result.push({ dx: forward, dy: sideways });
  }
  if (
    unrestricted ||
    ['ll', 'ss', 'bl', 'bs', 'bh', 'lh', 'hl'].some(hasDirection)
  ) {
    result.push({ dx: -forward, dy: -sideways });
  }
  if (
    unrestricted ||
    ['bb', 'vv', 'rb', 'rv', 'bh', 'rh', 'hl'].some(hasDirection)
  ) {
    result.push({ dx: sideways, dy: -forward });
  }
  if (
    unrestricted ||
    ['ff', 'vv', 'lf', 'lv', 'fh', 'lh', 'hl'].some(hasDirection)
  ) {
    result.push({ dx: -sideways, dy: forward });
  }

  return uniqueDirections(result);
}

export interface ParseBetzaOptions {
  /** Return an error when Fairy-Stockfish would ignore any input fragment. */
  readonly strict?: boolean;
}

/**
 * Parse the Betza subset accepted by Fairy-Stockfish's `from_betza()` parser.
 *
 * The default mode intentionally mirrors Fairy-Stockfish: unknown characters
 * are ignored without resetting pending modifiers. Diagnostics are returned as
 * warnings so callers can explain what the engine ignored. Use
 * `parseBetzaStrict()` only for authoring or debugging tools.
 */
export function parseBetza(
  notation: string,
  options: ParseBetzaOptions = {}
): BetzaParseResult<BetzaMovement> {
  const terms: BetzaTerm[] = [];
  const warnings: BetzaDiagnostic[] = [];
  const modalities: ('m' | 'c')[] = [];
  const preliminaryDirections: string[] = [];
  let hopper = false;
  let lame = false;
  let initialOnly = false;
  let distance = 0;
  let modifiers = '';
  let pendingStart: number | undefined;

  const markPending = (index: number): void => {
    if (pendingStart === undefined) pendingStart = index;
  };

  const resetState = (): void => {
    modalities.length = 0;
    preliminaryDirections.length = 0;
    hopper = false;
    lame = false;
    initialOnly = false;
    distance = 0;
    modifiers = '';
    pendingStart = undefined;
  };

  for (let index = 0; index < notation.length; index += 1) {
    const char = notation[index];

    if (char === 'm' || char === 'c') {
      markPending(index);
      modalities.push(char);
      modifiers += char;
      continue;
    }

    if (char === 'p' || char === 'g') {
      markPending(index);
      hopper = true;
      modifiers += char;
      if (char === 'g') distance = 1;
      continue;
    }

    if (char === 'n') {
      markPending(index);
      lame = true;
      modifiers += char;
      continue;
    }

    if (char === 'i') {
      markPending(index);
      initialOnly = true;
      modifiers += char;
      continue;
    }

    const vertical = FSF_VERTICAL_MODIFIERS.includes(char);
    const horizontal = FSF_HORIZONTAL_MODIFIERS.includes(char);
    if (vertical || horizontal) {
      markPending(index);
      const next = notation[index + 1];
      const nextVertical = next !== undefined && FSF_VERTICAL_MODIFIERS.includes(next);
      const nextHorizontal = next !== undefined && FSF_HORIZONTAL_MODIFIERS.includes(next);
      const canCombine =
        next !== undefined &&
        (next === char || (vertical && nextHorizontal) || (horizontal && nextVertical));

      if (canCombine) {
        preliminaryDirections.push(`${char}${next}`);
        modifiers += `${char}${next}`;
        index += 1;
      } else {
        preliminaryDirections.push(char.repeat(2));
        modifiers += char;
      }
      continue;
    }

    const leaperAtoms = FSF_LEAPER_ATOMS.get(char);
    const riderAtoms = FSF_RIDER_ATOMS.get(char);
    const atoms = riderAtoms ?? leaperAtoms;
    if (!atoms) {
      warnings.push(
        diagnostic(
          `Ignored by Fairy-Stockfish's Betza parser: "${char}"`,
          index,
          char
        )
      );
      continue;
    }

    let atomIsRider = riderAtoms !== undefined;
    const next = notation[index + 1];
    if (next !== undefined && (/\d/.test(next) || next === char)) {
      atomIsRider = true;
      if (/\d/.test(next)) {
        distance = Number(next);
        index += 1;
      }
    }

    if (!atomIsRider && lame) distance = -1;
    const splitOrthogonalDirections = atoms.length === 1 && atoms[0].sideways === 0;
    const moveType = fsfMoveType(modalities);

    for (const atom of atoms) {
      const directions = fsfDirections(
        atom,
        preliminaryDirections,
        splitOrthogonalDirections
      );
      const isVectorRider = atomIsRider || hopper;
      const maxSteps = isVectorRider
        ? distance > 0
          ? distance
          : 'unbounded'
        : 1;
      const vectorJumps = Math.max(atom.forward, atom.sideways) > 1;

      terms.push({
        atom: char,
        atomCoords: { x: atom.sideways, y: atom.forward },
        directions,
        maxSteps,
        moveType,
        hopType: hopper ? (modifiers.includes('p') ? 'p' : 'g') : null,
        jumpType: lame ? 'non-jumping' : vectorJumps ? 'jumping' : 'non-jumping',
        initialOnly,
        modifiers,
      });
    }

    resetState();
  }

  if (pendingStart !== undefined) {
    warnings.push(
      diagnostic(
        'Betza modifiers without a following supported atom are ignored by Fairy-Stockfish',
        pendingStart,
        notation.slice(pendingStart)
      )
    );
  }

  if (options.strict && warnings.length) return { ok: false, errors: warnings };
  return { ok: true, value: { notation, terms }, warnings };
}

export function parseBetzaStrict(notation: string): BetzaParseResult<BetzaMovement> {
  return parseBetza(notation, { strict: true });
}
