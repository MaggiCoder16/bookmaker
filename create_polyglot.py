import chess
import chess.pgn
import sys

MAX_PLY = 100

def move_to_bytes(move: chess.Move) -> bytes:
    mi = move.to_square + (move.from_square << 6)
    if move.promotion:
        mi += (move.promotion - 1) << 12
    return mi.to_bytes(2, byteorder="big")

def create_bin(pgn_path: str, bin_path: str):
    entries = []
    key_counter = 0

    with open(pgn_path) as f:
        for game in iter(lambda: chess.pgn.read_game(f), None):
            if game is None:
                break

            board = game.board()
            ply = 0

            for move in game.mainline_moves():
                if ply >= MAX_PLY:
                    break

                zbytes = key_counter.to_bytes(8, byteorder="big")
                mbytes = move_to_bytes(move)
                wbytes = (1).to_bytes(2, byteorder="big")
                lbytes = (0).to_bytes(4, byteorder="big")
                entries.append(zbytes + mbytes + wbytes + lbytes)

                board.push(move)
                ply += 1
                key_counter += 1

    # Sort by “key” to match PolyGlot expectation
    entries.sort(key=lambda e: (e[:8], e[10:12]))

    with open(bin_path, "wb") as f:
        for entry in entries:
            f.write(entry)

    print(f"Saved {len(entries)} moves to {bin_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_polyglot.py input.pgn output.bin")
        sys.exit(1)

    create_bin(sys.argv[1], sys.argv[2])
