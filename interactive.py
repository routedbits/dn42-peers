#!/usr/bin/env python3

import argparse
import cmd
import yaml
import validate_config as validations

from os import listdir
from pathlib import Path
from registry import Registry
from validate_config import validate

class output:
    OK = '\033[92m'
    WARN = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def fail(msg):
        output.print(msg, status=output.FAIL, lines_before=1, lines_after=1)

    def warning(msg):
        output.print(msg, status=output.WARN, lines_before=1, lines_after=1)

    def ok(msg):
        output.print(msg, status=output.OK, lines_before=1, lines_after=1)

    def ask(msg, status=str(), lines_before=1, lines_after=0):
        prompt = '{}{}{}{}{}'.format('\n' * lines_before, status, msg, output.ENDC, '\n' * lines_after)
        return input(prompt)

    def print(msg, status=str(), lines_before=0, lines_after=0):
        prompt = '{}{}{}{}{}'.format('\n' * lines_before, status, msg, output.ENDC, '\n' * lines_after)
        print(prompt)

    def choices(question, options, status=str(), lines_before=0, lines_after=0):
        output.print(question, lines_after=1)

        # https://stackoverflow.com/a/59627245
        cmd.Cmd().columnize(
            [f'\t{idx+1}. {option}' for idx, option in enumerate(options)],
            displaywidth=80
        )

        try:
            return int(output.ask('Selection: '))
        except ValueError:
            output.fail('ERROR: Not a valid selection, try again')

    def table(data, status=str(), lines_before=0, lines_after=0):
        print('\n' * lines_before)
        for key, val in data.items():
            output.print(f'{key}:\t{val}', status=status)
        print('\n' * lines_after)

class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)

def load_router_peers(router):
    with open(f'routers/{router}.yml', 'r') as fd:
        peers = yaml.safe_load(fd)

    # no peers set to empty list to avoid NoneType
    if not peers:
        peers = []

    return peers

def save_router_peers(router, peers):
    # Sort peers by name before saving
    peers = sorted(peers, key=lambda peer: peer['name'])

    with open(f'routers/{router}.yml', 'w') as fd:
        # YAML document header
        fd.write('---\n')
        # Write out each peer to router file (do not sort each peers keys)
        for peer in peers:
            fd.write(yaml.dump([peer], Dumper=IndentDumper, sort_keys=False))
            # Don't write newline after last peer
            if peer != peers[-1]:
                fd.write('\n')

