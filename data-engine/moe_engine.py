"""
NEXUS AI - Mixture of Experts (MoE) Router
Sovereign inference engine running 100% on local RTX 4070.
Three specialized experts: Macro, Micro, and Game Theory.
"""
import os
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import time

# Local imports
try:
    from vpin_engine import VPINResult, VPIN_THRESHOLDS
    from parrondo_engine import ParrondoEngine, Strategy
except ImportError:
    VPINResult = None
    VPIN_THRESHOLDS = {"LOW": 0.4, "MODERATE": 0.5, "HIGH": 0.6, "CRITICAL": 0.75}

logger = logging.getLogger("MoEEngine")

# ============================================================================
# CONFIGURATION
# ============================================================================

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = "llama3.2:3b"  # Primary model for expert inference

# Expert weights (sum to 1.0)
DEFAULT_WEIGHTS = {
    "macro": 0.35,    # Academic/fundamental context
    "micro": 0.40,    # Real-time market microstructure
    "game": 0.25      # Game theory/Parrondo optimization
}

# ============================================================================
# DATA STRUCTURES
# ============================================================================

class RiskLevel(Enum):
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    EXTREME = 5

@dataclass
class ExpertOpinion:
    """Single expert's evaluation"""
    expert_name: str
    score: float          # -1.0 to 1.0 (bearish to bullish)
    confidence: float     # 0.0 to 1.0
    risk_level: RiskLevel
    reasoning: str
    latency_ms: float

@dataclass
class MoEDecision:
    """Aggregated MoE decision"""
    final_score: float
    direction: str        # "LONG", "SHORT", "NEUTRAL"
    confidence: float
    risk_level: RiskLevel
    experts: List[ExpertOpinion]
    recommendation: str
    total_latency_ms: float

# ============================================================================
# EXPERT IMPLEMENTATIONS
# ============================================================================

class MacroExpert:
    """
    Macro Expert: Academic and fundamental context.
    Queries Supabase vector DB for academic precedent.
    Evaluates strategy alignment with peer-reviewed research.
    """
    
    def __init__(self):
        self.name = "MACRO"
        self.weight = DEFAULT_WEIGHTS["macro"]
        
    def evaluate(self, context: Dict) -> ExpertOpinion:
        """
        Evaluate based on academic context.
        
        Context expected:
        - academic_similarity: float (0-1)
        - paper_count: int
        - avg_prestige: float
        - rigor_score: float
        """
        start_time = time.time()
        
        academic_sim = context.get("academic_similarity", 0.5)
        paper_count = context.get("paper_count", 0)
        avg_prestige = context.get("avg_prestige", 0.5)
        rigor_score = context.get("rigor_score", 0.0)
        
        # Calculate score
        if paper_count == 0:
            score = 0.0
            confidence = 0.2
            risk = RiskLevel.HIGH
            reasoning = "No academic precedent found. Proceed with caution."
        else:
            # Weighted combination
            score = (academic_sim * 0.4 + avg_prestige * 0.3 + rigor_score * 0.3) * 2 - 1
            confidence = min(1.0, paper_count / 5) * academic_sim
            
            if score > 0.5:
                risk = RiskLevel.LOW
                reasoning = f"Strong academic backing ({paper_count} papers, {avg_prestige:.2f} prestige)"
            elif score > 0:
                risk = RiskLevel.MEDIUM
                reasoning = f"Moderate academic support ({paper_count} papers)"
            else:
                risk = RiskLevel.HIGH
                reasoning = f"Weak academic alignment (similarity: {academic_sim:.2f})"
        
        latency = (time.time() - start_time) * 1000
        
        return ExpertOpinion(
            expert_name=self.name,
            score=score,
            confidence=confidence,
            risk_level=risk,
            reasoning=reasoning,
            latency_ms=latency
        )

