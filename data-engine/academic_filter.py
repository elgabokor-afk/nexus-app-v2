"""
NEXUS AI - Academic Filter (Institutional Grade)
Hard exclusion, dual-keyword validation, and prestige scoring for academic papers
"""
import re
from typing import Dict, Tuple, List, Optional

# ============================================================================
# 1. HARD EXCLUSION BLACKLIST (Zero Tolerance)
# ============================================================================

NOISE_BLACKLIST = {
    # Social/Behavioral Noise
    "social media sentiment", "twitter sentiment", "reddit sentiment",
    "esg", "environmental social governance", "sustainability reporting",
    "retail investor behavior", "retail trading", "robinhood",
    "political forecasting", "election prediction", "polling data",
    "survey-based", "questionnaire study", "behavioral survey",
    
    # Irrelevant Domains
    "genomics", "gene expression", "dna sequencing",
    "bio-informatics", "protein folding", "crispr",
    "robotics", "autonomous vehicles", "drone technology",
    "hardware engineering", "circuit design", "semiconductor",
    "renewable energy", "solar panel", "wind turbine",
    
    # Crypto Retail Noise
    "nft", "non-fungible token", "digital collectible",
    "dao governance", "decentralized autonomous",
    "staking rewards", "proof of stake rewards",
    "yield farming", "liquidity mining",
    "meme coin", "dogecoin", "shiba inu", "pepe coin",
    
    # Low-Signal Academic Patterns
    "case study of", "exploratory analysis", "preliminary findings",
    "qualitative research", "interview-based", "focus group"
}

# Exception: Allow renewable energy if focused on commodity derivatives
COMMODITY_EXCEPTION_KEYWORDS = ["futures", "derivatives", "commodity trading", "energy trading"]

# ============================================================================
# 2. DUAL-KEYWORD VALIDATION (Alpha Standard)
# ============================================================================

ALPHA_KEYWORDS = {
    "execution_liquidity": [
        "adverse selection", "order flow toxicity", "vpin", "volume-synchronized probability",
        "market impact", "price impact model", "latency arbitrage", "high frequency trading",
        "optimal execution", "almgren-chriss", "implementation shortfall", "arrival price",
        "bid-ask spread dynamics", "limit order book", "order book imbalance"
    ],
    
    "signal_processing": [
        "kalman filter", "extended kalman", "particle filter",
        "fourier transform", "spectral analysis", "frequency domain",
        "wavelet analysis", "wavelet transform", "time-frequency",
        "regime switching", "markov switching", "hidden markov model",
        "state space model", "dynamic linear model"
    ],
    
    "statistical_arbitrage": [
        "cointegration", "johansen test", "engle-granger",
        "pair trading", "pairs trading", "statistical pairs",
        "mean reversion", "ornstein-uhlenbeck", "mean-reverting process",
        "vector error correction", "vecm", "error correction model",
        "kelly criterion", "optimal bet sizing", "fractional kelly"
    ],
    
    "paradox_theory": [
        "parrondo's paradox", "parrondo paradox", "losing game paradox",
        "game theory", "nash equilibrium", "game theoretic",
        "strategic interaction", "mechanism design", "auction theory",
        "adversarial trading", "predatory trading"
    ],
    
    "quantitative_foundations": [
        "stochastic calculus", "ito's lemma", "ito calculus",
        "partial differential equation", "pde", "black-scholes pde",
        "stochastic differential equation", "sde", "geometric brownian",
        "monte carlo simulation", "variance reduction", "importance sampling",
        "maximum likelihood", "bayesian inference", "mcmc"
    ]
}

# ============================================================================
# 3. PRESTIGE SCORING
# ============================================================================

ELITE_JOURNALS = [
    "journal of finance", "journal of financial economics", "review of financial studies",
    "journal of econometrics", "econometrica", "journal of political economy",
    "quarterly journal of economics", "american economic review",
    "journal of financial and quantitative analysis", "mathematical finance",
    "quantitative finance", "journal of derivatives"
]

ELITE_UNIVERSITIES = [
    "harvard", "mit", "massachusetts institute of technology",
    "stanford", "princeton", "oxford", "cambridge",
    "yale", "columbia", "university of chicago", "chicago booth",
    "wharton", "london school of economics", "lse",
    "berkeley", "caltech", "nyu stern"
]

NBER_KEYWORDS = ["nber", "national bureau of economic research", "nber working paper"]

