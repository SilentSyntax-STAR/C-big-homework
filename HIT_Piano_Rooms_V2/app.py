"""Entry point: python app.py"""
import argparse
from piano_manager import PianoService
from piano_manager.database import default_database_path


def main():
    parser = argparse.ArgumentParser(description='二校区琴房管理系统（课程项目升级版）')
    parser.add_argument('--db', default=str(default_database_path()), help='SQLite 数据库路径（用于测试或备份）')
    options = parser.parse_args()
    # Import GUI lazily, allowing headless unit tests of the business layer.
    from piano_manager.ui import PianoApp
    app = PianoApp(PianoService(options.db))
    app.mainloop()


if __name__ == '__main__':
    main()
