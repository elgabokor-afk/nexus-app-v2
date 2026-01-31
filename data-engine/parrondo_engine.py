"""
NEXUS AI - Parrondo's Paradox Engine
Finds winning strategies by combining two individually losing games.
Implementation based on game-theoretic principles for strategy optimization.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger("ParrondoEngine")

# ============================================================================
# PARRONDO'S PARADOX THEORY
# ============================================================================
# 
# Paradox: Two individually losing games (A and B) can produce
# a winning outcome when played in alternation.
#
# Game A: Simple coin with P(win) = 0.5 - ε (slightly biased loss)
# Game B: State-dependent game based on capital modulo M
#   - If capital % M == 0: P(win) = 0.1 - ε (bad odds)
#   - Otherwise: P(win) = 0.75 - ε (good odds)
#
# When played AABBAABB..., expected value becomes positive.
# ============================================================================

class GameType(Enum):
    GAME_A = "A"  # Simple biased coin
    GAME_B = "B"  # State-dependent game

@dataclass
class Strategy:
    """Trading strategy representation"""
    name: str
    win_rate: float
    expected_return: float
    sharpe_ratio: float
    recent_returns: List[float]
    
    @property
    def is_losing(self) -> bool:
        return self.expected_return < 0

@dataclass
class SwitchingResult:
    """Result of Parrondo optimization"""
    optimal_pattern: str  # e.g., "AABBAABB"
    combined_expected_return: float
    improvement_over_best: float
    confidence: float

# ============================================================================
# PARRONDO ENGINE
# ============================================================================

class ParrondoEngine:
    """
    Implements Parrondo's Paradox for trading strategy optimization.
    Finds optimal switching patterns between two strategies.
    """
    
    def __init__(self, modulo: int = 3, epsilon: float = 0.005):
        """
        Args:
            modulo: The M value for state-dependent Game B
            epsilon: Bias factor that makes individual games losing
        """
        self.modulo = modulo
        self.epsilon = epsilon
        
        # Simulation parameters
        self.simulation_steps = 10000
        self.monte_carlo_runs = 1000
        
        logger.info(f"   [PARRONDO] Engine initialized (M={modulo}, ε={epsilon})")
    
    def simulate_game_a(self, capital: float, stake: float = 1.0) -> Tuple[float, bool]:
        """
        Game A: Simple biased coin
        P(win) = 0.5 - epsilon
        """
        prob_win = 0.5 - self.epsilon
        win = np.random.random() < prob_win
        
        if win:
            return capital + stake, True
        else:
            return capital - stake, False
    
    def simulate_game_b(self, capital: float, stake: float = 1.0) -> Tuple[float, bool]:
        """
        Game B: State-dependent
        If capital % M == 0: P(win) = 0.1 - epsilon (bad branch)
        Otherwise: P(win) = 0.75 - epsilon (good branch)
        """
        if int(capital) % self.modulo == 0:
            prob_win = 0.1 - self.epsilon
        else:
            prob_win = 0.75 - self.epsilon
        
        win = np.random.random() < prob_win
        
        if win:
            return capital + stake, True
        else:
            return capital - stake, False
    
    def simulate_sequence(
        self, 
        pattern: str, 
        initial_capital: float = 0,
        steps: int = None
    ) -> Dict:
        """
        Simulate a game sequence defined by pattern.
        Pattern example: "AABB" means play A, A, B, B, repeat.
        """
        if steps is None:
            steps = self.simulation_steps
        
        capital = initial_capital
        capital_history = [capital]
        wins = 0
        
        pattern_len = len(pattern)
        
        for i in range(steps):
            game = pattern[i % pattern_len]
            
            if game == 'A':
                capital, won = self.simulate_game_a(capital)
            else:
                capital, won = self.simulate_game_b(capital)
            
            if won:
                wins += 1
            capital_history.append(capital)
        
        return {
            "final_capital": capital,
            "total_return": capital - initial_capital,
            "win_rate": wins / steps,
            "expected_per_step": (capital - initial_capital) / steps,
            "max_drawdown": self._calculate_max_drawdown(capital_history),
            "sharpe_approximation": self._calculate_sharpe(capital_history)
        }
    
    def _calculate_max_drawdown(self, history: List[float]) -> float:
        """Calculate maximum drawdown from capital history"""
        peak = history[0]
        max_dd = 0
        
        for value in history:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak != 0 else 0
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    def _calculate_sharpe(self, history: List[float], risk_free: float = 0) -> float:
        """Approximate Sharpe ratio from capital history"""
        returns = np.diff(history)
        if len(returns) == 0 or np.std(returns) == 0:
            return 0
        return (np.mean(returns) - risk_free) / np.std(returns)
    
    def find_optimal_pattern(
        self, 
        max_pattern_length: int = 8
    ) -> SwitchingResult:
        """
        Find the optimal switching pattern through Monte Carlo simulation.
        Tests various patterns like A, B, AB, BA, AAB, ABB, AABB, etc.
        """
        patterns_to_test = self._generate_patterns(max_pattern_length)
        
        best_pattern = None
        best_return = float('-inf')
        results = {}
        
        for pattern in patterns_to_test:
            # Monte Carlo simulation
            total_return = 0
            for _ in range(self.monte_carlo_runs):
                result = self.simulate_sequence(pattern, steps=1000)
                total_return += result['total_return']
            
            avg_return = total_return / self.monte_carlo_runs
            results[pattern] = avg_return
            
            if avg_return > best_return:
                best_return = avg_return
                best_pattern = pattern
        
        # Calculate improvement
        pure_a = results.get('A', 0)
        pure_b = results.get('B', 0)
        best_single = max(pure_a, pure_b)
        improvement = best_return - best_single
        
        # Confidence based on consistency
        confidence = min(1.0, abs(improvement) / 0.1) if improvement > 0 else 0
        
        return SwitchingResult(
            optimal_pattern=best_pattern,
            combined_expected_return=best_return,
            improvement_over_best=improvement,
            confidence=confidence
        )
    
    def _generate_patterns(self, max_length: int) -> List[str]:
        """Generate all meaningful patterns up to max_length"""
        patterns = ['A', 'B']
        
        for length in range(2, max_length + 1):
            for i in range(2 ** length):
                pattern = ''.join('A' if (i >> j) & 1 else 'B' for j in range(length))
                # Skip trivial patterns (all A or all B)
                if 'A' in pattern and 'B' in pattern:
                    patterns.append(pattern)
        
        return list(set(patterns))[:50]  # Limit for performance
    
    def apply_to_trading_strategies(
        self,
        strategy_a: Strategy,
        strategy_b: Strategy
    ) -> Dict:
        """
        Apply Parrondo analysis to two actual trading strategies.
        Maps strategy characteristics to game probabilities.
        """
        # Map win rates to game probabilities
        # Adjust epsilon based on how close to 50% the strategies are
        epsilon_a = max(0, 0.5 - strategy_a.win_rate)
        epsilon_b = max(0, 0.5 - strategy_b.win_rate)
        
        # Run optimization
        self.epsilon = (epsilon_a + epsilon_b) / 2
        optimal = self.find_optimal_pattern(max_pattern_length=6)
        
        # Calculate blended allocation
        a_count = optimal.optimal_pattern.count('A')
        b_count = optimal.optimal_pattern.count('B')
        total = a_count + b_count
        
        return {
            "strategy_a": strategy_a.name,
            "strategy_b": strategy_b.name,
            "optimal_pattern": optimal.optimal_pattern,
            "allocation": {
                "strategy_a_pct": a_count / total * 100,
                "strategy_b_pct": b_count / total * 100
            },
            "expected_improvement": optimal.improvement_over_best,
            "confidence": optimal.confidence,
            "recommendation": self._generate_recommendation(optimal, strategy_a, strategy_b)
        }
    
    def _generate_recommendation(
        self, 
        result: SwitchingResult,
        strategy_a: Strategy,
        strategy_b: Strategy
    ) -> str:
        """Generate human-readable recommendation"""
        if result.improvement_over_best <= 0:
            return f"No paradox benefit found. Stick with {strategy_a.name if strategy_a.expected_return > strategy_b.expected_return else strategy_b.name}"
        
        if result.confidence < 0.3:
            return f"Weak paradox signal. Consider {result.optimal_pattern} pattern but monitor closely."
        
        if result.confidence < 0.7:
            return f"Moderate paradox signal. Recommend {result.optimal_pattern} pattern with {result.improvement_over_best:.2%} expected improvement."
        
        return f"Strong Parrondo signal! Switch {result.optimal_pattern} for {result.improvement_over_best:.2%} edge."

# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

parrondo_engine = ParrondoEngine()

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PARRONDO'S PARADOX ENGINE TEST")
    print("=" * 60)
    
    engine = ParrondoEngine(modulo=3, epsilon=0.005)
    
    # Test individual games
    print("\n1. Testing Individual Games (1000 steps each):")
    print("-" * 40)
    
    result_a = engine.simulate_sequence("A", steps=10000)
    print(f"Game A Only: Return={result_a['total_return']:.2f}, WR={result_a['win_rate']:.2%}")
    
    result_b = engine.simulate_sequence("B", steps=10000)
    print(f"Game B Only: Return={result_b['total_return']:.2f}, WR={result_b['win_rate']:.2%}")
    
    # Test combined patterns
    print("\n2. Testing Combined Patterns:")
    print("-" * 40)
    
    for pattern in ["AB", "AAB", "ABB", "AABB", "AAABBB"]:
        result = engine.simulate_sequence(pattern, steps=10000)
        print(f"Pattern {pattern}: Return={result['total_return']:.2f}, WR={result['win_rate']:.2%}")
    
    # Find optimal
    print("\n3. Finding Optimal Pattern (Monte Carlo):")
    print("-" * 40)
    
    optimal = engine.find_optimal_pattern(max_pattern_length=6)
    print(f"Optimal Pattern: {optimal.optimal_pattern}")
    print(f"Expected Return: {optimal.combined_expected_return:.4f}")
    print(f"Improvement: {optimal.improvement_over_best:.4f}")
    print(f"Confidence: {optimal.confidence:.2%}")
    
    # Test with mock strategies
    print("\n4. Trading Strategy Application:")
    print("-" * 40)
    
    strat_a = Strategy(
        name="Mean Reversion",
        win_rate=0.48,
        expected_return=-0.02,
        sharpe_ratio=0.3,
        recent_returns=[-0.01, 0.02, -0.03, 0.01]
    )
    
    strat_b = Strategy(
        name="Momentum",
        win_rate=0.45,
        expected_return=-0.05,
        sharpe_ratio=0.2,
        recent_returns=[-0.02, -0.01, 0.05, -0.02]
    )
    
    recommendation = engine.apply_to_trading_strategies(strat_a, strat_b)
    print(f"Strategies: {strat_a.name} vs {strat_b.name}")
    print(f"Optimal Pattern: {recommendation['optimal_pattern']}")
    print(f"Allocation: {recommendation['allocation']}")
    print(f"Recommendation: {recommendation['recommendation']}")
