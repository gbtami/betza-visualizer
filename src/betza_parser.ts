import { Move } from './types.js';

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
        const newTokens = expansion.match(/[A-Z]\d*/g) || [];
        tokenWorklist.unshift(...newTokens);
        continue;
      }

      if (!this.atoms.has(letter)) continue;

      const atom = letter;
      const countStr = suffix;

      let moveType: Move['moveType'] = 'move_capture';
      if (currentMods.includes('m') && !currentMods.includes('c'))
        moveType = 'move';
      else if (currentMods.includes('c') && !currentMods.includes('m'))
        moveType = 'capture';
      else if (currentMods.includes('m') && currentMods.includes('c')) {
        moveType =
          currentMods.lastIndexOf('c') > currentMods.lastIndexOf('m')
            ? 'capture'
            : 'move';
      }

      const hopType: Move['hopType'] = currentMods.includes('p')
        ? 'p'
        : currentMods.includes('g')
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
        if (currentMods.includes('n')) {
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
        currentMods,
        atom
      );

      for (let i = 1; i <= maxSteps; i++) {
        for (const { dx, dy } of allowedDirections) {
          const move: Move = {
            x: dx * i,
            y: dy * i,
            moveType,
            hopType,
            jumpType,
            atom,
          };
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
    // Fibnif special case: fbN should be treated as ffN union bbN
    if (mods === 'fb' && atom === 'N') {
      const ffDirs = this._filterDirections(directions, 'ff', atom);
      const bbDirs = this._filterDirections(directions, 'bb', atom);
      return new Set([...ffDirs, ...bbDirs]);
    }

    if (mods.includes('s')) mods += 'lr';
    if (mods.includes('v')) mods += 'fb';

    const dirMods = mods
      .split('')
      .filter((c) => 'fblr'.includes(c))
      .join('');

    const { x: atomX, y: atomY } = this.atoms.get(atom)!;
    const isOrthogonal = atomX * atomY === 0;

    let filtered: Set<{ dx: number; dy: number }>;

    if (!dirMods) {
      filtered = directions;
    } else {
      filtered = new Set();
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
    }

    const constrainDoubleVertical = mods.includes('ff') || mods.includes('bb');
    const constrainDoubleHorizontal =
      mods.includes('ll') || mods.includes('rr');

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
