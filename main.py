from dotenv import load_dotenv
load_dotenv()

from fastmcp import FastMCP

mcp = FastMCP(
    name="Acting Talent Agency",
    instructions="""
        This server will make a call to the Freelance API to find gigs for actors. 
        The client will provide details about details of the gigs they are looking for.
        Make sure the response is concise and only includes relevant information.
    """,
)

from gigs import register_tools   # <-- import the registrar, not mcp
register_tools(mcp)               # <-- attach tools to the EXACT mcp being exported

if __name__ == "__main__":
    mcp.run()