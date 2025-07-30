import sys
from pathlib import Path
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from analysis import analyze_stock

# Configure paths
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Cache the analysis
@st.cache_data
def cached_analysis(stock_name, timeframe):
    return analyze_stock(stock_name, timeframe)

# Page configuration
st.set_page_config(
    page_title="Advanced Stock Analysis",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stTextInput input, .stSelectbox select {
        font-size: 16px !important;
    }
    .stButton>button {
        width: 100%;
        padding: 10px;
        font-weight: bold;
    }
    .card {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        background: #f8f9fa;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .level-line {
        font-weight: bold;
        margin: 5px 0;
    }
    @media (max-width: 768px) {
        .stTextInput input {
            font-size: 14px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

def plot_chart(data, ema_50, stock_name, timeframe, levels):
    """Enhanced chart with support/resistance levels"""
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Price and EMA
    linewidth = 1.5 if timeframe in ['5m','15m','1h','4h'] else 2
    ax.plot(data.index, data['Close'], label='Price', linewidth=linewidth)
    
    # Only show EMA for daily+ timeframes
    if timeframe not in ['5m','15m','1h','4h']:
        ax.plot(data.index, ema_50, label='50 EMA', color='orange', linestyle='--', alpha=0.8)
    
    # Support levels (green)
    for level in levels['support']:
        ax.axhline(y=level, color='green', linestyle='--', alpha=0.6, linewidth=1.2,
                  label=f'Support {level:.2f}')
    
    # Resistance levels (red)
    for level in levels['resistance']:
        ax.axhline(y=level, color='red', linestyle='--', alpha=0.6, linewidth=1.2,
                  label=f'Resistance {level:.2f}')
    
    # Format x-axis based on timeframe
    if timeframe in ['5m','15m']:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.xticks(rotation=45)
    elif timeframe in ['1h','4h']:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        plt.xticks(rotation=45)
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    
    ax.set_title(f"{stock_name} ({timeframe}) - Support/Resistance Levels")
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
    ax.grid(True, linestyle=':', alpha=0.5)
    plt.tight_layout()
    st.pyplot(fig)

def main():
    st.title("📈 Multi-Timeframe Stock Analyzer")
    
    with st.form("analysis_form"):
        col1, col2 = st.columns(2)
        with col1:
            stock = st.text_input("Stock Symbol", "TCS.NS").strip().upper()
        with col2:
            timeframe = st.selectbox(
                "Timeframe",
                options=['5m', '15m', '1h', '4h', '1d', '1wk', '1mo'],
                index=4
            )
        
        if st.form_submit_button("Analyze Now", type="primary"):
            with st.spinner(f"Analyzing {stock} ({timeframe})..."):
                result = cached_analysis(stock, timeframe)
                
            if not result:
                st.error("""
                ❌ Analysis failed. Common issues:
                - Invalid symbol (e.g. use 'TCS.NS' not 'TCS')
                - Market closed for intraday timeframes
                - Yahoo Finance API limit
                """)
            else:
                # Results summary
                passing = sum(result["results"].values())
                st.subheader(f"Analysis Results ({passing}/6 criteria met)")
                
                if passing >= 5:
                    st.success("✅ STRONG BUY SIGNAL")
                elif passing >= 3:
                    st.warning("⚠️ NEUTRAL - Trade with Caution")
                else:
                    st.error("❌ AVOID TRADE - Weak Setup")
                
                # Checklist
                st.markdown("#### Technical Checklist")
                for name, passed in result["results"].items():
                    st.markdown(f"""
                    <div class="card">
                        <b>{name}</b> {"✅" if passed else "❌"}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Levels display
                st.markdown("#### Key Levels")
                cols = st.columns(2)
                with cols[0]:
                    st.markdown("**Support Levels**")
                    for level in result["levels"]['support']:
                        st.markdown(f'<div class="level-line" style="color:green;">▼ {level:.2f}</div>', 
                                   unsafe_allow_html=True)
                with cols[1]:
                    st.markdown("**Resistance Levels**")
                    for level in result["levels"]['resistance']:
                        st.markdown(f'<div class="level-line" style="color:red;">▲ {level:.2f}</div>', 
                                   unsafe_allow_html=True)
                
                # Risk management
                st.markdown("#### Risk Management")
                cols = st.columns(3)
                with cols[0]:
                    st.metric("Stop Loss", f"{result['stop_loss']:.2f}")
                with cols[1]:
                    st.metric("Target", f"{result['target']:.2f}")
                with cols[2]:
                    st.metric("Risk/Reward", f"{result['rr_ratio']:.2f}:1")
                
                # Chart
                st.markdown("#### Price Analysis")
                plot_chart(
                    result["data"], 
                    result["ema_50"], 
                    stock, 
                    timeframe, 
                    result["levels"]
                )

if __name__ == "__main__":
    main()