import {
  BetzaDiagnostic,
  BetzaMovement,
  BetzaTerm,
  Move,
} from './types.js';

type Direction = { dx: number; dy: number };
type AtomVector = {
  readonly atom: string;
  readonly forward: number;
  readonly sideways: number;
};
type AtomDefinition = {
  readonly vectors: readonly AtomVector[];
  readonly rider: boolean;
};

const ATOMS: ReadonlyMap<string, AtomDefinition> = new Map([
  ['W', { vectors: [{ atom: 'W', forward: 1, sideways: 0 }], rider: false }],
  ['F', { vectors: [{ atom: 'F', forward: 1, sideways: 1 }], rider: false }],
  ['D', { vectors: [{ atom: 'D', forward: 2, sideways: 0 }], rider: false }],
  ['N', { vectors: [{ atom: 'N', forward: 2, sideways: 1 }], rider: false }],
  ['A', { vectors: [{ atom: 'A', forward: 2, sideways: 2 }], rider: false }],
  ['H', { vectors: [{ atom: 'H', forward: 3, sideways: 0 }], rider: false }],
  ['L', { vectors: [{ atom: 'L', forward: 3, sideways: 1 }], rider: false }],
  ['C', { vectors: [{ atom: 'C', forward: 3, sideways: 1 }], rider: false }],
  ['J', { vectors: [{ atom: 'J', forward: 3, sideways: 2 }], rider: false }],
  ['Z', { vectors: [{ atom: 'Z', forward: 3, sideways: 2 }], rider: false }],
  ['G', { vectors: [{ atom: 'G', forward: 3, sideways: 3 }], rider: false }],
  [
    'K',
    {
      vectors: [
        { atom: 'W', forward: 1, sideways: 0 },
        { atom: 'F', forward: 1, sideways: 1 },
      ],
      rider: false,
    },
  ],
  ['R', { vectors: [{ atom: 'W', forward: 1, sideways: 0 }], rider: true }],
  ['B', { vectors: [{ atom: 'F', forward: 1, sideways: 1 }], rider: true }],
  [
    'Q',
    {
      vectors: [
        { atom: 'W', forward: 1, sideways: 0 },
        { atom: 'F', forward: 1, sideways: 1 },
      ],
      rider: true,
    },
  ],
]);

const COMPOUND_ALIASES: ReadonlyMap<string, string> = new Map([
  ['E', 'RN'],
  ['M', 'FC'],
]);

const JUMPING_ATOMS = new Set(['N', 'C', 'L', 'Z', 'J']);
const KNOWN_MODIFIERS = new Set('mcpgnifbvhrls'.split(''));
const VERTICAL_MODIFIERS = 'fbvh';
const HORIZONTAL_MODIFIERS = 'rlsh';

interface WorkToken {
  readonly text: string;
  readonly index: number;
}

function tokenize(notation: string): WorkToken[] {
  const tokens: WorkToken[] = [];
  const regex = /[a-z]+|[A-Z]\d*/g;
  let match: RegExpExecArray | null;
  while ((match = regex.exec(notation)) !== null) {
    tokens.push({ text: match[0], index: match.index });
  }
  return tokens;
}

