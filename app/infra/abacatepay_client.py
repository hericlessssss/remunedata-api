"""
app/infra/abacatepay_client.py
Cliente HTTP assíncrono para a API AbacatePay v1.
Documentação: https://docs.abacatepay.com
"""

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class AbacatePayClient:
    """
    Encapsula as chamadas à API AbacatePay v1.
    Autenticação: Bearer Token no header Authorization.
    """

    def __init__(self):
        self._base_url = settings.abacatepay_base_url
        self._headers = {
            "Authorization": f"Bearer {settings.abacatepay_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _post(self, path: str, payload: dict) -> dict[str, Any]:
        """Executa um POST autenticado e retorna o campo 'data' da resposta."""
        url = f"{self._base_url}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=self._headers)
            response.raise_for_status()
            body = response.json()
            if body.get("error"):
                raise ValueError(f"AbacatePay error: {body['error']}")
            return body.get("data", body)

    async def _get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        """Executa um GET autenticado e retorna o campo 'data' da resposta."""
        url = f"{self._base_url}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params, headers=self._headers)
            response.raise_for_status()
            body = response.json()
            if body.get("error"):
                raise ValueError(f"AbacatePay error: {body['error']}")
            return body.get("data", body)

    async def create_customer(
        self,
        name: str,
        email: str,
        cellphone: str,
        tax_id: str,
    ) -> dict[str, Any]:
        """
        Cria ou recupera um cliente na AbacatePay.
        POST /v1/customer/create
        """
        payload = {
            "name": name,
            "email": email,
            "cellphone": cellphone,
            "taxId": tax_id,
        }
        return await self._post("/customer/create", payload)

    async def create_billing(
        self,
        customer_id: str,
        plan_slug: str,
        plan_name: str,
        plan_description: str,
        price_cents: int,
        external_id: str,
    ) -> dict[str, Any]:
        """
        Cria uma cobrança (ONE_TIME) via PIX + Cartão.
        POST /v1/billing/create
        Retorna: { id, url, status, ... }
        """
        payload = {
            "frequency": "ONE_TIME",
            "methods": ["PIX", "CREDIT_CARD"],
            "products": [
                {
                    "externalId": external_id,
                    "name": plan_name,
                    "description": plan_description,
                    "quantity": 1,
                    "price": price_cents,
                }
            ],
            "returnUrl": f"{settings.front_url}/planos",
            "completionUrl": f"{settings.front_url}/assinatura/sucesso?billing={external_id}",
            "customerId": customer_id,
        }
        return await self._post("/billing/create", payload)

    async def get_billing(self, billing_id: str) -> dict[str, Any]:
        """
        Busca uma cobrança pelo ID.
        GET /v1/billing/get?id=...
        """
        return await self._get("/billing/get", params={"id": billing_id})


# Instância global compartilhada
abacatepay_client = AbacatePayClient()
