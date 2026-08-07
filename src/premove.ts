import { parseBetza } from './betza_parser.js';
import {
  BetzaMovement,
  BetzaPosition,
  BetzaPremove,
  BetzaPremoveContext,
} from './types.js';

function isInsideBoard(
  x: number,
  y: number,
  context: BetzaPremoveContext
): boolean {
  return (
    x >= 0 && x < context.board.width && y >= 0 && y < context.board.height
  );
}

/**
 * Produce a conservative premove movement envelope from the full Betza model.
 *
 * Occupancy, capture modality, intermediate blockers, hopper screens,
 * initial-only restrictions, check and variant-level legality are deliberately
 * ignored. The opponent may change those facts before the premove executes,
 * and the authoritative pyffish server validates the eventual move.
 */
export function betzaPremoveDestinations(
  movement: BetzaMovement,
  context: BetzaPremoveContext
): BetzaPosition[] {
  const [originX, originY] = context.origin;
  if (!isInsideBoard(originX, originY, context)) return [];

  const destinations: BetzaPosition[] = [];
  const seen = new Set<string>();
  const colorFactor = context.color === 'white' ? 1 : -1;

  for (const term of movement.terms) {
    for (const direction of term.directions) {
      const dx = direction.dx * colorFactor;
      const dy = direction.dy * colorFactor;
      // A hurdle can appear anywhere on the ray after the opponent's move, so
      // hopper geometry is deliberately widened to the whole board ray.
      const maxSteps =
        term.hopType || term.maxSteps === 'unbounded'
          ? Number.POSITIVE_INFINITY
          : term.maxSteps;

      for (let step = 1; step <= maxSteps; step += 1) {
        const x = originX + dx * step;
        const y = originY + dy * step;
        if (!isInsideBoard(x, y, context)) break;

        const key = `${x},${y}`;
        if (seen.has(key)) continue;
        seen.add(key);
        destinations.push([x, y]);
      }
    }
  }

  return destinations;
}

export function createBetzaPremove(notation: string): BetzaPremove {
  const movement = parseBetza(notation);
  return (context) => betzaPremoveDestinations(movement, context);
}
