"""Pure-stdlib Tk/ttk desktop interface for the original campus scenario."""
import tkinter as tk
from tkinter import ttk, messagebox

from .config import ANNOUNCEMENT, ROOM_COUNT, slot_label
from .service import PianoError

BG = '#F3F6FB'
WHITE = '#FFFFFF'
INK = '#162337'
MUTED = '#65758A'
NAVY = '#132742'
BLUE = '#2866D4'
PALE = '#E9F1FF'
BORDER = '#DDE5F0'
GREEN = '#087C65'
FONT = 'Microsoft YaHei UI'
STATUS = {'booked': '已预约', 'signed_in': '已签到', 'signed_out': '已签退'}


class PianoApp(tk.Tk):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self.title('琴房管理系统 · 二校区场景复刻 V2.0')
        self.geometry('1140x760')
        self.minsize(980, 680)
        self.configure(bg=BG)
        self._selected_room = None
        self._set_style()
        self.protocol('WM_DELETE_WINDOW', self._on_close)
        self._build_shell()
        self.show_page('home')
        self._tick()

    def _set_style(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        self.option_add('*Font', (FONT, 10))
        style.configure('TFrame', background=BG)
        style.configure('Card.TFrame', background=WHITE)
        style.configure('TLabel', background=BG, foreground=INK, font=(FONT, 10))
        style.configure('Card.TLabel', background=WHITE, foreground=INK, font=(FONT, 10))
        style.configure('Muted.TLabel', background=WHITE, foreground=MUTED, font=(FONT, 10))
        style.configure('Hero.TLabel', background=BG, foreground=INK, font=(FONT, 21, 'bold'))
        style.configure('Primary.TButton', background=BLUE, foreground=WHITE,
                        font=(FONT, 10, 'bold'), borderwidth=0, padding=(18, 10))
        style.map('Primary.TButton', background=[('active', '#1B50B2')])
        style.configure('Secondary.TButton', background=PALE, foreground=BLUE,
                        font=(FONT, 10, 'bold'), borderwidth=0, padding=(14, 9))
        style.map('Secondary.TButton', background=[('active', '#D8E7FF')])
        style.configure('TEntry', padding=(8, 8), fieldbackground=WHITE, foreground=INK)
        style.configure('TCombobox', padding=(8, 7), fieldbackground=WHITE, foreground=INK)
        style.configure('Treeview', background=WHITE, fieldbackground=WHITE, foreground=INK,
                        rowheight=34, bordercolor=BORDER, borderwidth=0, font=(FONT, 10))
        style.configure('Treeview.Heading', background='#ECF1F8', foreground=INK,
                        font=(FONT, 10, 'bold'), padding=(9, 10), borderwidth=0)
        style.map('Treeview', background=[('selected', '#DCEAFF')], foreground=[('selected', INK)])

    def _build_shell(self):
        self.sidebar = tk.Frame(self, bg=NAVY, width=213)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text='PIANO  /  HIT', fg=WHITE, bg=NAVY,
                 font=(FONT, 18, 'bold'), anchor='w').pack(fill='x', padx=23, pady=(33, 5))
        tk.Label(self.sidebar, text='二校区琴房管理', fg='#A6B9D2', bg=NAVY,
                 font=(FONT, 10), anchor='w').pack(fill='x', padx=23, pady=(0, 40))
        self.nav = {}
        for key, title in [('home','总览'), ('register','学生注册'), ('book','预约琴房'),
                           ('check','签到与签退'), ('history','我的预约'), ('notice','使用公告')]:
            button = tk.Button(self.sidebar, text='  '+title, anchor='w', fg='#C5D3E7',
                bg=NAVY, activebackground='#274367', activeforeground=WHITE,
                relief='flat', bd=0, padx=20, pady=13, cursor='hand2',
                font=(FONT, 11), command=lambda k=key: self.show_page(k))
            button.pack(fill='x', padx=12, pady=3)
            self.nav[key] = button
        tk.Label(self.sidebar, text='课程作品升级版  V2.0\n非官方预约平台',
                 fg='#8197B5', bg=NAVY, justify='left', anchor='w',
                 font=(FONT, 9)).pack(side='bottom', fill='x', padx=23, pady=26)

        right = tk.Frame(self, bg=BG)
        right.pack(side='left', fill='both', expand=True)
        top = tk.Frame(right, bg=BG, height=67)
        top.pack(fill='x', padx=36, pady=(18, 0))
        self.clock_label = tk.Label(top, text='', fg=MUTED, bg=BG, font=(FONT, 10))
        self.clock_label.pack(side='right', pady=16)
        viewport = tk.Frame(right, bg=BG)
        viewport.pack(fill='both', expand=True, padx=(36, 17), pady=(0, 10))
        self.scrollbar = ttk.Scrollbar(viewport, orient='vertical')
        self.scrollbar.pack(side='right', fill='y')
        self.canvas = tk.Canvas(viewport, bg=BG, highlightthickness=0, borderwidth=0,
                                yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.config(command=self.canvas.yview)
        self.main = tk.Frame(self.canvas, bg=BG)
        self.window_id = self.canvas.create_window((0, 0), window=self.main, anchor='nw')
        self.canvas.bind('<Configure>', lambda event: self.canvas.itemconfigure(
            self.window_id, width=event.width-8))
        self.main.bind('<Configure>', lambda event: self.canvas.configure(
            scrollregion=self.canvas.bbox('all')))
        # Scroll with the mouse anywhere in the app's content area.
        self.bind_all('<MouseWheel>', self._mousewheel)
        self.bind_all('<Button-4>', lambda e: self.canvas.yview_scroll(-2, 'units'))
        self.bind_all('<Button-5>', lambda e: self.canvas.yview_scroll(2, 'units'))
        self.footer = tk.Label(right, bg=BG, fg=MUTED, font=(FONT, 9),
            text='按北京时间执行开放与预约规则  ·  所有记录仅存储在本机  ·  学校真实预约请以官方渠道为准')
        self.footer.pack(fill='x', pady=(0, 14))

    def _mousewheel(self, event):
        if event.delta:
            self.canvas.yview_scroll(int(-event.delta/120), 'units')

    def _tick(self):
        try:
            self.clock_label.config(text=self.service.now().strftime('北京时间   %Y-%m-%d  %H:%M'))
            self.after(30000, self._tick)
        except tk.TclError:
            pass

    def _on_close(self):
        self.service.close()
        self.destroy()

    def show_page(self, key):
        for child in self.main.winfo_children():
            child.destroy()
        self.canvas.yview_moveto(0)
        for nav, button in self.nav.items():
            button.config(bg=('#27476E' if nav == key else NAVY),
                          fg=(WHITE if nav == key else '#C5D3E7'))
        {'home': self._home, 'register': self._register_page, 'book': self._book,
         'check': self._check, 'history': self._history, 'notice': self._notice}[key]()

    def _heading(self, title, subtitle):
        ttk.Label(self.main, text=title, style='Hero.TLabel').pack(anchor='w', pady=(7, 6))
        ttk.Label(self.main, text=subtitle, foreground=MUTED,
                  font=(FONT, 10)).pack(anchor='w', pady=(0, 22))

    def _card(self, parent=None, padding=24):
        frame = tk.Frame(parent or self.main, bg=WHITE, highlightbackground=BORDER,
                         highlightthickness=1)
        frame.pack(fill='both', expand=False, pady=(0, 16))
        inner = ttk.Frame(frame, style='Card.TFrame', padding=padding)
        inner.pack(fill='both', expand=True)
        return inner

    def _title(self, frame, title, subtitle=None):
        ttk.Label(frame, text=title, style='Card.TLabel',
                  font=(FONT, 13, 'bold')).pack(anchor='w', pady=(0, 7))
        if subtitle:
            ttk.Label(frame, text=subtitle, style='Muted.TLabel',
                      wraplength=760).pack(anchor='w', pady=(0, 16))

    def _input(self, parent, label, secret=False, width=28):
        area = ttk.Frame(parent, style='Card.TFrame')
        area.pack(fill='x', pady=(0, 14))
        ttk.Label(area, text=label, style='Muted.TLabel').pack(anchor='w', pady=(0, 5))
        entry = ttk.Entry(area, width=width, show='●' if secret else '')
        entry.pack(fill='x')
        return entry

    def _input_grid(self, parent, fields):
        """Place 2-column form fields with common visual spacing."""
        cells = tk.Frame(parent, bg=WHITE)
        cells.pack(fill='x')
        cells.grid_columnconfigure(0, weight=1, uniform='entry')
        cells.grid_columnconfigure(1, weight=1, uniform='entry')
        entries = {}
        for i, (key, label, secret) in enumerate(fields):
            cell = tk.Frame(cells, bg=WHITE)
            cell.grid(row=i // 2, column=i % 2, sticky='ew', padx=(0 if i % 2 == 0 else 11,
                                                                   11 if i % 2 == 0 else 0), pady=(0, 15))
            tk.Label(cell, text=label, bg=WHITE, fg=MUTED,
                     font=(FONT, 10), anchor='w').pack(fill='x', pady=(0, 5))
            entry = ttk.Entry(cell, show='●' if secret else '')
            entry.pack(fill='x')
            entries[key] = entry
        return entries

    def _button(self, parent, title, callback, secondary=False):
        return ttk.Button(parent, text=title, command=callback,
                          style='Secondary.TButton' if secondary else 'Primary.TButton')

    def _run(self, callback, success=None):
        try:
            result = callback()
        except PianoError as exc:
            messagebox.showwarning('操作未完成', str(exc), parent=self)
            return None
        except Exception as exc:
            messagebox.showerror('系统错误', f'操作未完成，数据未确认写入。\n{exc}', parent=self)
            return None
        if success:
            messagebox.showinfo('操作成功', success(result) if callable(success) else success, parent=self)
        return result

    def _table(self, parent, columns, widths=None, height=8):
        outer = ttk.Frame(parent, style='Card.TFrame')
        outer.pack(fill='both', expand=True, pady=(9, 0))
        table = ttk.Treeview(outer, columns=columns, show='headings', height=height, selectmode='browse')
        for i, name in enumerate(columns):
            table.heading(name, text=name)
            table.column(name, width=(widths[i] if widths else 100), minwidth=65, anchor='center')
        bar = ttk.Scrollbar(outer, orient='vertical', command=table.yview)
        table.configure(yscrollcommand=bar.set)
        table.pack(side='left', fill='both', expand=True)
        bar.pack(side='right', fill='y')
        return table

    def _home(self):
        self._heading('琴房总览', '熟悉的二校区场景，改进后的预约体验。')
        summary = self.service.daily_summary()
        stats = tk.Frame(self.main, bg=BG)
        stats.pack(fill='x', pady=(0, 16))
        items = [('20 间', '琴房编号 01～20'),
                 (str(summary['today_bookings']), '今日预约次数'),
                 (str(summary['signed_in']), '当前已签到未签退'),
                 ('—' if summary['current_free'] is None else str(summary['current_free']),
                  '当前时段剩余琴房')]
        for n, (count, title) in enumerate(items):
            stats.grid_columnconfigure(n, weight=1, uniform='stat')
            card = tk.Frame(stats, bg=WHITE, highlightthickness=1, highlightbackground=BORDER)
            card.grid(row=0, column=n, sticky='nsew', padx=(0 if n == 0 else 7, 7 if n < 3 else 0))
            tk.Label(card, text=count, bg=WHITE, fg=BLUE, font=(FONT, 23, 'bold')).pack(anchor='w', padx=18, pady=(20, 5))
            tk.Label(card, text=title, bg=WHITE, fg=MUTED, font=(FONT, 9)).pack(anchor='w', padx=18, pady=(0, 20))
        card = self._card(padding=22)
        self._title(card, '今日剩余可预约时段',
                    '与旧版一致：过了整点后30分钟，当小时的琴房不再接受新预约。')
        hours = self.service.available_hours()
        table = self._table(card, ('时间段', '空闲琴房数量', '使用规则'), (180, 160, 300), height=8)
        for hour in hours:
            table.insert('', 'end', values=(slot_label(hour),
                         f'{len(self.service.availability(hour))} / {ROOM_COUNT}',
                         '开放预约' if self.service.availability(hour) else '本时段已约满'))
        if not hours:
            table.insert('', 'end', values=('今日预约已截止', '—', '请在次日北京时间开放时段操作'))
        self._button(card, '去预约琴房 →', lambda: self.show_page('book')).pack(anchor='e', pady=(14, 0))

    def _register_page(self):
        self._heading('学生注册', '填写原项目规定的五项资料。注册后即可开始预约。')
        card = self._card(padding=28)
        self._title(card, '创建学生账号', '系统最多接纳2000名注册学生，学号作为唯一账号。')
        entries = self._input_grid(card, [('id', '学号（仅数字）', False),
                            ('name','姓名', False), ('class','班级', False),
                            ('instrument','乐器种类', False), ('pwd','设置密码', True),
                            ('confirm','确认密码', True)])
        def save():
            if entries['pwd'].get() != entries['confirm'].get():
                raise PianoError('两次输入的密码不一致。')
            sid = self.service.register(entries['id'].get(),entries['name'].get(),
                entries['class'].get(),entries['instrument'].get(),entries['pwd'].get())
            for e in entries.values():
                e.delete(0, tk.END)
            return sid
        self._button(card, '完成注册', lambda: self._run(save, '注册成功！现在可以去预约琴房。')).pack(anchor='e', pady=8)
        card2 = self._card(padding=18)
        ttk.Label(card2, text='安全提示：密码采用加盐哈希存储，不会像旧版那样保存在明文文本文件中。',
                  style='Muted.TLabel').pack(anchor='w')

    def _book(self):
        self._heading('预约琴房', '只支持预约当天时段。选定时间、房间后，使用学号和密码确认。')
        times = self.service.available_hours()
        if not times:
            card = self._card()
            self._title(card, '今日预约时间已结束', '每天开放07:00–22:00；21:30后已无可预约时段。')
            self._button(card, '查看公告', lambda: self.show_page('notice'), True).pack(anchor='w')
            return
        box = self._card(padding=20)
        top = tk.Frame(box, bg=WHITE)
        top.pack(fill='x', pady=(0, 12))
        tk.Label(top, text='选择时间段', bg=WHITE, fg=INK, font=(FONT, 13, 'bold')).pack(side='left')
        mapping = {slot_label(h): h for h in times}
        selection = ttk.Combobox(top, values=list(mapping), state='readonly', width=22)
        selection.pack(side='right')
        selection.set(next(iter(mapping)))
        info = tk.Label(box, bg=WHITE, fg=MUTED, anchor='w', font=(FONT, 10))
        info.pack(fill='x', pady=(0, 12))
        tk.Frame(box, bg=BORDER, height=1).pack(fill='x', pady=(0, 15))
        rooms = tk.Frame(box, bg=WHITE)
        rooms.pack(fill='x')
        picked = tk.Label(box, bg=WHITE, fg=BLUE, font=(FONT, 10, 'bold'), anchor='w',
                          text='尚未选择琴房')
        picked.pack(fill='x', pady=(16, 0))
        widgets = {}
        def pick(room):
            self._selected_room = room
            picked.config(text=f'已选择：{room:02d}号琴房   |   {selection.get()}')
            for n, button in widgets.items():
                available = n in self.service.availability(mapping[selection.get()])
                button.config(bg=(BLUE if n == room else ('#E7F6F2' if available else '#F1F3F6')),
                              fg=(WHITE if n == room else (GREEN if available else '#A2AAB7')))
        def refresh(*_):
            self._selected_room = None
            widgets.clear()
            for child in rooms.winfo_children():
                child.destroy()
            hour = mapping[selection.get()]
            available = set(self.service.availability(hour))
            info.config(text=f'可预约 {len(available)} 间   /   共{ROOM_COUNT}间     ·     绿色可选，灰色已被预约')
            picked.config(text='尚未选择琴房')
            for room in range(1, ROOM_COUNT + 1):
                button = tk.Button(rooms, text=f'{room:02d}号', font=(FONT, 10, 'bold'),
                    bg=('#E7F6F2' if room in available else '#F1F3F6'),
                    fg=(GREEN if room in available else '#A2AAB7'),
                    relief='flat', cursor=('hand2' if room in available else 'arrow'),
                    padx=10, pady=12, borderwidth=0,
                    command=lambda n=room: pick(n))
                button.grid(row=(room-1)//5, column=(room-1)%5, sticky='ew', padx=5, pady=5)
                if room not in available:
                    button.config(state='disabled')
                rooms.grid_columnconfigure((room-1)%5, weight=1)
                widgets[room] = button
        selection.bind('<<ComboboxSelected>>', refresh)
        refresh()
        cred = self._card(padding=22)
        self._title(cred, '确认预约身份', '请使用已注册学号与密码，提交前系统会再次检查房间是否已被占用。')
        entries = self._input_grid(cred, [('id', '学号', False), ('password', '密码', True)])
        bottom = tk.Frame(cred, bg=WHITE)
        bottom.pack(fill='x')
        def booking():
            if self._selected_room is None:
                raise PianoError('请先选择一个空闲琴房。')
            room = self._selected_room
            hour = mapping[selection.get()]
            if not messagebox.askyesno('确认预约', f'确认预约{room:02d}号琴房，{slot_label(hour)}吗？', parent=self):
                return None
            result = self.service.book(entries['id'].get(), entries['password'].get(), hour, room)
            entries['password'].delete(0, tk.END)
            refresh()
            return result
        def do_book():
            result = self._run(booking)
            if result is not None:
                messagebox.showinfo('预约成功', f'预约成功！预约记录编号：{result}\n请按预约时间使用琴房。', parent=self)
        self._button(bottom, '刷新琴房状态', refresh, True).pack(side='left')
        self._button(bottom, '确认预约', do_book).pack(side='right')

    def _check(self):
        self._heading('签到与签退', '按“注册 → 预约 → 签到 → 签退”依次操作，完成签到后不能重复签到。')
        cred = self._card(padding=18)
        fields = self._input_grid(cred, [('id', '学号', False), ('name','姓名', False),
                                         ('password','密码', True)])
        table_card = self._card(padding=20)
        self._title(table_card, '我的预约记录', '先验证身份，再从下方选择一条今天的预约记录。')
        table = self._table(table_card, ('编号','日期','时间段','琴房','状态'), (90, 140, 180, 105, 120), height=8)
        def query():
            self.service.authenticate(fields['id'].get(), fields['password'].get(), fields['name'].get())
            rows = self.service.reservations_for(fields['id'].get(), fields['password'].get())
            for item in table.get_children():
                table.delete(item)
            for r in rows:
                table.insert('', 'end', iid=str(r['id']), values=(r['id'], r['reservation_date'],
                             slot_label(r['slot_hour']), f'{r["room_no"]:02d}号',STATUS[r['status']]))
            return rows
        self._button(cred, '验证身份并查询', lambda: self._run(query)).pack(anchor='e')
        actions = tk.Frame(table_card, bg=WHITE)
        actions.pack(fill='x', pady=(17, 0))
        def apply(action):
            selected = table.selection()
            if not selected:
                messagebox.showwarning('请选择预约', '请先选择一条预约记录。', parent=self)
                return
            rid = int(selected[0])
            def operation():
                params = (rid, fields['id'].get(), fields['name'].get(), fields['password'].get())
                return (self.service.sign_in(*params) if action == 'in' else self.service.sign_out(*params))
            message = self._run(operation)
            if message:
                self._run(query)
                messagebox.showinfo('操作成功', message, parent=self)
        self._button(actions, '签到', lambda: apply('in')).pack(side='right', padx=(10, 0))
        self._button(actions, '签退', lambda: apply('out'), True).pack(side='right')
        tk.Label(table_card, bg=WHITE, fg=MUTED, anchor='w', font=(FONT, 9),
                 text='为保护账号，升级版在签退时也会校验密码；提前签到不代表可以提前进入琴房。').pack(fill='x', pady=(15, 0))

    def _history(self):
        self._heading('我的预约', '使用学号和密码查询自己的历史预约，不会公开其他学生记录。')
        cred = self._card(padding=22)
        fields = self._input_grid(cred, [('id','学号',False), ('password','密码',True)])
        table_card = self._card(padding=20)
        self._title(table_card, '历史预约明细')
        table = self._table(table_card, ('日期','时间段','琴房','预约状态','签到时间','签退时间'),
                            (126, 155, 92, 110, 155, 155), height=11)
        def query():
            rows = self.service.reservations_for(fields['id'].get(), fields['password'].get())
            for item in table.get_children():
                table.delete(item)
            for r in rows:
                fmt = lambda value: value[11:16] if value else '—'
                table.insert('', 'end', values=(r['reservation_date'], slot_label(r['slot_hour']),
                    f'{r["room_no"]:02d}号',STATUS[r['status']],fmt(r['checked_in_at']),fmt(r['checked_out_at'])))
            return rows
        self._button(cred, '查询我的预约', lambda: self._run(query)).pack(anchor='e')

    def _notice(self):
        self._heading('琴房使用公告', '忠实保留你在2024年课程项目中写下的原始公告内容。')
        box = self._card(padding=20)
        tk.Label(box, text='说明：以下为原项目中的历史公告，不代表学校目前最新管理规定。',
                 bg='#FFF4E3', fg='#825100', anchor='w', padx=15, pady=12,
                 font=(FONT, 10)).pack(fill='x', pady=(0, 15))
        container = tk.Frame(box, bg=WHITE)
        container.pack(fill='both', expand=True)
        text = tk.Text(container, wrap='word', bg=WHITE, fg=INK, relief='flat',
                       font=(FONT, 11), padx=10, pady=10, spacing3=9, height=25,
                       highlightthickness=0)
        sb = ttk.Scrollbar(container, command=text.yview)
        text.configure(yscrollcommand=sb.set)
        text.insert('1.0', ANNOUNCEMENT)
        text.config(state='disabled')
        text.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
