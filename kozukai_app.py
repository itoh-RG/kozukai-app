# -*- coding: utf-8 -*-
"""
小遣い管理アプリ
Pythonista 3 for iOS 対応

【使い方】
1. このファイルを Pythonista の Documents フォルダにコピーする
2. Pythonista で開き、実行ボタン（▶︎）を押す
3. データは ~/Documents/kozukai_data.json に自動保存されます

【機能】
- 支出の記録（日付・金額・内容）
- 「無駄だった」チェック
- 期間フィルター（今週/今月/今年/全期間/期間指定）
- 合計・無駄遣い合計の集計
- 無駄遣いを30年・年利7%複利で運用した場合のシミュレーション
"""

import ui
import json
import os
import console
from datetime import date, datetime, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# 定数
# ─────────────────────────────────────────────────────────────────────────────

DATA_PATH      = os.path.expanduser('~/Documents/kozukai_data.json')
COMPOUND_YEARS = 30
COMPOUND_RATE  = 0.07

def compound_value(amount):
    return amount * ((1 + COMPOUND_RATE) ** COMPOUND_YEARS)

# ─────────────────────────────────────────────────────────────────────────────
# データ層
# ─────────────────────────────────────────────────────────────────────────────

_expenses = []
_next_id  = 1

def load_data():
    global _expenses, _next_id
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            _expenses = raw.get('expenses', [])
            _next_id  = raw.get('next_id', 1)
        except Exception:
            _expenses, _next_id = [], 1
    else:
        _expenses, _next_id = [], 1

def save_data():
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump({'expenses': _expenses, 'next_id': _next_id},
                  f, ensure_ascii=False, indent=2)

def add_expense(date_str, amount, desc, wasteful):
    global _next_id
    _expenses.append({'id': _next_id, 'date': date_str,
                      'amount': amount, 'description': desc,
                      'wasteful': wasteful})
    _next_id += 1
    save_data()

def update_expense(eid, date_str, amount, desc, wasteful):
    for e in _expenses:
        if e['id'] == eid:
            e.update({'date': date_str, 'amount': amount,
                      'description': desc, 'wasteful': wasteful})
            break
    save_data()

def delete_expense(eid):
    global _expenses
    _expenses = [e for e in _expenses if e['id'] != eid]
    save_data()

def get_expenses(start: str, end: str):
    return sorted(
        [e for e in _expenses if start <= e['date'] <= end],
        key=lambda x: x['date'], reverse=True
    )

# ─────────────────────────────────────────────────────────────────────────────
# 期間ユーティリティ
# ─────────────────────────────────────────────────────────────────────────────

def period_this_week():
    today = date.today()
    start = today - timedelta(days=today.weekday())
    return start.isoformat(), today.isoformat()

def period_this_month():
    today = date.today()
    return date(today.year, today.month, 1).isoformat(), today.isoformat()

def period_this_year():
    today = date.today()
    return date(today.year, 1, 1).isoformat(), today.isoformat()

def period_all():
    return '0000-01-01', '9999-12-31'

PERIOD_FUNCS = [period_this_week, period_this_month, period_this_year, period_all]
PERIOD_NAMES = ['今週', '今月', '今年', '全期間', '期間指定']

def fmt_date(date_str):
    try:
        d = datetime.strptime(date_str, '%Y-%m-%d').date()
        today = date.today()
        if d == today:
            return '今日'
        if d == today - timedelta(days=1):
            return '昨日'
        if d.year == today.year:
            return f'{d.month}/{d.day}'
        return f'{d.year}/{d.month}/{d.day}'
    except Exception:
        return date_str

# ─────────────────────────────────────────────────────────────────────────────
# 追加・編集画面
# ─────────────────────────────────────────────────────────────────────────────

