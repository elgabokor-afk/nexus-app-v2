
import os
import json
from web3 import Web3
from dotenv import load_dotenv

# Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

# Minimal ABI for Uniswap V3 Pool
POOL_ABI = [
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
            {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
            {"internalType": "bool", "name": "unlocked", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

class EVMIndexer:
    def __init__(self, chain="base"):
        # RPC Mapping
        rpcs = {
            "ethereum": "https://eth.llamarpc.com",
            "base": "https://mainnet.base.org"
        }
        self.w3 = Web3(Web3.HTTPProvider(rpcs.get(chain, rpcs['base'])))
        self.chain_name = chain
        
        # Database Initialization
        from supabase import create_client
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None
        
        # Known Pools (Base example: CBETH/WETH 0.01% pool)
        self.base_pools = {
            "CBETH/WETH": "0x12745348864f89d81352d819ed9919f968798efd"
        }

    def test_connection(self):
        """Checks if the RPC is reachable."""
        try:
            return self.w3.is_connected()
        except:
            return False

    def fetch_uniswap_v3_price(self, pool_address, dec0, dec1, is_token1_base=True):
        """
        Calculates price from Uniswap V3 sqrtPriceX96.
        """
        try:
            if not self.test_connection():
                return 0

            target = self.w3.to_checksum_address(pool_address)
            contract = self.w3.eth.contract(address=target, abi=POOL_ABI)
            
            # Diagnostic: check if code exists at address
            code = self.w3.eth.get_code(target)
            if len(code) < 10:
                print(f"   [EVM INDEXER] WARNING: No contract found at {target} on this RPC.")
                return 0

            slot0 = contract.functions.slot0().call()
            sqrt_price_x96 = slot0[0]
            print(f"   [EVM INDEXER] Raw sqrtPriceX96: {sqrt_price_x96}")
            
            # Math: price = (sqrtPriceX96 / 2**96)**2
            price_raw = (sqrt_price_x96 / (2**96)) ** 2
            
            if is_token1_base:
                # We want price of Token1 (ETH) in terms of Token0 (USDC)
                # price_raw is Token1/Token0 (raw)
                # human_price = (Token1/10^dec1) / (Token0/10^dec0) = price_raw * 10^(dec0-dec1)
                # Wait, if price_raw = 3.65e8. And we want 2739.
                # 3.65e8 / 1e12 = 0.000365. 1 / 0.000365 = 2739.
                # So it's 1 / (price_raw * 10^(dec0-dec1))
                human_price = 1 / (price_raw * 10**(dec0 - dec1))
            else:
                # Price of Token0 in term of Token1
                human_price = price_raw * (10**(dec0 - dec1))
            
            return round(human_price, 2)


        except Exception as e:
            print(f"EVM Indexer Error ({pool_address}): {e}")
            return 0

    def log_to_vault(self, symbol, price, liquidity=0):
        """Logs data to the sovereign vault."""
        if not self.supabase: return
        try:
            self.supabase.table("nexus_data_vault").insert({
                "symbol": symbol,
                "price": price,
                "liquidity": liquidity,
                "nli_score": 1.0, # EVM NLI TBD
                "source": f"EVM_{self.chain_name.upper()}_UNISWAP_V3"
            }).execute()
        except Exception as e:
            print(f"Vault Log Error: {e}")

if __name__ == "__main__":
    indexer = EVMIndexer(chain="ethereum")
    print(f"/// N E X U S  E V M  I N D E X E R  (Sovereign V1.0) ///")
    print(f"Connection Status: {'ACTIVE' if indexer.test_connection() else 'FAILED'}")
    
    if indexer.test_connection():
        # Ethereum WETH/USDC 0.05%
        # Token0: USDC (6), Token1: WETH (18)
        price = indexer.fetch_uniswap_v3_price("0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640", 6, 18, True)
        print(f"Uniswap V3 ETH Price: ${price:.2f}")




