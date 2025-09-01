import chess
import chess.pgn
import chess.polyglot

PGN_FILE = "forced-line.pgn"      # your PGN with 43 moves
BOOK_FILE = "main.bin"       # your polyglot book

def check_book_vs_pgn(pgn_file, book_file):
    # Load PGN
    with open(pgn_file) as f:
        game = chess.pgn.read_game(f)

    board = game.board()

    with chess.polyglot.open_reader(book_file) as reader:
        for i, move in enumerate(game.mainline_moves(), start=1):
            # Check if current board position is in book
            try:
                entries = list(reader.find_all(board))
            except IndexError:
                print(f"❌ Book has no entries at move {i}: {board.fen()}")
                return

            # See if PGN move matches one of the book entries
            if move in [e.move for e in entries]:
                print(f"✅ Move {i}: {board.san(move)} found in book")
            else:
                print(f"❌ Divergence at move {i}: {board.san(move)} not in book")
                return

            board.push(move)

        print("🎉 PGN fully matches the book!")

if __name__ == "__main__":
    check_book_vs_pgn(PGN_FILE, BOOK_FILE)
