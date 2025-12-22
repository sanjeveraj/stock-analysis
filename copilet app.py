# main.py
# Stock Live Analysis App with Colorful UI and Animated Text
# Requires: kivy, yfinance
# pip install kivy yfinance

import threading
import time
from datetime import datetime

import yfinance as yf
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, ColorProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.animation import Animation

KV = """
#:import rgba kivy.utils.get_color_from_hex

<MarqueeLabel@Label>:
    size_hint_y: None
    height: dp(32)
    canvas.before:
        Color:
            rgba: rgba('#10172A')  # dark background
        Rectangle:
            pos: self.pos
            size: self.size

<StockCard@BoxLayout>:
    orientation: 'vertical'
    padding: dp(12)
    spacing: dp(8)
    size_hint_y: None
    height: self.minimum_height
    canvas.before:
        Color:
            rgba: root.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [12, 12, 12, 12]
    Label:
        text: root.symbol
        font_size: '20sp'
        bold: True
        color: rgba('#FFFFFF')
        size_hint_y: None
        height: self.texture_size[1]
    Label:
        id: price_label
        text: root.price_text
        font_size: '28sp'
        color: root.price_color
        size_hint_y: None
        height: self.texture_size[1]
    BoxLayout:
        spacing: dp(12)
        size_hint_y: None
        height: dp(24)
        Label:
            text: root.change_text
            color: rgba('#FFFFFF')
            font_size: '16sp'
        Label:
            text: root.percent_text
            color: rgba('#FFFFFF')
            font_size: '16sp'
    Label:
        text: root.updated_text
        color: rgba('#D1D5DB')
        font_size: '12sp'
        size_hint_y: None
        height: self.texture_size[1]

<Content>:
    orientation: 'vertical'
    spacing: dp(12)
    canvas.before:
        Color:
            rgba: rgba('#0B1220')  # page background
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        size_hint_y: None
        height: dp(56)
        padding: dp(12)
        spacing: dp(8)
        canvas.before:
            Color:
                rgba: rgba('#1F2937')
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: "Live Stock Analysis"
            color: rgba('#FFFFFF')
            font_size: '20sp'
            bold: True
        Button:
            text: "Refresh"
            background_color: rgba('#10B981')  # teal
            color: rgba('#0B1220')
            on_release: root.manual_refresh()
    MarqueeLabel:
        id: marquee
        text: root.marquee_text
        color: rgba('#93C5FD')  # soft blue
        font_size: '16sp'
    ScrollView:
        do_scroll_x: False
        bar_width: dp(3)
        GridLayout:
            id: grid
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            padding: dp(12)
            spacing: dp(12)
"""

class StockCard(BoxLayout):
    symbol = StringProperty("")
    price_text = StringProperty("--")
    change_text = StringProperty("--")
    percent_text = StringProperty("--")
    updated_text = StringProperty("Updated: --")
    price_color = ColorProperty([1, 1, 1, 1])
    bg_color = ColorProperty([0.12, 0.16, 0.32, 1])  # default dark indigo

    def pulse_price(self, up=True):
        # Animate price color pulse on update
        target = [0.22, 0.73, 0.49, 1] if up else [0.9, 0.33, 0.33, 1]
        anim = Animation(price_color=target, duration=0.15) + Animation(price_color=[1, 1, 1, 1], duration=0.5)
        anim.start(self)

class Content(BoxLayout):
    marquee_text = StringProperty("Markets open. Stay nimble. Diversify. Risk management first.")
    symbols = ListProperty(["AAPL", "TSLA", "INFY.NS", "RELIANCE.NS", "HDFCBANK.NS"])
    cards = {}

    def on_kv_post(self, base_widget):
        grid = self.ids.grid
        # Assign different vibrant backgrounds per card
        palette = [
            [0.09, 0.60, 0.98, 1],  # blue
            [0.95, 0.51, 0.15, 1],  # orange
            [0.10, 0.72, 0.61, 1],  # teal
            [0.88, 0.26, 0.49, 1],  # pink
            [0.55, 0.47, 0.95, 1],  # violet
        ]
        for i, sym in enumerate(self.symbols):
            card = StockCard(symbol=sym)
            card.bg_color = palette[i % len(palette)]
            grid.add_widget(card)
            self.cards[sym] = card

        # Start marquee animation and data loop
        Clock.schedule_once(lambda dt: self.start_marquee(), 0.3)
        threading.Thread(target=self.data_loop, daemon=True).start()

    def start_marquee(self):
        label = self.ids.marquee
        # Start the text off-screen right and move left continuously
        label.texture_update()
        width = self.width if self.width > 0 else 360
        label.x = width
        def animate():
            label.texture_update()
            text_width = label.texture_size[0] + 40
            anim = Animation(x=-text_width, duration=10, t='linear')
            anim.bind(on_complete=lambda *args: reset())
            anim.start(label)
        def reset():
            label.x = self.width
            animate()
        animate()

    def manual_refresh(self):
        threading.Thread(target=self.fetch_all, daemon=True).start()
        self.flash_marquee("Manual refresh…")

    def flash_marquee(self, text):
        self.marquee_text = text
        # brief color flash
        label = self.ids.marquee
        anim = Animation(color=[1, 1, 1, 1], duration=0.15) + Animation(color=[0.58, 0.77, 0.99, 1], duration=0.7)
        anim.start(label)

    def data_loop(self):
        # Continuous fetch every 10 seconds
        while True:
            self.fetch_all()
            time.sleep(10)

    def fetch_all(self):
        updates = []
        for sym in self.symbols:
            data = self.fetch_symbol(sym)
            if data:
                updates.append(data)
        if updates:
            Clock.schedule_once(lambda dt: self.apply_updates(updates))

    def fetch_symbol(self, sym):
        try:
            t = yf.Ticker(sym)
            # Try fast_info first for quick price
            price = None
            change = None
            percent = None

            # Fast path
            try:
                fi = t.fast_info
                price = fi.get("last_price")
                prev_close = fi.get("previous_close")
                if price is not None and prev_close:
                    change = price - prev_close
                    percent = (change / prev_close) * 100
            except Exception:
                pass

            # Fallback via recent 1m data
            if price is None:
                hist = t.history(period="1d", interval="1m")
                if not hist.empty:
                    price = float(hist["Close"].iloc[-1])
                    prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
                    change = price - prev_close
                    percent = (change / prev_close) * 100 if prev_close else 0.0

            if price is None:
                return None

            # Format and pass back
            now = datetime.now().strftime("%H:%M:%S")
            return {
                "symbol": sym,
                "price": price,
                "change": change or 0.0,
                "percent": percent or 0.0,
                "updated": f"Updated: {now}",
            }
        except Exception:
            return None

    def apply_updates(self, updates):
        # Update UI on main thread
        for u in updates:
            card = self.cards.get(u["symbol"])
            if not card:
                continue
            price_prev = None
            try:
                # Parse previous price from text, if any
                if card.price_text != "--":
                    price_prev = float(card.price_text.replace(",", ""))
            except Exception:
                price_prev = None

            card.price_text = f"{u['price']:.2f}"
            sign = "+" if u["change"] >= 0 else "-"
            card.change_text = f"Change: {sign}{abs(u['change']):.2f}"
            card.percent_text = f"{sign}{abs(u['percent']):.2f}%"
            card.updated_text = u["updated"]

            # Pulse animation if price changed
            if price_prev is None or u["price"] != price_prev:
                card.pulse_price(up=(u["change"] >= 0))

class StockLiveApp(App):
    def build(self):
        Builder.load_string(KV)
        return Content()

if __name__ == "__main__":
    StockLiveApp().run()
