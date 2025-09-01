import chess
import chess.pgn
import chess.polyglot


def build_book_file(pgn_path: str, book_path: str):
    entries = []

    with open(pgn_path, "r", encoding="utf-8") as pgn_file:
        while True:
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break

            # Handle Chess960 / custom FEN
            if game.headers.get("SetUp", "0") == "1" and "FEN" in game.headers:
                board = chess.Board(fen=game.headers["FEN"])
            else:
                board = chess.Board()

            for move in game.mainline_moves():
                # Create entry manually
                entry = chess.polyglot.Entry(
                    key=chess.polyglot.zobrist_hash(board),
                    move=move,
                    weight=1,
                    learn=0
                )
                entries.append(entry)
                board.push(move)

    # Write all entries to .bin
    with open(book_path, "wb") as out:
        writer = chess.polyglot.Writer(out)
        for entry in entries:
            writer.write(entry)

    print(f"Saved {len(entries)} moves to book: {book_path}")


def dump_book(book_path: str, max_entries: int = 50):
    with chess.polyglot.open_reader(book_path) as reader:
        for i, entry in enumerate(reader, start=1):
            print(
                f"Key: {entry.key} | Move: {entry.move.uci()} | "
                f"Weight: {entry.weight} | Learn: {entry.learn}"
            )
            if i >= max_entries:
                break


if __name__ == "__main__":
    build_book_file("forced-line.pgn", "main.bin")
    dump_book("main.bin", 50)
