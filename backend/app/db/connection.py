import httpx
from typing import Optional, Any
from functools import lru_cache

from app.config.settings import get_settings
from app.config.logging import get_logger

logger = get_logger("db.connection")


class SupabaseClient:
    def __init__(self, url: str, key: str):
        self.url = url.rstrip("/")
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        self._client: Optional[httpx.AsyncClient] = None
    
    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.url,
                headers=self.headers,
                timeout=30.0
            )
        return self._client
    
    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def auth_sign_up(self, email: str, password: str, data: dict = None) -> dict:
        client = await self.get_client()
        payload = {"email": email, "password": password}
        if data:
            payload["data"] = data
        response = await client.post("/auth/v1/signup", json=payload)
        if response.status_code >= 400:
            error_data = response.json()
            error_msg = error_data.get("error_description") or error_data.get("msg") or error_data.get("message") or str(error_data)
            raise ValueError(f"Supabase signup error: {error_msg}")
        return response.json()
    
    async def auth_sign_in(self, email: str, password: str) -> dict:
        client = await self.get_client()
        response = await client.post(
            "/auth/v1/token",
            params={"grant_type": "password"},
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        return response.json()
    
    async def auth_sign_out(self, access_token: str) -> None:
        client = await self.get_client()
        headers = {**self.headers, "Authorization": f"Bearer {access_token}"}
        await client.post("/auth/v1/logout", headers=headers)
    
    async def auth_get_user(self, access_token: str) -> dict:
        client = await self.get_client()
        headers = {**self.headers, "Authorization": f"Bearer {access_token}"}
        response = await client.get("/auth/v1/user", headers=headers)
        response.raise_for_status()
        return response.json()
    
    async def auth_refresh_token(self, refresh_token: str) -> dict:
        client = await self.get_client()
        response = await client.post(
            "/auth/v1/token",
            params={"grant_type": "refresh_token"},
            json={"refresh_token": refresh_token}
        )
        response.raise_for_status()
        return response.json()
    
    async def auth_reset_password(self, email: str, redirect_to: str = None) -> None:
        client = await self.get_client()
        payload = {"email": email}
        if redirect_to:
            payload["redirect_to"] = redirect_to
        await client.post("/auth/v1/recover", json=payload)
    
    async def auth_update_user(self, access_token: str, data: dict) -> dict:
        client = await self.get_client()
        headers = {**self.headers, "Authorization": f"Bearer {access_token}"}
        response = await client.put("/auth/v1/user", headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def get_oauth_url(self, provider: str, redirect_to: str, scopes: str = None) -> str:
        url = f"{self.url}/auth/v1/authorize?provider={provider}&redirect_to={redirect_to}"
        if scopes:
            url += f"&scopes={scopes}"
        return url
    
    async def auth_exchange_code(self, code: str) -> dict:
        client = await self.get_client()
        response = await client.post(
            "/auth/v1/token",
            params={"grant_type": "authorization_code"},
            json={"auth_code": code}
        )
        response.raise_for_status()
        return response.json()
    
    async def table(self, table_name: str) -> "TableQuery":
        return TableQuery(self, table_name)


class TableQuery:
    def __init__(self, client: SupabaseClient, table_name: str):
        self.client = client
        self.table_name = table_name
        self._select = "*"
        self._filters: list[tuple[str, str, Any]] = []
        self._limit: Optional[int] = None
        self._order: Optional[tuple[str, bool]] = None
    
    def select(self, columns: str = "*") -> "TableQuery":
        self._select = columns
        return self
    
    def eq(self, column: str, value: Any) -> "TableQuery":
        self._filters.append((column, "eq", value))
        return self
    
    def limit(self, count: int) -> "TableQuery":
        self._limit = count
        return self
    
    def order(self, column: str, desc: bool = False) -> "TableQuery":
        self._order = (column, desc)
        return self
    
    async def execute(self) -> dict:
        http_client = await self.client.get_client()
        url = f"/rest/v1/{self.table_name}?select={self._select}"
        
        for col, op, val in self._filters:
            url += f"&{col}={op}.{val}"
        
        if self._limit:
            url += f"&limit={self._limit}"
        
        if self._order:
            col, desc = self._order
            url += f"&order={col}.{'desc' if desc else 'asc'}"
        
        response = await http_client.get(url)
        response.raise_for_status()
        return {"data": response.json()}
    
    async def insert(self, data: dict) -> dict:
        http_client = await self.client.get_client()
        response = await http_client.post(
            f"/rest/v1/{self.table_name}",
            json=data,
            headers={**self.client.headers, "Prefer": "return=representation"}
        )
        response.raise_for_status()
        return {"data": response.json()}


_supabase_client: Optional[SupabaseClient] = None


async def get_async_supabase_client() -> SupabaseClient:
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        _supabase_client = SupabaseClient(
            settings.supabase_url,
            settings.supabase_anon_key
        )
        logger.info("Supabase client initialized")
    return _supabase_client


async def close_async_client() -> None:
    global _supabase_client
    if _supabase_client is not None:
        await _supabase_client.close()
        _supabase_client = None
        logger.info("Supabase client closed")


async def check_db_health() -> dict:
    try:
        client = await get_async_supabase_client()
        http_client = await client.get_client()
        response = await http_client.get("/rest/v1/")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