class AddEditView(ui.View):
    def __init__(self, expense=None, on_done=None):
        self.expense  = expense
        self.on_done  = on_done
        self.name     = '編集' if expense else '追加'
        self.background_color = 'white'
        self._built   = False

    def layout(self):
        if not self._built:
            self._build()
        self.scroll.frame = (0, 0, self.width, self.height)

    def _build(self):
        self._built = True
        W = self.width or 375

        self.scroll = ui.ScrollView(frame=(0, 0, W, self.height))
        self.scroll.autoresizing = 'WH'
        self.add_subview(self.scroll)

        y = 20

        # ── 日付 ──────────────────────────────────────────────────────────
        self._section_label(y, W, '日付（YYYY-MM-DD）')
        y += 26

        self.date_tf = ui.TextField(frame=(16, y, W - 32, 46))
        self.date_tf.placeholder = '例: 2025-01-15'
        self.date_tf.border_width = 0.5
        self.date_tf.border_color = (0.8, 0.8, 0.8, 1)
        self.date_tf.corner_radius = 8
        self.date_tf.font = ('<system>', 22)
        self.date_tf.text = (self.expense['date'] if self.expense
                             else datetime.now().strftime('%Y-%m-%d'))
        self.scroll.add_subview(self.date_tf)
        y += 54

        # ── 金額 ──────────────────────────────────────────────────────────
        self._section_label(y, W, '金額（円）')
        y += 26

        self.amount_tf = ui.TextField(frame=(16, y, W - 32, 46))
        self.amount_tf.placeholder = '例: 500'
        self.amount_tf.text_alignment = ui.ALIGN_RIGHT
        self.amount_tf.border_width = 0.5
        self.amount_tf.border_color = (0.8, 0.8, 0.8, 1)
        self.amount_tf.corner_radius = 8
        self.amount_tf.font = ('<system>', 22)
        if self.expense:
            self.amount_tf.text = str(self.expense['amount'])
        self.scroll.add_subview(self.amount_tf)
        y += 54

        # ── 内容 ──────────────────────────────────────────────────────────
        self._section_label(y, W, '内容')
        y += 26

        self.desc_tf = ui.TextField(frame=(16, y, W - 32, 46))
        self.desc_tf.placeholder = '例: コーヒー、ランチ、本...'
        self.desc_tf.border_width = 0.5
        self.desc_tf.border_color = (0.8, 0.8, 0.8, 1)
        self.desc_tf.corner_radius = 8
        self.desc_tf.font = ('<system>', 17)
        if self.expense:
            self.desc_tf.text = self.expense['description']
        self.scroll.add_subview(self.desc_tf)
        y += 54

        # ── 無駄だった ────────────────────────────────────────────────────
        self._add_sep(y, W); y += 1

        waste_lbl = ui.Label(frame=(16, y + 12, W - 90, 28))
        waste_lbl.text = '💸 無駄だった'
        waste_lbl.font = ('<system>', 17)
        self.scroll.add_subview(waste_lbl)

        self.waste_sw = ui.Switch(frame=(W - 67, y + 12, 51, 31))
        self.waste_sw.value = self.expense.get('wasteful', False) if self.expense else False
        self.scroll.add_subview(self.waste_sw)
        y += 54

        self._add_sep(y, W); y += 12

        # ── 保存ボタン ────────────────────────────────────────────────────
        save_btn = ui.Button(frame=(16, y, W - 32, 48))
        save_btn.title = '保存する'
        save_btn.background_color = '#007AFF'
        save_btn.tint_color = 'white'
        save_btn.corner_radius = 10
        save_btn.font = ('<system-bold>', 17)
        save_btn.action = self._save
        self.scroll.add_subview(save_btn)
        y += 58

        # ── 削除ボタン（編集時のみ）──────────────────────────────────────
        if self.expense:
            del_btn = ui.Button(frame=(16, y, W - 32, 48))
            del_btn.title = '削除する'
            del_btn.background_color = '#FF3B30'
            del_btn.tint_color = 'white'
            del_btn.corner_radius = 10
            del_btn.font = ('<system-bold>', 17)
            del_btn.action = self._delete
            self.scroll.add_subview(del_btn)
            y += 58

        self.scroll.content_size = (W, y + 20)

    def _section_label(self, y, W, text):
        lbl = ui.Label(frame=(16, y, W - 32, 22))
        lbl.text = text
        lbl.font = ('<system>', 13)
        lbl.text_color = '#888'
        self.scroll.add_subview(lbl)

    def _add_sep(self, y, W):
        sep = ui.View(frame=(0, y, W, 0.5))
        sep.background_color = '#e5e5e5'
        self.scroll.add_subview(sep)

    def _save(self, sender):
        raw = self.amount_tf.text.replace(',', '').replace('¥', '').strip()
        try:
            amount = int(raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            console.hud_alert('正しい金額を入力してください', 'error', 1.5)
            return

        desc = self.desc_tf.text.strip()
        if not desc:
            console.hud_alert('内容を入力してください', 'error', 1.5)
            return

        date_str = self.date_tf.text.strip()
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            console.hud_alert('日付は YYYY-MM-DD 形式で入力してください', 'error', 2)
            return
        wasteful  = self.waste_sw.value

        if self.expense:
            update_expense(self.expense['id'], date_str, amount, desc, wasteful)
        else:
            add_expense(date_str, amount, desc, wasteful)

        if self.on_done:
            self.on_done()
        if self.navigation_view:
            self.navigation_view.pop_view()

    def _delete(self, sender):
        delete_expense(self.expense['id'])
        if self.on_done:
            self.on_done()
        if self.navigation_view:
            self.navigation_view.pop_view()

# ─────────────────────────────────────────────────────────────────────────────
# 期間指定画面
# ─────────────────────────────────────────────────────────────────────────────

class CustomPeriodView(ui.View):
    def __init__(self, start_str, end_str, on_apply):
        self.on_apply    = on_apply
        self.name        = '期間を指定'
        self.background_color = 'white'
        self._start_str  = start_str
        self._end_str    = end_str
        self._built      = False

    def layout(self):
        if not self._built:
            self._build()

    def _build(self):
        self._built = True
        W = self.width or 375
        y = 20

        def section_lbl(text):
            nonlocal y
            lbl = ui.Label(frame=(16, y, W - 32, 22))
            lbl.text = text
            lbl.font = ('<system>', 13)
            lbl.text_color = '#888'
            self.add_subview(lbl)
            y += 26

        section_lbl('開始日（YYYY-MM-DD）')
        self.start_tf = ui.TextField(frame=(16, y, W - 32, 46))
        self.start_tf.border_width = 0.5
        self.start_tf.border_color = (0.8, 0.8, 0.8, 1)
        self.start_tf.corner_radius = 8
        self.start_tf.font = ('<system>', 20)
        self.start_tf.text = self._start_str
        self.add_subview(self.start_tf)
        y += 54

        section_lbl('終了日（YYYY-MM-DD）')
        self.end_tf = ui.TextField(frame=(16, y, W - 32, 46))
        self.end_tf.border_width = 0.5
        self.end_tf.border_color = (0.8, 0.8, 0.8, 1)
        self.end_tf.corner_radius = 8
        self.end_tf.font = ('<system>', 20)
        self.end_tf.text = self._end_str
        self.add_subview(self.end_tf)
        y += 54

        apply_btn = ui.Button(frame=(16, y, W - 32, 48))
        apply_btn.title = 'この期間で絞り込む'
        apply_btn.background_color = '#007AFF'
        apply_btn.tint_color = 'white'
        apply_btn.corner_radius = 10
        apply_btn.font = ('<system-bold>', 17)
        apply_btn.action = self._apply
        self.add_subview(apply_btn)

    def _apply(self, sender):
        s = self.start_tf.text.strip()
        e = self.end_tf.text.strip()
        try:
            datetime.strptime(s, '%Y-%m-%d')
            datetime.strptime(e, '%Y-%m-%d')
        except ValueError:
            console.hud_alert('日付は YYYY-MM-DD 形式で入力してください', 'error', 2)
            return
        if s > e:
            s, e = e, s
        self.on_apply(s, e)
        if self.navigation_view:
            self.navigation_view.pop_view()

# ─────────────────────────────────────────────────────────────────────────────
# メインリスト画面
# ─────────────────────────────────────────────────────────────────────────────

STATS_H = 132

class ExpenseListView(ui.View):
    def __init__(self):
        self.name         = '小遣い管理'
        self.background_color = 'white'
        self._nav         = None
        self._built       = False
        self._period_idx  = 1          # 今月
        s, e = period_this_month()
        self._custom_start = s
        self._custom_end   = e
        self._items        = []

    def set_nav(self, nav):
        self._nav = nav

    def layout(self):
        if not self._built:
            self._build()
            return
        W, H = self.width, self.height
        self.seg.frame        = (8,   8, W - 16, 32)
        self.period_lbl.frame = (8,  46, W - 16, 20)
        self.tbl.frame        = (0,  70, W, H - 70 - STATS_H)
        self.stats_bg.frame   = (0, H - STATS_H, W, STATS_H)
        self.total_lbl.frame  = (16, H - STATS_H + 8,  W - 32, 24)
        self.waste_lbl.frame  = (16, H - STATS_H + 36, W - 32, 24)
        self.cmpd_lbl.frame   = (16, H - STATS_H + 64, W - 32, 60)

    def _build(self):
        self._built = True
        W, H = self.width, self.height

        # セグメント（期間選択）
        self.seg = ui.SegmentedControl(frame=(8, 8, W - 16, 32))
        self.seg.segments = PERIOD_NAMES
        self.seg.selected_index = self._period_idx
        self.seg.action = self._on_period
        self.add_subview(self.seg)

        # 選択中の期間ラベル
        self.period_lbl = ui.Label(frame=(8, 46, W - 16, 20))
        self.period_lbl.font = ('<system>', 12)
        self.period_lbl.text_color = '#888'
        self.period_lbl.text_alignment = ui.ALIGN_CENTER
        self.add_subview(self.period_lbl)

        # 明細テーブル
        self.tbl = ui.TableView(frame=(0, 70, W, H - 70 - STATS_H))
        self.tbl.row_height = 54
        self.tbl.data_source = self
        self.tbl.delegate    = self
        self.add_subview(self.tbl)

        # 統計エリア（背景）
        self.stats_bg = ui.View(frame=(0, H - STATS_H, W, STATS_H))
        self.stats_bg.background_color = '#F2F2F7'
        self.add_subview(self.stats_bg)

        sep = ui.View(frame=(0, 0, W, 0.5))
        sep.background_color = '#C6C6C8'
        self.stats_bg.add_subview(sep)

        # 統計ラベル群
        self.total_lbl = ui.Label(frame=(16, H - STATS_H + 8, W - 32, 24))
        self.total_lbl.font = ('<system-bold>', 15)
        self.add_subview(self.total_lbl)

        self.waste_lbl = ui.Label(frame=(16, H - STATS_H + 36, W - 32, 24))
        self.waste_lbl.font = ('<system>', 14)
        self.waste_lbl.text_color = '#FF3B30'
        self.add_subview(self.waste_lbl)

        self.cmpd_lbl = ui.Label(frame=(16, H - STATS_H + 64, W - 32, 60))
        self.cmpd_lbl.font = ('<system>', 13)
        self.cmpd_lbl.text_color = '#FF9500'
        self.cmpd_lbl.number_of_lines = 0
        self.add_subview(self.cmpd_lbl)

        # ナビバー右ボタン（追加）
        add_btn = ui.ButtonItem(title='追加 +')
        add_btn.action = self._on_add
        self.right_button_items = [add_btn]

        self._refresh()

    # ── フィルター ──────────────────────────────────────────────────────────

    def _on_period(self, sender):
        self._period_idx = sender.selected_index
        self._refresh()
        if self._period_idx == 4:
            view = CustomPeriodView(self._custom_start, self._custom_end,
                                    self._on_custom_period)
            if self._nav:
                self._nav.push_view(view)

    def _on_custom_period(self, start, end):
        self._custom_start = start
        self._custom_end   = end
        self._refresh()

    def _refresh(self):
        idx = self._period_idx
        s, e = (PERIOD_FUNCS[idx]() if idx < 4
                else (self._custom_start, self._custom_end))
        self._items = get_expenses(s, e)
        if self._built:
            self._update_period_label(s, e)
            self.tbl.reload_data()
            self._update_stats()

    def _update_period_label(self, s, e):
        if self._period_idx < 4:
            self.period_lbl.text = ['今週', '今月', '今年', '全期間'][self._period_idx]
        else:
            self.period_lbl.text = f'{s}  〜  {e}'

    def _update_stats(self):
        total      = sum(e['amount'] for e in self._items)
        wasteful   = [e for e in self._items if e.get('wasteful')]
        w_total    = sum(e['amount'] for e in wasteful)
        future     = compound_value(w_total)

        self.total_lbl.text = f'合計  ¥{total:,}  （{len(self._items)}件）'

        if w_total > 0:
            self.waste_lbl.text = f'💸 無駄遣い  ¥{w_total:,}  （{len(wasteful)}件）'
            gain = int(future) - w_total
            self.cmpd_lbl.text = (
                f'30年・年利7%複利で運用していたら\n'
                f'¥{w_total:,} → ¥{int(future):,}（+¥{gain:,}の機会損失）'
            )
        else:
            self.waste_lbl.text = '💸 無駄遣い  ¥0'
            self.cmpd_lbl.text  = '無駄遣いなし 👍'

    # ── 追加 ────────────────────────────────────────────────────────────────

    def _on_add(self, sender):
        view = AddEditView(on_done=self._refresh)
        if self._nav:
            self._nav.push_view(view)

    # ── TableViewDataSource ──────────────────────────────────────────────────

    def tableview_number_of_sections(self, tv):
        return 1

    def tableview_number_of_rows(self, tv, section):
        return len(self._items)

    def tableview_cell_for_row(self, tv, section, row):
        e    = self._items[row]
        cell = ui.TableViewCell('subtitle')

        cell.text_label.text   = e['description']
        cell.text_label.font   = ('<system>', 16)
        cell.detail_text_label.text  = fmt_date(e['date'])
        cell.detail_text_label.font  = ('<system>', 12)
        cell.detail_text_label.text_color = '#888'

        # 金額ラベル（右側）
        amt = ui.Label()
        amt.text       = f'¥{e["amount"]:,}'
        amt.font       = ('<system-bold>', 16)
        amt.text_color = '#FF3B30' if e.get('wasteful') else '#111'
        amt.size_to_fit()
        cell.accessory_view = amt

        if e.get('wasteful'):
            cell.content_view.background_color = '#FFF2F2'

        return cell

    # ── TableViewDelegate ────────────────────────────────────────────────────

    def tableview_did_select(self, tv, section, row):
        e    = self._items[row]
        view = AddEditView(expense=e, on_done=self._refresh)
        if self._nav:
            self._nav.push_view(view)

    def tableview_can_delete(self, tv, section, row):
        return True

    def tableview_delete(self, tv, section, row):
        delete_expense(self._items[row]['id'])
        self._refresh()

# ─────────────────────────────────────────────────────────────────────────────
# エントリーポイント
# ─────────────────────────────────────────────────────────────────────────────

def main():
    load_data()
    list_view = ExpenseListView()
    nav = ui.NavigationView(list_view)
    nav.name = '小遣い管理'
    list_view.set_nav(nav)
    nav.present('fullscreen')


if __name__ == '__main__':
    main()
