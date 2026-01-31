"""
NEXUS AI - VPIN Flow Toxicity Engine
Volume-Synchronized Probability of Informed Trading (Easley et al. 2012)
Detects information asymmetry and toxic order flow in real-time.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import time
import logging

logger = logging.getLogger("VPINEngine")

# ============================================================================
# VPIN THRESHOLDS (Institutional Calibration)
# ============================================================================

VPIN_THRESHOLDS = {
    "LOW": 0.40,       # Safe trading conditions
    "MODERATE": 0.50,  # Caution advised
    "HIGH": 0.60,      # Reduce position sizes
    "CRITICAL": 0.75   # Halt new entries
}

RISK_ACTIONS = {
    "LOW": "NORMAL_TRADING",
    "MODERATE": "REDUCE_SIZE_25PCT",
    "HIGH": "HALT_NEW_ENTRIES",
    "CRITICAL": "EMERGENCY_LIQUIDATION"
}

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Trade:
    """Single trade event"""
    timestamp: float
    side: str  # 'buy' or 'sell'
    volume: float
    price: float

@dataclass
class VolumeBucket:
    """Volume-synchronized bucket for VPIN calculation"""
    timestamp: float
    buy_volume: float
    sell_volume: float
    
    @property
    def total_volume(self) -> float:
        return self.buy_volume + self.sell_volume
    
    @property
    def imbalance(self) -> float:
        if self.total_volume == 0:
            return 0
        return abs(self.buy_volume - self.sell_volume) / self.total_volume

@dataclass 
class VPINResult:
    """VPIN calculation result"""
    vpin: float
    risk_level: str
    action: str
    bucket_count: int
    timestamp: float
    
# ============================================================================
# VPIN ENGINE
# ============================================================================

class VPINEngine:
    """
    VPIN Implementation according to Easley et al. (2012)
    "Flow Toxicity and Liquidity in a High Frequency World"
    
    Calculates Volume-Synchronized Probability of Informed Trading
    to detect toxic order flow and information asymmetry.
    """
    
    def __init__(
        self, 
        bucket_size: float = 50.0,      # Volume per bucket
        window_size: int = 50,          # Number of buckets for VPIN
        decay_factor: float = 0.95      # Exponential decay for old buckets
    ):
        self.bucket_size = bucket_size
        self.window_size = window_size
        self.decay_factor = decay_factor
        
        # State
        self.buckets: deque = deque(maxlen=window_size * 2)  # Keep extra for analysis
        self.current_bucket = VolumeBucket(
            timestamp=time.time(),
            buy_volume=0,
            sell_volume=0
        )
        self.cumulative_volume = 0
        
        # Metrics
        self.last_vpin = 0.0
        self.vpin_history: deque = deque(maxlen=1000)
        
        logger.info(f"   [VPIN] Engine initialized (bucket={bucket_size}, window={window_size})")
    
    def process_trade(self, trade: Trade) -> Optional[VPINResult]:
        """
        Process incoming trade and update VPIN.
        Returns VPINResult if bucket completed, None otherwise.
        """
        # Update current bucket
        if trade.side.lower() in ['buy', 'b', '1']:
            self.current_bucket.buy_volume += trade.volume
        else:
            self.current_bucket.sell_volume += trade.volume
        
        self.cumulative_volume += trade.volume
        
        # Check if bucket is full
        if self.cumulative_volume >= self.bucket_size:
            # Finalize and store bucket
            self.current_bucket.timestamp = trade.timestamp
            self.buckets.append(self.current_bucket)
            
            # Start new bucket
            self.current_bucket = VolumeBucket(
                timestamp=trade.timestamp,
                buy_volume=0,
                sell_volume=0
            )
            self.cumulative_volume = 0
            
            # Calculate VPIN if enough buckets
            if len(self.buckets) >= self.window_size:
                return self.calculate_vpin()
        
        return None
    
    def calculate_vpin(self) -> VPINResult:
        """
        Calculate VPIN over the last N buckets.
        VPIN = Average(|V_buy - V_sell| / (V_buy + V_sell)) over N volume buckets
        """
        recent_buckets = list(self.buckets)[-self.window_size:]
        
        if not recent_buckets:
            return VPINResult(
                vpin=0.0,
                risk_level="LOW",
                action=RISK_ACTIONS["LOW"],
                bucket_count=0,
                timestamp=time.time()
            )
        
        # Calculate VPIN with exponential decay
        weighted_sum = 0.0
        weight_total = 0.0
        
        for i, bucket in enumerate(recent_buckets):
            # Newer buckets get higher weight
            weight = self.decay_factor ** (len(recent_buckets) - 1 - i)
            weighted_sum += bucket.imbalance * weight
            weight_total += weight
        
        vpin = weighted_sum / weight_total if weight_total > 0 else 0
        
        # Determine risk level
        risk_level = self._classify_risk(vpin)
        action = RISK_ACTIONS[risk_level]
        
        # Log if significant
        if vpin > VPIN_THRESHOLDS["MODERATE"]:
            logger.warning(f"   [VPIN ALERT] Toxicity detected: {vpin:.3f} ({risk_level})")
        
        result = VPINResult(
            vpin=vpin,
            risk_level=risk_level,
            action=action,
            bucket_count=len(recent_buckets),
            timestamp=time.time()
        )
        
        # Store result
        self.last_vpin = vpin
        self.vpin_history.append(result)
        
        return result
    
    def _classify_risk(self, vpin: float) -> str:
        """Classify VPIN into risk levels"""
        if vpin >= VPIN_THRESHOLDS["CRITICAL"]:
            return "CRITICAL"
        elif vpin >= VPIN_THRESHOLDS["HIGH"]:
            return "HIGH"
        elif vpin >= VPIN_THRESHOLDS["MODERATE"]:
            return "MODERATE"
        else:
            return "LOW"
    
    def get_current_state(self) -> Dict:
        """Get current VPIN state for monitoring"""
        return {
            "vpin": self.last_vpin,
            "risk_level": self._classify_risk(self.last_vpin),
            "bucket_count": len(self.buckets),
            "pending_volume": self.cumulative_volume,
            "bucket_size": self.bucket_size,
            "window_size": self.window_size
        }
    
    def get_statistics(self) -> Dict:
        """Get VPIN statistics over history"""
        if not self.vpin_history:
            return {"error": "No history available"}
        
        vpins = [r.vpin for r in self.vpin_history]
        
        return {
            "current": self.last_vpin,
            "mean": np.mean(vpins),
            "std": np.std(vpins),
            "max": np.max(vpins),
            "min": np.min(vpins),
            "samples": len(vpins),
            "high_toxicity_pct": sum(1 for v in vpins if v > VPIN_THRESHOLDS["HIGH"]) / len(vpins) * 100
        }

# ============================================================================
# BINARY PACKET ENCODER (For Low-Latency Transmission)
# ============================================================================

def encode_vpin_packet(result: VPINResult, symbol_hash: int, obi: float, price: float) -> bytes:
    """
    Encode VPIN result into 32-byte binary packet for low-latency transmission.
    
    Packet Structure:
    [0-7]   timestamp (uint64)
    [8-15]  symbol_hash (uint64)
    [16-19] vpin (float32)
    [20-23] obi (float32)
    [24-27] price (float32)
    [28-31] flags (uint32) - risk level encoded
    """
    import struct
    
    # Encode risk level as flags
    risk_flags = {
        "LOW": 0,
        "MODERATE": 1,
        "HIGH": 2,
        "CRITICAL": 3
    }
    flags = risk_flags.get(result.risk_level, 0)
    
    packet = struct.pack(
        '<QQfffI',  # Little endian: uint64, uint64, float32, float32, float32, uint32
        int(result.timestamp * 1000),  # Milliseconds
        symbol_hash,
        result.vpin,
        obi,
        price,
        flags
    )
    
    return packet

def decode_vpin_packet(packet: bytes) -> Dict:
    """Decode 32-byte binary packet"""
    import struct
    
    timestamp_ms, symbol_hash, vpin, obi, price, flags = struct.unpack('<QQfffI', packet)
    
    risk_levels = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    
    return {
        "timestamp": timestamp_ms / 1000,
        "symbol_hash": symbol_hash,
        "vpin": vpin,
        "obi": obi,
        "price": price,
        "risk_level": risk_levels[min(flags, 3)]
    }

# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

vpin_engine = VPINEngine()

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import random
    
    print("=" * 60)
    print("VPIN ENGINE TEST")
    print("=" * 60)
    
    engine = VPINEngine(bucket_size=10, window_size=10)
    
    # Simulate trades
    for i in range(200):
        # Create realistic trade patterns
        if i < 100:
            # Normal market: balanced flow
            side = random.choice(['buy', 'sell'])
        else:
            # Toxic flow: informed selling
            side = 'sell' if random.random() < 0.8 else 'buy'
        
        trade = Trade(
            timestamp=time.time() + i * 0.1,
            side=side,
            volume=random.uniform(1, 5),
            price=100 + random.uniform(-1, 1)
        )
        
        result = engine.process_trade(trade)
        
        if result and i % 20 == 0:
            print(f"Trade {i}: VPIN={result.vpin:.3f}, Risk={result.risk_level}, Action={result.action}")
    
    print("\n" + "=" * 60)
    print("STATISTICS:")
    print(engine.get_statistics())
    
    # Test binary encoding
    print("\n" + "=" * 60)
    print("BINARY PACKET TEST:")
    result = VPINResult(vpin=0.65, risk_level="HIGH", action="HALT", bucket_count=50, timestamp=time.time())
    packet = encode_vpin_packet(result, 12345, 0.55, 42000.0)
    print(f"Packet size: {len(packet)} bytes")
    decoded = decode_vpin_packet(packet)
    print(f"Decoded: {decoded}")
