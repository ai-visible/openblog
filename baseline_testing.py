#!/usr/bin/env python3
"""
Blog Writer Baseline Testing Script

Generates 20 real test articles with the current system to establish:
1. Current AEO score distribution
2. Actual generation times
3. Broken citation/internal link rates
4. Content similarity patterns
5. Quality issues root causes

This provides the factual baseline before making any improvements.
"""

import asyncio
import json
import logging
import time
import requests
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple
from urllib.parse import urlparse
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'baseline_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BaselineTestRunner:
    """Runs comprehensive baseline tests on current blog writer system."""
    
    def __init__(self):
        self.api_base = "https://clients--blog-writer-fastapi-app.modal.run"
        self.test_keywords = [
            # Start with just 3 keywords for initial testing
            "AI in manufacturing",
            "Digital marketing automation", 
            "Customer experience optimization"
        ]
        
        self.results = []
        self.broken_links = {"citations": [], "internal": []}
        self.quality_issues = []
        
    def create_test_job(self, keyword: str) -> Dict[str, Any]:
        """Create a test job configuration for a keyword."""
        return {
            "primary_keyword": keyword,
            "company_name": "SCAILE",
            "company_url": "https://scaile.tech",
            "language": "en",
            "content_generation_instruction": "Generate high-quality, data-driven content with citations and internal links.",
            "company_data": {
                "description": "AI growth agency specializing in automation and optimization",
                "industry": "Technology Services",
                "target_audience": ["B2B companies seeking AI solutions"],
                "competitors": ["OpenAI", "Anthropic", "Jasper"],
                "author_name": "SCAILE AI Team",
                "author_bio": "AI specialists focused on business automation and optimization.",
                "author_url": "https://scaile.tech/about"
            },
            "sitemap_urls": [
                "/blog/ai-automation-guide",
                "/blog/machine-learning-roi", 
                "/blog/digital-transformation",
                "/blog/data-analytics-insights",
                "/blog/customer-experience-ai"
            ],
            "existing_blog_slugs": [
                {"slug": "/blog/ai-automation-guide", "title": "AI Automation Guide", "keyword": "AI automation"},
                {"slug": "/blog/machine-learning-roi", "title": "ML ROI Analysis", "keyword": "machine learning ROI"},
                {"slug": "/blog/digital-transformation", "title": "Digital Transformation", "keyword": "digital transformation"},
                {"slug": "/blog/data-analytics-insights", "title": "Data Analytics Insights", "keyword": "data analytics"},
                {"slug": "/blog/customer-experience-ai", "title": "Customer Experience AI", "keyword": "customer experience AI"}
            ],
            "tone": "professional",
            "word_count": 1500
        }
    
    async def generate_article(self, job_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a single article and capture metrics."""
        keyword = job_config["primary_keyword"]
        logger.info(f"Generating article for: {keyword}")
        
        start_time = time.time()
        
        try:
            # Call blog writer API
            response = requests.post(
                f"{self.api_base}/write",
                json=job_config,
                timeout=600  # 10 minute timeout for first generation
            )
            
            generation_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract key metrics from the new response format
                quality_report = result.get("quality_report", {})
                
                metrics = {
                    "keyword": keyword,
                    "success": result.get("success", False),
                    "generation_time": result.get("duration_seconds", generation_time),
                    "aeo_score": result.get("aeo_score", 0),
                    "word_count": quality_report.get("metrics", {}).get("word_count", 0) if quality_report else 0,
                    "readability": quality_report.get("metrics", {}).get("readability", 0) if quality_report else 0,
                    "critical_issues": result.get("critical_issues_count", 0),
                    "suggestions": len(quality_report.get("suggestions", [])) if quality_report else 0,
                    "passed_quality": not bool(result.get("critical_issues_count", 0)),
                    "article_content": {
                        "headline": result.get("headline", ""),
                        "intro": result.get("intro", ""),
                        "sections": result.get("sections", []),
                        "literature": result.get("literature", []),
                        "more_links": result.get("more_links", []),
                        "Sources": "\n".join([f"[{c['number']}]: {c['url']} - {c['description']}" for c in result.get("literature", [])])
                    },
                    "quality_report": quality_report,
                    "raw_response": result  # Store full response for debugging
                }
                
                logger.info(f"✅ {keyword}: AEO={metrics['aeo_score']}/100, Time={generation_time:.1f}s")
                return metrics
                
            else:
                logger.error(f"❌ {keyword}: API error {response.status_code}")
                return {
                    "keyword": keyword,
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "generation_time": generation_time
                }
                
        except requests.Timeout:
            logger.error(f"❌ {keyword}: Timeout after 5 minutes")
            return {
                "keyword": keyword, 
                "success": False,
                "error": "Timeout",
                "generation_time": time.time() - start_time
            }
        except Exception as e:
            logger.error(f"❌ {keyword}: Exception - {e}")
            return {
                "keyword": keyword,
                "success": False, 
                "error": str(e),
                "generation_time": time.time() - start_time
            }
    
    def analyze_broken_links(self, article_content: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Analyze article for broken citations and internal links."""
        broken_citations = []
        broken_internal = []
        
        # Extract citations from literature field
        literature = article_content.get("literature", [])
        for citation in literature:
            url = citation.get("url", "")
            if url:
                try:
                    response = requests.head(url, timeout=10, allow_redirects=True)
                    if response.status_code != 200:
                        broken_citations.append(f"{url} -> {response.status_code}")
                        logger.debug(f"Broken citation: {url} -> {response.status_code}")
                except Exception as e:
                    broken_citations.append(f"{url} -> {str(e)}")
                    logger.debug(f"Citation error: {url} -> {str(e)}")
        
        # Extract internal links from more_links and sections
        more_links = article_content.get("more_links", [])
        for link in more_links:
            link_url = link.get("url", "")
            if link_url.startswith("/"):
                full_url = f"https://scaile.tech{link_url}"  # Use test company URL
                try:
                    response = requests.head(full_url, timeout=10, allow_redirects=True)
                    if response.status_code != 200:
                        broken_internal.append(f"{link_url} -> {response.status_code}")
                        logger.debug(f"Broken internal link: {link_url} -> {response.status_code}")
                except Exception as e:
                    broken_internal.append(f"{link_url} -> {str(e)}")
                    logger.debug(f"Internal link error: {link_url} -> {str(e)}")
        
        # Also check sections for inline links
        sections = article_content.get("sections", [])
        for section in sections:
            content = section.get("content", "")
            internal_links = re.findall(r'href="(/[^"]*)"', content)
            
            for link in internal_links:
                full_url = f"https://scaile.tech{link}"
                try:
                    response = requests.head(full_url, timeout=10, allow_redirects=True)
                    if response.status_code != 200:
                        broken_internal.append(f"{link} -> {response.status_code}")
                        logger.debug(f"Broken section link: {link} -> {response.status_code}")
                except Exception as e:
                    broken_internal.append(f"{link} -> {str(e)}")
                    logger.debug(f"Section link error: {link} -> {str(e)}")
        
        return broken_citations, broken_internal
    
    def analyze_content_similarity(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze content similarity between articles using simple text comparison."""
        similarities = []
        
        for i, article1 in enumerate(articles):
            if not article1.get("success") or not article1.get("article_content"):
                continue
                
            content1 = self.extract_article_text(article1["article_content"])
            
            for j, article2 in enumerate(articles[i+1:], i+1):
                if not article2.get("success") or not article2.get("article_content"):
                    continue
                    
                content2 = self.extract_article_text(article2["article_content"])
                
                # Simple similarity calculation (shared words)
                words1 = set(content1.lower().split())
                words2 = set(content2.lower().split())
                
                if len(words1) > 0 and len(words2) > 0:
                    intersection = len(words1.intersection(words2))
                    union = len(words1.union(words2))
                    similarity = intersection / union if union > 0 else 0
                    
                    if similarity > 0.3:  # 30% similarity threshold
                        similarities.append({
                            "article1": article1["keyword"],
                            "article2": article2["keyword"],
                            "similarity": similarity,
                            "shared_words": intersection,
                            "total_unique_words": union
                        })
        
        return similarities
    
    def extract_article_text(self, article_content: Dict[str, Any]) -> str:
        """Extract all text content from article."""
        text_parts = []
        
        # Add headline and intro
        text_parts.append(article_content.get("headline", ""))
        text_parts.append(article_content.get("intro", ""))
        
        # Add section content (strip HTML)
        sections = article_content.get("sections", [])
        for section in sections:
            content = section.get("content", "")
            if content:
                # Remove HTML tags
                clean_content = re.sub(r'<[^>]+>', ' ', content)
                text_parts.append(clean_content)
        
        return " ".join(text_parts)
    
    def analyze_quality_patterns(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in quality issues."""
        successful_articles = [a for a in articles if a.get("success")]
        
        if not successful_articles:
            return {"error": "No successful articles to analyze"}
        
        # AEO score distribution
        aeo_scores = [a["aeo_score"] for a in successful_articles]
        
        # Generation time distribution  
        gen_times = [a["generation_time"] for a in successful_articles]
        
        # Quality pass rate
        passed_quality = [a["passed_quality"] for a in successful_articles]
        pass_rate = sum(passed_quality) / len(passed_quality) * 100
        
        # Common quality issues
        all_issues = []
        for article in successful_articles:
            quality_report = article.get("quality_report", {})
            all_issues.extend(quality_report.get("critical_issues", []))
            all_issues.extend(quality_report.get("suggestions", []))
        
        # Count issue types
        issue_counts = {}
        for issue in all_issues:
            # Categorize issues by keywords
            issue_lower = issue.lower()
            if "aeo" in issue_lower or "score" in issue_lower:
                issue_counts["AEO Score"] = issue_counts.get("AEO Score", 0) + 1
            elif "citation" in issue_lower:
                issue_counts["Citations"] = issue_counts.get("Citations", 0) + 1
            elif "paragraph" in issue_lower:
                issue_counts["Paragraphs"] = issue_counts.get("Paragraphs", 0) + 1
            elif "link" in issue_lower:
                issue_counts["Links"] = issue_counts.get("Links", 0) + 1
            else:
                issue_counts["Other"] = issue_counts.get("Other", 0) + 1
        
        return {
            "total_articles": len(successful_articles),
            "aeo_scores": {
                "min": min(aeo_scores) if aeo_scores else 0,
                "max": max(aeo_scores) if aeo_scores else 0,
                "avg": sum(aeo_scores) / len(aeo_scores) if aeo_scores else 0,
                "distribution": aeo_scores
            },
            "generation_times": {
                "min": min(gen_times) if gen_times else 0,
                "max": max(gen_times) if gen_times else 0,
                "avg": sum(gen_times) / len(gen_times) if gen_times else 0,
                "distribution": gen_times
            },
            "quality_pass_rate": pass_rate,
            "common_issues": issue_counts
        }
    
    async def run_baseline_test(self) -> Dict[str, Any]:
        """Run complete baseline test."""
        logger.info("🚀 Starting baseline testing of current blog writer system")
        logger.info(f"Testing {len(self.test_keywords)} keywords...")
        
        start_time = time.time()
        
        # Generate all articles
        for i, keyword in enumerate(self.test_keywords, 1):
            logger.info(f"Progress: {i}/{len(self.test_keywords)} - {keyword}")
            
            job_config = self.create_test_job(keyword)
            result = await self.generate_article(job_config)
            self.results.append(result)
            
            # Analyze broken links for successful articles
            if result.get("success") and result.get("article_content"):
                broken_cit, broken_int = self.analyze_broken_links(result["article_content"])
                self.broken_links["citations"].extend(broken_cit)
                self.broken_links["internal"].extend(broken_int)
            
            # Small delay to be nice to the API
            await asyncio.sleep(2)
        
        total_time = time.time() - start_time
        
        # Analyze results
        logger.info("📊 Analyzing results...")
        
        quality_analysis = self.analyze_quality_patterns(self.results)
        content_similarity = self.analyze_content_similarity(self.results)
        
        # Generate final report
        report = {
            "test_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_test_time": total_time,
                "keywords_tested": len(self.test_keywords),
                "api_endpoint": self.api_base
            },
            "success_metrics": {
                "successful_generations": len([r for r in self.results if r.get("success")]),
                "failed_generations": len([r for r in self.results if not r.get("success")]),
                "success_rate": len([r for r in self.results if r.get("success")]) / len(self.results) * 100
            },
            "quality_analysis": quality_analysis,
            "broken_links": {
                "total_broken_citations": len(self.broken_links["citations"]),
                "total_broken_internal": len(self.broken_links["internal"]),
                "broken_citation_examples": self.broken_links["citations"][:10],
                "broken_internal_examples": self.broken_links["internal"][:10]
            },
            "content_similarity": {
                "similar_pairs": len(content_similarity),
                "similarity_examples": content_similarity[:5]
            },
            "detailed_results": self.results
        }
        
        # Save full report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"baseline_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Full report saved to: {report_file}")
        
        return report
    
    def print_summary(self, report: Dict[str, Any]):
        """Print executive summary of baseline test."""
        logger.info("=" * 80)
        logger.info("📋 BASELINE TEST SUMMARY")
        logger.info("=" * 80)
        
        success_metrics = report["success_metrics"]
        quality = report["quality_analysis"]
        broken_links = report["broken_links"]
        
        logger.info(f"🎯 Success Rate: {success_metrics['success_rate']:.1f}%")
        logger.info(f"   ✅ Successful: {success_metrics['successful_generations']}")
        logger.info(f"   ❌ Failed: {success_metrics['failed_generations']}")
        
        if quality.get("aeo_scores"):
            aeo = quality["aeo_scores"]
            logger.info(f"📊 AEO Scores: {aeo['avg']:.1f}/100 average")
            logger.info(f"   📈 Range: {aeo['min']:.0f} - {aeo['max']:.0f}")
            logger.info(f"   🎯 85+ Score Rate: {len([s for s in aeo['distribution'] if s >= 85])}/{len(aeo['distribution'])} ({len([s for s in aeo['distribution'] if s >= 85])/len(aeo['distribution'])*100:.1f}%)")
        
        if quality.get("generation_times"):
            times = quality["generation_times"]
            logger.info(f"⏱️  Generation Time: {times['avg']:.1f}s average")
            logger.info(f"   ⚡ Range: {times['min']:.1f}s - {times['max']:.1f}s")
        
        logger.info(f"🔗 Link Quality:")
        logger.info(f"   ❌ Broken Citations: {broken_links['total_broken_citations']}")
        logger.info(f"   ❌ Broken Internal Links: {broken_links['total_broken_internal']}")
        
        logger.info(f"📝 Quality Pass Rate: {quality.get('quality_pass_rate', 0):.1f}%")
        
        if quality.get("common_issues"):
            logger.info(f"🚨 Common Issues:")
            for issue_type, count in quality["common_issues"].items():
                logger.info(f"   • {issue_type}: {count}")
        
        similarity = report["content_similarity"]
        logger.info(f"🔄 Content Similarity: {similarity['similar_pairs']} similar pairs found")
        
        logger.info("=" * 80)

async def main():
    """Run baseline test."""
    runner = BaselineTestRunner()
    
    try:
        report = await runner.run_baseline_test()
        runner.print_summary(report)
        
        logger.info("🎉 Baseline testing complete!")
        logger.info("Now we have factual data to guide improvements.")
        
    except Exception as e:
        logger.error(f"❌ Baseline test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())