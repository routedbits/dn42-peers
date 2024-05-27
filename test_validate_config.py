from unittest import TestCase

import os

from validate_config import read_yaml, \
        validate,  validate_unique_peers, \
        validate_asn, validate_boolean, \
        validate_name, validate_ip, \
        validate_sessions, validate_wireguard

class TestValidateConfig(TestCase):

    def test_validate(self):
        # load all fixture files, test each
        for fixture in sorted(os.listdir('tests/fixtures')):
            test_case = read_yaml(f'tests/fixtures/{fixture}')
            self.assertEqual(
                list(validate(test_case['peer'])),
                test_case['errors'],
                f'test_case::{fixture}')

    def test_validate_unique_peers(self):
        not_unique = [
            '192.0.2.1/24',
            '192.0.2.1/24'
        ]
        self.assertFalse(validate_unique_peers(not_unique))

        unique = [
            '192.0.2.1/24',
            '192.0.2.2/24'
        ]
        self.assertTrue(validate_unique_peers(unique))
        
    def test_validate_asn(self):        
        private_asn = 65000
        private_asn_error = validate_asn(private_asn)
        self.assertEqual(private_asn_error, None)

        asn_cases = [
            424241000, # too low
            4242439999, # too high
        ]

        for asn_case in asn_cases:
            self.assertEqual(validate_asn(asn_case), f"asn: '{asn_case}' must exist in the DN42 registry")

        valid_asn = 4242420207
        self.assertEqual(validate_asn(valid_asn), None)

    def test_validate_boolean(self):
        not_bool = 'foo'
        self.assertEqual(validate_boolean(not_bool), f"{not_bool} is not true or false (boolean)")

        is_bool = True
        self.assertEqual(validate_boolean(is_bool), None)

    def test_validate_name(self):
        invalid_name_cases = [
            'abc', # all lowercase
            '123', # doesn't start with letter,
            'abc#123', # doesn't use - or _ separator
            'ABC-abc', # not all uppercase
        ]
        for name_case in invalid_name_cases:
            self.assertEqual(validate_name(name_case), f"name: '{name_case}' is not in a valid format, must match ^[A-Z][A-Z0-9-_]+$")

        valid_name_cases = [
            'ABC', # all uppercase',
            'ABC-123', # all uppercase, numbers, hyphen
            'ABC_123', # all uppercase, numbers, underscore
            'ABC-123_XYZ', # all uppercase, numbers, hyphen, and unscore
            'A1234_-', # starts with letter, all numbers or separators
        ]
        for name_case in valid_name_cases:
            self.assertEqual(validate_name(name_case), None)

    def test_validate_ip(self):
        not_ip_or_prefix = {
            'addr': 'abc123',
            'af': 'ipv4',
            'attrib': 'test'
        }
        self.assertEqual(validate_ip(**not_ip_or_prefix), f"{not_ip_or_prefix['attrib']}: '{not_ip_or_prefix['addr']}' is not a valid IP address or prefix")

        ipv6_address_af_ipv4 = {
            'addr': '2001:db8::1/128',
            'af': 'ipv4',
            'attrib': 'test'         
        }
        self.assertEqual(validate_ip(**ipv6_address_af_ipv4), f"{ipv6_address_af_ipv4['attrib']}: '{ipv6_address_af_ipv4['addr']}' is not an IPv4 address")

        ipv4_address_not_in_range = {
            'addr': '192.0.2.0/24',
            'af': 'ipv4',
            'attrib': 'test'         
        }
        self.assertEqual(validate_ip(**ipv4_address_not_in_range), f"{ipv4_address_not_in_range['attrib']}: '{ipv4_address_not_in_range['addr']}' is not within 172.20.0.0/14")

        ipv4_address_af_ipv6 = {
            'addr': '192.0.2.1/32',
            'af': 'ipv6',
            'attrib': 'test'         
        }
        self.assertEqual(validate_ip(**ipv4_address_af_ipv6), f"{ipv4_address_af_ipv6['attrib']}: '{ipv4_address_af_ipv6['addr']}' is not an IPv6 address")

        ipv6_address_not_in_range = {
            'addr': '2001:db8::1/128',
            'af': 'ipv6',
            'attrib': 'test'         
        }
        self.assertEqual(validate_ip(**ipv6_address_not_in_range), f"{ipv6_address_not_in_range['attrib']}: '{ipv6_address_not_in_range['addr']}' is not within fe80::/10 or fc00::/7")

        valid_addresses_or_prefixes = [
            { 'addr': '172.20.1.1', 'af': 'ipv4', 'attrib': 'test'}, # IPv4 address
            { 'addr': '172.20.0.0/24', 'af': 'ipv4', 'attrib': 'test'}, # IPv4 prefix
            { 'addr': 'fe80::100', 'af': 'ipv6', 'attrib': 'test'}, # Link Local address
            { 'addr': 'fe80::100/64', 'af': 'ipv6', 'attrib': 'test'}, # Link Local prefix
            { 'addr': 'fd00::100', 'af': 'ipv6', 'attrib': 'test'}, # ULA Address
            { 'addr': 'fd00::100/64', 'af': 'ipv6', 'attrib': 'test'} # ULA Prefix
        ]
        for valid_address_or_prefix in valid_addresses_or_prefixes:
            self.assertEqual(validate_ip(**valid_address_or_prefix), None)

    def test_validate_sessions(self):
        session_not_list = 'abc123'
        self.assertEqual(validate_sessions(session_not_list, None), [f"sessions: '{session_not_list}' must be a list"])

        sessions_not_ipv4_ipv6 = [
            [],
            ['abc', '123']
        ]
        for session in sessions_not_ipv4_ipv6:
            self.assertEqual(validate_sessions(session, None), [f"sessions: '{session}' must include 'ipv4' and/or 'ipv6'"])

        session_ipv4_peer_not_ipv4 = {
            'sessions': ['ipv4'],
            'peer': []
        }

        self.assertEqual(validate_sessions(**session_ipv4_peer_not_ipv4), ["ipv4 required when sessions['ipv4']"])
        session_ipv6_peer_not_ipv6 = {
            'sessions': ['ipv6'],
            'peer': []
        }
        self.assertEqual(validate_sessions(**session_ipv6_peer_not_ipv6), ["ipv6 required when sessions['ipv6']"])

        session_all_peer_none = {
            'sessions': ['ipv4', 'ipv6'],
            'peer': []
        }
        self.assertEqual(validate_sessions(**session_all_peer_none), ["ipv4 required when sessions['ipv4']", "ipv6 required when sessions['ipv6']"])

        sessions_valid = [
            {'sessions': ['ipv4'], 'peer': ['ipv4']},
            {'sessions': ['ipv6'], 'peer': ['ipv6']},
            {'sessions': ['ipv4', 'ipv6'], 'peer': ['ipv4', 'ipv6']},
        ]
        for session in sessions_valid:
            self.assertEqual(validate_sessions(**session), [])

    def test_validate_wireguard(self):
        not_dict = []
        self.assertEqual(validate_wireguard(not_dict), f"wireguard: '{not_dict}' must be type dictionary")

        # allow dynamic peers (no remote address)
        # no_remote_address = {
        #     'foo': 'bar'
        # }
        # self.assertIn("wireguard.remote_address: must exist", validate_wireguard(no_remote_address))

        remote_address_invalid_msg = "wireguard.remote_address is not a valid IPv4/IPv6 address or no DNS A/AAAA record found"

        remote_address_not_ip = {
            'remote_address': 'foobar'
        }
        self.assertIn(remote_address_invalid_msg, validate_wireguard(remote_address_not_ip))

        remote_address_valid_ip = {
            'remote_address': '192.0.2.1'
        }
        self.assertNotIn(remote_address_invalid_msg, validate_wireguard(remote_address_valid_ip))

        remote_address_invalid_fqdn = {
            'remote_address': 'foobar.non_exist_tld'
        }
        self.assertIn(remote_address_invalid_msg, validate_wireguard(remote_address_invalid_fqdn))

        remote_address_valid_fqdn = {
            'remote_address': 'google.com'
        }
        self.assertNotIn(remote_address_invalid_msg, validate_wireguard(remote_address_valid_fqdn))

        no_remote_port_with_address = {
            'remote_address': '192.0.2.1',
        }
        self.assertIn("wireguard.remote_port: must exist when remote_address defined", validate_wireguard(no_remote_port_with_address))

        no_address_with_remote_port = {
            'remote_port': 50001,
        }
        self.assertIn("wireguard.remote_address: must exist when remote_port defined", validate_wireguard(no_address_with_remote_port))

        remote_port_not_int = {
            'remote_address': '192.0.2.1',
            'remote_port': 'abc123'
        }
        self.assertIn("wireguard.remote_port: must be an integer", validate_wireguard(remote_port_not_int))

        remote_port_out_of_range = [
            {'remote_address': '192.0.2.1', 'remote_port': -1}, # below range
            {'remote_address': '192.0.2.1', 'remote_port': 100000}, # above range           
        ]
        for remote_port in remote_port_out_of_range:
            self.assertIn("wireguard.remote_port: must be between 0 and 65535", validate_wireguard(remote_port))

        no_public_key = {
            'remote_address': '192.0.2.1',
            'remote_port': 30000
        }
        self.assertIn("wireguard.public_key: must exist", validate_wireguard(no_public_key))

        public_key_not_valid = {
            'remote_address': '192.0.2.1',
            'remote_port': 30000,
            'public_key': 'abc123'
        }
        self.assertIn("wireguard.public_key: is not a valid WireGuard public key", validate_wireguard(public_key_not_valid))

        wireguard_valid = {
            'remote_address': '192.0.2.1',
            'remote_port': 30000,
            'public_key': 'vLfdP6SrkTfOnn/iYPM/ytMIU/vseZVNoAdgNbo1yV4='
        }
        self.assertEqual(validate_wireguard(wireguard_valid), [])


