import argparse
import asyncio
import json
import logging
import sys

from   apsis.agent.client import Agent

#-------------------------------------------------------------------------------

def sync(coro):
    task = asyncio.ensure_future(coro)
    asyncio.get_event_loop().run_until_complete(task)
    return task.result()


async def clean(agent):
    processes = await agent.get_processes()
    return await asyncio.gather(*(
        agent.del_process(p["proc_id"]) for p in processes ))


def main():
    logging.basicConfig(level="INFO")

    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(title="commands")
    parser.set_defaults(cmd=None)

    cmd = commands.add_parser("start")
    cmd.set_defaults(cmd="start")

    cmd = commands.add_parser("list")
    cmd.set_defaults(cmd="list")

    cmd = commands.add_parser("get")
    cmd.add_argument("proc_id")
    cmd.set_defaults(cmd="get")

    cmd = commands.add_parser("del")
    cmd.add_argument("proc_id")
    cmd.set_defaults(cmd="del")

    cmd = commands.add_parser("shut_down")
    cmd.set_defaults(cmd="shut_down")

    cmd = commands.add_parser("clean")
    cmd.set_defaults(cmd="clean")

    args = parser.parse_args()
    agent = Agent(restart=False)  # FIXME: Who, where?
    sync(agent.start())

    if args.cmd is None:
        raise SystemExit(0)
    elif args.cmd == "start":
        result = agent.start()
    elif args.cmd == "list":
        result = agent.get_processes()
    elif args.cmd == "get":
        result = agent.get_process(args.proc_id)
    elif args.cmd == "del":
        result = agent.del_process(args.proc_id)
    elif args.cmd == "shut_down":
        result = agent.shut_down()
    elif args.cmd == "clean":
        result = clean(agent)

    try:
        result = sync(result)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
    else:
        json.dump(result, sys.stdout, indent=2)
        print()


if __name__ == "__main__":
    main()