function warningsForUnsupportedCharacters(
  notation: string,
  tokens: readonly WorkToken[]
): BetzaDiagnostic[] {
  const covered = new Array<boolean>(notation.length).fill(false);
  for (const token of tokens) {
    for (let offset = 0; offset < token.text.length; offset += 1) {
      covered[token.index + offset] = true;
    }
  }

  const warnings: BetzaDiagnostic[] = [];
  for (let index = 0; index < notation.length; index += 1) {
    const character = notation[index];
    if (covered[index] || /\s/.test(character)) continue;
    warnings.push({
      message: `Unsupported Betza character "${character}" was ignored`,
      index,
      token: character,
    });
  }
  return warnings;
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

function directionalTokens(modifiers: string): string[] {
  const result: string[] = [];
  for (let index = 0; index < modifiers.length; index += 1) {
    const character = modifiers[index];
    const vertical = VERTICAL_MODIFIERS.includes(character);
    const horizontal = HORIZONTAL_MODIFIERS.includes(character);
    if (!vertical && !horizontal) continue;

    const next = modifiers[index + 1];
    const nextVertical =
      next !== undefined && VERTICAL_MODIFIERS.includes(next);
    const nextHorizontal =
      next !== undefined && HORIZONTAL_MODIFIERS.includes(next);
    const canCombine =
      next !== undefined &&
      (next === character ||
        (vertical && nextHorizontal) ||
        (horizontal && nextVertical));

    if (canCombine) {
      result.push(`${character}${next}`);
      index += 1;
    } else {
      result.push(character.repeat(2));
    }
  }
  return result;
}

/**
 * Expand original Betza directional modifiers for one atom vector.
 *
 * The mapping intentionally matches Fairy-Stockfish for the subset it
 * supports. It is part of the one general parser, not a separate FSF parser.
 */
function directionsForVector(
  vector: AtomVector,
  sourceDirections: readonly string[],
  splitOrthogonalDirections: boolean
): Direction[] {
  const directions = splitOrthogonalDirections
    ? sourceDirections.flatMap((value) =>
        value[0] !== value[1]
          ? [value[0].repeat(2), value[1].repeat(2)]
          : [value]
      )
    : [...sourceDirections];
  const hasDirection = (value: string): boolean => directions.includes(value);
  const unrestricted = directions.length === 0;
  const { forward, sideways } = vector;
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

function moveType(modifiers: string): Move['moveType'] {
  const quiet = modifiers.includes('m');
  const capture = modifiers.includes('c');
  if (quiet && !capture) return 'move';
  if (capture && !quiet) return 'capture';
  return 'move_capture';
}

function warningsForModifiers(
  modifiers: string,
  index: number
): BetzaDiagnostic[] {
  return [...modifiers]
    .filter((modifier) => !KNOWN_MODIFIERS.has(modifier))
    .map((modifier) => ({
      message: `Unsupported Betza modifier "${modifier}" was ignored`,
      index,
      token: modifier,
    }));
}

/**
 * Parse Betza notation into a reusable movement model.
 *
 * This is the single parser used by both the visualizer and the premove
 * generator. It intentionally remains permissive: unsupported fragments are
 * ignored and reported as warnings, matching the visualizer's historical
 * best-effort behavior. The parser can be extended with more original Betza or
 * XBetza syntax without introducing a consumer-specific parser.
 */
export function parseBetza(notation: string): BetzaMovement {
  const terms: BetzaTerm[] = [];
  const warnings: BetzaDiagnostic[] = [];
  const worklist = tokenize(notation);
  warnings.push(...warningsForUnsupportedCharacters(notation, worklist));
  let currentModifiers = '';
  let currentModifierIndex = 0;

  while (worklist.length > 0) {
    const token = worklist.shift()!;
    const text = token.text;

    if (text.toLowerCase() === text) {
      currentModifiers = text;
      currentModifierIndex = token.index;
      warnings.push(...warningsForModifiers(text, token.index));
      continue;
    }

    const match = /^([A-Z])(\d*)$/.exec(text);
    if (!match) continue;
    const [, letter, suffix] = match;

    // Original Betza's doubled-atom notation denotes an unlimited rider.
    if (suffix === '' && worklist[0]?.text === letter) {
      worklist.shift();
      worklist.unshift({ text: `${letter}0`, index: token.index });
      continue;
    }

    const expansion = COMPOUND_ALIASES.get(letter);
    if (expansion) {
      const expanded = suffix
        ? expansion.replace(/([A-Z])\d*/g, `$1${suffix}`)
        : expansion;
      const replacement: WorkToken[] = [];
      for (const expandedToken of tokenize(expanded)) {
        if (currentModifiers) {
          replacement.push({
            text: currentModifiers,
            index: currentModifierIndex,
          });
        }
        replacement.push({ text: expandedToken.text, index: token.index });
      }
      worklist.unshift(...replacement);
      currentModifiers = '';
      continue;
    }

    const definition = ATOMS.get(letter);
    if (!definition) {
      warnings.push({
        message: `Unsupported Betza atom "${letter}" was ignored`,
        index: token.index,
        token: letter,
      });
      // Keep pending modifiers. Expressions such as mXR therefore degrade to
      // mR, matching the project's established permissive behavior.
      continue;
    }

    const modifiers = currentModifiers;
    currentModifiers = '';
    const explicitlyRepeated = suffix !== '';
    const rider = definition.rider || explicitlyRepeated;
    const maxSteps: BetzaTerm['maxSteps'] = rider
      ? suffix && suffix !== '0'
        ? Math.max(1, Number.parseInt(suffix, 10))
        : 'unbounded'
      : 1;
    const parsedDirections = directionalTokens(modifiers);
    const commonMoveType = moveType(modifiers);
    const hopType: Move['hopType'] = modifiers.includes('p')
      ? 'p'
      : modifiers.includes('g')
        ? 'g'
        : null;

    for (const vector of definition.vectors) {
      const splitOrthogonalDirections =
        definition.vectors.length === 1 && vector.sideways === 0;
      terms.push({
        atom: vector.atom,
        atomCoords: { x: vector.forward, y: vector.sideways },
        directions: directionsForVector(
          vector,
          parsedDirections,
          splitOrthogonalDirections
        ),
        maxSteps,
        moveType: commonMoveType,
        hopType,
        jumpType: modifiers.includes('n')
          ? 'non-jumping'
          : JUMPING_ATOMS.has(vector.atom)
            ? 'jumping'
            : rider
              ? 'non-jumping'
              : 'jumping',
        initialOnly: modifiers.includes('i'),
        modifiers,
      });
    }
  }

  if (currentModifiers) {
    warnings.push({
      message: 'Betza modifiers without a following atom were ignored',
      index: currentModifierIndex,
      token: currentModifiers,
    });
  }

  return { notation, terms, warnings };
}

export function expandBetzaMovement(
  movement: BetzaMovement,
  boardSize?: number,
  infinityCap = 12
): Move[] {
  const moves: Move[] = [];
  for (const term of movement.terms) {
    const maxSteps =
      term.maxSteps === 'unbounded'
        ? boardSize
          ? Math.floor(boardSize / 2)
          : infinityCap
        : term.maxSteps;

    for (let step = 1; step <= maxSteps; step += 1) {
      for (const { dx, dy } of term.directions) {
        const move: Move = {
          x: dx * step,
          y: dy * step,
          moveType: term.moveType,
          hopType: term.hopType,
          jumpType: term.jumpType,
          atom: term.atom,
          atomCoords: {
            x: term.atomCoords.x,
            y: term.atomCoords.y,
          },
        };
        if (term.initialOnly) move.initialOnly = true;
        moves.push(move);
      }
    }
  }
  return moves;
}

export class BetzaParser {
  public readonly infinityCap = 12;

  public parseDetailed(notation: string): BetzaMovement {
    return parseBetza(notation);
  }

  public parse(notation: string, boardSize?: number): Move[] {
    return expandBetzaMovement(
      this.parseDetailed(notation),
      boardSize,
      this.infinityCap
    );
  }
}
