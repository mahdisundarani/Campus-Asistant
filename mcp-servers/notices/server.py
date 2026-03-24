from fastmcp import FastMCP
import json
import os

# Initialize FastMCP server
mcp = FastMCP("Notices")

# Path to the notices data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOTICES_FILE = os.path.join(BASE_DIR, "../../data/notices/notices.json")

def load_notices():
    if not os.path.exists(NOTICES_FILE):
        return []
    with open(NOTICES_FILE, "r") as f:
        return json.load(f)

@mcp.tool()
def get_latest_notices(department: str = None, limit: int = 5) -> str:
    """
    Fetch the latest campus notices/announcements.
    
    Args:
        department: Optional department filter (e.g. 'CS', 'IT').
        limit: Max number of notices to return.
    """
    notices = load_notices()
    
    if department:
        notices = [n for n in notices if n.get("department") == department or n.get("department") == "General"]
    
    # Sort by date (descending)
    notices.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    return json.dumps(notices[:limit], indent=2)

if __name__ == "__main__":
    mcp.run()
