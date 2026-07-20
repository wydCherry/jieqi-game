"""
揭棋对战 Web 版 - Flask 应用入口
"""

from flask import Flask, jsonify, request, render_template, send_from_directory
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game import Board, Rules, ChessAI, GameManager, GameState
from game.leaderboard import Leaderboard, get_leaderboard

app = Flask(__name__,
            template_folder='web/templates',
            static_folder='web/static')

# 游戏管理器（单例模式，简化演示）
game_manager = GameManager()
leaderboard = get_leaderboard()  # 使用全局排行榜实例
ai = ChessAI('medium')


# ==================== 页面路由 ====================

@app.route('/')
def index():
    """游戏主页"""
    return render_template('index.html')


@app.route('/rules')
def rules():
    """规则页面"""
    return render_template('rules.html')


# ==================== API 路由 ====================

@app.route('/api/new-game', methods=['POST'])
def new_game():
    """开始新游戏"""
    data = request.get_json() or {}
    mode = data.get('mode', 'pvp')  # pvp, pve
    difficulty = data.get('difficulty', 'medium')

    global ai
    ai = ChessAI(difficulty)

    game_manager.start_game(mode)

    # 人机对战：玩家执黑方先手，AI执红方后手
    if mode == 'pve':
        game_manager.current_player = 'black'  # 黑方（玩家）先手

    return jsonify({
        'success': True,
        'state': get_board_state()
    })


@app.route('/api/board', methods=['GET'])
def get_board():
    """获取当前棋盘状态"""
    return jsonify(get_board_state())


@app.route('/api/move', methods=['POST'])
def make_move():
    """执行走棋"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': '无效请求数据'}), 400

    from_row = data.get('from_row')
    from_col = data.get('from_col')
    to_row = data.get('to_row')
    to_col = data.get('to_col')

    if None in [from_row, from_col, to_row, to_col]:
        return jsonify({'success': False, 'error': '缺少坐标参数'}), 400

    # 选择棋子
    piece = game_manager.board.get_piece_at(from_row, from_col)
    if not piece:
        return jsonify({'success': False, 'error': '该位置无棋子'}), 400

    # 检查是否是当前玩家的棋子
    if piece.is_flipped:
        # 明子：按颜色判断
        if piece.color != game_manager.current_player:
            return jsonify({'success': False, 'error': f'不是你的回合（当前: {game_manager.current_player}, 棋子: {piece.color}）'}), 400
    else:
        # 暗子：按位置判断归属
        piece_owner = 'red' if from_row <= 4 else 'black'
        if piece_owner != game_manager.current_player:
            return jsonify({'success': False, 'error': f'不能操作对方区域的暗子（当前: {game_manager.current_player}, 区域: {piece_owner}）'}), 400

    game_manager.selected_piece = piece
    valid_moves = Rules.get_valid_moves(piece, game_manager.board)

    if (to_row, to_col) not in valid_moves:
        return jsonify({'success': False, 'error': f'非法移动（合法位置: {valid_moves[:5]}...）'}), 400

    # 执行移动
    success = game_manager.make_move(to_row, to_col)

    if not success:
        return jsonify({'success': False, 'error': '移动失败'}), 400

    response = {
        'success': True,
        'state': get_board_state(),
        'captured': None
    }

    # 检查是否吃子
    if game_manager.move_history:
        last_move = game_manager.move_history[-1]
        if last_move.captured:
            response['captured'] = {
                'type': last_move.captured.piece_type,
                'color': last_move.captured.color
            }

    # AI 回合（人机对战模式）
    if game_manager.state == GameState.PLAYING and game_manager.game_mode == 'pve':
        if game_manager.current_player == 'red':  # AI 执红
            ai_move = ai.get_best_move(game_manager.board, 'red')
            if ai_move:
                from_pos, to_pos = ai_move
                ai_piece = game_manager.board.get_piece_at(from_pos[0], from_pos[1])
                game_manager.selected_piece = ai_piece
                game_manager.make_move(to_pos[0], to_pos[1])
                response['ai_move'] = {
                    'from': {'row': from_pos[0], 'col': from_pos[1]},
                    'to': {'row': to_pos[0], 'col': to_pos[1]}
                }

    return jsonify(response)


@app.route('/api/select', methods=['POST'])
def select_piece():
    """选择棋子，获取合法移动"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': '无效请求数据'}), 400

    row = data.get('row')
    col = data.get('col')

    if None in [row, col]:
        return jsonify({'success': False, 'error': '缺少坐标参数'}), 400

    piece = game_manager.board.get_piece_at(row, col)
    if not piece or not piece.is_alive:
        return jsonify({'success': False, 'error': '该位置无棋子', 'valid_moves': []}), 400

    # 检查是否是当前玩家的棋子
    if piece.is_flipped:
        # 明子：按颜色判断
        if piece.color != game_manager.current_player:
            return jsonify({'success': False, 'error': f'不是你的棋子（当前: {game_manager.current_player}）', 'valid_moves': []}), 400
    else:
        # 暗子：按位置判断归属
        piece_owner = 'red' if row <= 4 else 'black'
        if piece_owner != game_manager.current_player:
            return jsonify({'success': False, 'error': f'不能操作对方区域的暗子（当前回合: {game_manager.current_player}, 点击区域: {piece_owner}）', 'valid_moves': []}), 400

    # 获取合法移动
    valid_moves = Rules.get_valid_moves(piece, game_manager.board)

    return jsonify({
        'success': True,
        'piece': {
            'type': piece.piece_type,
            'color': piece.color,
            'flipped': piece.is_flipped,
            'row': piece.row,
            'col': piece.col
        },
        'valid_moves': [{'row': m[0], 'col': m[1]} for m in valid_moves],
        'current_player': game_manager.current_player  # 添加当前玩家信息
    })


