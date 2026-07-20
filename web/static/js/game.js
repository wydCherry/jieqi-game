/**
 * 揭棋对战 Web 版 - 游戏逻辑
 */

class JieqiGame {
    constructor() {
        // 游戏状态
        this.pieces = [];
        this.currentPlayer = 'red';
        this.selectedPiece = null;
        this.validMoves = [];
        this.gameActive = false;
        this.gameMode = 'pvp';
        this.capturedRed = [];
        this.capturedBlack = [];

        // Canvas 相关
        this.canvas = document.getElementById('board-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.cellSize = 50;
        this.padding = 30;

        // 颜色配置
        this.colors = {
            boardBg: '#D2B48C',
            boardLine: '#5D3A1A',
            pieceRed: '#B43232',
            pieceRedBg: '#FFEBCD',
            pieceBlack: '#282828',
            pieceBlackBg: '#F5F5DC',
            pieceHidden: '#8B5A2B',
            pieceHiddenBg: '#D2B48C',
            highlight: 'rgba(0, 200, 0, 0.6)',
            selected: 'rgba(255, 215, 0, 0.6)',
            capture: 'rgba(255, 0, 0, 0.6)'
        };

        // 初始化
        this.initCanvas();
        this.bindEvents();
    }

    // ==================== 初始化 ====================

    initCanvas() {
        // 根据屏幕大小调整 Canvas
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
    }

    resizeCanvas() {
        const container = document.getElementById('board-container');
        const maxWidth = container.clientWidth - 20;
        const maxHeight = container.clientHeight - 20;

        // 棋盘比例：宽9列，高10行
        const boardWidth = maxWidth;
        const boardHeight = boardWidth * 10 / 9;

        if (boardHeight > maxHeight) {
            this.cellSize = Math.floor((maxHeight - this.padding * 2) / 10);
        } else {
            this.cellSize = Math.floor((maxWidth - this.padding * 2) / 9);
        }

        this.cellSize = Math.max(35, Math.min(this.cellSize, 60));

        const canvasWidth = this.cellSize * 8 + this.padding * 2;
        const canvasHeight = this.cellSize * 9 + this.padding * 2;

        this.canvas.width = canvasWidth;
        this.canvas.height = canvasHeight;

        if (this.pieces.length > 0) {
            this.draw();
        }
    }

    bindEvents() {
        // 鼠标点击
        this.canvas.addEventListener('click', (e) => this.handleClick(e));

        // 触摸事件
        this.canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            this.handleClick(touch);
        }, { passive: false });

        // 按钮事件
        document.getElementById('btn-new-game').addEventListener('click', () => this.showMenu());
        document.getElementById('btn-undo').addEventListener('click', () => this.undo());
        document.getElementById('btn-hint').addEventListener('click', () => this.showHint());
        document.getElementById('btn-resign').addEventListener('click', () => this.resign());

