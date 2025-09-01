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

  public parse(notation: string): Move[] {
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

      let jumpType: Move['jumpType'] = 'normal';
      if (currentMods.includes('n')) jumpType = 'non-jumping';
      else if (currentMods.includes('j')) jumpType = 'jumping';

      const maxSteps =
        countStr === ''
          ? 1
          : countStr === '0'
            ? this.infinityCap
            : parseInt(countStr);
      const { x: atomX, y: atomY } = this.atoms.get(atom)!;

      const baseDirections = this._getDirections(atomX, atomY);
      const allowedDirections = this._filterDirections(
        baseDirections,
        currentMods
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
    mods: string
  ): Set<{ dx: number; dy: number }> {
    if (mods.includes('s')) mods += 'lr';
    if (mods.includes('v')) mods += 'fb';
    const dirMods = mods
      .split('')
      .filter((c) => 'fblr'.includes(c))
      .join('');
    if (!dirMods) return directions;

    const constrainF = dirMods.includes('f') && !dirMods.includes('b');
    const constrainB = dirMods.includes('b') && !dirMods.includes('f');
    const constrainL = dirMods.includes('l') && !dirMods.includes('r');
    const constrainR = dirMods.includes('r') && !dirMods.includes('l');

    const constrainDoubleVertical = mods.includes('ff') || mods.includes('bb');
    const constrainDoubleHorizontal =
      mods.includes('ll') || mods.includes('rr');

    const filtered = new Set<{ dx: number; dy: number }>();
    for (const { dx, dy } of directions) {
      let isValid = true;
      if (constrainF && dy <= 0) isValid = false;
      if (constrainB && dy >= 0) isValid = false;
      if (constrainL && dx >= 0) isValid = false;
      if (constrainR && dx <= 0) isValid = false;
      if (constrainDoubleVertical && Math.abs(dy) <= Math.abs(dx))
        isValid = false;
      if (constrainDoubleHorizontal && Math.abs(dx) <= Math.abs(dy))
        isValid = false;

      if (isValid) filtered.add({ dx, dy });
    }
    return filtered;
  }
}
