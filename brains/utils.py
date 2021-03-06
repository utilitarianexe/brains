from pathlib import Path

def data_dir_file_path(file_name):
    base_path = Path(__file__).parent / "data"
    file_path = (base_path / file_name).resolve()
    return file_path

def decay(initial_value, decay_rate, step_size):
    return initial_value * (1 - decay_rate)**step_size

def newtons_square_root(n):
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x
