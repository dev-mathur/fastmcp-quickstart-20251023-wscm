"""
FastMCP Acting Talent Agency Server
"""
from fastmcp import FastMCP

# Create server
mcp = FastMCP(
    name="Acting Talent Agency",
    instructions="""
        This server will make a call to the Freelance API to find gigs for actors. 
        The client will provide details about details of the gigs they are looking for.
        Make sure the response is concise and only includes relevant information.
    """,
)

# Try to import gigs and show any errors
try:
    import gigs
    print("✅ gigs module imported successfully")
except Exception as e:
    print(f"❌ Failed to import gigs: {e}")
    import traceback
    traceback.print_exc()

if __name__ == "__main__":
    mcp.run()