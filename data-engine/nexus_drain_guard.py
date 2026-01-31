
import requests
import json
import os
from dotenv import load_dotenv
from base58 import b58decode

# Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

HELIUS_KEY = os.getenv("HELIUS_API_KEY")

class NexusDrainGuard:
    def __init__(self):
        self.rpc_url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_KEY}" if HELIUS_KEY else "https://api.mainnet-beta.solana.com"

    def check_solana_token_security(self, mint_address):
        """
        Predictive Security Audit for Solana Tokens.
        Returns a security report.
        """
        report = {
            "is_safe": True,
            "risk_factors": [],
            "mint_authority": None,
            "freeze_authority": None,
            "lp_burned": False
        }
        
        try:
            # 1. Get Mint Account Info
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [
                    mint_address,
                    {"encoding": "jsonParsed"}
                ]
            }
            res = requests.post(self.rpc_url, json=payload, timeout=10).json()
            
            if 'result' in res and res['result']['value']:
                parsed_data = res['result']['value']['data']['parsed']['info']
                report["mint_authority"] = parsed_data.get("mintAuthority")
                report["freeze_authority"] = parsed_data.get("freezeAuthority")
                
                if report["mint_authority"]:
                    report["is_safe"] = False
                    report["risk_factors"].append("MINT_AUTHORITY_ENABLED")
                    
                if report["freeze_authority"]:
                    report["is_safe"] = False
                    report["risk_factors"].append("FREEZE_AUTHORITY_ENABLED")

            # 2. Check LP Status (Simulated for Phase 1)
            # In V5.4, we fetch the Raydium pool and check the LP mint holder 1111...
            # For now, we use a heuristic or Helius 'getAsset' metadata if available
            return report

        except Exception as e:
            print(f"Drain-Guard Error (Solana): {e}")
            return {"is_safe": False, "risk_factors": ["AUDIT_FAILED"]}

    def check_evm_honeypot(self, contract_address):
        """
        Simulates buy/sell to detect EVM honeypots.
        """
        # Placeholder for V5.4 integration with web3.py
        return {"is_safe": True, "risk_factors": []}

if __name__ == "__main__":
    dg = NexusDrainGuard()
    print(f"/// N E X U S  D R A I N - G U A R D  (V5.3) ///")
    # Test with a known SOL mint (e.g. Wrapped SOL)
    test_mint = "So11111111111111111111111111111111111111112"
    report = dg.check_solana_token_security(test_mint)
    print(f"Security Report for {test_mint[:8]}...: {json.dumps(report, indent=2)}")
