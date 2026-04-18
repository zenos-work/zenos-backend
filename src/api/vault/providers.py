"""Vault providers: Cloudflare first, encrypted D1 fallback."""

import base64
import hashlib


class CloudflareVaultProvider:
    def __init__(self, env):
        self._binding = None
        for key in ("VAULT_STORE", "CLOUDFLARE_VAULT", "VAULT"):
            candidate = getattr(env, key, None)
            if candidate is not None:
                self._binding = candidate
                break

    @property
    def available(self) -> bool:
        return self._binding is not None

    async def store(self, key_ref: str, value: str) -> str:
        if not self._binding:
            raise RuntimeError("Cloudflare vault binding is unavailable")
        if hasattr(self._binding, "put"):
            await self._binding.put(key_ref, value)
            return key_ref
        if hasattr(self._binding, "put_secret"):
            await self._binding.put_secret(key_ref, value)
            return key_ref
        raise RuntimeError("Cloudflare vault binding does not support put/put_secret")

    async def resolve(self, key_ref: str) -> str:
        if not self._binding:
            return ""
        if hasattr(self._binding, "get"):
            return (await self._binding.get(key_ref)) or ""
        if hasattr(self._binding, "get_secret"):
            return (await self._binding.get_secret(key_ref)) or ""
        return ""

    async def delete(self, key_ref: str):
        if not self._binding:
            return
        if hasattr(self._binding, "delete"):
            await self._binding.delete(key_ref)


class D1FallbackVaultProvider:
    """Stores only encrypted payloads (never raw values) in D1 fallback table."""

    def __init__(self, env, repo):
        self._env = env
        self._repo = repo

    def _master_key(self) -> str:
        return getattr(self._env, "VAULT_FALLBACK_KEY", "") or ""

    def _derive_stream(self, secret_id: str) -> bytes:
        seed = f"{self._master_key()}:{secret_id}".encode("utf-8")
        return hashlib.sha256(seed).digest()

    def _xor_crypt(self, secret_id: str, data: bytes) -> bytes:
        key = self._derive_stream(secret_id)
        if not key:
            return b""
        out = bytearray()
        for i, b in enumerate(data):
            out.append(b ^ key[i % len(key)])
        return bytes(out)

    async def store(self, secret_id: str, value: str) -> str:
        master = self._master_key()
        if not master:
            raise RuntimeError("D1 fallback requires VAULT_FALLBACK_KEY")
        cipher = self._xor_crypt(secret_id, value.encode("utf-8"))
        encoded = base64.b64encode(cipher).decode("ascii")
        await self._repo.upsert_fallback_payload(secret_id, encoded)
        return f"d1:{secret_id}"

    async def resolve(self, secret_id: str) -> str:
        payload = await self._repo.get_fallback_payload(secret_id)
        if not payload:
            return ""
        try:
            cipher = base64.b64decode(payload.encode("ascii"))
            plain = self._xor_crypt(secret_id, cipher)
            return plain.decode("utf-8")
        except Exception:
            return ""

    async def delete(self, secret_id: str):
        await self._repo.delete_fallback_payload(secret_id)


class VaultProviderRouter:
    def __init__(self, env, repo):
        self.cloudflare = CloudflareVaultProvider(env)
        self.d1 = D1FallbackVaultProvider(env, repo)

    async def store(
        self,
        *,
        secret_id: str,
        key_ref: str,
        secret_value: str,
        preferred_provider: str = "cloudflare",
    ) -> tuple[str, str]:
        provider = (preferred_provider or "cloudflare").strip().lower()

        if provider == "cloudflare" and self.cloudflare.available:
            ref = await self.cloudflare.store(key_ref, secret_value)
            return "cloudflare", ref

        ref = await self.d1.store(secret_id, secret_value)
        return "d1-db", ref

    async def resolve(self, provider: str, key_ref: str, secret_id: str) -> str:
        if provider == "cloudflare":
            return await self.cloudflare.resolve(key_ref)
        return await self.d1.resolve(secret_id)

    async def delete(self, provider: str, key_ref: str, secret_id: str):
        if provider == "cloudflare":
            await self.cloudflare.delete(key_ref)
            return
        await self.d1.delete(secret_id)