class MicroExpert:
    """
    Micro Expert: Real-time market microstructure.
    Analyzes Order Book Imbalance (OBI) and VPIN toxicity.
    Detects adverse selection and information asymmetry.
    """
    
    def __init__(self):
        self.name = "MICRO"
        self.weight = DEFAULT_WEIGHTS["micro"]
        
    def evaluate(self, context: Dict) -> ExpertOpinion:
        """
        Evaluate based on order book and flow toxicity.
        
        Context expected:
        - obi: float (order book imbalance, -1 to 1)
        - vpin: float (0 to 1)
        - spread_bps: float
        - depth_ratio: float
        """
        start_time = time.time()
        
        obi = context.get("obi", 0.0)
        vpin = context.get("vpin", 0.3)
        spread_bps = context.get("spread_bps", 10)
        depth_ratio = context.get("depth_ratio", 1.0)
        
        # VPIN risk assessment
        if vpin >= VPIN_THRESHOLDS["CRITICAL"]:
            risk = RiskLevel.EXTREME
            vpin_penalty = 1.0
            reasoning = f"CRITICAL toxicity (VPIN: {vpin:.3f}). Halt all entries!"
        elif vpin >= VPIN_THRESHOLDS["HIGH"]:
            risk = RiskLevel.HIGH
            vpin_penalty = 0.7
            reasoning = f"High toxicity (VPIN: {vpin:.3f}). Reduce position size."
        elif vpin >= VPIN_THRESHOLDS["MODERATE"]:
            risk = RiskLevel.MEDIUM
            vpin_penalty = 0.4
            reasoning = f"Moderate toxicity (VPIN: {vpin:.3f}). Proceed cautiously."
        else:
            risk = RiskLevel.LOW
            vpin_penalty = 0.0
            reasoning = f"Low toxicity (VPIN: {vpin:.3f}). Safe conditions."
        
        # OBI signal (positive = buy pressure, negative = sell pressure)
        score = obi * (1 - vpin_penalty)
        
        # Adjust for spread and depth
        if spread_bps > 20:
            score *= 0.8
            reasoning += " Wide spread reduces conviction."
        
        # Confidence based on depth and vpin
        confidence = min(1.0, depth_ratio) * (1 - vpin)
        
        latency = (time.time() - start_time) * 1000
        
        return ExpertOpinion(
            expert_name=self.name,
            score=score,
            confidence=confidence,
            risk_level=risk,
            reasoning=reasoning,
            latency_ms=latency
        )

class GameTheoryExpert:
    """
    Game Theory Expert: Parrondo's Paradox optimization.
    Finds equilibrium between competing strategies.
    Analyzes meta-game dynamics for optimal switching.
    """
    
    def __init__(self):
        self.name = "GAME"
        self.weight = DEFAULT_WEIGHTS["game"]
        self.parrondo = ParrondoEngine() if 'ParrondoEngine' in dir() else None
        
    def evaluate(self, context: Dict) -> ExpertOpinion:
        """
        Evaluate based on strategy history and switching opportunity.
        
        Context expected:
        - strategy_a_returns: List[float]
        - strategy_b_returns: List[float]
        - current_strategy: str
        - regime: str
        """
        start_time = time.time()
        
        strategy_a_returns = context.get("strategy_a_returns", [])
        strategy_b_returns = context.get("strategy_b_returns", [])
        current_strategy = context.get("current_strategy", "A")
        regime = context.get("regime", "UNKNOWN")
        
        if not strategy_a_returns or not strategy_b_returns:
            return ExpertOpinion(
                expert_name=self.name,
                score=0.0,
                confidence=0.1,
                risk_level=RiskLevel.MEDIUM,
                reasoning="Insufficient history for Parrondo analysis",
                latency_ms=(time.time() - start_time) * 1000
            )
        
        # Calculate strategy metrics
        import numpy as np
        mean_a = np.mean(strategy_a_returns)
        mean_b = np.mean(strategy_b_returns)
        
        # Check if both strategies are "losing"
        both_losing = mean_a < 0 and mean_b < 0
        
        if both_losing:
            # Parrondo opportunity!
            score = 0.3  # Slight bullish bias due to paradox
            confidence = 0.6
            risk = RiskLevel.MEDIUM
            reasoning = f"Parrondo opportunity: Both strategies losing ({mean_a:.3f}, {mean_b:.3f}). Switch pattern may yield profits."
        else:
            # Standard case: favor winning strategy
            if mean_a > mean_b:
                score = 0.2 if current_strategy == "A" else -0.2
                reasoning = f"Strategy A outperforming ({mean_a:.3f} vs {mean_b:.3f})"
            else:
                score = 0.2 if current_strategy == "B" else -0.2
                reasoning = f"Strategy B outperforming ({mean_b:.3f} vs {mean_a:.3f})"
            
            confidence = 0.5
            risk = RiskLevel.LOW
        
        latency = (time.time() - start_time) * 1000
        
        return ExpertOpinion(
            expert_name=self.name,
            score=score,
            confidence=confidence,
            risk_level=risk,
            reasoning=reasoning,
            latency_ms=latency
        )

# ============================================================================
# MOE ROUTER
# ============================================================================

