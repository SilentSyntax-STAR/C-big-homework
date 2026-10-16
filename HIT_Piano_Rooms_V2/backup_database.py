"""Consistent online backup for the SQLite file, including WAL content."""
import argparse
from pathlib import Path
import sqlite3
from piano_manager.database import default_database_path


def main():
    parser = argparse.ArgumentParser(description='安全备份琴房 SQLite 数据库')
    parser.add_argument('--db', default=str(default_database_path()), help='原数据库')
    parser.add_argument('--out', required=True, help='输出 .sqlite3 文件，必须不存在')
    args = parser.parse_args()
    source, dest = Path(args.db), Path(args.out)
    if not source.is_file():
        parser.error('源数据库不存在。请先启动一次程序。')
    if dest.exists():
        parser.error('目标文件已存在，防止覆盖备份。')
    dest.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(f'file:{source.resolve().as_posix()}?mode=ro', uri=True) as conn:
        with sqlite3.connect(str(dest)) as backup:
            conn.backup(backup)
    print('数据库已备份：', dest)


if __name__ == '__main__':
    main()