MATH_COMPLEXITY_INDICATORS = [
    "partial differential equation", "stochastic integral", "ito's lemma",
    "eigenvalue", "eigenvector", "spectral decomposition",
    "martingale", "filtration", "sigma-algebra",
    "hilbert space", "banach space", "functional analysis",
    "measure theory", "probability measure"
]

# ============================================================================
# 4. MATHEMATICAL RIGOR REQUIREMENTS (Martingale/Markov Foundation)
# ============================================================================

REQUIRED_MATH_FOUNDATIONS = [
    # Martingale Theory
    "martingale", "submartingale", "supermartingale",
    "martingale theory", "optional stopping theorem",
    "doob's inequality", "martingale convergence",
    
    # Markov Processes
    "markov process", "markov chain", "hidden markov",
    "markov switching", "transition matrix", "stationary distribution",
    "ergodic", "markov decision process", "mdp",
    
    # Stochastic Calculus
    "stochastic differential equation", "sde",
    "ito lemma", "ito's lemma", "ito calculus", "itô",
    "brownian motion", "wiener process", "geometric brownian",
    "stochastic integral", "ito integral",
    
    # Advanced Stochastic
    "poisson process", "jump diffusion", "levy process",
    "fokker-planck", "kolmogorov equation", "backward equation",
    "feynman-kac", "girsanov theorem",
    
    # Measure Theory
    "measure theory", "probability measure", "lebesgue",
    "radon-nikodym", "borel sigma-algebra"
]

# Topics that require mathematical foundations
TOPICS_REQUIRING_MATH_FOUNDATION = [
    "market microstructure", "limit order book", "order book dynamics",
    "parrondo", "complex network stability", "systemic risk",
    "optimal execution", "price impact", "market making"
]

# ============================================================================
# FILTER FUNCTIONS
# ============================================================================

def check_hard_exclusion(text: str) -> Tuple[bool, Optional[str]]:
    """
    Hard exclusion filter. Returns (should_abort, reason).
    If any blacklist term is found, abort unless commodity exception applies.
    """
    text_lower = text.lower()
    
    for term in NOISE_BLACKLIST:
        if term in text_lower:
            # Check for commodity exception
            if any(kw in text_lower for kw in COMMODITY_EXCEPTION_KEYWORDS):
                continue  # Allow renewable energy if commodity-focused
            
            return True, f"Blacklist term detected: '{term}'"
    
    return False, None


def validate_dual_keywords(text: str) -> Tuple[bool, int, List[str]]:
    """
    Dual-keyword validation. Returns (is_valid, match_count, matched_categories).
    Requires at least 2 keywords from ANY category.
    """
    text_lower = text.lower()
    matched_categories = []
    total_matches = 0
    
    for category, keywords in ALPHA_KEYWORDS.items():
        category_matches = sum(1 for kw in keywords if kw in text_lower)
        if category_matches > 0:
            matched_categories.append(category)
            total_matches += category_matches
    
    is_valid = total_matches >= 2
    return is_valid, total_matches, matched_categories


def validate_mathematical_rigor(text: str) -> Tuple[bool, float, List[str]]:
    """
    Validate paper has Martingale/Markov theoretical foundation.
    Papers touching advanced topics MUST have mathematical rigor.
    Returns (is_valid, rigor_score, matched_foundations).
    """
    text_lower = text.lower()
    
    # Check if paper touches topics requiring math foundation
    requires_foundation = any(
        topic in text_lower for topic in TOPICS_REQUIRING_MATH_FOUNDATION
    )
    
    # Count mathematical foundations present
    matched_foundations = [
        foundation for foundation in REQUIRED_MATH_FOUNDATIONS 
        if foundation in text_lower
    ]
    
    foundation_count = len(matched_foundations)
    
    # Calculate rigor score (0.0 to 1.0)
    rigor_score = min(1.0, foundation_count / 3.0)  # 3+ foundations = max score
    
    # Validation logic:
    # - If requires foundation: must have at least 1 match
    # - If doesn't require: pass automatically
    if requires_foundation:
        is_valid = foundation_count >= 1
    else:
        is_valid = True
        
    return is_valid, rigor_score, matched_foundations


