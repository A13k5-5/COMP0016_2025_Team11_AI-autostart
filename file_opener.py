import subprocess


game_path = r"C:\Users\pison\OneDrive\Počítač\saved_games\Hobbit 2 - George.noui"


def run_file_and_wait(path: str) -> None:
    subprocess.run(["cmd", "/c", "start", "", "/wait", path])


if __name__ == "__main__":
    # stop the capturing here
    run_file_and_wait(game_path)
    # resume capturing here
    # might be a bit tricky with threads
    print("Game file closed, resuming capture...")
