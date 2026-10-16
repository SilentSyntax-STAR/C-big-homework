"""Manual automated GUI startup smoke test; needs a graphical desktop/Xvfb."""
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from piano_manager.config import BEIJING_TZ
from piano_manager.service import PianoService
from piano_manager.ui import PianoApp

service = PianoService(':memory:', clock=lambda: datetime(2026, 10, 16, 10, 12, tzinfo=BEIJING_TZ))
app = PianoApp(service)
try:
    for page in ('home', 'register', 'book', 'check', 'history', 'notice'):
        app.show_page(page)
        app.update_idletasks()
        app.update()
        assert app.main.winfo_height() > 0
        app.canvas.yview_moveto(1.0)
        app.update_idletasks()
        print('GUI page OK:', page)
    print('All six UI pages rendered successfully.')
finally:
    app.destroy()
    service.close()
