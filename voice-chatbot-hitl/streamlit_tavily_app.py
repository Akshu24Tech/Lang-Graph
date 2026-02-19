"""
Streamlit UI for Tavily-powered Voice Chatbot
Beautiful interface for internship hunting, company research, and more.
"""

import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime
from src.integrations.tavily_integration import (
    create_internship_hunter,
    create_company_researcher,
    create_lead_enricher,
    create_news_monitor
)

load_dotenv()

# Page config
st.set_page_config(
    page_title="AI Career Assistant",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        padding: 1.5rem;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
    }
    .result-card {
        padding: 1rem;
        border-left: 4px solid #1f77b4;
        background-color: #ffffff;
        margin-bottom: 1rem;
        border-radius: 5px;
        color: #000000;
    }
    .result-card h4 {
        color: #1f77b4;
    }
    .result-card p {
        color: #333333;
    }
    .result-card a {
        color: #1f77b4;
        text-decoration: none;
    }
    .result-card a:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🎯 AI Career Assistant</div>', unsafe_allow_html=True)
st.markdown("**Powered by Tavily & LangGraph** | Find internships, research companies, enrich leads, and stay updated")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Check API key
    api_key = os.getenv("TAVILY_API_KEY")
    if api_key and api_key != "your-tavily-api-key-here":
        st.success("✅ Tavily API Connected")
    else:
        st.error("❌ Tavily API Key Missing")
        st.info("Add TAVILY_API_KEY to your .env file")
    
    st.divider()
    
    st.header("📚 Features")
    st.markdown("""
    - 🎯 **Internship Hunter**
    - 🏢 **Company Research**
    - 🔍 **Lead Enrichment**
    - 📰 **News Monitor**
    """)
    
    st.divider()
    
    st.header("🔗 Quick Links")
    st.markdown("[📖 Documentation](./TAVILY_INTEGRATION.md)")
    st.markdown("[🚀 Quick Start](./QUICKSTART_TAVILY.md)")
    st.markdown("[🌐 Tavily API](https://tavily.com)")

# Main content - Tabs for each feature
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Internship Hunter", "🏢 Company Research", "🔍 Lead Enrichment", "📰 News Monitor"])

