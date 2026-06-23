from tavily import TavilyClient
import os
import requests
from dotenv import load_dotenv
from tools.network import disable_local_proxy

load_dotenv()
disable_local_proxy()


# https://www.tavily.com/ 
# Signup and login, On dashboard- > under api keys you will see the default key.
# Use that or click on + to create new one. Then save it in .env file

client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)

# test it
#################################
# response = client.search(
    # query="Best hotels in Dubai"
# )

# print(response)

####################################



def tavily_search(query):
    if not os.getenv("TAVILY_API_KEY"):
        return "Hotel search is not configured. Add TAVILY_API_KEY to your .env file."

    try:
        client.session.trust_env = False
        response = client.search(
            query=query,
            max_results=5
        )
    except requests.RequestException as exc:
        return f"Hotel search is temporarily unavailable: {exc}"
    except Exception as exc:
        return f"Hotel search error: {exc}"

    results = []

    for i, r in enumerate(response.get("results", []), 1):
        title   = r.get("title", "Unknown")
        url     = r.get("url", "")
        snippet = r.get("content", "").strip()
        # Keep only the first 300 characters to avoid wall-of-text
        if len(snippet) > 300:
            snippet = snippet[:300].rsplit(" ", 1)[0] + "..."

        results.append(f"{i}. **{title}**\n   {url}\n   {snippet}")

    return "\n\n".join(results) or "No hotel data returned."
    
    
    
