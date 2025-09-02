import chess
import chess.pgn
import datetime

MAX_BOOK_PLIES = 100

def format_zobrist_key_hex(zobrist_key):
    return f"{zobrist_key:016x}"

def get_zobrist_key_hex(board):
    # Modern python-chess compatible substitute for Zobrist key
    return format_zobrist_key_hex(hash(board.fen()) & 0xFFFFFFFFFFFFFFFF)

class BookMove:
    def __init__(self, move):
        self.weight = 1  # always 1
        self.move = move

class BookPosition:
    def __init__(self):
        self.moves = []  # store every move, even repeated
        self.fen = ""

    def add_move(self, move):
        self.moves.append(BookMove(move))

class Book:
    def __init__(self):
        self.positions = []  # list of (zobrist_key_hex, BookPosition)

    def add_position(self, zobrist_key_hex, move):
        pos = BookPosition()
        pos.add_move(move)
        self.positions.append((zobrist_key_hex, pos))

    def save_as_polyglot(self, path):
        with open(path, 'wb') as outfile:
            for key_hex, pos in self.positions:
                zbytes = bytes.fromhex(key_hex)
                for bm in pos.moves:
                    move = bm.move
                    mi = move.to_square + (move.from_square << 6)
                    if move.promotion:
                        mi += ((move.promotion - 1) << 12)
                    mbytes = mi.to_bytes(2, byteorder="big")
                    wbytes = (1).to_bytes(2, byteorder="big")  # weight = 1
                    lbytes = (0).to_bytes(4, byteorder="big")  # learn = 0
                    outfile.write(zbytes + mbytes + wbytes + lbytes)
        print(f"Saved {len(self.positions)} positions to book: {path}")

class LichessGame:
    def __init__(self, game):
        self.game = game

    def result(self):
        return self.game.headers.get("Result", "*")

    def score(self):
        return 1  # ignored, all moves weight = 1

def correct_castling_uci(uci, board):
    if board.piece_at(chess.parse_square(uci[:2])).piece_type == chess.KING:
        if uci == "e1g1": return "e1h1"
        if uci == "e1c1": return "e1a1"
        if uci == "e8g8": return "e8h8"
        if uci == "e8c8": return "e8a8"
    return uci

def build_book_file(pgn_path="forced-line.pgn", book_path="main.bin"):
    book = Book()
    with open(pgn_path) as pgn_file:
        for i, game in enumerate(iter(lambda: chess.pgn.read_game(pgn_file), None), start=1):
            if game is None:
                break
            if i % 100 == 0:
                print(f"Processed {i} games")

            board = game.board()
            ply = 0

            for move in game.mainline_moves():
                if ply >= MAX_BOOK_PLIES:
                    break

                uci = correct_castling_uci(move.uci(), board)
                move_obj = chess.Move.from_uci(uci)
                zobrist_key_hex = get_zobrist_key_hex(board)
                book.add_position(zobrist_key_hex, move_obj)  # no deduplication, weight=1

                board.push(move)
                ply += 1

    book.save_as_polyglot(book_path)

if __name__ == "__main__":
    build_book_file()
