# NEXUS AI - Python Code Quality Standards

## Logging Standards

### Use Logging, Not Print

**❌ BAD:**
```python
print("Starting worker...")
print(f"Error: {e}")
```

**✅ GOOD:**
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Starting worker...")
logger.error(f"Error occurred: {e}", exc_info=True)
```

### Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| `DEBUG` | Detailed diagnostic info | `logger.debug(f"Variable x = {x}")` |
| `INFO` | General informational messages | `logger.info("Worker started successfully")` |
| `WARNING` | Warning messages | `logger.warning("Low balance detected")` |
| `ERROR` | Error messages | `logger.error("Failed to connect to API")` |
| `CRITICAL` | Critical failures | `logger.critical("System shutdown imminent")` |

### Structured Logging Format

```python
# Use consistent prefixes for easier log filtering
logger.info(f"[COSMOS WORKER] Starting market scan...")
logger.info(f"[AI ORACLE] Generated prediction for {symbol}")
logger.error(f"[BINANCE] API rate limit exceeded")
```

---

## Error Handling

### Always Use Try-Except for External APIs

**❌ BAD:**
```python
response = requests.get(url)
data = response.json()
```

**✅ GOOD:**
```python
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
except requests.RequestException as e:
    logger.error(f"API request failed: {e}", exc_info=True)
    return None
```

### Provide Fallback Values

```python
try:
    price = float(api_response['price'])
except (KeyError, ValueError, TypeError):
    logger.warning(f"Invalid price data, using fallback")
    price = 0.0
```

### Log Full Stack Trace for Critical Errors

```python
except Exception as e:
    logger.error(f"Unexpected error in {function_name}", exc_info=True)
    # exc_info=True includes full stack trace
```

---

## Import Organization

### Standard Import Order

```python
# 1. Standard library
import os
import sys
import json
from datetime import datetime

# 2. Third-party packages
import numpy as np
import pandas as pd
from fastapi import FastAPI

# 3. Local application imports
from cosmos_engine import CosmosEngine
from db import insert_signal
```

### Avoid Wildcard Imports

**❌ BAD:**
```python
from cosmos_engine import *
```

**✅ GOOD:**
```python
from cosmos_engine import CosmosEngine, calculate_metrics
```

---

## Type Hints (Recommended)

```python
from typing import Dict, List, Optional

def analyze_market(
    symbol: str,
    timeframe: str = "1h"
) -> Optional[Dict[str, float]]:
    """
    Analyze market data for a given symbol.
    
    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        timeframe: Chart timeframe
        
    Returns:
        Dict with analysis results, or None if failed
    """
    try:
        # Implementation
        return {"confidence": 0.85, "direction": 1}
    except Exception as e:
        logger.error(f"Market analysis failed: {e}")
        return None
```

---

## Configuration Management

### Use Environment Variables

**❌ BAD:**
```python
API_KEY = "sk-1234567890"  # Hardcoded secret
```

**✅ GOOD:**
```python
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    logger.error("OPENAI_API_KEY not configured")
    raise EnvironmentError("Missing required API key")
```

---

## Database Operations

### Use Context Managers for Connections

```python
# For connection pooling
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = create_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# Usage
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute(query)
```

### Validate Data Before Insertion

```python
def save_signal(signal_data: Dict) -> bool:
    """Validate and save signal to database."""
    required_fields = ['symbol', 'direction', 'confidence']
    
    # Validation
    for field in required_fields:
        if field not in signal_data:
            logger.error(f"Missing required field: {field}")
            return False
    
    # Save
    try:
        supabase.table('signals').insert(signal_data).execute()
        logger.info(f"Signal saved for {signal_data['symbol']}")
        return True
    except Exception as e:
        logger.error(f"Database insert failed: {e}", exc_info=True)
        return False
```

---

## Async/Await Best Practices

### Use Async for I/O Bound Operations

```python
import asyncio

