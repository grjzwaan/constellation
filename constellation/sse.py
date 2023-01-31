import httpx
from dataclasses import dataclass


@dataclass
class SSEMessage:
    event: str = None
    data: str = None
    id: str = None
    retry: int = None


async def sse_stream(url):  #
    def get_content(s):
        # Get everything _after_ the first colon :
        return s.partition(":")[2].strip()

    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url) as r:
            msg = SSEMessage()
            async for line in r.aiter_lines():
                if line.strip() == "":
                    # End of previous message
                    yield msg
                    msg = SSEMessage()
                elif line.startswith(":"):
                    pass  # Ignore these
                # Process the fields
                elif line.startswith("event:"):
                    msg.event = get_content(line)
                elif line.startswith("data:"):
                    # The protocol specifies that there can be multiple lines, that are concatenated with a newline
                    if msg.data is None:
                        msg.data = get_content(line)
                    else:
                        msg.data = msg.data + "\n" + get_content(line)
                elif line.startswith("id:"):
                    msg.id = get_content(line)
                elif line.startswith("retry:"):
                    msg.retry = int(get_content(line))
                else:
                    pass  # Ignore