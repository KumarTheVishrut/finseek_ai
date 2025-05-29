# app.py
import streamlit as st
import requests
import time
import json
import pandas as pd
from io import BytesIO
import base64
from audio_recorder_streamlit import audio_recorder
import os

# Configure Streamlit page
st.set_page_config(
    page_title="🤑 FinSeek AI - Multi-Agent Finance Assistant",
    page_icon="🤑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Service URLs - Use environment variable if available, otherwise default to Kubernetes service
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator-service:8004")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    .portfolio-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.markdown('<h1 class="main-header">🤑 FinSeek AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Your AI-Powered Portfolio Manager & Market Intelligence Assistant</p>', unsafe_allow_html=True)

# Sidebar for portfolio overview
with st.sidebar:
    st.header("📊 Portfolio Overview")
    
    # Load portfolio data
    try:
        portfolio_df = pd.read_csv("portfolio.csv")
        total_value = portfolio_df['current_value'].sum()
        
        st.metric("Total Portfolio Value", f"${total_value:,.2f}")
        st.metric("Number of Holdings", len(portfolio_df))
        
        # Portfolio breakdown
        st.subheader("Holdings")
        for _, row in portfolio_df.iterrows():
            allocation = (row['current_value'] / total_value) * 100
            st.write(f"**{row['ticker']}**: {allocation:.1f}% (${row['current_value']:.2f})")
            
    except Exception as e:
        st.error(f"Could not load portfolio: {e}")
        st.info("Using sample data...")

# Main interface tabs
tab1, tab2, tab3 = st.tabs(["🎤 Voice Assistant", "💬 Text Analysis", "📈 Market Dashboard"])

with tab1:
    st.header("🎤 Voice Market Brief")
    st.write("Ask me about your Asia tech portfolio risk exposure, earnings surprises, or market outlook!")
    
    # Audio recorder
    audio_bytes = audio_recorder(
        text="Click to record your question",
        recording_color="#e74c3c",
        neutral_color="#34495e",
        icon_name="microphone",
        icon_size="2x"
    )
    
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        
        with st.spinner("🔄 Processing your voice query..."):
            try:
                # Convert audio to file-like object
                audio_file = BytesIO(audio_bytes)
                audio_file.name = "recording.wav"
                
                # Send to orchestrator
                files = {"audio": ("recording.wav", audio_file, "audio/wav")}
                response = requests.post(f"{ORCHESTRATOR_URL}/voice-query", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Display transcript
                    st.success("✅ Voice processed successfully!")
                    st.subheader("📝 What you asked:")
                    st.write(f"*\"{result['transcript']}\"*")
                    
                    # Display AI response
                    st.subheader("🤖 AI Market Brief:")
                    st.write(result['response'])
                    
                    # Play audio response if available
                    if result.get('audio_file'):
                        st.subheader("🔊 Audio Response:")
                        st.info("Audio response generated! (Note: Audio playback requires file system access)")
                    
                    # Display additional data in expandable sections
                    with st.expander("📊 Detailed Market Data"):
                        if result.get('market_data'):
                            st.json(result['market_data'])
                    
                    with st.expander("📈 Portfolio Analysis"):
                        if result.get('portfolio_analysis'):
                            st.json(result['portfolio_analysis'])
                
                else:
                    st.error(f"Error processing voice query: {response.text}")
                    
            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    st.header("💬 Text-Based Market Analysis")
    
    # Text input
    user_query = st.text_area(
        "Ask about your portfolio, market conditions, or specific stocks:",
        placeholder="e.g., What's our risk exposure in Asia tech stocks today? Any earnings surprises?",
        height=100
    )
    
    # Analysis options
    col1, col2 = st.columns(2)
    with col1:
        region_focus = st.selectbox("Region Focus", ["asia", "us", "europe", "global"])
    with col2:
        include_portfolio = st.checkbox("Include Portfolio Analysis", value=True)
    
    if st.button("🔍 Analyze", type="primary"):
        if user_query:
            with st.spinner("🔄 Generating market analysis..."):
                try:
                    payload = {
                        "query": user_query,
                        "region": region_focus
                    }
                    
                    response = requests.post(f"{ORCHESTRATOR_URL}/market-brief", json=payload)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Display main response
                        st.subheader("📊 Market Analysis")
                        st.write(result['response'])
                        
                        # Create columns for additional info
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if result.get('market_data'):
                                st.subheader("💹 Market Metrics")
                                market_data = result['market_data']
                                if market_data.get('risk_exposure'):
                                    st.metric("Risk Exposure", f"{market_data['risk_exposure']}%")
                        
                        with col2:
                            if result.get('earnings_data'):
                                st.subheader("📈 Earnings Data")
                                earnings = result['earnings_data']
                                if earnings.get('surprise_pct'):
                                    surprise = earnings['surprise_pct']
                                    delta_color = "normal" if surprise >= 0 else "inverse"
                                    st.metric("Earnings Surprise", f"{surprise}%", delta=f"{surprise}%")
                        
                        # Portfolio analysis
                        if include_portfolio and result.get('portfolio_analysis'):
                            st.subheader("🏦 Portfolio Impact Analysis")
                            portfolio_data = result['portfolio_analysis']
                            if portfolio_data.get('analysis'):
                                holdings_df = pd.DataFrame(portfolio_data['analysis'])
                                st.dataframe(holdings_df[['ticker', 'allocation_pct', 'current_value']], use_container_width=True)
                        
                        # Relevant documents
                        if result.get('relevant_documents', {}).get('results'):
                            with st.expander("📄 Supporting Research & Intelligence"):
                                docs = result['relevant_documents']['results']
                                for i, doc in enumerate(docs[:3]):
                                    st.write(f"**Source {i+1}** (Relevance: {doc.get('score', 0):.2f})")
                                    st.write(doc.get('content', '')[:300] + "...")
                                    st.write("---")
                    
                    else:
                        st.error(f"Error: {response.text}")
                        
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
        else:
            st.warning("Please enter a question to analyze.")

with tab3:
    st.header("📈 Real-Time Market Dashboard")
    
    # Refresh button
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    try:
        # Get portfolio data
        portfolio_response = requests.get(f"{ORCHESTRATOR_URL}/portfolio")
        
        if portfolio_response.status_code == 200:
            portfolio_data = portfolio_response.json()
            
            # Portfolio metrics
            st.subheader("💼 Portfolio Performance")
            
            if portfolio_data.get('analysis'):
                col1, col2, col3, col4 = st.columns(4)
                
                holdings = portfolio_data['analysis']
                total_value = sum(h['current_value'] for h in holdings)
                num_holdings = len(holdings)
                avg_allocation = total_value / num_holdings if num_holdings > 0 else 0
                
                with col1:
                    st.metric("Total Value", f"${total_value:,.2f}")
                with col2:
                    st.metric("Holdings", num_holdings)
                with col3:
                    st.metric("Avg. Position", f"${avg_allocation:,.2f}")
                with col4:
                    largest_position = max(holdings, key=lambda x: x['allocation_pct'])
                    st.metric("Largest Position", f"{largest_position['ticker']} ({largest_position['allocation_pct']:.1f}%)")
                
                # Holdings table
                st.subheader("📊 Current Holdings")
                holdings_df = pd.DataFrame(holdings)
                st.dataframe(
                    holdings_df[['ticker', 'current_value', 'allocation_pct']].round(2),
                    use_container_width=True
                )
                
                # Allocation chart
                st.subheader("🥧 Portfolio Allocation")
                chart_data = holdings_df.set_index('ticker')['allocation_pct']
                st.bar_chart(chart_data)
        
        else:
            st.error("Could not fetch portfolio data")
            
    except Exception as e:
        st.error(f"Dashboard error: {e}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>🤑 FinSeek AI - Powered by Multi-Agent Architecture</p>
        <p>API Agent | Scraper Agent | Retriever Agent | LLM Agent | Voice Agent</p>
    </div>
    """,
    unsafe_allow_html=True
)
