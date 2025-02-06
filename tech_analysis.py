import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import ollama
import tempfile
import base64
import os

# Set up Streamlit app
st.set_page_config(layout="wide")
st.title("AI-Powered Technical Stock Analysis Dashboard")
st.sidebar.header("Configuration")

# Input for stock ticker and date range
ticker =st.sidebar.text_input("Enter stock TIcker, default: AAPL")
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2024-01-01"))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2025-01-01"))

# Fetch stock data
if st.sidebar.button("Fetch Data"):
    st.session_state["stock_data"] = yf.download(ticker, start=start_date, end=end_date, interval="1h")
    st.success("Stock data loaded successfully")

# Check if data is available
if "stock_data" in st.session_state:
    data = st.session_state["stock_data"]

    # Plot candlestick chart
    fig = go.Figure(data=[
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Candlestick"
        )
    ])

    # Sidebar: Select technical indicator
    st.sidebar.subheader("Technical Indicators")
    indicators = st.sidebar.multiselect(
        "Select Indicators:",
        ["20-Day SMA", "20-Day EMA", "20-Day Bollinger Bands", "VWAP"],
        default=["20-Day SMA"]
    )

    # Helper function to add indicators to the chart
    def add_indicator(indicator):
        if indicator == "20-Day SMA":
            sma = data['Close'].rolling(window=20).mean()
            fig.add_trace(go.Scatter(x=data.index, y=sma, mode='lines', name='SMA (20)'))
        elif indicator == "20-Day EMA":
            ema = data['Close'].ewm(span=20).mean()
            fig.add_trace(go.Scatter(x=data.index, y=ema, mode='lines', name='EMA (20)'))
        elif indicator == "20-Day Bollinger Bands":
            sma = data['Close'].rolling(window=20).mean()
            std = data['Close'].rolling(window=20).std()
            bb_upper = sma + 2 * std
            bb_lower = sma - 2 * std
            fig.add_trace(go.Scatter(x=data.index, y=bb_upper, mode='lines', name='BB Upper 2sigma'))
            fig.add_trace(go.Scatter(x=data.index, y=bb_lower, mode='lines', name='BB Lower 2sigma'))
        elif indicator == "VWAP":
            data['VWAP'] = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
            fig.add_trace(go.Scatter(x=data.index, y=data['VWAP'] , mode='lines', name='VWAP'))

    # Add selected indicators to the chart
    for indicator in indicators:
        add_indicator(indicator)

    fig.update_layout(xaxis_rangeslider_visible=False)
    st.plotly_chart(fig)

    # Analyze chart with AI vision
    st.subheader("AI Analysis")
    if st.button("Run AI Analysis"):
        with st.spinner("Analyzing the chart, please wait..."):
            # Save chart as a temporary image
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                fig.write_image(tmpfile.name)
                tmpfile_path = tmpfile.name

            # Read image and encode to base64
            with open(tmpfile_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            # Prepare AI analysis request
            messages = [{
                'role': 'user',
                'content': """You are a stocker trader specializing in technical analysis at a top financial institution.
                            Analyze the stop chart's technical indicators and provide a buy/hold/sell recommandation.
                            Base your recommendation only on the candlestick chart and the displayed technical indicators.
                            First, provide the recommandation, then, provide your detailed reasoning.""",
                'images': [image_data]
            }]
            response = ollama.chat(model='llama3.2-vision', messages=messages)

            # Display AI response
            st.write("**AI Analysis Results:**")
            st.write(response["message"]["content"])

            # Clean up temporary file
            os.remove(tmpfile_path)