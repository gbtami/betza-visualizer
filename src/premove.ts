import { parseBetza } from './betza_parser.js';
import {
  BetzaMovement,
  BetzaParseResult,
  BetzaPosition,
  BetzaPremove,
  BetzaPremoveContext,
} from './types.js';

function isInsideBoard(
  x: number,
  y: number,
  context: BetzaPremoveContext
): boolean {
  return x >= 0 && x < context.board.width && y >= 0 && y < context.board.height;
}

/**
 * Produce a conservative premove movement envelope.
 *
 * Occupancy, capture modality, intermediate blockers, hopper screens,
 * initial-only restrictions, check and all variant-level legality are ignored
 * deliberately. The opponent may change those facts before the premove is
 * executed; the authoritative game server validates the eventual move.
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
      // A hopper's hurdle may be on any square along its vector after the
      // opponent's move, so even a grasshopper's one-square post-hurdle
      // distance becomes an unbounded conservative premove ray.
      const maxSteps =
        term.hopType || term.maxSteps === 'unbounded' ? Infinity : term.maxSteps;

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

export function createBetzaPremove(
  notation: string
): BetzaParseResult<BetzaPremove> {
  const parsed = parseBetza(notation);
  if (!parsed.ok) return parsed;
  return {
    ok: true,
    value: (context) => betzaPremoveDestinations(parsed.value, context),
    warnings: parsed.warnings,
  };
}
