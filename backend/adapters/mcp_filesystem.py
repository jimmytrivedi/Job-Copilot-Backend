from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client
import json
from datetime import datetime
from backend.config import PROJECT_ROOT

LOGS_DIR = str(PROJECT_ROOT / "logs")

server_params = StdioServerParameters(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", LOGS_DIR]
)

async def log_application(jd: str, assessment: dict) -> str:
    filename = f"application _{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    content = json.dumps({"jd": jd, "assessment": assessment}, indent=2)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool(
                "write_file",
                arguments={"path": filename, "content": content}
            )
    return filename