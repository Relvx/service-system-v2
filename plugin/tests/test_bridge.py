import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('service_bridge', root / 'scripts/server.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class BridgeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.connection = Path(self.temp.name) / 'connection.json'
        self.token = 'ssr_' + 'x' * 43
        self.connection.write_text(json.dumps({'base_url': 'https://example.test/api', 'token': self.token}))
        env = patch.dict(os.environ, {'SERVICE_SYSTEM_CONNECTION': str(self.connection)})
        env.start()
        self.addCleanup(env.stop)

    async def test_https_and_scoped_key_required(self):
        for base in ['http://example.test/api', 'https://user:pass@example.test/api',
                     'https://example.test/api?next=secret', 'file:///api']:
            self.connection.write_text(json.dumps({'base_url': base, 'token': self.token}))
            with self.assertRaises(ValueError):
                bridge.read_connection()

    async def test_fixed_paths_no_redirects_and_no_secret_in_errors(self):
        actual = httpx.AsyncClient
        calls = []
        def respond(request):
            calls.append(request)
            self.assertEqual(request.headers['authorization'], 'Bearer ' + self.token)
            return httpx.Response(302, headers={'location': 'https://evil.test'}, text=self.token)
        transport = httpx.MockTransport(respond)
        with patch.object(bridge.httpx, 'AsyncClient', side_effect=lambda **kw: actual(transport=transport, **kw)):
            result = await bridge.get_completed_report(5)
        self.assertEqual(str(calls[0].url), 'https://example.test/api/work-reports/5')
        self.assertEqual(len(calls), 1)
        self.assertNotIn(self.token, json.dumps(result))
        self.assertEqual(result['status'], 302)

    async def test_prepare_only_sends_proposal(self):
        actual = httpx.AsyncClient
        calls = []
        def respond(request):
            calls.append(request)
            return httpx.Response(200, json={'proposal_id': 8, 'status': 'pending'})
        with patch.object(bridge.httpx, 'AsyncClient', side_effect=lambda **kw: actual(transport=httpx.MockTransport(respond), **kw)):
            result = await bridge.prepare_defect_proposal(5, 'a' * 64, 'Неисправен насос', 'work_summary', 'Неисправен насос')
        self.assertEqual(result['status'], 'pending')
        self.assertEqual(calls[0].url.path, '/api/work-reports/proposals')
        self.assertEqual(json.loads(calls[0].content)['source_quote'], 'Неисправен насос')

    async def test_real_stdio_protocol_and_tool_permissions(self):
        params = StdioServerParameters(command=sys.executable, args=[str(root / 'scripts/server.py')],
                                        env={'SERVICE_SYSTEM_CONNECTION': str(Path(self.temp.name) / 'missing.json')})
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listing = await session.list_tools()
                tools = {tool.name: tool for tool in listing.tools}
                self.assertEqual(set(tools), {'list_completed_reports', 'get_completed_report', 'prepare_defect_proposal'})
                self.assertTrue(tools['get_completed_report'].annotations.readOnlyHint)
                self.assertFalse(tools['prepare_defect_proposal'].annotations.destructiveHint)
                result = await session.call_tool('get_completed_report', {'visit_id': 5})
                payload = result.structuredContent or json.loads(result.content[0].text)
                self.assertIn('error', payload)
                self.assertNotIn(self.token, str(result))


if __name__ == '__main__':
    unittest.main()