@app.route('/api/hint', methods=['GET'])
def get_hint():
    """获取走棋提示"""
    hints = game_manager.get_hint()
    return jsonify({
        'success': True,
        'hints': [
            {
                'from': {'row': h[0].row, 'col': h[0].col},
                'to': {'row': h[1][0], 'col': h[1][1]},
                'piece_type': h[0].piece_type
            }
            for h in hints
        ]
    })


@app.route('/api/undo', methods=['POST'])
def undo_move():
    """悔棋"""
    if game_manager.game_mode == 'pve':
        # 人机对战悔两步（玩家和AI各一步）
        game_manager.undo_move()
        game_manager.undo_move()
    else:
        game_manager.undo_move()

    return jsonify({
        'success': True,
        'state': get_board_state()
    })


@app.route('/api/resign', methods=['POST'])
def resign():
    """认输"""
    data = request.get_json() or {}
    color = data.get('color', game_manager.current_player)
    game_manager.resign(color)

    return jsonify({
        'success': True,
        'state': get_board_state(),
        'winner': 'black' if color == 'red' else 'red'
    })


@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard_api():
    """获取排行榜"""
    stats = leaderboard.get_stats()
    recent_records = leaderboard.get_recent_records(10)

    # 转换记录为可序列化的格式
    records = []
    for r in recent_records:
        records.append({
            'date': r.date,
            'mode': r.mode,
            'result': r.result,
            'opponent': r.opponent,
            'duration': r.duration
        })

    return jsonify({
        'success': True,
        'stats': stats,
        'records': records
    })


# ==================== 辅助函数 ====================

def get_board_state():
    """获取棋盘状态"""
    pieces = []
    for piece in game_manager.board.pieces:
        if piece.is_alive:
            pieces.append({
                'type': piece.piece_type,
                'color': piece.color,
                'row': piece.row,
                'col': piece.col,
                'flipped': piece.is_flipped
            })

    return {
        'pieces': pieces,
        'current_player': game_manager.current_player,
        'state': game_manager.state.value if game_manager.state else 'playing',
        'winner': game_manager.winner,
        'mode': game_manager.game_mode,
        'captured_red': [p.piece_type for p in game_manager.board.captured_red],
        'captured_black': [p.piece_type for p in game_manager.board.captured_black],
        'in_check': Rules.is_in_check(game_manager.current_player, game_manager.board),
        'move_count': len(game_manager.move_history)
    }


# ==================== 启动服务器 ====================

if __name__ == '__main__':
    # 从环境变量获取端口（云平台部署）
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    print("=" * 50)
    print("揭棋对战 Web 版")
    print("=" * 50)
    print(f"访问地址: http://localhost:{port}")
    print("=" * 50)

    app.run(host='0.0.0.0', port=port, debug=debug)