# Prune invalid peers from routers
import os

from routedbits import RoutedBits

from interactive import load_router_peers, save_router_peers
from validate_config import validate


def add_report_entry(report, router, peer, errors):
    """Add a removed peer to the report"""
    messages = report.get(router, [])
    messages.append({"name": peer["name"], "reasons": errors})

    report[router] = messages
    return report[router]


def print_report(report):
    """Print the contents of the report summary"""
    print("============ PRUNE REPORT ============")

    if len(report):
        for router, peers in report.items():
            print(f"### {router}")
            for peer in peers:
                print(f"- {peer['name']}")
                for reason in peer["reasons"]:
                    print(f"  * {reason}")
            print("")
    else:
        print("No changes.")


def main():
    node_types = {
        node["hostname"]: node["type"]
        for node in RoutedBits().nodes(minimal=True)  # noqa
    }
    report = {}

    for yaml_file in sorted(os.listdir("routers")):
        router = yaml_file[:-4]
        peers = load_router_peers(router)

        print(f"------------ {router} ------------")

        if peers:
            node_type = node_types[router]

            for peer in peers:
                errors = list(validate(node_type, peer))
                is_invalid = bool(len(errors))

                if is_invalid:
                    add_report_entry(report, router, peer, errors)
                    peers.remove(peer)

            save_router_peers(router, peers)

    print_report(report)


if __name__ == "__main__":
    main()
