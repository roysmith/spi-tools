import logging
from collections import defaultdict
from ipaddress import ip_address, ip_network, IPv4Network, IPv6Network

from django.http import JsonResponse
from django.views import View

import requests

# pylint: disable=invalid-name

logger = logging.getLogger('api.views')


class CidrView(View):
    """Given a set of IP addresses, returns a minimal set of CIDR ranges
    which cover the addresses.

    Aggregation into ranges based on the asn_cidr data returned from
    whois.  Within a set of addresses from a given asn_cidr, we also
    compute an observed_cidr based on the actual addresses provided.
    For example, given the addresses:

      100.0.0.1
      100.0.0.3
      100.0.0.4
      100.0.0.5

    If the whois data says these all belong to 100.0.0.0/24, the
    returned data for that range will be:

      {
        'asn_cidr': '100.0.0.0/24',
        'observerd_cidr': '100.0.0.0/29'
      }

    The observed_cidr will always be a subset of the asn_cidr.

    """
    def get(self, request):
        ips = request.GET.getlist('ip')
        logger.debug("ips = %s", ips)
        return JsonResponse({
            'ranges': get_ranges(ips)
        })


def get_ranges(ips):
    networks = defaultdict(list)
    for ip in ips:
        address = ip_address(ip)
        whois_data = get_whois_data(ip)
        network = ip_network(whois_data['asn_cidr'])
        networks[network].append(address)
    return [{'asn_cidr': str(range),
             'observed_cidr': str(find_smallest_range(ips)),
             } for range, ips in networks.items()]


# Based on get_whois_data() from
# https://github.com/GeneralNotability/bullseye/blob/main/bullseyeapp/utils.py
def get_whois_data(ip):
    """ip is a string representing either an IPv4 or IPv6 address, i.e. '1.2.3.4'.

    Returns a dict containing the returned data from the whois gateway.

    """
    payload = {
        'ip': ip,
        'lookup': 'true',
        'format': 'json'
    }
    r = requests.get('https://whois-referral.toolforge.org/w/gateway.py', params=payload)
    r.raise_for_status()
    return r.json()


def find_smallest_range(ips):
    """Given a list of IPv[46]Address objects, return the IPv[46]Network
    with the smallest prefix_lenth which encompasses all the
    addresses.

    There must be at least 1 address, and all the addresses must be of
    the same type (v4 or v6).

    """
    lengths = {ip.max_prefixlen for ip in ips}
    if len(lengths) == 0:
        raise ValueError('empty ip list')
    if len(lengths) > 1:
        raise ValueError('multiple ip types')
    ip_length = lengths.pop()
    bit_vectors = []
    for ip in ips:
        bit_vectors.append(int_to_bits(int(ip), ip_length))

    # bit_sets is the set of observed bits for each of the 32 or 128 bits
    # in the addresses.  If we started with:
    #
    # IPv4Address('128.0.0.1')
    # IPv4Address('128.0.0.3')
    # IPv4Address('128.0.0.5')
    #
    # bit_sets would be:
    #
    # [{1},    {0},    {0},    {0},    {0},    {0},    {0},    {0},
    #  {0},    {0},    {0},    {0},    {0},    {0},    {0},    {0},
    #  {0},    {0},    {0},    {0},    {0},    {0},    {0},    {0},
    #  {0},    {0},    {0},    {0},    {0},    {0, 1}, {0, 1}, {1}]
    bit_sets = [set(bits) for bits in zip(*bit_vectors)]

    network_number = 0
    netmask = 0
    in_mask = True
    for s in bit_sets:
        if in_mask and len(s) == 1:
            bit = s.pop()
            netmask += 1
        else:
            bit = 0
            in_mask = False
        network_number = (network_number << 1) + bit

    if ip_length == 32:
        return IPv4Network((network_number, netmask))
    else:
        return IPv6Network((network_number, netmask))


def int_to_bits(i, n):
    """Converts an integer (i) into a list of n bits.  Bits are high-order
    first, zero-padded.

    int_to_bits(5, 8) => [0, 0, 0, 0, 0, 1, 0, 1]

    It is an error for the integer to not fit into n bits.

    """
    if i < 0:
        raise ValueError(f'cannot convert negative values ({i})')
    bits = []
    temp = i
    for _ in range(n):
        bits.append(temp % 2)
        temp >>= 1
    if temp:
        raise ValueError(f'{i} does not fit into {n} bits')
    return list(reversed(bits))
