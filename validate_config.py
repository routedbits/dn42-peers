#!/usr/bin/env python3

import dns.resolver
import github_action_utils as github
import ipaddress
import logging
import os
import re
import yaml

from yaml.loader import SafeLoader
from registry import Registry


class SafeLineLoader(SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = super(SafeLineLoader, self).construct_mapping(node, deep=deep)
        # Add 1 so line numbering starts at 1
        mapping["__line__"] = node.start_mark.line + 1
        return mapping

valid_asns = []

def main():
    errors = []
    file_count = 0

    logging.basicConfig(level=logging.FATAL)

    for yaml_file in sorted(os.listdir("routers")):
        filename = f"routers/{yaml_file}"
        peers = read_yaml(filename)
        file_count += 1

        if peers is not None:
            logging.info(f"Validating peers in: {filename}")

            # collect and ensure peer addrs are unique per router
            peer_ipv4_addrs = [peer["ipv4"] for peer in peers if "ipv4" in peer]
            peer_ipv6_addrs = [peer["ipv6"] for peer in peers if "ipv6" in peer]

            for peer in peers:
                peer_errors = list(validate(peer))

                if not validate_unique_peers(peer_ipv4_addrs):
                    peer_errors.append("ipv4 address must be unique per router")

                if not validate_unique_peers(peer_ipv6_addrs):
                    peer_errors.append("ipv6 address must be unique per router")

                for e in peer_errors:
                    post_annotation(e, filename, peer["__line__"])
                    errors.append(f"{filename}:{peer['__line__']} {e}")

        else:
            logging.debug("No peers found")

    if len(errors):
        for e in errors:
            print(e)
        exit(2)
    else:
        exit(0)


def post_annotation(error, file, line):
    if os.getenv("GITHUB_ACTIONS") == "true" and os.getenv("GITHUB_WORKFLOW"):
        github.error(error, title="Validation Error", file=file, line=line)


def read_yaml(filename):
    with open(filename, "r") as stream:
        try:
            return yaml.load(stream, Loader=SafeLineLoader)
        except yaml.YAMLError as e:
            print(e)
            exit(1)


def validate(peer):
    errors = []

    print(f"Validating peer: {peer.get('name', '<missing>')}...", end="")

    if "name" in peer:
        errors.append(validate_name(peer["name"]))
    else:
        errors.append("name must exist")

    if "asn" in peer:
        errors.append(validate_asn(peer["asn"]))
    else:
        errors.append("asn must exist")

    if "ipv4" in peer:
        errors.append(validate_ip(peer["ipv4"], af="ipv4", attrib="ipv4"))
    elif "ipv6" not in peer:
        errors.append("ipv4 or ipv6 must exist")

    if "local_ipv4" in peer:
        errors.append(validate_ip(peer["local_ipv4"], af="ipv4", attrib="local_ipv4"))

    if "ipv6" in peer:
        errors.append(validate_ip(peer["ipv6"], af="ipv6", attrib="ipv6"))

    if "local_ipv6" in peer:
        errors.append(validate_ip(peer["local_ipv6"], af="ipv6", attrib="local_ipv6"))

    if "multiprotocol" in peer:
        errors.append(validate_boolean(peer["multiprotocol"]))

    if "extended_nexthop" in peer:
        errors.append(validate_boolean(peer["extended_nexthop"]))
        if "ipv6" not in peer:
            errors.append("ipv6 required for extended_nexthop")
        if "ipv6" not in peer["sessions"]:
            errors.append("sessions: [ipv6] required for extended_nexthop")
        if "ipv4" in peer["sessions"]:
            errors.append("sessions: [ipv4] must not exist with extended_nexthop")

    if "sessions" in peer:
        errors += validate_sessions(peer["sessions"], peer)
    else:
        errors.append("sessions must exist")

    if "wireguard" in peer:
        errors += validate_wireguard(peer["wireguard"])
    else:
        errors.append("wireguard must exist")

    if len(list(filter(None, errors))):
        print('\033[91m FAIL \033[0m')
    else:
        print('\033[92m ok \033[0m')

    return filter(None, errors)


def validate_unique_peers(peer_ip_addrs):
    if len(set(peer_ip_addrs)) < len(peer_ip_addrs):
        return False

    return True


def validate_asn(number):
    # Build ASN cache
    global valid_asns
    if not valid_asns:
        valid_asns = Registry().asns()

    if f'AS{number}' not in valid_asns:
        return f"asn: '{number}' must exist in the DN42 registry"

def validate_boolean(attrib):
    if not isinstance(attrib, bool):
        return f"{attrib} is not true or false (boolean)"


def validate_name(name):
    # Validate format: must be all uppercase, start with letter,
    # only '-' and '_' separators allowed
    required_format = "^[A-Z][A-Z0-9-_]+$"
    if not re.match(required_format, name):
        return f"name: '{name}' is not in a valid format, must match {required_format}"


def validate_ip(addr, af, attrib):
    try:
        ip = ipaddress.ip_network(addr, strict=False)
    except ValueError:
        return f"{attrib}: '{addr}' is not a valid IP address or prefix"

    if af == "ipv4":
        if ip.version != 4:
            return f"{attrib}: '{addr}' is not an IPv4 address"
        if not ip.subnet_of(ipaddress.ip_network("172.20.0.0/14")):
            return f"{attrib}: '{addr}' is not within 172.20.0.0/14"

    if af == "ipv6":
        if ip.version != 6:
            return f"{attrib}: '{addr}' is not an IPv6 address"
        if not ip.is_link_local and not ip.subnet_of(ipaddress.ip_network("fc00::/7")):
            return f"{attrib}: '{addr}' is not within fe80::/10 or fc00::/7"


def validate_sessions(sessions, peer):
    errors = []

    if not type(sessions) is list:
        return [f"sessions: '{sessions}' must be a list"]
    if "ipv4" not in sessions and "ipv6" not in sessions:
        return [f"sessions: '{sessions}' must include 'ipv4' and/or 'ipv6'"]

    if "ipv4" in sessions and "ipv4" not in peer:
        errors.append("ipv4 required when sessions['ipv4']")
    if "ipv6" in sessions and "ipv6" not in peer:
        errors.append("ipv6 required when sessions['ipv6']")

    return errors


def validate_wireguard(wg):
    errors = []

    if not type(wg) is dict:
        return f"wireguard: '{wg}' must be type dictionary"

    if "remote_address" in wg.keys():
        if "remote_port" not in wg.keys():
            errors.append("wireguard.remote_port: must exist when remote_address defined")

        try:
            ipaddress.ip_network(wg["remote_address"])
        except ValueError:
            try:
                # if not an IP address; attempt to resolve AAAA record
                dns.resolver.resolve(wg["remote_address"], "AAAA")
            except dns.exception.DNSException:
                try:
                    # if no AAAA record; attempt to resolve A record
                    dns.resolver.resolve(wg["remote_address"], "A")
                except dns.exception.DNSException:
                    errors.append(
                        "wireguard.remote_address is not a valid IPv4/IPv6 address or no DNS A/AAAA record found"
                    )

    if "remote_port" in wg.keys():
        if "remote_address" not in wg.keys():
            errors.append("wireguard.remote_address: must exist when remote_port defined")
        if not type(wg["remote_port"]) is int:
            errors.append("wireguard.remote_port: must be an integer")
        elif not 0 < wg["remote_port"] <= 65535:
            errors.append("wireguard.remote_port: must be between 0 and 65535")

    if "public_key" not in wg.keys():
        errors.append("wireguard.public_key: must exist")
    else:
        if not re.match("^[A-Za-z0-9+/]{42}[AEIMQUYcgkosw480]=$", wg["public_key"]):
            errors.append("wireguard.public_key: is not a valid WireGuard public key")

    return errors


if __name__ == "__main__":
    main()
