from rosen.gcomm import GCOMM

import asyncio
async def handle_client(reader, writer):
    while True:
        try:
            data = await reader.readexactly(GCOMM.size)
            remote_addr = writer.get_extra_info('peername')
            g = GCOMM.parse(data)
            print(f"Received from {remote_addr}:\n    {g}")
        except EOFError:
            break
        except ConnectionResetError:
            print("Client disconnected in middle of message")
            break
        # respond with OK
        writer.write(GCOMM('ok').build())
        await writer.drain()
        # artificially slow the server down a bit
        await asyncio.sleep(0.3)

    print(f"Shutting down server")

async def run_server(host, port):
    server = await asyncio.start_server(handle_client, host, port)
    print(f"Serving on {host} {port}")
    async with server:
        await server.serve_forever()

def server(args):
    """Run a test server which simply responds OK to all valid packets"""
    # asyncio.run(run_server(args.host, args.port))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_server(args.host, args.port))
