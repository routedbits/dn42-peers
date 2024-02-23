# RoutedBits: DN42 Peering Configuration

This repository contains the peering configuration for each of our
DN42 routers.

## Requesting/Managing Peering

Pull-requests are welcomed by users requesting peering to one or
more locations. Information about nodes and configuration information about
each location can be found on our [site](https://dn42.routedbits.com/nodes).
You may also modify your peering by submitting additional pull requests with
your desired changes.

Please note that prefixes are subject to the following:

* Must be within DN42 IPv4 or IPv6 [address space](https://dn42.eu/howto/Address-Space)
* Must not be RPKI invalid (properly configured in the registry, see 
[Getting Started](https://dn42.eu/howto/Getting-Started))

#### Alternative Method

You can [click here](https://forms.gle/rt9YZ8AoFfX5YmE8A) to submit a peering request via Google Form. This is an easier method for users that do not wish to interact with Git or GitHub.

### Steps

1. Fork this repository
2. Update the appropriate [router](routers/) with your peering information
3. Create a PR

Once approved and merged, we automatically distribute your configuration to the routers in our network.
Please allow some time for the process to complete.

### Examples

1. Multi-protocol (IPv4/IPv6) with Extended Nexthop Capability **(Preferred)**

```yaml
- name: YOUR-PEER-NAME    # Name your connection; please use capital letters and dashes only
  asn: 4242420000         # Your DN42 ASN
  ipv6: fe80::1234        # Your IPv6 tunnel address (Link-local preferred, /64 assumed unless specified)
  multiprotocol: true     # Send both IPv4 and IPv6 AFIs in the same BGP session
  extended_nexthop: true  # Enable BGP Extended Nexthop Capability
  sessions: [ipv6]        # Protocol to use for session connection (ipv6)
  wireguard:
    remote_address: 2001:db8:abcd:ef::1                        # Your clear net/public IPv4 or IPv6 address (or FQDN)
    remote_port: 20207                                         # Your WireGuard Listen Port
    public_key: abdcefabdcefabdcefabdcefabdcefabdcefabdcefg=   # Your WireGuard Public Key
```

2. Multi-protocol (IPv4/IPv6)

```yaml
- name: YOUR-PEER-NAME    # Name your connection; please use capital letters and dashes only
  asn: 4242420000         # Your DN42 ASN
  ipv4: 172.20.0.1        # Your IPv4 tunnel/endpoint address
  ipv6: fe80::1234        # Your IPv6 tunnel address (Link-local preferred, /64 assumed unless specified)
  multiprotocol: true     # Send both IPv4 and IPv6 AFIs in the same BGP session
  sessions: [ipv6]        # Protocol to use for session connection (ipv4 or ipv6)
  wireguard:
    remote_address: 2001:db8:abcd:ef::1                        # Your clear net/public IPv4 or IPv6 address (or FQDN)
    remote_port: 20207                                         # Your WireGuard Listen Port
    public_key: abdcefabdcefabdcefabdcefabdcefabdcefabdcefg=   # Your WireGuard Public Key
```

3. IPv4 and IPv6 in separate sessions

```yaml
- name: YOUR-PEER-NAME    # Name your connection; please use capital letters and dashes only
  asn: 4242420000         # Your DN42 ASN
  ipv4: 172.20.0.1        # Your IPv4 tunnel/endpoint address
  ipv6: fe80::1234        # Your IPv6 tunnel address (Link-local preferred, /64 assumed unless specified)
  sessions: [ipv4,ipv6]   # Protocol to use for session connection (ipv4 and ipv6)
  wireguard:
    remote_address: 2001:db8:abcd:ef::1                        # Your clear net/public IPv4 or IPv6 address (or FQDN)
    remote_port: 20207                                         # Your WireGuard Listen Port
    public_key: abdcefabdcefabdcefabdcefabdcefabdcefabdcefg=   # Your WireGuard Public Key
```

4. IPv4 Only

```yaml
- name: YOUR-PEER-NAME    # Name your connection; please use capital letters and dashes only
  asn: 4242420000         # Your DN42 ASN
  ipv4: 172.20.0.1        # Your IPv4 tunnel/endpoint address
  sessions: [ipv4]        # Protocol to use for session connection (ipv4)
  wireguard:
    remote_address: 2001:db8:abcd:ef::1                        # Your clear net/public IPv4 or IPv6 address (or FQDN)
    remote_port: 20207                                         # Your WireGuard Listen Port
    public_key: abdcefabdcefabdcefabdcefabdcefabdcefabdcefg=   # Your WireGuard Public Key
```

5. IPv6 Only

```yaml
- name: YOUR-PEER-NAME    # Name your connection; please use capital letters and dashes only
  asn: 4242420000         # Your DN42 ASN
  ipv6: fe80::1234        # Your IPv6 tunnel address (Link-local preferred, /64 assumed unless specified)
  sessions: [ipv6]        # Protocol to use for session connection (ipv4 or ipv6)
  wireguard:
    remote_address: 2001:db8:abcd:ef::1                        # Your clear net/public IPv4 or IPv6 address (or FQDN)
    remote_port: 20207                                         # Your WireGuard Listen Port
    public_key: abdcefabdcefabdcefabdcefabdcefabdcefabdcefg=   # Your WireGuard Public Key
```
