import chess
import chess.pgn

MAX_BOOK_PLIES = 1000  # just a safety limit

def format_zobrist_key_hex(zobrist_key: int) -> str:
    return f"{zobrist_key:016x}"

def get_zobrist_key_hex(board: chess.Board) -> str:
    return format_zobrist_key_hex(chess.polyglot.zobrist_hash(board))

class BookMove:
    def __init__(self, move: chess.Move):
        self.move = move
        self.weight = 1  # always 1

class BookPosition:
    def __init__(self):
        self.moves = []

    def add_move(self, move: chess.Move):
        self.moves.append(BookMove(move))

class Book:
    def __init__(self):
        self.positions = []

    def add_position(self, board: chess.Board, move: chess.Move):
        zobrist_key_hex = get_zobrist_key_hex(board)
        self.positions.append((zobrist_key_hex, move))

    def save_as_polyglot(self, path: str):
        with open(path, "wb") as f:
            for key_hex, move in self.positions:
                zbytes = bytes.fromhex(key_hex)
                mi = move.to_square + (move.from_square << 6)
                if move.promotion:
                    mi += (move.promotion - 1) << 12
                mbytes = mi.to_bytes(2, byteorder="big")
                wbytes = (1).to_bytes(2, byteorder="big")  # weight = 1
                lbytes = (0).to_bytes(4, byteorder="big")  # learn = 0
                f.write(zbytes + mbytes + wbytes + lbytes)
        print(f"Saved {len(self.positions)} moves to book: {path}")

def build_book_file(pgn_path: str, book_path: str):
    book = Book()
    with open(pgn_path) as pgn_file:
        while True:
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break
            # Chess960 or standard
            if game.headers.get("SetUp", "0") == "1" and "FEN" in game.headers:
                board = chess.Board(fen=game.headers["FEN"])
            else:
                board = chess.Board()
            ply = 0
            for move in game.mainline_moves():
                if ply >= MAX_BOOK_PLIES:
                    break
                book.add_position(board, move)
                board.push(move)
                ply += 1
    book.save_as_polyglot(book_path)

if __name__ == "__main__":
    build_book_file("forced-line.pgn", "main.bin")
