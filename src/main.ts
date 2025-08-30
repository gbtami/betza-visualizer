import { BetzaParser } from './betza_parser.js';
import { Move } from './types.js';

const parser = new BetzaParser();
const inputEl = document.getElementById('betzaInput') as HTMLInputElement;
const boardContainer = document.getElementById('board-container')!;

const BOARD_SIZE = 13;
const CELL_SIZE = 40;
const SVG_NS = "http://www.w3.org/2000/svg";

const COLORS = {
    standard: "#4169E1",
    move: "#FFD700",
    capture: "#DC143C",
    hop: "#32CD32",
    hurdle: "#606060",
};

const sign = (n: number): number => Math.sign(n);

function renderBoard(moves: Move[]) {
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("width", "100%");
    svg.setAttribute("height", "100%");
    svg.setAttribute("viewBox", `0 0 ${BOARD_SIZE * CELL_SIZE} ${BOARD_SIZE * CELL_SIZE}`);

    for (let r = 0; r < BOARD_SIZE; r++) {
        for (let c = 0; c < BOARD_SIZE; c++) {
            const rect = document.createElementNS(SVG_NS, "rect");
            rect.setAttribute("x", String(c * CELL_SIZE));
            rect.setAttribute("y", String(r * CELL_SIZE));
            rect.setAttribute("width", String(CELL_SIZE));
            rect.setAttribute("height", String(CELL_SIZE));
            rect.setAttribute("fill", (r + c) % 2 === 0 ? "#769656" : "#eeeed2");
            svg.appendChild(rect);
        }
    }

    const center = Math.floor(BOARD_SIZE / 2);

    const hurdles = new Set<string>();
    const specialMoves = moves.filter(m => m.hopType !== null || m.jumpType !== 'normal');

    if (specialMoves.length > 0) {
        const hopperMoves = specialMoves.filter(m => m.hopType !== null);
        if (hopperMoves.length > 0) {
            const uniqueDirections = [...new Set(hopperMoves.map(m => `${sign(m.x)},${sign(m.y)}`))];
            if (uniqueDirections.length === 4) {
                const isRookLike = ['0,1', '0,-1', '1,0', '-1,0'].every(d => uniqueDirections.includes(d));
                const isBishopLike = ['1,1', '1,-1', '-1,1', '-1,-1'].every(d => uniqueDirections.includes(d));
                if (isRookLike || isBishopLike) uniqueDirections.pop();
            }
            uniqueDirections.forEach(dir => hurdles.add(`${dir.split(',').map(Number)[0] * 2},${dir.split(',').map(Number)[1] * 2}`));
        }

        const njLeapers = specialMoves.filter(m => m.jumpType !== 'normal');
        if (njLeapers.length > 0) {
            ['0,1', '-1,0'].forEach(dir => hurdles.add(dir));
        }

        hurdles.forEach(h => {
            const [hx, hy] = h.split(',').map(Number);
            const cx = (center + hx) * CELL_SIZE + CELL_SIZE / 2;
            const cy = (center - hy) * CELL_SIZE + CELL_SIZE / 2;
            const hurdle = document.createElementNS(SVG_NS, "text");
            hurdle.textContent = "♙";
            hurdle.setAttribute("x", String(cx));
            hurdle.setAttribute("y", String(cy));
            hurdle.setAttribute("font-size", String(CELL_SIZE * 0.7));
            hurdle.setAttribute("text-anchor", "middle");
            hurdle.setAttribute("dominant-baseline", "central");
            hurdle.setAttribute("fill", COLORS.hurdle);
            hurdle.setAttribute("opacity", "0.8");
            svg.appendChild(hurdle);
        });
    }

    moves.forEach(move => {
        const {x, y, moveType, hopType, jumpType} = move;
        const cx = (center + x) * CELL_SIZE + CELL_SIZE / 2;
        const cy = (center - y) * CELL_SIZE + CELL_SIZE / 2;
        let color = "";
        let isValid = true;

        if (jumpType === 'non-jumping') {
            let blockX = 0, blockY = 0;
            if (Math.abs(x) > Math.abs(y)) blockX = sign(x);
            else if (Math.abs(y) > Math.abs(x)) blockY = sign(y);
            if (hurdles.has(`${blockX},${blockY}`)) isValid = false;
        } else if (jumpType === 'jumping') {
            isValid = false;
            let blockX = 0, blockY = 0;
            if (Math.abs(x) > Math.abs(y)) blockX = sign(x);
            else if (Math.abs(y) > Math.abs(x)) blockY = sign(y);
            if (hurdles.has(`${blockX},${blockY}`)) isValid = true;
        } else if (hopType) {
            isValid = false;
            const path: string[] = [];
            const dx = sign(x); const dy = sign(y);
            for (let i = 1; i < Math.max(Math.abs(x), Math.abs(y)); i++) {
                path.push(`${i * dx},${i * dy}`);
            }
            const hurdlesOnPath = path.filter(p => hurdles.has(p));
            if (hurdlesOnPath.length === 1) {
                if (hopType === 'p') isValid = true;
                else if (hopType === 'g') {
                    const [hx, hy] = hurdlesOnPath[0].split(',').map(Number);
                    if (x === hx + dx && y === hy + dy) isValid = true;
                }
            }
        }

        if (!isValid) return;

        if (hopType || jumpType === 'jumping') {
            if (moveType === 'move') color = COLORS.move;
            else if (moveType === 'capture') color = COLORS.capture;
            else color = COLORS.hop;
        } else {
             if (moveType === 'move') color = COLORS.move;
             else if (moveType === 'capture') color = COLORS.capture;
             else color = COLORS.standard;
        }

        const circle = document.createElementNS(SVG_NS, "circle");
        circle.setAttribute("cx", String(cx));
        circle.setAttribute("cy", String(cy));
        circle.setAttribute("r", String(CELL_SIZE * 0.3));
        circle.setAttribute("fill", color);
        // --- FIX: Use a lower opacity to make the circles semi-transparent ---
        circle.setAttribute("opacity", "0.6");
        svg.appendChild(circle);
    });

    const piece = document.createElementNS(SVG_NS, "text");
    piece.textContent = "🧚";
    piece.setAttribute("x", String(center * CELL_SIZE + CELL_SIZE / 2));
    piece.setAttribute("y", String(center * CELL_SIZE + CELL_SIZE / 2));
    piece.setAttribute("font-size", String(CELL_SIZE * 0.8));
    piece.setAttribute("text-anchor", "middle");
    piece.setAttribute("dominant-baseline", "central");
    piece.setAttribute("fill", "#000000");
    svg.appendChild(piece);

    boardContainer.innerHTML = "";
    boardContainer.appendChild(svg);
}

renderBoard([]);

inputEl.addEventListener('input', () => {
    const moves = parser.parse(inputEl.value);
    renderBoard(moves);
});
