import sys
from pathlib import Path
import streamlit as st
import matplotlib.pyplot as plt

# Fix path issues
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from analysis import analyze_stock

@st.cache_data
def cached_analysis(stock_name, timeframe):
    return analyze_stock(stock_name, timeframe)

st.set_page_config(
    page_title="Stock Analysis",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Mobile-friendly CSS
st.markdown("""
<style>
    .stTextInput input, .stSelectbox select {
        font-size: 16px !important;
    }
    .stButton>button {
        width: 100%;
        padding: 10px;
    }
    .card {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        background: #f0f2f6;
    }
    @media (max-width: 768px) {
        .stTextInput input {
            font-size: 14px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

def plot_chart(data, ema_50, stock_name, timeframe, resistance_levels=None, support_levels=None):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(data.index, data['Close'], label='Price', linewidth=2)
    ax.plot(data.index, ema_50, label='50 EMA', color='orange', linestyle='--')

    # Plot resistance levels
    if resistance_levels:
        for res in resistance_levels:
            ax.axhline(y=res, color='red', linestyle='--', linewidth=1, alpha=0.6, label='Resistance')

    # Plot support levels
    if support_levels:
        for sup in support_levels:
            ax.axhline(y=sup, color='green', linestyle='--', linewidth=1, alpha=0.6, label='Support')

    ax.set_title(f"{stock_name} ({timeframe}) Price Chart")
    ax.legend(loc='upper left')
    ax.grid(True, linestyle=':', alpha=0.7)
    st.pyplot(fig)

def main():
    st.title("📊 Stock Analysis Tool")

    with st.form("analysis_form"):
        col1, col2 = st.columns(2)
        with col1:
            stock = st.text_input("Stock Symbol", "TCS.NS").strip().upper()
        with col2:
            timeframe = st.selectbox("Timeframe", ["1d", "1wk", "1mo"])

        if st.form_submit_button("Analyze", type="primary"):
            with st.spinner("Analyzing..."):
                result = cached_analysis(stock, timeframe)

            if not result:
                st.error("""
                ❌ Analysis failed. Check:
                - Symbol format (e.g. TCS.NS, AAPL)
                - Internet connection
                - Try different timeframe
                """)
            else:
                passing = sum(result["results"].values())
                st.subheader(f"Results ({passing}/6 criteria met)")

                if passing >= 5:
                    st.success("✅ STRONG BUY SIGNAL")
                elif passing >= 3:
                    st.warning("⚠️ NEUTRAL SIGNAL")
                else:
                    st.error("❌ AVOID TRADE")

                for name, passed in result["results"].items():
                    st.markdown(f"""
                    <div class="card" style="border-left: 5px solid {'#4CAF50' if passed else '#F44336'}">
                        <b>{name}</b> {"✅" if passed else "❌"}
                    </div>
                    """, unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Stop Loss", f"{result['stop_loss']:.2f}")
                with col2:
                    st.metric("Target", f"{result['target']:.2f}")

                # Final chart with S/R
                plot_chart(
                    result["data"],
                    result["ema_50"],
                    stock,
                    timeframe,
                    resistance_levels=result.get("resistance_levels"),
                    support_levels=result.get("support_levels")
                )

if __name__ == "__main__":
    main()
