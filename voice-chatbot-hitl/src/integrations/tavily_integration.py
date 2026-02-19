"""
Tavily Integration for LangGraph Voice Chatbot
Provides real-time web intelligence for internship hunting, company research, and networking.
"""

import os
import json
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class TavilyClient:
    """Client for interacting with Tavily API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Tavily client.
        
        Args:
            api_key: Tavily API key. If None, loads from TAVILY_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")
        
        self.base_url = "https://api.tavily.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def search(
        self,
        query: str,
        max_results: int = 10,
        search_depth: str = "advanced",
        time_range: Optional[str] = None,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search the web using Tavily.
        
        Args:
            query: Search query
            max_results: Maximum number of results (0-20)
            search_depth: Search depth (ultra-fast, fast, basic, advanced)
            time_range: Time range filter (day, week, month, year)
            include_domains: List of domains to include
            exclude_domains: List of domains to exclude
            
        Returns:
            Search results dictionary
        """
        payload = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth
        }
        
        if time_range:
            payload["time_range"] = time_range
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        
        response = requests.post(
            f"{self.base_url}/search",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def research(
        self,
        input_text: str,
        model: str = "pro"
    ) -> Dict[str, Any]:
        """
        Conduct comprehensive research on a topic.
        
        Args:
            input_text: Research topic or question
            model: Model to use (mini, pro, auto)
            
        Returns:
            Research results with citations
        """
        payload = {
            "input": input_text,
            "model": model
        }
        
        response = requests.post(
            f"{self.base_url}/research",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def extract(
        self,
        urls: List[str],
        query: Optional[str] = None,
        chunks_per_source: int = 3,
        extract_depth: str = "basic"
    ) -> Dict[str, Any]:
        """
        Extract content from specific URLs.
        
        Args:
            urls: List of URLs to extract (max 20)
            query: Optional query to rerank chunks by relevance
            chunks_per_source: Number of chunks per URL (1-5)
            extract_depth: Extraction depth (basic, advanced)
            
        Returns:
            Extracted content dictionary
        """
        payload = {
            "urls": urls,
            "extract_depth": extract_depth
        }
        
        if query:
            payload["query"] = query
            payload["chunks_per_source"] = chunks_per_source
        
        response = requests.post(
            f"{self.base_url}/extract",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()


class InternshipHunter:
    """Find and analyze internship opportunities."""
    
    def __init__(self, tavily_client: TavilyClient):
        self.client = tavily_client
    
    def find_internships(
        self,
        role: str = "AI/ML",
        location: Optional[str] = None,
        time_range: str = "week"
    ) -> Dict[str, Any]:
        """
        Find recent internship opportunities.
        
        Args:
            role: Role/field (e.g., "AI/ML", "Software Engineering")
            location: Optional location filter
            time_range: Time range for results (day, week, month)
            
        Returns:
            Dictionary with internship listings
        """
        # Build search query
        query = f"{role} internship opportunities"
        if location:
            query += f" in {location}"
        
        # Search with filters for job sites
        results = self.client.search(
            query=query,
            max_results=10,
            search_depth="advanced",
            time_range=time_range,
            include_domains=[
                "linkedin.com",
                "glassdoor.com",
                "indeed.com",
                "internships.com",
                "simplify.jobs"
            ]
        )
        
        return {
            "query": query,
            "time_range": time_range,
            "results": results.get("results", []),
            "count": len(results.get("results", []))
        }
    
    def analyze_job_requirements(self, job_url: str) -> Dict[str, Any]:
        """
        Extract and analyze job requirements from a URL.
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            Extracted requirements and analysis
        """
        extraction = self.client.extract(
            urls=[job_url],
            query="job requirements skills qualifications responsibilities",
            chunks_per_source=5,
            extract_depth="advanced"
        )
        
        return {
            "url": job_url,
            "content": extraction.get("results", []),
            "analysis_ready": True
        }


class CompanyResearcher:
    """Deep dive research on companies for interview preparation."""
    
    def __init__(self, tavily_client: TavilyClient):
        self.client = tavily_client
    
    def research_company(self, company_name: str) -> Dict[str, Any]:
        """
        Comprehensive company research for interview prep.
        
        Args:
            company_name: Name of the company
            
        Returns:
            Comprehensive research report
        """
        # Research query
        research_query = f"""
        Research {company_name} for interview preparation:
        - Recent funding and financial news
        - Latest AI/ML projects and initiatives
        - Company culture and values
        - Recent news and press releases
        - Employee reviews and sentiment
        """
        
        research_results = self.client.research(
            input_text=research_query,
            model="pro"
        )
        
        return {
            "company": company_name,
            "research_date": datetime.now().isoformat(),
            "report": research_results,
            "summary_available": True
        }
    
    def get_recent_news(self, company_name: str, days: int = 30) -> Dict[str, Any]:
        """
        Get recent news about a company.
        
        Args:
            company_name: Name of the company
            days: Number of days to look back
            
        Returns:
            Recent news articles
        """
        time_range = "month" if days >= 30 else "week"
        
        results = self.client.search(
            query=f"{company_name} news AI ML projects",
            max_results=10,
            search_depth="advanced",
            time_range=time_range
        )
        
        return {
            "company": company_name,
            "time_range": time_range,
            "news": results.get("results", [])
        }


class LeadEnricher:
    """Enrich leads for networking and outreach."""
    
    def __init__(self, tavily_client: TavilyClient):
        self.client = tavily_client
    
    def enrich_lead(
        self,
        name: str,
        company: Optional[str] = None,
        linkedin_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enrich a lead with recent activity and content.
        
        Args:
            name: Person's name
            company: Optional company name
            linkedin_url: Optional LinkedIn profile URL
            
        Returns:
            Enriched lead information
        """
        # Build search query
        query = f"{name}"
        if company:
            query += f" {company}"
        query += " recent posts articles blog GitHub"
        
        # Search for recent activity
        results = self.client.search(
            query=query,
            max_results=10,
            search_depth="advanced",
            time_range="month"
        )
        
        enriched_data = {
            "name": name,
            "company": company,
            "linkedin_url": linkedin_url,
            "recent_activity": results.get("results", []),
            "enrichment_date": datetime.now().isoformat()
        }
        
        # If LinkedIn URL provided, extract profile details
        if linkedin_url:
            try:
                profile_data = self.client.extract(
                    urls=[linkedin_url],
                    query="experience skills projects",
                    chunks_per_source=3
                )
                enriched_data["profile_details"] = profile_data.get("results", [])
            except Exception as e:
                enriched_data["profile_error"] = str(e)
        
        return enriched_data


class NewsMonitor:
    """Monitor and summarize AI/ML news."""
    
    def __init__(self, tavily_client: TavilyClient):
        self.client = tavily_client
    
    def get_daily_brief(
        self,
        topics: Optional[List[str]] = None,
        max_items: int = 5
    ) -> Dict[str, Any]:
        """
        Get daily AI/ML news brief.
        
        Args:
            topics: Optional list of specific topics to focus on
            max_items: Maximum number of news items
            
        Returns:
            Daily news brief
        """
        if not topics:
            topics = ["AI", "machine learning", "LLM", "artificial intelligence"]
        
        # Search for recent AI news
        query = " OR ".join(topics) + " breakthrough news"
        
        results = self.client.search(
            query=query,
            max_results=max_items,
            search_depth="advanced",
            time_range="day",
            include_domains=[
                "techcrunch.com",
                "arxiv.org",
                "venturebeat.com",
                "theverge.com",
                "arstechnica.com"
            ]
        )
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "topics": topics,
            "news_items": results.get("results", []),
            "count": len(results.get("results", []))
        }
    
    def research_topic(self, topic: str) -> Dict[str, Any]:
        """
        Deep research on a specific AI/ML topic.
        
        Args:
            topic: Topic to research
            
        Returns:
            Research report
        """
        research_results = self.client.research(
            input_text=f"Latest developments and breakthroughs in {topic}",
            model="pro"
        )
        
        return {
            "topic": topic,
            "research_date": datetime.now().isoformat(),
            "report": research_results
        }


# Convenience functions for easy integration
def get_tavily_client() -> TavilyClient:
    """Get or create Tavily client instance."""
    return TavilyClient()


def create_internship_hunter() -> InternshipHunter:
    """Create InternshipHunter instance."""
    return InternshipHunter(get_tavily_client())


def create_company_researcher() -> CompanyResearcher:
    """Create CompanyResearcher instance."""
    return CompanyResearcher(get_tavily_client())


def create_lead_enricher() -> LeadEnricher:
    """Create LeadEnricher instance."""
    return LeadEnricher(get_tavily_client())


def create_news_monitor() -> NewsMonitor:
    """Create NewsMonitor instance."""
    return NewsMonitor(get_tavily_client())
