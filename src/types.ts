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

export interface VariantProperties {
  double_step: boolean;
}