async def fetch_market_data(symbols: List[str]) -> List[Dict]:
    """Fetch data concurrently for multiple symbols."""
    tasks = [fetch_single_symbol(symbol) for symbol in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]

async def fetch_single_symbol(symbol: str) -> Dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.example.com/{symbol}") as resp:
            return await resp.json()
```

---

## Performance Optimization

### Cache Expensive Operations

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_token_metadata(address: str) -> Dict:
    """Cached token metadata lookup."""
    # Expensive API call
    return fetch_from_api(address)
```

### Use Connection Pooling

```python
# For Supabase
supabase_client = create_client(
    SUPABASE_URL, 
    SUPABASE_KEY,
    options=ClientOptions(
        postgrest_client_timeout=10,
        storage_client_timeout=10
    )
)
```

---

## Testing

### Write Unit Tests

```python
import unittest

class TestSignalGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = SignalGenerator()
    
    def test_confidence_calculation(self):
        data = {"price": 100, "volume": 1000}
        confidence = self.generator.calculate_confidence(data)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_invalid_data_handling(self):
        with self.assertRaises(ValueError):
            self.generator.calculate_confidence({})
```

---

## Security

### Sanitize User Input

```python
import re

def validate_symbol(symbol: str) -> bool:
    """Ensure symbol contains only valid characters."""
    pattern = r'^[A-Z]{2,10}USDT?$'
    return bool(re.match(pattern, symbol))

# Usage
if not validate_symbol(user_input):
    logger.warning(f"Invalid symbol format: {user_input}")
    return {"error": "Invalid symbol"}
```

### Rate Limiting

```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def allow_request(self) -> bool:
        now = time.time()
        
        # Remove old requests
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False
```

---

## Documentation

### Docstrings for Public Functions

```python
def generate_signal(
    symbol: str,
    market_data: Dict,
    ai_analysis: Dict
) -> Optional[Dict]:
    """
    Generate trading signal combining market and AI data.
    
    This function integrates technical analysis with AI predictions
    to produce high-confidence trading signals. It validates all
    inputs and applies risk management filters.
    
    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        market_data: Dictionary with OHLCV data
        ai_analysis: AI model predictions
    
    Returns:
        Signal dictionary with fields:
            - symbol: str
            - direction: int (1 for LONG, -1 for SHORT)
            - confidence: float (0.0 to 1.0)
            - entry_price: float
            - stop_loss: float
            - take_profit: float
        
        Returns None if signal generation fails.
    
    Raises:
        ValueError: If input data is invalid
        
    Example:
        >>> signal = generate_signal(
        ...     "BTCUSDT",
        ...     {"close": 50000, "volume": 1000},
        ...     {"prediction": 0.75}
        ... )
        >>> signal['direction']
        1
    """
    # Implementation
    pass
```

---

## File Structure

```
data-engine/
├── core/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── logger.py          # Logging setup
│   └── exceptions.py      # Custom exceptions
├── workers/
│   ├── cosmos_worker.py   # Signal generation
│   ├── ai_oracle.py       # AI predictions
│   └── macro_feed.py      # Macro analysis
├── engines/
│   ├── binance_engine.py  # Exchange integration
│   ├── redis_engine.py    # Cache layer
│   └── cosmos_engine.py   # Core logic
├── utils/
│   ├── validators.py      # Input validation
│   ├── helpers.py         # Utility functions
│   └── constants.py       # Constants
└── tests/
    ├── test_workers.py
    └── test_engines.py
```

---

## Quick Checklist

Before committing code, ensure:

- [ ] No `print()` statements (use `logger` instead)
- [ ] All API calls have try-except blocks
- [ ] Sensitive data uses environment variables
- [ ] Functions have type hints and docstrings
- [ ] Imports are organized (stdlib → 3rd party → local)
- [ ] Log messages use consistent prefixes
- [ ] No hardcoded secrets or API keys
- [ ] Critical errors log full stack traces (`exc_info=True`)