# Tab 1: Internship Hunter
with tab1:
    st.header("🎯 Find Internship Opportunities")
    st.markdown("Search for the latest internships from top job sites")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        role = st.selectbox(
            "Role/Field",
            ["AI/ML", "Software Engineering", "Data Science", "Full Stack", "Backend", "Frontend"]
        )
    
    with col2:
        time_range = st.selectbox(
            "Time Range",
            ["week", "day", "month"],
            index=0
        )
    
    location = st.text_input("Location (optional)", placeholder="e.g., San Francisco, Remote")
    
    if st.button("🔍 Search Internships", type="primary"):
        with st.spinner("Searching for opportunities..."):
            try:
                hunter = create_internship_hunter()
                results = hunter.find_internships(
                    role=role,
                    location=location if location else None,
                    time_range=time_range
                )
                
                st.success(f"✅ Found {results['count']} opportunities!")
                
                if results['count'] > 0:
                    for idx, result in enumerate(results['results'], 1):
                        with st.container():
                            st.markdown(f"""
                            <div class="result-card">
                                <h4 style="color: #1f77b4;">{idx}. {result.get('title', 'Untitled')}</h4>
                                <p style="color: #333;"><strong>🔗 URL:</strong> <a href="{result.get('url', '#')}" target="_blank" style="color: #1f77b4;">{result.get('url', 'N/A')}</a></p>
                                <p style="color: #333;"><strong>📝 Description:</strong> {result.get('content', 'No description')[:200]}...</p>
                                <p style="color: #333;"><strong>⭐ Relevance Score:</strong> {result.get('score', 'N/A')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.warning("No results found. Try adjusting your search criteria.")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Tab 2: Company Research
with tab2:
    st.header("🏢 Company Deep Dive")
    st.markdown("Comprehensive research for interview preparation")
    
    company_name = st.text_input("Company Name", placeholder="e.g., Google, Microsoft, OpenAI")
    
    col1, col2 = st.columns(2)
    
    with col1:
        research_type = st.radio(
            "Research Type",
            ["Full Research (60-120s)", "Recent News Only (10-20s)"]
        )
    
    if st.button("🔍 Research Company", type="primary"):
        if not company_name:
            st.warning("Please enter a company name")
        else:
            with st.spinner(f"Researching {company_name}..."):
                try:
                    researcher = create_company_researcher()
                    
                    if research_type == "Full Research (60-120s)":
                        results = researcher.research_company(company_name)
                        
                        st.success(f"✅ Research completed for {company_name}")
                        
                        report = results.get('report', {})
                        
                        if isinstance(report, dict):
                            if 'answer' in report:
                                st.markdown("### 📊 Research Summary")
                                st.markdown(report['answer'])
                            
                            if 'sources' in report:
                                st.markdown("### 📚 Sources")
                                for source in report['sources']:
                                    st.markdown(f"- [{source}]({source})")
                        else:
                            st.markdown(str(report))
                    
                    else:  # Recent News Only
                        results = researcher.get_recent_news(company_name, days=30)
                        
                        st.success(f"✅ Found {len(results['news'])} recent news articles")
                        
                        for idx, news in enumerate(results['news'], 1):
                            with st.container():
                                st.markdown(f"""
                                <div class="result-card">
                                    <h4 style="color: #1f77b4;">{idx}. {news.get('title', 'Untitled')}</h4>
                                    <p style="color: #333;"><strong>🔗 URL:</strong> <a href="{news.get('url', '#')}" target="_blank" style="color: #1f77b4;">{news.get('url', 'N/A')}</a></p>
                                    <p style="color: #333;">{news.get('content', '')[:200]}...</p>
                                </div>
                                """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Tab 3: Lead Enrichment
with tab3:
    st.header("🔍 Lead Enrichment")
    st.markdown("Research people for networking and personalized outreach")
    
    col1, col2 = st.columns(2)
    
    with col1:
        lead_name = st.text_input("Person's Name", placeholder="e.g., John Doe")
    
    with col2:
        lead_company = st.text_input("Company (optional)", placeholder="e.g., Google")
    
    linkedin_url = st.text_input("LinkedIn URL (optional)", placeholder="https://linkedin.com/in/...")
    
    if st.button("🔍 Enrich Lead", type="primary"):
        if not lead_name:
            st.warning("Please enter a person's name")
        else:
            with st.spinner(f"Enriching lead: {lead_name}..."):
                try:
                    enricher = create_lead_enricher()
                    results = enricher.enrich_lead(
                        name=lead_name,
                        company=lead_company if lead_company else None,
                        linkedin_url=linkedin_url if linkedin_url else None
                    )
                    
                    st.success(f"✅ Lead enrichment completed for {lead_name}")
                    
                    # Display basic info
                    st.markdown("### 👤 Lead Information")
                    st.markdown(f"**Name:** {results['name']}")
                    if results.get('company'):
                        st.markdown(f"**Company:** {results['company']}")
                    st.markdown(f"**Enrichment Date:** {results['enrichment_date']}")
                    
                    # Display recent activity
                    recent_activity = results.get('recent_activity', [])
                    if recent_activity:
                        st.markdown("### 📰 Recent Activity")
                        for idx, activity in enumerate(recent_activity, 1):
                            with st.container():
                                st.markdown(f"""
                                <div class="result-card">
                                    <h4 style="color: #1f77b4;">{idx}. {activity.get('title', 'Untitled')}</h4>
                                    <p style="color: #333;"><strong>🔗 URL:</strong> <a href="{activity.get('url', '#')}" target="_blank" style="color: #1f77b4;">{activity.get('url', 'N/A')}</a></p>
                                    <p style="color: #333;">{activity.get('content', '')[:150]}...</p>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # Display profile details if available
                    if results.get('profile_details'):
                        st.markdown("### 💼 Profile Details")
                        for detail in results['profile_details']:
                            st.markdown(detail.get('raw_content', '')[:300])
                    
                    # Outreach suggestion
                    st.markdown("### 💡 Outreach Tips")
                    st.info("Use the recent activity above to personalize your connection message. Mention specific articles or projects they've worked on!")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Tab 4: News Monitor
with tab4:
    st.header("📰 AI/ML News Monitor")
    st.markdown("Stay updated with the latest breakthroughs")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        topics = st.multiselect(
            "Topics",
            ["AI", "Machine Learning", "LLM", "Computer Vision", "NLP", "Reinforcement Learning", "Robotics"],
            default=["AI", "Machine Learning", "LLM"]
        )
    
    with col2:
        max_items = st.slider("Max Items", 3, 10, 5)
    
    if st.button("📰 Get Daily Brief", type="primary"):
        with st.spinner("Fetching latest news..."):
            try:
                monitor = create_news_monitor()
                brief = monitor.get_daily_brief(
                    topics=topics if topics else None,
                    max_items=max_items
                )
                
                st.success(f"✅ Found {brief['count']} news items for {brief['date']}")
                
                news_items = brief.get('news_items', [])
                if news_items:
                    for idx, item in enumerate(news_items, 1):
                        with st.container():
                            st.markdown(f"""
                            <div class="result-card">
                                <h4 style="color: #1f77b4;">{idx}. {item.get('title', 'Untitled')}</h4>
                                <p style="color: #333;"><strong>🔗 URL:</strong> <a href="{item.get('url', '#')}" target="_blank" style="color: #1f77b4;">{item.get('url', 'N/A')}</a></p>
                                <p style="color: #333;">{item.get('content', '')[:250]}...</p>
                                <p style="color: #333;"><strong>⭐ Relevance:</strong> {item.get('score', 'N/A')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.warning("No news found. Try different topics or check back later.")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666;">
    Built with ❤️ using <strong>LangGraph</strong> and <strong>Tavily</strong><br>
    🚀 Supercharge your internship hunt and career growth
</div>
""", unsafe_allow_html=True)