def main(args):
    peer = {}
    registry = Registry()

    # Router
    router = None
    while True:
        question = 'What router would you like to peer at?'
        routers = sorted([Path(router).stem for router in listdir('routers')])

        try:
            router = routers[output.choices(question, routers)-1]
            break
        except (IndexError, TypeError, ValueError):
            output.fail('ERROR: Not a valid selection, try again')

    # ASN
    while True:
        try:
            asn = int(output.ask('DN42 ASN: '))
            if not (error := validations.validate_asn(asn)):
                break
            output.fail(error)
        except ValueError:
            output.fail('ERROR: Not an valid ASN number')

    # Print ASN data from registry
    if args.registry:
        r_asn = registry.asn(asn)
        output.table({
            'AS-NAME': r_asn.get('as-name', ''),
            'Description': r_asn.get('descr', '')
        }, status=output.OK)

    # Name
    while True:
        peer_name = output.ask('Peer Name: ')
        if not (error := validations.validate_name(peer_name)):
            break
        output.fail(error)

    peer['name'] = peer_name
    peer['asn'] = asn

    # Type of BGP Peering
    peering_types = {
        'mp-bgp-extnh': 'Multi-protocol (IPv4 and IPv6) with Extended Nexthop capability (preferred)',
        'mp-bgp': 'Multi-protocol (IPv4 and IPv6)',
        'ipv4v6': 'IPv4 and IPv6 (separate sessions)',
        'ipv4': 'IPv4 ONLY',
        'ipv6': 'IPv6 ONLY'
    }
    peering_type = None
    while True:
        question = 'Which BGP peering type are you requesting?'
        try:
            selection = output.choices(question, peering_types.values(), lines_before=1, lines_after=1)
            peering_type = list(peering_types.keys())[selection-1]
            break
        except (ValueError, IndexError):
            output.fail('ERROR: Not a valid selection, try again')

    # IPv4 Tunnel Address
    def ipv4_tunnel_address():
        while True:
            answer = output.ask('IPv4 tunnel address: ')
            if not (error := validations.validate_ip(answer, af='ipv4', attrib='ipv4')):
                break
            output.fail(error)
        peer['ipv4'] = answer

    # IPv6 Tunnel Address
    def ipv6_tunnel_address():
        while True:
            answer = output.ask('IPv6 tunnel address (Link-local preferred, /64 assumed unless specified): ')
            if not (error := validations.validate_ip(answer, af='ipv6', attrib='ipv6')):
                break
            output.fail(error)
        peer['ipv6'] = answer

    # Session Address Family
    def session_address_family():
        session = []
        while True:
            valid_af = ['ipv4', 'ipv6']
            answer = output.ask('Session Address Family (ipv4, ipv6): ')
            if answer in valid_af:
                session = [answer]
                break
            else:
                output.fail('ERROR: not a valid session address family')
        return session

    # Multi-protocol (IPv4 and IPv6) with Extended Nexthop capability
    if peering_type == 'mp-bgp-extnh':
        ipv6_tunnel_address()
        peer['multiprotocol'] = True
        peer['extended_nexthop'] = True
        peer['sessions'] = ['ipv6']

    # Multi-protocol (IPv4 and IPv6)
    elif peering_type == 'mp-bgp':
        session = session_address_family()
        ipv4_tunnel_address()
        ipv6_tunnel_address()
        peer['multiprotocol'] = True
        peer['sessions'] = session

    # IPv4 + IPv6
    elif peering_type == 'ipv4v6':
        ipv4_tunnel_address()
        ipv6_tunnel_address()
        peer['sessions'] = ['ipv4', 'ipv6']

    # IPv4 ONLY
    elif peering_type == 'ipv4':
        ipv4_tunnel_address()
        peer['sessions'] = ['ipv4']

    # IPv6 ONLY
    elif peering_type == 'ipv6':
        ipv6_tunnel_address()
        peer['sessions'] = ['ipv6']

    # Wireguard
    while True:
        wireguard = {}

        # Wireguard Endpoint
        remote_address = output.ask('Wireguard Endpoint: ')
        if remote_address:
            wireguard['remote_address'] = remote_address

        # Wireguard Listen Port
        # Port only required if remote_address specified
        if remote_address:
            try:
                remote_port = int(output.ask('Wireguard Port: '))
                wireguard['remote_port'] = remote_port
            except ValueError:
                output.fail('ERROR: Not a valid port number')
                continue

        # Wireguard Public Key
        public_key = output.ask('Wireguard Public Key: ')
        if public_key:
            wireguard['public_key'] = public_key

        if not (errors := validations.validate_wireguard(wireguard)):
            break

        for error in errors:
            output.fail(error)
    peer['wireguard'] = wireguard

    print()

    # Final validation as a whole
    peer_errors = list(validate(peer))
    for peer_error in peer_errors:
        output.fail(peer_error)

    if args.stdout:
        # Output YAML to stdout
        peers = [peer]
        output.ok('--- Generated Configuration ---')
        output.print(f'# routers/{router}.yml', lines_after=1)
        output.print(yaml.dump(peers, Dumper=IndentDumper, sort_keys=False))
    else:
        # Write YAML to selected router
        peers = load_router_peers(router)
        peers.append(peer)
        save_router_peers(router, peers)
        output.ok(f'Successfully saved peer to {router}.yml')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate dn42-peers configuration')
    parser.add_argument('--stdout', action=argparse.BooleanOptionalAction,
            help='Output peer configuration to stdout')
    parser.add_argument('--registry', action=argparse.BooleanOptionalAction,
            help='Output registry data during questions')
    args = parser.parse_args()
    main(args)
