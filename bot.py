import sys
import asyncio, base64, json, os, pytz
from datetime import datetime
from aiohttp import ClientResponseError, ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector
from colorama import *

wib = pytz.timezone('Asia/Jakarta')

# Browser အလိုက် User-Agent သတ်မှတ်ချက်များ
USER_AGENTS = {
    "chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "edge": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "brave": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "opera": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.0"
}

class OptimaiBot:
    def __init__(self):
        self.BASE_API = "https://api.optimai.network"
        self.access_tokens = {}

    def log(self, message):
        print(f"{Fore.CYAN}[{datetime.now().astimezone(wib).strftime('%X')}]{Style.RESET_ALL} {message}")

    def decode_response_data(self, data):
        try:
            decoded = base64.b64decode(data).decode('utf-8')
            filtered = ''.join([char for i, char in enumerate(decoded) if (i + 1) % 5 != 0])
            reversed_str = filtered[::-1]
            a = 7
            result = ''.join(chr(int(reversed_str[i:i+2], 16) ^ (a + i//2)) for i in range(0, len(reversed_str), 2))
            return json.loads(result)
        except: return None

    async def get_access_token(self, refresh_token, browser_type):
        url = f"{self.BASE_API}/auth/refresh"
        headers = {"Content-Type": "application/json", "User-Agent": USER_AGENTS.get(browser_type, USER_AGENTS['chrome'])}
        async with ClientSession() as session:
            try:
                async with session.post(url, json={"refresh_token": refresh_token}, headers=headers) as resp:
                    data = await resp.json()
                    return data.get("access_token")
            except Exception as e:
                self.log(f"{Fore.RED}Token Error ({browser_type}): {e}")
                return None

    async def run_node(self, account_data):
        token = account_data["refreshToken"]
        b_type = account_data["browser_type"]
        reg_payload = account_data["registerPayload"]
        upt_payload = account_data["uptimePayload"]

        self.log(f"{Fore.YELLOW}Starting Node for {b_type.upper()}...{Style.RESET_ALL}")
        
        # Initial Token Get
        self.access_tokens[b_type] = await self.get_access_token(token, b_type)
        
        while True:
            try:
                headers = {
                    "Authorization": f"Bearer {self.access_tokens[b_type]}",
                    "Content-Type": "application/json",
                    "User-Agent": USER_AGENTS.get(b_type)
                }

                # Online Ping (Update Uptime)
                async with ClientSession() as session:
                    async with session.post(f"{self.BASE_API}/uptime/online", json={"data": upt_payload}, headers=headers) as resp:
                        if resp.status == 401: # Token expired
                            self.access_tokens[b_type] = await self.get_access_token(token, b_type)
                            continue
                        
                        res_json = await resp.json()
                        decoded = self.decode_response_data(res_json.get("data", ""))
                        if decoded and "reward" in decoded:
                            self.log(f"{Fore.GREEN}{b_type.upper()}: Ping Success! Reward: {decoded['reward']} OPI")
                        else:
                            self.log(f"{Fore.RED}{b_type.upper()}: Ping Failed")

                await asyncio.sleep(600) # 10 မိနစ်တစ်ခါ ပို့မယ်

            except Exception as e:
                self.log(f"{Fore.RED}{b_type.upper()} Error: {e}")
                await asyncio.sleep(30)

    async def main(self):
        with open("accounts.json", "r") as f:
            accounts = json.load(f)

        tasks = [self.run_node(acc) for acc in accounts]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    bot = OptimaiBot()
    asyncio.run(bot.main())
