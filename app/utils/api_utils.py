"""
This module defines an async API client for making asynchronous HTTP requests.
"""

import aiohttp
from typing import Dict, Any, Optional

class AsyncAPIClient:
    def __init__(self, base_url: str = '', headers: Optional[Dict[str, str]] = None, timeout: int = 10, auth: Optional[aiohttp.BasicAuth] = None):
        """
        Initialize the async API client with a base URL, optional headers, timeout, and authentication.
        :param base_url: The base URL for the API.
        :param headers: Optional default headers to include with each request.
        :param timeout: The default timeout for requests (in seconds).
        :param auth: Optional BasicAuth object for Basic Authentication.
        """
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {}
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.auth = auth

    def _full_url(self, endpoint: str) -> str:
        """
        Construct the full URL from the base URL and endpoint.
        :param endpoint: The API endpoint.
        :return: The full URL.
        """
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _prepare_headers(self, auth_token: Optional[str] = None) -> Dict[str, str]:
        """
        Prepare headers for the API request, including any authentication tokens.
        :param auth_token: Optional Bearer token for authentication.
        :return: The prepared headers.
        """
        headers = self.headers.copy()
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        return headers

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform an async GET request.
        :param endpoint: The API endpoint.
        :param params: Optional query parameters.
        :param auth_token: Optional Bearer token for authentication.
        :return: The response data.
        """
        url = self._full_url(endpoint)
        headers = self._prepare_headers(auth_token)

        async with aiohttp.ClientSession(headers=headers, timeout=self.timeout, auth=self.auth) as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform an async POST request.
        :param endpoint: The API endpoint.
        :param data: Form data to send in the body of the request.
        :param json: JSON data to send in the body of the request.
        :param params: Optional query parameters.
        :param auth_token: Optional Bearer token for authentication.
        :return: The response data.
        """
        url = self._full_url(endpoint)
        headers = self._prepare_headers(auth_token)

        async with aiohttp.ClientSession(headers=headers, timeout=self.timeout, auth=self.auth) as session:
            async with session.post(url, data=data, json=json, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform an async PUT request.
        :param endpoint: The API endpoint.
        :param data: Form data to send in the body of the request.
        :param json: JSON data to send in the body of the request.
        :param params: Optional query parameters.
        :param auth_token: Optional Bearer token for authentication.
        :return: The response data.
        """
        url = self._full_url(endpoint)
        headers = self._prepare_headers(auth_token)

        async with aiohttp.ClientSession(headers=headers, timeout=self.timeout, auth=self.auth) as session:
            async with session.put(url, data=data, json=json, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def patch(self, endpoint: str, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform an async PATCH request.
        :param endpoint: The API endpoint.
        :param data: Form data to send in the body of the request.
        :param json: JSON data to send in the body of the request.
        :param params: Optional query parameters.
        :param auth_token: Optional Bearer token for authentication.
        :return: The response data.
        """
        url = self._full_url(endpoint)
        headers = self._prepare_headers(auth_token)

        async with aiohttp.ClientSession(headers=headers, timeout=self.timeout, auth=self.auth) as session:
            async with session.patch(url, data=data, json=json, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform an async DELETE request.
        :param endpoint: The API endpoint.
        :param params: Optional query parameters.
        :param auth_token: Optional Bearer token for authentication.
        :return: The response data.
        """
        url = self._full_url(endpoint)
        headers = self._prepare_headers(auth_token)

        async with aiohttp.ClientSession(headers=headers, timeout=self.timeout, auth=self.auth) as session:
            async with session.delete(url, params=params) as response:
                response.raise_for_status()
                return await response.json()

    def set_headers(self, headers: Dict[str, str]):
        """
        Set or update headers for the API client.
        :param headers: The headers to set.
        """
        self.headers.update(headers)

    def set_base_url(self, base_url: str):
        """
        Set or update the base URL for the API client.
        :param base_url: The base URL to set.
        """
        self.base_url = base_url.rstrip('/')

if __name__ == "__main__":
    # Example usage of the AsyncAPIClient
    async def main():
        async with AsyncAPIClient() as client:
            response = await client.get("https://jsonplaceholder.typicode.com/posts/1")
            print(response)

    import asyncio
    asyncio.run(main())
