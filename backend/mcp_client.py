from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client
import asyncio
import json
from datetime import datetime
import os

LOGS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs"
)

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

if __name__ == "__main__":
    asyncio.run(log_application(
        jd="We are seeking a Senior Android Developer with over 5 years of experience to build high-performance mobile applications using Kotlin and Jetpack Compose. You will architect robust client-side frameworks and integrate advanced artificial intelligence capabilities, including on-device machine learning models and cloud-based LLM APIs. In this role, you will also leverage AI-assisted development workflows to accelerate feature delivery while ensuring optimal application performance.",
        assessment="""
        {
  "match_score": 62,
  "strengths": [
    "9 years of Android experience — well beyond the 5-year requirement",
    "Proficient in Kotlin and Jetpack Compose with hands-on production usage",
    "Strong client-side architecture chops — MVVM, system design, project architecture ownership at Zivame and Ajio",
    "Proven at scale — managed apps with 1Cr+ users",
    "Solid app performance optimization experience — memory usage, overdraw resolution, crash analysis",
    "Extensive third-party API and cloud service integration (Firebase, AWS, Retrofit, PayU, Juspay, etc.)"
  ],
  "gaps": [
    "Zero evidence of on-device ML model integration — no TensorFlow Lite, ML Kit, or any equivalent mentioned anywhere",
    "No cloud-based LLM API integration — no GPT, Gemini, OpenAI, or any generative AI API work found",
    "No AI-assisted development workflow experience mentioned — no GitHub Copilot, Gemini Code Assist, or similar tools referenced",
    "No mention of any AI or ML capabilities whatsoever — this is a significant and repeated gap for a role where AI integration is a core responsibility"
  ],
  "tailored_bullets": [
    "9+ years of Android development with deep expertise in Kotlin and Jetpack Compose for production apps",
    "Architected client-side frameworks and led system design at Zivame, driving proposals for new features and underlying technology stack",
    "Optimized app performance across memory usage and overdraw resolution for apps serving 1Cr+ users",
    "Integrated multiple cloud services including Firebase Crashlytics, Performance Monitoring, Remote Config, Realtime Database, and Firestore",
    "Led tech stack migrations, SDK upgrades, and library architecture transitions in large-scale Android projects",
    "Managed full feature delivery lifecycle: requirement analysis, UI/UX implementation, API integration, testing, and documentation"
  ],
  "verdict": "Moderate fit at best. Jimmy is a solid, experienced Android engineer — no question there. But this JD is explicitly AI-heavy: on-device ML, LLM API integration, and AI-assisted workflows are core expectations, not bonuses. His resume shows zero AI or ML exposure. If the team needs someone to hit the ground running on AI feature integration, Jimmy isn't that person right now. Could work if the org is willing to ramp him up on the AI side, but don't hire him expecting AI expertise on day one."
}"""
    ))