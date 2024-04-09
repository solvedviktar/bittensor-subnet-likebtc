import os


LIKE_BITCOIN_NET_FILE = 'likebtc_hashes.txt'


def get_last_likebtc_hash() -> str:
    with open(LIKE_BITCOIN_NET_FILE, 'ab+') as f:
        try:
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            f.seek(0)
        return f.readline().decode().replace('\n', '')


def add_likebtc_hash(line: str) -> None:
    with open(LIKE_BITCOIN_NET_FILE, 'a+') as f:
        f.write(line + '\n')
