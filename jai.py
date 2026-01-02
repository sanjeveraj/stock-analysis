# ===================== IMPORTS =====================
import yfinance as yf
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression

# ===================== PAGE CONFIG =====================
st.set_page_config(page_title="Ultimate Stock Dashboard", layout="wide")
st.title("📈 Ultimate Stock Market Analysis Dashboard")

# ===================== STOCK LIST =====================
stocks = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS",
    "ICICIBANK.NS", "SBIN.NS", "RPOWER.NS", "ITC.NS"
]

stock = st.selectbox("Select NSE Stock", stocks)

# ===================== DATA DOWNLOAD =====================
try:
    data = yf.download(stock, period="6mo", progress=False)
    nifty = yf.download("^NSEI", period="6mo", progress=False)
except:
    st.error("❌ Data download failed")
    st.stop()

if data.empty:
    st.error("❌ No stock data found")
    st.stop()

# ===================== INDICATORS =====================
data["MA20"] = data["Close"].rolling(20).mean()
data["MA50"] = data["Close"].rolling(50).mean()

# RSI
delta = data["Close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)
avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()
rs = avg_gain / avg_loss
data["RSI"] = 100 - (100 / (1 + rs))

# MACD
ema12 = data["Close"].ewm(span=12, adjust=False).mean()
ema26 = data["Close"].ewm(span=26, adjust=False).mean()
data["MACD"] = ema12 - ema26
data["MACD_Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()

# ===================== MARKET TREND =====================
# ---------------- NIFTY TREND (FIXED) ----------------
nifty["MA50"] = nifty["Close"].rolling(50).mean()

market_trend = "⚠️ Not enough NIFTY data"

try:
    nifty_close = float(nifty["Close"].iloc[-1])
    nifty_ma50 = float(nifty["MA50"].iloc[-1])

    if not np.isnan(nifty_ma50):
        if nifty_close > nifty_ma50:
            market_trend = "🟢 Bullish"
        else:
            market_trend = "🔴 Bearish"
except:
    market_trend = "⚠️ NIFTY data error"


# ===================== SIGNAL =====================
close = float(data["Close"].iloc[-1])
ma20 = float(data["MA20"].iloc[-1])
rsi = float(data["RSI"].iloc[-1])
macd = float(data["MACD"].iloc[-1])
macd_sig = float(data["MACD_Signal"].iloc[-1])

if close > ma20 and rsi < 70 and macd > macd_sig and market_trend == "🟢 Bullish":
    signal = "🟢 BUY"
elif close < ma20 and rsi > 30:
    signal = "🔴 SELL"
else:
    signal = "🟡 HOLD"

# ===================== DISPLAY =====================
st.subheader(f"📌 Signal: {signal}")
st.write(f"Last Price: **₹{close:.2f}**")
st.write(f"RSI: **{rsi:.2f}**")
st.write(f"Market Trend (NIFTY): **{market_trend}**")

# ===================== PRICE CHART =====================
st.subheader("🕯️ Price Chart")
plt.figure(figsize=(12,5))
plt.plot(data["Close"], label="Close")
plt.plot(data["MA20"], label="MA20")
plt.plot(data["MA50"], label="MA50")
plt.legend()
st.pyplot(plt)
plt.clf()

# ===================== VOLUME =====================
st.subheader("📦 Volume")
plt.figure(figsize=(12,3))
plt.bar(data.index, data["Volume"])
st.pyplot(plt)
plt.clf()

# ===================== MACD =====================
st.subheader("📊 MACD")
plt.figure(figsize=(12,3))
plt.plot(data["MACD"], label="MACD")
plt.plot(data["MACD_Signal"], label="Signal")
plt.legend()
st.pyplot(plt)
plt.clf()

# ===================== RSI =====================
st.subheader("📉 RSI")
plt.figure(figsize=(12,3))
plt.plot(data["RSI"])
plt.axhline(70)
plt.axhline(30)
st.pyplot(plt)
plt.clf()

# ===================== ML PREDICTION =====================
st.subheader("🤖 ML Prediction (Educational)")

df = data.reset_index()
df["Day"] = np.arange(len(df))
X = df[["Day"]]
y = df["Close"]

model = LinearRegression()
model.fit(X, y)

predicted_price = float(model.predict([[len(df)]]))
st.success(f"Predicted Next Price: ₹{predicted_price:.2f}")

# ===================== PRICE ALERT =====================
st.subheader("🔔 Price Alert")
alert_price = st.number_input("Set Alert Price", value=float(close))
if close >= alert_price:
    st.warning("⚠️ Alert Triggered!")

# ===================== SIMILAR STOCKS =====================
st.subheader("🔁 Similar Stocks")

similar = {
    "RPOWER": ["NTPC.NS", "ADANIPOWER.NS", "POWERGRID.NS"]
}

key = stock.replace(".NS", "")
if key in similar:
    for s in similar[key]:
        try:
            p = yf.Ticker(s).fast_info["last_price"]
            st.write(f"{s} → ₹{p}")
        except:
            st.write(f"{s} → Data not available")

# ===================== SHAREHOLDING (STATIC SAFE) =====================
st.subheader("👥 Shareholding Pattern")

shareholding = {
    "Retail": 58.18,
    "Promoters": 24.98,
    "FIIs": 13.09,
    "DIIs": 3.02,
    "Mutual Funds": 0.72
}

sh_df = pd.DataFrame(shareholding.items(), columns=["Category", "Percent"])
st.bar_chart(sh_df.set_index("Category"))

# ===================== FUNDAMENTALS (SAFE) =====================
st.subheader("📌 Fundamentals")

try:
    info = yf.Ticker(stock).fast_info
except:
    info = {}

c1, c2 = st.columns(2)

with c1:
    st.metric("Market Cap", info.get("market_cap", "N/A"))
    st.metric("Day High", info.get("day_high", "N/A"))
    st.metric("Day Low", info.get("day_low", "N/A"))

with c2:
    st.metric("52W High", info.get("year_high", "N/A"))
    st.metric("52W Low", info.get("year_low", "N/A"))
    st.metric("Volume", info.get("last_volume", "N/A"))

# ===================== DATA TABLE =====================
with st.expander("📄 View Data"):
    st.dataframe(data.tail(15))
