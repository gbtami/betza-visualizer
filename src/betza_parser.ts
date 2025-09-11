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
      const fDirs = this._filterDirections(directions, 'f' + otherMods, atom);
      const bDirs = this._filterDirections(directions, 'b' + otherMods, atom);
      return new Set([...fDirs, ...bDirs]);
    }
    if (mods.includes('s')) {
      const otherMods = mods.replace('s', '');
      const lDirs = this._filterDirections(directions, 'l' + otherMods, atom);
      const rDirs = this._filterDirections(directions, 'r' + otherMods, atom);
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

    const filtered: Set<{ dx: number; dy: number }> = new Set();
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
