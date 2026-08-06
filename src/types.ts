export interface Piece {
  name: string;
  variant: string;
  betza: string;
}

export interface Move {
  x: number;
  y: number;
  moveType: 'move_capture' | 'move' | 'capture';
  hopType: 'p' | 'g' | null;
  jumpType: 'normal' | 'non-jumping' | 'jumping';
  atom: string;
  atomCoords: { x: number; y: number };
  initialOnly?: boolean;
}

export interface BetzaDiagnostic {
  readonly message: string;
  readonly index: number;
  readonly token?: string;
}

export type BetzaParseResult<T> =
  | { readonly ok: true; readonly value: T; readonly warnings: BetzaDiagnostic[] }
  | { readonly ok: false; readonly errors: BetzaDiagnostic[] };

export interface BetzaTerm {
  readonly atom: string;
  readonly atomCoords: { readonly x: number; readonly y: number };
  readonly directions: readonly { readonly dx: number; readonly dy: number }[];
  readonly maxSteps: number | 'unbounded';
  readonly moveType: Move['moveType'];
  readonly hopType: Move['hopType'];
  readonly jumpType: Move['jumpType'];
  readonly initialOnly: boolean;
  readonly modifiers: string;
}

export interface BetzaMovement {
  readonly notation: string;
  readonly terms: readonly BetzaTerm[];
}

export type BetzaColor = 'white' | 'black';
export type BetzaPosition = readonly [x: number, y: number];

export interface BetzaBoardDimensions {
  readonly width: number;
  readonly height: number;
}

export interface BetzaPremoveContext {
  readonly origin: BetzaPosition;
  readonly color: BetzaColor;
  readonly board: BetzaBoardDimensions;
}

export type BetzaPremove = (context: BetzaPremoveContext) => BetzaPosition[];
