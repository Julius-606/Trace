
#>>>--- START_FILE_BLOCK: backend/test_neon_db.py
################################################################################
# FILE: backend/test_neon_db.py
# VERSION: 1.0.0 | SYSTEM: Neon DB Snitch / Diagnostic EA
################################################################################
#
# PURPOSE: 
# Bypasses the main app to interrogate the Neon Postgres Database directly.
# Detects cold-starts, invalid passwords, SSL tantrums, and connection drops.

import asyncio
import asyncpg
import os
import time
from urllib.parse import urlparse, unquote

async def run_snitch():
    print("==================================================")
    print(" 🕵️‍♂️ NEON DB SNITCH v1.0 (INITIALIZING PROBE) ")
    print("==================================================")

    # 1. Fetch the raw liquidity (Environment Variable)
    raw_url = os.getenv("TRACE_DATABASE_URL")
    
    if not raw_url:
        print("❌ FATAL: TRACE_DATABASE_URL is completely missing! Mr. Hugging Face's vault is empty.")
        return

    # Hide the password so we don't leak it on the public blockchain (logs)
    parsed = urlparse(raw_url)
    safe_url = raw_url.replace(parsed.password, "********") if parsed.password else raw_url
    print(f"🔍 RAW URL DETECTED: {safe_url}")

    # 2. Apply the Anti-Slippage Fixes exactly like config.py
    # Remove SQLAlchemy's '+asyncpg' because pure asyncpg hates it
    clean_url = raw_url.replace("postgresql+asyncpg://", "postgresql://")
    
    # Strip Neon's weird parameters
    if "?" in clean_url:
        clean_url = clean_url.split("?")[0]
        
    # Force pure SSL
    clean_url += "?ssl=require"

    clean_parsed = urlparse(clean_url)
    safe_clean_url = clean_url.replace(clean_parsed.password, "********") if clean_parsed.password else clean_url
    print(f"🛠️ CLEANED URL (Executing Trade): {safe_clean_url}")
    print("--------------------------------------------------")

    # 3. Execution Phase: Attempt Connection & Time the Cold Start
    print("⏳ Sending Ping to Neon Postgres... Waiting for DB to put its boots on...")
    start_time = time.time()

    try:
        # We establish a raw connection, zero intermediaries.
        conn = await asyncpg.connect(clean_url, timeout=15.0)
        
        latency = round((time.time() - start_time) * 1000, 2)
        print(f"✅ CONNECTION SECURED! (Latency: {latency} ms)")
        
        if latency > 2000:
            print("⚠️ WARNING: High latency detected! Neon was definitely sleeping. That's a cold start.")
        else:
            print("⚡ DB is wide awake and routing fast!")

        # 4. Take Profit: Run a test query
        version = await conn.fetchval('SELECT version();')
        print(f"📊 NEON POSTGRES VERSION: {version[:50]}...")
        
        await conn.close()
        print("==================================================")
        print(" 🟢 ALL SYSTEMS GO. THE VAULT IS OPEN. ")
        print("==================================================")

    except asyncpg.exceptions.InvalidAuthorizationSpecificationError:
        print("❌ ERROR: Invalid Password or Username! Neon rejected your credentials. Check your Hugging Face secrets.")
    except asyncpg.exceptions.InvalidCatalogNameError:
        print(f"❌ ERROR: Database name '{clean_parsed.path[1:]}' does not exist on this Neon server!")
    except asyncio.TimeoutError:
        print("❌ ERROR: Connection Timed Out! Neon took too long to wake up, or Safaricom dropped the packet somewhere over Thika.")
    except Exception as e:
        print(f"❌ UNKNOWN SLIPPAGE DETECTED: {str(e)}")
        print("   -> Tip: Check if the error mentions 'ssl' or 'channel_binding'.")
    finally:
        print("\n[Snitch execution finished]")

if __name__ == "__main__":
    asyncio.run(run_snitch())

#<<<--- END_FILE_BLOCK: backend/test_neon_db.py

