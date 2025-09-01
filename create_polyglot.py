import chess
import chess.pgn
import chess.polyglot

MAX_BOOK_PLIES = 1000
MAX_BOOK_WEIGHT = 10000

def format_zobrist_key_hex(zobrist_key):
    return f"{zobrist_key:016x}"

def get_zobrist_key_hex(board):
    return format_zobrist_key_hex(chess.polyglot.zobrist_hash(board))

class BookMove:
    def __init__(self):
        self.weight = 0
        self.move = None

class BookPosition:
    def __init__(self):
        self.moves = {}

    def get_move(self, uci):
        return self.moves.setdefault(uci, BookMove())

class Book:
    def __init__(self):
        self.positions = {}

    def get_position(self, zobrist_key_hex):
        return self.positions.setdefault(zobrist_key_hex, BookPosition())

    def normalize_weights(self):
        for pos in self.positions.values():
            total_weight = sum(bm.weight for bm in pos.moves.values())
            if total_weight > 0:
                for bm in pos.moves.values():
                    bm.weight = int(bm.weight / total_weight * MAX_BOOK_WEIGHT)

    def save_as_polyglot(self, path):
        with open(path, 'wb') as outfile:
            entries = []
            for key_hex, pos in self.positions.items():
                zbytes = bytes.fromhex(key_hex)
                for uci, bm in pos.moves.items():
                    if bm.weight <= 0:
                        continue
                    move = bm.move
                    mi = move.to_square + (move.from_square << 6)
                    if move.promotion:
                        mi += ((move.promotion - 1) << 12)
                    mbytes = mi.to_bytes(2, byteorder="big")
                    wbytes = bm.weight.to_bytes(2, byteorder="big")
                    lbytes = (0).to_bytes(4, byteorder="big")
                    entries.append(zbytes + mbytes + wbytes + lbytes)

            entries.sort(key=lambda e: (e[:8], e[10:12]))
            for entry in entries:
                outfile.write(entry)
            print(f"Saved {len(entries)} moves to book: {path}")

class LichessGame:
    def __init__(self, game):
        self.game = game

    def result(self):
        return self.game.headers.get("Result", "*")

    def score(self):
        res = self.result()
        return {"1-0": 2, "1/2-1/2": 1}.get(res, 0)

def build_book_file(pgn_path, book_path):
    book = Book()
    with open(pgn_path) as pgn_file:
        for i, game in enumerate(iter(lambda: chess.pgn.read_game(pgn_file), None), start=1):
            ligame = LichessGame(game)

            if game.headers.get("SetUp", "0") == "1" and "FEN" in game.headers:
                board = chess.Board(fen=game.headers["FEN"])
            else:
                board = chess.Board()

            score = ligame.score()
            ply = 0
            for move in game.mainline_moves():
                if ply >= MAX_BOOK_PLIES:
                    break
                uci = move.uci()
                zobrist_key_hex = get_zobrist_key_hex(board)
                position = book.get_position(zobrist_key_hex)
                bm = position.get_move(uci)
                bm.move = chess.Move.from_uci(uci)
                bm.weight += score if board.turn == chess.WHITE else (2 - score)
                board.push(move)
                ply += 1

    book.normalize_weights()
    book.save_as_polyglot(book_path)

def dump_book(book_path, max_entries=50):
    with chess.polyglot.open_reader(book_path) as reader:
        count = 0
        board = chess.Board()
        for entry in reader.find_all(board):
            move = entry.move()
            print(f"FEN: {board.fen()} | Move: {board.san(move)} | Weight: {entry.weight}")
            count += 1
            if count >= max_entries:
                break

if __name__ == "__main__":
    build_book_file("forced-line.pgn", "main.bin")
    dump_book("main.bin", 50)
