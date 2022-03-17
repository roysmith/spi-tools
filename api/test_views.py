from unittest.mock import patch, NonCallableMock
from ipaddress import IPv4Address, IPv6Address, IPv4Network, IPv6Network

from django.test import TestCase
from django.test import Client

from api.views import CidrView, get_ranges, get_whois_data, find_smallest_range, int_to_bits

@patch('api.views.get_whois_data')
class CidrViewTest(TestCase):
    def test_get_with_no_ips_returns_empty_list_in_json_data(self, mock_get_whois_data):
        mock_get_whois_data.return_value = {'asn_cidr': ''}
        response = self.client.get('/api/cidr/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'ranges': []
            })


    def test_get_with_one_ip_returns_correct_ranges_in_json_data(self, mock_get_whois_data):
        mock_get_whois_data.return_value = {'asn_cidr': '100.0.0.0/24'}
        response = self.client.get('/api/cidr/?ip=100.0.0.1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'ranges': [{'asn_cidr': '100.0.0.0/24',
                        'observed_cidr': '100.0.0.1/32',
            }]})


@patch('api.views.get_whois_data')
class GetRangesTest(TestCase):
    def test_get_ranges_with_multiple_ips_in_the_same_range_returns_correct_ranges(self, mock_get_whois_data):
        mock_get_whois_data.return_value = {'asn_cidr': '100.0.0.0/24'}
        ranges = get_ranges(['100.0.0.1',
                             '100.0.0.3',
                             '100.0.0.4',
                             '100.0.0.5'])
        self.assertEqual(ranges, [{'asn_cidr': '100.0.0.0/24',
                                   'observed_cidr': '100.0.0.0/29'}
                                  ])


    def test_get_ranges_with_ips_in_different_ranges_returns_correct_ranges(self, mock_get_whois_data):
        values = {'100.0.0.1': {'asn_cidr': '100.0.0.0/24'},
                  '100.0.0.2': {'asn_cidr': '100.0.0.0/24'},
                  '200.0.0.2': {'asn_cidr': '200.0.0.0/24'},
                  }
        mock_get_whois_data.side_effect = lambda ip: values[ip]
        ranges = get_ranges(['100.0.0.1',
                             '100.0.0.2',
                             '200.0.0.2'])
        self.assertCountEqual(ranges, [
            {'asn_cidr': '100.0.0.0/24',
             'observed_cidr': '100.0.0.0/30'},
            {'asn_cidr': '200.0.0.0/24',
             'observed_cidr': '200.0.0.2/32'},
            ])


@patch('api.views.requests')
class GetWhoisDataTest(TestCase):
    def test_json_data_is_returned(self, mock_requests):
        whois_data = {
            "asn_cidr" : "1.2.3.0/24",
        }
        mock_requests.get().json.return_value = whois_data
        data = get_whois_data('1.2.3.4')
        self.assertEqual(data, whois_data)


    def test_backend_call_passes_correct_arguments(self, mock_requests):
        get_whois_data('1.2.3.4')
        mock_requests.get.assert_called_once_with('https://whois-referral.toolforge.org/w/gateway.py',
                                                  params = {
                                                      'ip': '1.2.3.4',
                                                      'lookup': 'true',
                                                      'format': 'json',
                                                  })


    def test_raise_for_status_is_called(self, mock_requests):
        get_whois_data('1.2.3.4')
        mock_requests.get().raise_for_status.assert_called_once_with()


class FindSmallestRangeTest(TestCase):
    def test_raises_value_error_with_no_addresses(self):
        with self.assertRaisesRegex(ValueError, 'empty ip list'):
            find_smallest_range([])


    def test_rasies_value_error_with_mixed_address_types(self):
        ips = [IPv4Address('1.2.3.4'), IPv6Address('2600::')]
        with self.assertRaisesRegex(ValueError, 'multiple ip types'):
            find_smallest_range(ips)


    def test_single_ipv4_returns_slash_32(self):
        ips = [IPv4Address('1.2.3.4')]
        self.assertEqual(find_smallest_range(ips), IPv4Network('1.2.3.4/32'))


    def test_multiple_ipv4_addresses_returns_correct_range(self):
        ips = [IPv4Address('100.0.0.1'),
               IPv4Address('100.0.0.3'),
               IPv4Address('100.0.0.4'),
               IPv4Address('100.0.0.5')]
        self.assertEqual(find_smallest_range(ips), IPv4Network('100.0.0.0/29'))


    def test_multiple_ipv6_addresses_returns_correct_range(self):
        ips = [IPv6Address('2000::1'),
               IPv6Address('2000::3'),
               IPv6Address('2000::4'),
               IPv6Address('2000::5')]
        self.assertEqual(find_smallest_range(ips), IPv6Network('2000::/125'))


class IntToBitsTest(TestCase):
    def test_rases_value_error_on_overflow(self):
        with self.assertRaises(ValueError, msg='9999 does not fit into 4 bits'):
            int_to_bits(9999, 4)


    def test_raises_value_error_on_negative_numbers(self):
        with self.assertRaises(ValueError, msg='cannot convert negative values (-1)'):
            int_to_bits(-1, 4)


    def test_zero_is_correctly_converted(self):
        self.assertEqual(int_to_bits(0, 8),
                         [0, 0, 0, 0, 0, 0, 0, 0])


    def test_positive_value_is_correctly_converted(self):
        self.assertEqual(int_to_bits(42, 8),
                         [0, 0, 1, 0, 1, 0, 1, 0])


    def test_large_value_is_correctly_converted(self):
        self.assertEqual(int_to_bits(1 << 127, 128),
                         [1] + [0] * 127)
