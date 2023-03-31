import socket

from rosen.gcomm import GCOMM

async def handle_client(reader, writer):
    while True:
        data = await reader.readexactly(1024)
        remote_addr = writer.get_extra_info('peername')
        g = GCOMM.parse(data)
        print(f"Received from {remote_addr}:\n    {g}")
        # reponse with ack before echoing
        writer.write(GCOMM('ok').build())
        writer.write(data)
        await writer.drain()
        # slow the server down a bit
        await asyncio.sleep(0.3)

    print(f"Shutting down server")

async def run_server(host, port):
    server = await asyncio.start_server(handle_client, host, port)
    print(f"Serving on {host} {port}")
    async with server:
        await server.serve_forever()

def server(args):
    asyncio.run(run_server(args.host, args.port))
