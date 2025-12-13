import yfinance as yf
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Ultimate Stock Dashboard", layout="wide")
st.title("📈 Ultimate Stock Market Analysis Dashboard")

# ---------------- NSE STOCK LIST ----------------
stocks = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS",
    "ICICIBANK.NS", "SBIN.NS", "RPOWER.NS", "ITC.NS"
]

stock = st.selectbox("Select NSE Stock", stocks)

# ---------------- DATA DOWNLOAD ----------------
data = yf.download(stock, period="6mo")
nifty = yf.download("^NSEI", period="6mo")

if data.empty:
    st.error("No data found")
    st.stop()

# ---------------- INDICATORS ----------------
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

# ---------------- NIFTY FILTER ----------------
nifty["MA50"] = nifty["Close"].rolling(50).mean()
nifty["MA50"] = nifty["Close"].rolling(50).mean()

latest_nifty_close = float(nifty["Close"].iloc[-1])
latest_nifty_ma50 = float(nifty["MA50"].iloc[-1])

if pd.isna(latest_nifty_ma50):
    market_trend = "⚠️ Not enough NIFTY data"
elif latest_nifty_close > latest_nifty_ma50:
    market_trend = "🟢 Bullish"
else:
    market_trend = "🔴 Bearish"


# ---------------- SIGNAL ----------------
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

# ---------------- DISPLAY ----------------
st.subheader(f"📌 Signal: {signal}")
st.write(f"Last Price: **{close:.2f}**")
st.write(f"RSI: **{rsi:.2f}**")
st.write(f"Market Trend (NIFTY): **{market_trend}**")

# ---------------- CANDLE + MA ----------------
st.subheader("🕯️ Price Chart")
plt.figure(figsize=(12,5))
plt.plot(data["Close"], label="Close")
plt.plot(data["MA20"], label="MA20")
plt.plot(data["MA50"], label="MA50")

if signal == "🟢 BUY":
    plt.scatter(data.index[-1], close, marker="^", s=200)
elif signal == "🔴 SELL":
    plt.scatter(data.index[-1], close, marker="v", s=200)

plt.legend()
st.pyplot(plt)

# ---------------- VOLUME ----------------
# ---------------- VOLUME ----------------
st.subheader("📦 Volume Analysis")

volume = data["Volume"].values.flatten()

plt.figure(figsize=(12, 3))
plt.bar(data.index, volume)
plt.xlabel("Date")
plt.ylabel("Volume")
st.pyplot(plt)

# ---------------- MACD ----------------
st.subheader("📊 MACD")
plt.figure(figsize=(12,3))
plt.plot(data["MACD"], label="MACD")
plt.plot(data["MACD_Signal"], label="Signal")
plt.legend()
st.pyplot(plt)

# ---------------- RSI ----------------
st.subheader("📉 RSI")
plt.figure(figsize=(12,3))
plt.plot(data["RSI"])
plt.axhline(70)
plt.axhline(30)
st.pyplot(plt)

# ---------------- ML PREDICTION ----------------
st.subheader("🤖 ML Price Prediction (Next Day)")

df = data.reset_index()
df["Day"] = np.arange(len(df))

X = df[["Day"]]
y = df["Close"]

model = LinearRegression()
model.fit(X, y)

next_day = [[len(df)]]
predicted_price = float(model.predict(next_day).item())

st.success(f"Predicted Next Price: ₹ {predicted_price:.2f}")

# ---------------- PRICE ALERT ----------------
st.subheader("🔔 Price Alert")
alert_price = st.number_input("Set Alert Price", value=close)

if close >= alert_price:
    st.warning("⚠️ Alert Triggered: Price Reached!")

# ---------------- DATA ----------------
with st.expander("📄 View Data"):
    st.dataframe(data.tail(15))
