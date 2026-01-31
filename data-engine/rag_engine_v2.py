"""
NEXUS AI - RAG Engine V2
Advanced Retrieval-Augmented Generation system for academic validation
"""
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('.env.local')

from academic_manager import academic_manager
from embedding_cache import embedding_cache

class RAGEngineV2:
    """Advanced RAG system with multi-query and hybrid search"""
    
    def __init__(self):
        self.manager = academic_manager
        self.cache = embedding_cache
        self.min_similarity = 0.70
        self.min_quality = 0.5
        
    def validate_trading_strategy(
        self,
        strategy_description: str,
        symbol: str,
        direction: str,
        technical_context: Dict
    ) -> Dict:
        """
        Validate a trading strategy against academic literature
        
        Returns:
            {
                'approved': bool,
                'confidence': float,
                'p_value': float,
                'papers': List[Dict],
                'reasoning': str,
                'thesis_id': int
            }
        """
        
        # Build comprehensive query
        query = self._build_validation_query(
            strategy_description,
            symbol,
            direction,
            technical_context
        )
        
        print(f"   [RAG V2] Validating: {query[:100]}...")
        
        # Multi-query search
        papers = self._multi_query_search(query)
        
        if not papers:
            return {
                'approved': False,
                'confidence': 0.0,
                'p_value': 1.0,
                'papers': [],
                'reasoning': 'No academic precedent found in database',
                'thesis_id': None
            }
        
        # Calculate validation metrics
        avg_similarity = sum(p.get('similarity', 0) for p in papers) / len(papers)
        avg_quality = sum(p.get('quality_score', 0.5) for p in papers) / len(papers)
        
        # Weighted confidence score
        confidence = (avg_similarity * 0.7) + (avg_quality * 0.3)
        
        # P-value (statistical significance)
        p_value = max(0.001, 1 - confidence)
        
        # Approval logic
        approved = confidence > 0.75 and len(papers) >= 2
        
        # Best paper
        best_paper = papers[0] if papers else None
        thesis_id = best_paper.get('id') if best_paper else None
        
        # Generate reasoning
        reasoning = self._generate_reasoning(papers, confidence, approved)
        
        # Log citations
        if best_paper:
            self.manager.increment_citation_count(thesis_id)
        
        return {
            'approved': approved,
            'confidence': confidence,
            'p_value': p_value,
            'papers': papers[:3],  # Top 3
            'reasoning': reasoning,
            'thesis_id': thesis_id
        }
    
    def _build_validation_query(
        self,
        strategy: str,
        symbol: str,
        direction: str,
        technical: Dict
    ) -> str:
        """Build comprehensive query for validation"""
        
        rsi = technical.get('rsi_value', 50)
        trend = technical.get('trend', 'NEUTRAL')
        imbalance = technical.get('imbalance_ratio', 0)
        
        query_parts = [
            f"Trading strategy: {strategy}",
            f"Asset: {symbol}",
            f"Direction: {direction}",
            f"Market conditions: {trend} trend",
            f"RSI: {rsi:.0f}",
        ]
        
        if abs(imbalance) > 0.3:
            query_parts.append(f"Order book imbalance: {imbalance:.2f}")
        
        return " | ".join(query_parts)
    
    def _multi_query_search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Multi-query search strategy:
        1. Try semantic search first
        2. Fall back to hybrid if needed
        3. Expand query if results are poor
        """
        
        # Try semantic search
        results = self.manager.search_papers_semantic(
            query,
            threshold=self.min_similarity,
            limit=limit
        )
        
        if results and len(results) >= 3:
            return results
        
        # Try hybrid search
        print(f"   [RAG V2] Semantic search insufficient, trying hybrid...")
        results = self.manager.search_papers_hybrid(
            query,
            threshold=self.min_similarity - 0.05,
            limit=limit
        )
        
        if results:
            return results
        
        # Expand query (remove specific details)
        expanded_query = self._expand_query(query)
        print(f"   [RAG V2] Expanding query: {expanded_query[:100]}...")
        
        results = self.manager.search_papers_semantic(
            expanded_query,
            threshold=self.min_similarity - 0.10,
            limit=limit
        )
        
        return results
    
    def _expand_query(self, query: str) -> str:
        """Expand query by removing specific details"""
        # Extract key concepts
        keywords = [
            'momentum', 'reversal', 'trend', 'volatility',
            'RSI', 'MACD', 'moving average', 'support', 'resistance',
            'order book', 'liquidity', 'volume'
        ]
        
        # Find matching keywords
        found_keywords = [kw for kw in keywords if kw.lower() in query.lower()]
        
        if found_keywords:
            return f"Trading strategies using {', '.join(found_keywords[:3])}"
        
        return "Quantitative trading strategies and technical analysis"
    
    def _generate_reasoning(
        self,
        papers: List[Dict],
        confidence: float,
        approved: bool
    ) -> str:
        """Generate human-readable reasoning"""
        
        if not papers:
            return "No academic support found for this strategy."
        
        paper_count = len(papers)
        universities = list(set(p.get('university', 'Unknown') for p in papers[:3]))
        avg_sim = sum(p.get('similarity', 0) for p in papers) / len(papers)
        
        if approved:
            reasoning = (
                f"Strategy validated by {paper_count} academic papers "
                f"from {', '.join(universities)}. "
                f"Average similarity: {avg_sim:.1%}. "
                f"Confidence: {confidence:.1%}."
            )
        else:
            reasoning = (
                f"Limited academic support. Found {paper_count} papers "
                f"with {avg_sim:.1%} similarity. "
                f"Confidence below threshold ({confidence:.1%} < 75%)."
            )
        
        return reasoning
    
    def get_strategy_recommendations(
        self,
        symbol: str,
        market_conditions: Dict
    ) -> List[Dict]:
        """
        Get strategy recommendations based on current market conditions
        """
        
        trend = market_conditions.get('trend', 'NEUTRAL')
        volatility = market_conditions.get('volatility', 'MEDIUM')
        
        query = f"{trend} market with {volatility} volatility trading strategies for {symbol}"
        
        papers = self.manager.search_papers_semantic(query, threshold=0.65, limit=10)
        
        recommendations = []
        for paper in papers:
            recommendations.append({
                'paper_id': paper.get('id'),
                'title': paper.get('paper_id', 'Unknown'),
                'authors': paper.get('authors', 'Unknown'),
                'university': paper.get('university', 'Unknown'),
                'similarity': paper.get('similarity', 0),
                'quality': paper.get('quality_score', 0.5),
                'summary': paper.get('content', '')[:200] + '...'
            })
        
        return recommendations
    
    def analyze_paper_cluster(self, cluster_id: int) -> Dict:
        """Analyze a cluster of papers"""
        
        papers = self.manager.get_papers_by_cluster(cluster_id)
        
        if not papers:
            return {'error': 'Cluster not found'}
        
        # Calculate cluster metrics
        avg_quality = sum(p.get('quality_score', 0.5) for p in papers) / len(papers)
        total_citations = sum(p.get('citation_count', 0) for p in papers)
        universities = list(set(p.get('university') for p in papers if p.get('university')))
        
        return {
            'cluster_id': cluster_id,
            'paper_count': len(papers),
            'avg_quality': avg_quality,
            'total_citations': total_citations,
            'universities': universities,
            'top_papers': papers[:5]
        }
    
    def get_research_insights(self, query: str) -> Dict:
        """
        Get comprehensive research insights for a query
        """
        
        # Search papers
        papers = self.manager.search_papers_hybrid(query, threshold=0.60, limit=20)
        
        if not papers:
            return {'error': 'No papers found'}
        
        # Analyze results
        universities = {}
        for paper in papers:
            uni = paper.get('university', 'Unknown')
            universities[uni] = universities.get(uni, 0) + 1
        
        # Top universities
        top_unis = sorted(universities.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Average metrics
        avg_similarity = sum(p.get('similarity', 0) for p in papers) / len(papers)
        avg_quality = sum(p.get('quality_score', 0.5) for p in papers) / len(papers)
        
        return {
            'query': query,
            'total_papers': len(papers),
            'avg_similarity': avg_similarity,
            'avg_quality': avg_quality,
            'top_universities': top_unis,
            'papers': papers[:10]
        }

# Singleton instance
rag_engine = RAGEngineV2()

if __name__ == "__main__":
    # Test
    print("Testing RAG Engine V2...")
    
    result = rag_engine.validate_trading_strategy(
        strategy_description="RSI divergence with volume confirmation",
        symbol="BTC/USD",
        direction="LONG",
        technical_context={
            'rsi_value': 35,
            'trend': 'BULLISH',
            'imbalance_ratio': 0.45
        }
    )
    
    print(f"\nValidation Result:")
    print(f"  Approved: {result['approved']}")
    print(f"  Confidence: {result['confidence']:.1%}")
    print(f"  P-Value: {result['p_value']:.4f}")
    print(f"  Papers: {len(result['papers'])}")
    print(f"  Reasoning: {result['reasoning']}")