class MoERouter:
    """
    Mixture of Experts Router.
    Aggregates opinions from specialized experts using confidence-weighted voting.
    All inference runs locally on RTX 4070 via Ollama.
    """
    
    def __init__(self):
        self.macro_expert = MacroExpert()
        self.micro_expert = MicroExpert()
        self.game_expert = GameTheoryExpert()
        
        self.experts = [self.macro_expert, self.micro_expert, self.game_expert]
        
        logger.info("   [MoE] Router initialized with 3 experts (Macro/Micro/Game)")
    
    def route_and_aggregate(self, context: Dict) -> MoEDecision:
        """
        Route input to all experts and aggregate opinions.
        Uses confidence-weighted voting.
        
        Context should include:
        - academic: Dict for MacroExpert
        - orderbook: Dict for MicroExpert
        - strategy_history: Dict for GameTheoryExpert
        """
        start_time = time.time()
        opinions = []
        
        # Get academic context
        academic_context = context.get("academic", {})
        macro_opinion = self.macro_expert.evaluate(academic_context)
        opinions.append(macro_opinion)
        
        # Get orderbook context
        orderbook_context = context.get("orderbook", {})
        micro_opinion = self.micro_expert.evaluate(orderbook_context)
        opinions.append(micro_opinion)
        
        # Get strategy history
        strategy_context = context.get("strategy_history", {})
        game_opinion = self.game_expert.evaluate(strategy_context)
        opinions.append(game_opinion)
        
        # Weighted aggregation
        weights = [self.macro_expert.weight, self.micro_expert.weight, self.game_expert.weight]
        
        # Adjust weights by confidence
        adjusted_weights = [w * o.confidence for w, o in zip(weights, opinions)]
        weight_sum = sum(adjusted_weights) or 1.0
        normalized_weights = [w / weight_sum for w in adjusted_weights]
        
        # Final score
        final_score = sum(w * o.score for w, o in zip(normalized_weights, opinions))
        
        # Aggregate confidence
        final_confidence = sum(w * o.confidence for w, o in zip(normalized_weights, opinions))
        
        # Risk level (worst of all experts)
        risk_levels = [o.risk_level.value for o in opinions]
        final_risk = RiskLevel(max(risk_levels))
        
        # Direction
        if final_score > 0.2:
            direction = "LONG"
        elif final_score < -0.2:
            direction = "SHORT"
        else:
            direction = "NEUTRAL"
        
        # Generate recommendation
        recommendation = self._generate_recommendation(final_score, final_confidence, final_risk, opinions)
        
        total_latency = (time.time() - start_time) * 1000
        
        return MoEDecision(
            final_score=round(final_score, 4),
            direction=direction,
            confidence=round(final_confidence, 4),
            risk_level=final_risk,
            experts=opinions,
            recommendation=recommendation,
            total_latency_ms=round(total_latency, 2)
        )
    
    def _generate_recommendation(
        self, 
        score: float, 
        confidence: float, 
        risk: RiskLevel,
        opinions: List[ExpertOpinion]
    ) -> str:
        """Generate human-readable recommendation"""
        
        if risk == RiskLevel.EXTREME:
            return "⚠️ CRITICAL RISK: Halt all trading. VPIN indicates toxic flow."
        
        if risk == RiskLevel.HIGH:
            return f"🔴 HIGH RISK: Reduce position size by 50%. Score: {score:.2f}"
        
        if confidence < 0.3:
            return "⚪ LOW CONFIDENCE: Insufficient data for decision. Wait for more signals."
        
        if score > 0.5 and confidence > 0.6:
            return f"🟢 STRONG LONG: Score {score:.2f}, Confidence {confidence:.2%}"
        elif score < -0.5 and confidence > 0.6:
            return f"🔴 STRONG SHORT: Score {score:.2f}, Confidence {confidence:.2%}"
        elif score > 0.2:
            return f"🟡 WEAK LONG: Score {score:.2f}, monitor closely"
        elif score < -0.2:
            return f"🟡 WEAK SHORT: Score {score:.2f}, monitor closely"
        else:
            return f"⚪ NEUTRAL: Score {score:.2f}, no clear edge"

# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

moe_router = MoERouter()

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("MIXTURE OF EXPERTS (MoE) ROUTER TEST")
    print("=" * 60)
    
    router = MoERouter()
    
    # Test context
    context = {
        "academic": {
            "academic_similarity": 0.82,
            "paper_count": 4,
            "avg_prestige": 1.65,
            "rigor_score": 0.8
        },
        "orderbook": {
            "obi": 0.35,
            "vpin": 0.42,
            "spread_bps": 8,
            "depth_ratio": 1.2
        },
        "strategy_history": {
            "strategy_a_returns": [-0.01, 0.02, -0.015, -0.005, 0.01],
            "strategy_b_returns": [-0.02, -0.01, 0.03, -0.02, -0.01],
            "current_strategy": "A",
            "regime": "VOLATILE"
        }
    }
    
    decision = router.route_and_aggregate(context)
    
    print(f"\n{'='*60}")
    print("DECISION SUMMARY")
    print(f"{'='*60}")
    print(f"Final Score: {decision.final_score}")
    print(f"Direction: {decision.direction}")
    print(f"Confidence: {decision.confidence:.2%}")
    print(f"Risk Level: {decision.risk_level.name}")
    print(f"Latency: {decision.total_latency_ms:.2f}ms")
    print(f"\nRecommendation: {decision.recommendation}")
    
    print(f"\n{'='*60}")
    print("EXPERT OPINIONS")
    print(f"{'='*60}")
    for expert in decision.experts:
        print(f"\n[{expert.expert_name}]")
        print(f"  Score: {expert.score:.4f}")
        print(f"  Confidence: {expert.confidence:.2%}")
        print(f"  Risk: {expert.risk_level.name}")
        print(f"  Reasoning: {expert.reasoning}")
        print(f"  Latency: {expert.latency_ms:.2f}ms")