def calculate_prestige_score(
    text: str,
    journal: Optional[str] = None,
    university: Optional[str] = None,
    abstract: Optional[str] = None
) -> float:
    """
    Calculate prestige score based on source authority and mathematical complexity.
    Returns score from 0.0 to 2.0+ (base 1.0, with multipliers).
    """
    score = 1.0
    text_lower = text.lower()
    
    # Journal bonus (+50%)
    if journal:
        journal_lower = journal.lower()
        if any(elite in journal_lower for elite in ELITE_JOURNALS):
            score *= 1.5
    
    # University bonus (+30%)
    if university:
        uni_lower = university.lower()
        if any(elite in uni_lower for elite in ELITE_UNIVERSITIES):
            score *= 1.3
    
    # NBER bonus (+40%)
    if any(nber in text_lower for nber in NBER_KEYWORDS):
        score *= 1.4
    
    # Mathematical complexity bonus (+50%)
    if abstract:
        abstract_lower = abstract.lower()
        math_matches = sum(1 for indicator in MATH_COMPLEXITY_INDICATORS if indicator in abstract_lower)
        if math_matches >= 2:
            score *= 1.5
        elif math_matches == 1:
            score *= 1.2
    
    return round(score, 2)


def comprehensive_filter(
    title: str,
    abstract: str,
    journal: Optional[str] = None,
    university: Optional[str] = None,
    full_text: Optional[str] = None
) -> Dict:
    """
    Run comprehensive filter pipeline.
    Returns dict with filter results and scores.
    """
    # Combine text for analysis
    combined_text = f"{title} {abstract}"
    if full_text:
        combined_text += f" {full_text[:5000]}"  # Limit to avoid performance issues
    
    # 1. Hard Exclusion
    should_abort, abort_reason = check_hard_exclusion(combined_text)
    if should_abort:
        return {
            "passed": False,
            "stage": "hard_exclusion",
            "reason": abort_reason,
            "prestige_score": 0.0,
            "keyword_matches": 0
        }
    
    # 2. Dual-Keyword Validation
    is_valid, match_count, categories = validate_dual_keywords(combined_text)
    if not is_valid:
        return {
            "passed": False,
            "stage": "keyword_validation",
            "reason": f"Insufficient alpha keywords (found {match_count}, need 2+)",
            "prestige_score": 0.0,
            "keyword_matches": match_count,
            "matched_categories": categories
        }
    
    # 2.5 Mathematical Rigor Validation (Martingale/Markov Foundation)
    math_valid, rigor_score, foundations = validate_mathematical_rigor(combined_text)
    if not math_valid:
        return {
            "passed": False,
            "stage": "mathematical_rigor",
            "reason": "Topic requires Martingale/Markov foundation but none found",
            "prestige_score": 0.0,
            "keyword_matches": match_count,
            "rigor_score": rigor_score
        }
    
    # 3. Prestige Scoring
    prestige = calculate_prestige_score(
        text=combined_text,
        journal=journal,
        university=university,
        abstract=abstract
    )
    
    # Boost prestige with rigor score
    prestige = prestige * (1 + rigor_score * 0.5)  # Up to +50% for math rigor
    
    return {
        "passed": True,
        "stage": "complete",
        "prestige_score": round(prestige, 2),
        "keyword_matches": match_count,
        "matched_categories": categories,
        "rigor_score": rigor_score,
        "math_foundations": foundations[:5],  # Top 5 for brevity
        "reason": "Passed all filters (including math rigor)"
    }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test 1: Should FAIL (social media noise)
    test1 = comprehensive_filter(
        title="Twitter Sentiment and Stock Returns",
        abstract="We analyze social media sentiment from Twitter to predict stock returns.",
        journal="Journal of Behavioral Finance"
    )
    print(f"Test 1 (Social Media): {test1}")
    
    # Test 2: Should PASS (high-quality quant)
    test2 = comprehensive_filter(
        title="Optimal Execution with Kalman Filtering",
        abstract="We develop an optimal execution strategy using Kalman filters and stochastic calculus to minimize market impact.",
        journal="Journal of Finance",
        university="MIT"
    )
    print(f"\nTest 2 (Elite Quant): {test2}")
    
    # Test 3: Should FAIL (insufficient keywords)
    test3 = comprehensive_filter(
        title="A Survey of Cryptocurrency Adoption",
        abstract="We survey 500 retail investors about their cryptocurrency preferences.",
        university="Random University"
    )
    print(f"\nTest 3 (Survey Study): {test3}")
    
    # Test 4: Should PASS (Parrondo's Paradox)
    test4 = comprehensive_filter(
        title="Parrondo's Paradox in Statistical Arbitrage",
        abstract="We apply game theory and Parrondo's paradox to develop a mean-reverting pairs trading strategy with cointegration.",
        journal="Quantitative Finance",
        university="Stanford"
    )
    print(f"\nTest 4 (Paradox Theory): {test4}")