        // 菜单按钮
        document.querySelectorAll('.menu-btn[data-mode]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const mode = e.target.dataset.mode;
                const difficulty = e.target.dataset.difficulty || 'medium';
                this.newGame(mode, difficulty);
            });
        });

        // 排行榜
        document.getElementById('btn-leaderboard').addEventListener('click', () => this.showLeaderboard());
        document.getElementById('btn-close-leaderboard').addEventListener('click', () => this.hideLeaderboard());

        // 游戏结束弹窗
        document.getElementById('btn-restart').addEventListener('click', () => {
            this.hideGameOver();
            this.showMenu();
        });
        document.getElementById('btn-back-menu').addEventListener('click', () => {
            this.hideGameOver();
            this.showMenu();
        });
    }

    // ==================== API 请求 ====================

    async api(url, method = 'GET', data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            return { success: false, error: '网络错误' };
        }
    }

    async newGame(mode = 'pvp', difficulty = 'medium') {
        const result = await this.api('/api/new-game', 'POST', { mode, difficulty });

        if (result.success) {
            this.gameMode = mode;
            this.updateState(result.state);
            this.hideMenu();
            this.draw();
        } else {
            alert('开始游戏失败: ' + result.error);
        }
    }

    async selectPieceAt(row, col) {
        const result = await this.api('/api/select', 'POST', { row, col });

        if (result.success) {
            this.selectedPiece = result.piece;
            this.validMoves = result.valid_moves;
            this.draw();
        } else {
            this.selectedPiece = null;
            this.validMoves = [];
            this.draw();
        }

        return result.success;
    }

    async makeMove(fromRow, fromCol, toRow, toCol) {
        const result = await this.api('/api/move', 'POST', {
            from_row: fromRow,
            from_col: fromCol,
            to_row: toRow,
            to_col: toCol
        });

        if (result.success) {
            this.updateState(result.state);

            // AI 移动动画
            if (result.ai_move) {
                setTimeout(() => {
                    this.draw();
                    this.checkGameOver(result.state);
                }, 300);
            } else {
                this.draw();
                this.checkGameOver(result.state);
            }
        } else {
            alert(result.error || '移动失败');
        }

        return result.success;
    }

    async undo() {
        const result = await this.api('/api/undo', 'POST');

        if (result.success) {
            this.updateState(result.state);
            this.selectedPiece = null;
            this.validMoves = [];
            this.draw();
        }
    }

    async showHint() {
        const result = await this.api('/api/hint', 'GET');

        if (result.success && result.hints.length > 0) {
            const hint = result.hints[0];
            this.selectedPiece = { row: hint.from.row, col: hint.from.col };
            this.validMoves = [{ row: hint.to.row, col: hint.to.col }];
            this.draw();
        }
    }

    async resign() {
        if (!confirm('确定要认输吗？')) return;

        const result = await this.api('/api/resign', 'POST');

        if (result.success) {
            this.showGameOver(result.winner, '认输');
        }
    }

    async showLeaderboard() {
        const result = await this.api('/api/leaderboard', 'GET');

        if (result.success) {
            document.getElementById('wins').textContent = result.stats.wins;
            document.getElementById('losses').textContent = result.stats.losses;
            document.getElementById('win-rate').textContent = result.stats.win_rate;
            document.getElementById('leaderboard-modal').classList.add('show');
        }
    }

    hideLeaderboard() {
        document.getElementById('leaderboard-modal').classList.remove('show');
    }

    // ==================== 状态更新 ====================

    updateState(state) {
        this.pieces = state.pieces;
        this.currentPlayer = state.current_player;
        this.gameActive = state.state === 'playing';
        this.capturedRed = state.captured_red || [];
        this.capturedBlack = state.captured_black || [];

        // 更新 UI
        const turnText = document.getElementById('turn-text');
        turnText.textContent = this.currentPlayer === 'red' ? '红方回合' : '黑方回合';
        turnText.className = this.currentPlayer;

        document.getElementById('captured-info').textContent =
            `已吃棋子: 红[${this.capturedRed.join(' ')}] 黑[${this.capturedBlack.join(' ')}]`;
        document.getElementById('move-count').textContent = `回合: ${state.move_count || 0}`;
    }

    checkGameOver(state) {
        if (state.state === 'game_over' && state.winner) {
            const winnerText = state.winner === 'red' ? '红方' : '黑方';
            this.showGameOver(state.winner, `${winnerText}胜利！`);
        }
    }

    // ==================== 绘制 ====================

    draw() {
        this.drawBoard();
        this.drawPieces();
        this.drawHighlights();
    }

    drawBoard() {
        const ctx = this.ctx;
        const cs = this.cellSize;
        const pd = this.padding;

        // 背景
        ctx.fillStyle = this.colors.boardBg;
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // 外框
        ctx.strokeStyle = this.colors.boardLine;
        ctx.lineWidth = 3;
        ctx.strokeRect(pd - 5, pd - 5, cs * 8 + 10, cs * 9 + 10);

        // 横线
        ctx.lineWidth = 1;
        for (let i = 0; i < 10; i++) {
            ctx.beginPath();
            ctx.moveTo(pd, pd + i * cs);
            ctx.lineTo(pd + 8 * cs, pd + i * cs);
            ctx.stroke();
        }

        // 竖线（中间断开）
        for (let i = 0; i < 9; i++) {
            if (i === 0 || i === 8) {
                ctx.beginPath();
                ctx.moveTo(pd + i * cs, pd);
                ctx.lineTo(pd + i * cs, pd + 9 * cs);
                ctx.stroke();
            } else {
                ctx.beginPath();
                ctx.moveTo(pd + i * cs, pd);
                ctx.lineTo(pd + i * cs, pd + 4 * cs);
                ctx.stroke();
                ctx.beginPath();
                ctx.moveTo(pd + i * cs, pd + 5 * cs);
                ctx.lineTo(pd + i * cs, pd + 9 * cs);
                ctx.stroke();
            }
        }

        // 九宫格斜线
        ctx.beginPath();
        ctx.moveTo(pd + 3 * cs, pd);
        ctx.lineTo(pd + 5 * cs, pd + 2 * cs);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(pd + 5 * cs, pd);
        ctx.lineTo(pd + 3 * cs, pd + 2 * cs);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(pd + 3 * cs, pd + 7 * cs);
        ctx.lineTo(pd + 5 * cs, pd + 9 * cs);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(pd + 5 * cs, pd + 7 * cs);
        ctx.lineTo(pd + 3 * cs, pd + 9 * cs);
        ctx.stroke();

        // 楚河汉界
        ctx.font = `${Math.floor(cs * 0.35)}px SimHei`;
        ctx.fillStyle = this.colors.boardLine;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('楚 河', pd + 2 * cs, pd + 4.5 * cs);
        ctx.fillText('汉 界', pd + 6 * cs, pd + 4.5 * cs);
    }

    drawPieces() {
        for (const piece of this.pieces) {
            this.drawPiece(piece);
        }
    }

    drawPiece(piece) {
        const ctx = this.ctx;
        const cs = this.cellSize;
        const pd = this.padding;

        const x = pd + piece.col * cs;
        const y = pd + piece.row * cs;
        const r = cs * 0.42;

        // 背景
        if (piece.flipped) {
            ctx.fillStyle = piece.color === 'red' ? this.colors.pieceRedBg : this.colors.pieceBlackBg;
        } else {
            ctx.fillStyle = this.colors.pieceHiddenBg;
        }

        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fill();

        // 边框
        ctx.strokeStyle = this.colors.boardLine;
        ctx.lineWidth = 2;
        ctx.stroke();

        // 文字
        const text = piece.flipped ? piece.type : '?';
        ctx.font = `bold ${Math.floor(r * 1.1)}px SimHei`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        if (piece.flipped) {
            ctx.fillStyle = piece.color === 'red' ? this.colors.pieceRed : this.colors.pieceBlack;
        } else {
            ctx.fillStyle = this.colors.pieceHidden;
        }

        ctx.fillText(text, x, y);
    }

    drawHighlights() {
        const ctx = this.ctx;
        const cs = this.cellSize;
        const pd = this.padding;

        // 选中棋子高亮
        if (this.selectedPiece) {
            const x = pd + this.selectedPiece.col * cs;
            const y = pd + this.selectedPiece.row * cs;
            const r = cs * 0.48;

            ctx.beginPath();
            ctx.arc(x, y, r, 0, Math.PI * 2);
            ctx.strokeStyle = this.colors.selected;
            ctx.lineWidth = 3;
            ctx.stroke();
        }

        // 可移动位置
        for (const move of this.validMoves) {
            const x = pd + move.col * cs;
            const y = pd + move.row * cs;

            // 检查目标位置是否有棋子
            const target = this.pieces.find(p => p.row === move.row && p.col === move.col);

            if (target) {
                // 可吃子 - 红色圆环
                ctx.beginPath();
                ctx.arc(x, y, cs * 0.45, 0, Math.PI * 2);
                ctx.strokeStyle = this.colors.capture;
                ctx.lineWidth = 3;
                ctx.stroke();
            } else {
                // 可移动 - 绿色小圆点
                ctx.beginPath();
                ctx.arc(x, y, cs * 0.12, 0, Math.PI * 2);
                ctx.fillStyle = this.colors.highlight;
                ctx.fill();
            }
        }
    }

    // ==================== 事件处理 ====================

    handleClick(e) {
        if (!this.gameActive) return;

        const rect = this.canvas.getBoundingClientRect();
        const x = (e.clientX || e.pageX) - rect.left;
        const y = (e.clientY || e.pageY) - rect.top;

        // 计算棋盘坐标
        const col = Math.round((x - this.padding) / this.cellSize);
        const row = Math.round((y - this.padding) / this.cellSize);

        if (row < 0 || row > 9 || col < 0 || col > 8) return;

        this.handleBoardClick(row, col);
    }

    async handleBoardClick(row, col) {
        // 检查是否点击了可移动位置
        if (this.selectedPiece && this.validMoves.some(m => m.row === row && m.col === col)) {
            // 执行移动
            await this.makeMove(this.selectedPiece.row, this.selectedPiece.col, row, col);
            this.selectedPiece = null;
            this.validMoves = [];
        } else {
            // 选择棋子
            await this.selectPieceAt(row, col);
        }
    }

    // ==================== UI 辅助 ====================

    showMenu() {
        document.getElementById('menu-overlay').classList.add('show');
    }

    hideMenu() {
        document.getElementById('menu-overlay').classList.remove('show');
    }

    showGameOver(winner, reason) {
        const winnerText = winner === 'red' ? '红方' : '黑方';
        document.getElementById('game-result').textContent = `${winnerText}胜利！`;
        document.getElementById('game-reason').textContent = reason;
        document.getElementById('game-over-modal').classList.add('show');
    }

    hideGameOver() {
        document.getElementById('game-over-modal').classList.remove('show');
    }
}

// ==================== 初始化 ====================

let game;

document.addEventListener('DOMContentLoaded', () => {
    game = new JieqiGame();

    // 显示菜单
    game.showMenu();
});