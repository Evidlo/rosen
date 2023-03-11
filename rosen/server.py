import asyncio
import asyncio_dgram

from rosen.gcomm import GCOMM

async def udp_echo_server(host, port):
    """Dumb echo server"""

    stream = await asyncio_dgram.bind((host, port))

    print(f"Serving on {stream.sockname}")

    while True:
        data, (remote_addr, remote_port) = await stream.recv()
        g = GCOMM.parse(data)
        print(f"Received from {remote_addr}:\n    {g}")
        # reponse with ack before echoing
        await stream.send(
            GCOMM('ok').build(),
            (remote_addr, remote_port)
        )
        await stream.send(data, (remote_addr, remote_port))
        # slow the server down a bit
        await asyncio.sleep(0.3)

    print(f"Shutting down server")


def server(args):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(udp_echo_server(args.host, args.port)))
