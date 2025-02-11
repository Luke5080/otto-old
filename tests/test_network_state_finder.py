import unittest
import responses
import hashlib
import json
from requests.exceptions import ConnectionError
from otto.ryu.network_state_db.network_state_finder import NetworkStateFinder
from exceptions import (
    SwitchRetrievalException, PortRetrievalException,
    PortMappingException, FlowRetrievalException,
    HostRetrievalException
)

class TestNetworkStateFinder(unittest.TestCase):

    @responses.activate
    def test_get_switches__requests_exceptions(self):
        responses.add(
            responses.GET,
            'http://127.0.0.1:8080/stats/switches',
            body=RuntimeError("Error")
        )

        with self.assertRaises(SwitchRetrievalException):
            db_creator = NetworkStateFinder()

            db_creator.get_switches()

    @responses.activate
    def test_get_switches__requests_connection_exception(self):
        responses.add(
            responses.GET,
            'http://127.0.0.1:8080/stats/switches',
            body=ConnectionError()
        )

        with self.assertRaises(SwitchRetrievalException):
            db_creator = NetworkStateFinder()

            db_creator.get_switches()

    @responses.activate
    def test_get_switches__non_200(self):
        responses.add(
            responses.GET,
            'http://127.0.0.1:8080/stats/switches',
            json = {'error': 'not found'},
            status=400
        )

        with self.assertRaises(SwitchRetrievalException):
            db_creator = NetworkStateFinder()

            db_creator.get_switches()

    @responses.activate
    def test_get_ports__exception(self):

        switch_dpid = "0000000000000001"
        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/v1.0/topology/switches/{switch_dpid}',
            body=RuntimeError('Error')
        )

        with self.assertRaises(PortRetrievalException):
            db_creator = NetworkStateFinder()

            db_creator.get_ports(switch_dpid)

    def test_get_ports__request_conn_exception(self):

        switch_dpid = "0000000000000001"
        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/v1.0/topology/switches/{switch_dpid}',
            body=ConnectionError()
        )

        with self.assertRaises(PortRetrievalException):
            db_creator = NetworkStateFinder()

            db_creator.get_ports(switch_dpid)

    @responses.activate
    def test_get_ports__non_200(self):

        switch_dpid = "0000000000000001"
        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/v1.0/topology/switches/{switch_dpid}',
            json = {'error': 'not found'},
            status=400
        )

        with self.assertRaises(PortRetrievalException):
            db_creator = NetworkStateFinder()

            db_creator.get_ports(switch_dpid)

    @responses.activate
    def test_get_ports__empty_response(self):

        switch_dpid = "0000000000000001"

        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/v1.0/topology/switches/{switch_dpid}',
            json = [],
            status=200
        )

        db_creator = NetworkStateFinder()

        result = db_creator.get_ports(switch_dpid)

        self.assertEqual(result, [])

    @responses.activate
    def test_get_ports__successful_response(self):
        switch_dpid = "0000000000000001"

        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/v1.0/topology/switches/{switch_dpid}',
            json=[
                {
                    "dpid": "0000000000000001",
                    "ports": [
                        {
                            "dpid": "0000000000000001",
                            "port_no": "00000001",
                            "hw_addr": "ae:b9:44:bc:5d:27",
                            "name": "s1-eth1"
                        },
                        {
                            "dpid": "0000000000000001",
                            "port_no": "00000002",
                            "hw_addr": "2e:2c:a8:da:77:10",
                            "name": "s1-eth2"
                        },
                        {
                            "dpid": "0000000000000001",
                            "port_no": "00000003",
                            "hw_addr": "16:20:f6:bd:52:24",
                            "name": "s1-eth3"
                        }
                    ]
                }
            ],
            status=200
        )

        expected_result = [
          {
            "port_no": "00000001",
            "hw_addr": "ae:b9:44:bc:5d:27",
            "name": "s1-eth1"
          },
          {
            "port_no": "00000002",
            "hw_addr": "2e:2c:a8:da:77:10",
            "name": "s1-eth2"
          },
          {
            "port_no": "00000003",
            "hw_addr": "16:20:f6:bd:52:24",
            "name": "s1-eth3"
          }
        ]

        db_creator = NetworkStateFinder()

        result = db_creator.get_ports(switch_dpid)

        self.assertEqual(result, expected_result)

    @responses.activate
    def test_get_port_mappings__exception(self):
        switch_dpid = "0000000000000001"

        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/v1.0/topology/links/{switch_dpid}',
            body=RuntimeError('Error')
        )

        with self.assertRaises(PortMappingException):
            db_creator = NetworkStateFinder()

            db_creator.get_port_mappings(switch_dpid)

    @responses.activate
    def test_get_port_mappings__non_200(self):
        switch_dpid = "0000000000000001"
        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/v1.0/topology/links/{switch_dpid}',
            json={'error': 'not found'},
            status=400
        )

        with self.assertRaises(PortMappingException):
            db_creator = NetworkStateFinder()

            db_creator.get_port_mappings(switch_dpid)

    @responses.activate
    def test_get_ports_mappings__empty_response(self):

        switch_dpid = "0000000000000001"

        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/v1.0/topology/links/{switch_dpid}',
            json = [],
            status=200
        )

        db_creator = NetworkStateFinder()

        result = db_creator.get_port_mappings(switch_dpid)

        self.assertEqual(result, {})

    @responses.activate
    def test_get_ports_mappings__successful_response(self):
        switch_dpid = "0000000000000001"

        expected_result = {"s1-eth2" : "s2-eth2", "s1-eth3" : "s5-eth1"}

        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/v1.0/topology/links/{switch_dpid}',
            json=[
                  {
                    "src": {
                      "dpid": "0000000000000001",
                      "port_no": "00000002",
                      "hw_addr": "2e:2c:a8:da:77:10",
                      "name": "s1-eth2"
                    },
                    "dst": {
                      "dpid": "0000000000000002",
                      "port_no": "00000002",
                      "hw_addr": "36:b2:42:ef:0a:88",
                      "name": "s2-eth2"
                    }
                  },
                  {
                    "src": {
                      "dpid": "0000000000000001",
                      "port_no": "00000003",
                      "hw_addr": "16:20:f6:bd:52:24",
                      "name": "s1-eth3"
                    },
                    "dst": {
                      "dpid": "0000000000000005",
                      "port_no": "00000001",
                      "hw_addr": "9a:b8:e0:7c:75:88",
                      "name": "s5-eth1"
                    }
                  }
                ],

            status=200
        )

        db_creator = NetworkStateFinder()

        result = db_creator.get_port_mappings(switch_dpid)

        self.assertEqual(result, expected_result)

    @responses.activate
    def test_get_connected_hosts__exception(self):
        switch_dpid = "0000000000000001"
        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/v1.0/topology/hosts/{switch_dpid}',
            body=RuntimeError('Error')
        )

        with self.assertRaises(HostRetrievalException):
            db_creator = NetworkStateFinder()

            db_creator.get_connected_hosts(switch_dpid)

    @responses.activate
    def test_get_connected_hosts__non_200(self):

        switch_dpid = "0000000000000001"
        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/v1.0/topology/hosts/{switch_dpid}',
            json = {'error': 'not found'},
            status=400
        )

        with self.assertRaises(HostRetrievalException):
            db_creator = NetworkStateFinder()

            db_creator.get_connected_hosts(switch_dpid)

    @responses.activate
    def test_get_connected_hosts__empty_response(self):

        switch_dpid = "0000000000000001"

        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/v1.0/topology/hosts/{switch_dpid}',
            json = [],
            status=200
        )

        db_creator = NetworkStateFinder()

        result = db_creator.get_connected_hosts(switch_dpid)

        self.assertEqual(result, {})

    @responses.activate
    def test_get_connected_hosts__successful_response(self):

        switch_dpid = "0000000000000001"

        expected_result = {
            "s1-eth1": {
            "mac": "00:00:aa:bb:cc:01",
            "ipv4": [],
            "ipv6": ["fe80::200:aaff:febb:cc01"],
            }
          }

        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/v1.0/topology/hosts/{switch_dpid}',
            json = [
                  {
                    "mac": "00:00:aa:bb:cc:01",
                    "ipv4": [],
                    "ipv6": [
                      "fe80::200:aaff:febb:cc01"
                    ],
                    "port": {
                      "dpid": "0000000000000001",
                      "port_no": "00000001",
                      "hw_addr": "ae:b9:44:bc:5d:27",
                      "name": "s1-eth1"
                    }
                  }
                ],
            status=200
        )

        db_creator = NetworkStateFinder()

        result = db_creator.get_connected_hosts(switch_dpid)

        self.assertEqual(result, expected_result)

    @responses.activate
    def test_get_installed_flows__exception(self):
        switch_dpid = "1"

        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/stats/flow/{switch_dpid}',
            body=RuntimeError('Error')
        )

        with self.assertRaises(FlowRetrievalException):
            db_creator = NetworkStateFinder()

            db_creator.get_installed_flows(switch_dpid)

    @responses.activate
    def test_get_installed_flows__non_200(self):

        switch_dpid = "1"
        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/stats/flow/{switch_dpid}',
            json = {'error': 'not found'},
            status=400
        )

        with self.assertRaises(FlowRetrievalException):
            db_creator = NetworkStateFinder()

            db_creator.get_installed_flows(switch_dpid)

    @responses.activate
    def test_get_installed_flows__empty_response(self):

        switch_dpid = "1"
        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/stats/flow/{switch_dpid}',
            json = {},
            status=200
        )

        db_creator = NetworkStateFinder()

        result = db_creator.get_installed_flows(switch_dpid)

        self.assertEqual(result, {})

    @responses.activate
    def test_get_installed_flows__successful_response(self):
        target_hash_fields = {
            'priority': 65535,
            'table_id': 0,
            'match':{ "dl_dst": "01:80:c2:00:00:0e", "dl_type": 35020},
            'actions': ["OUTPUT:CONTROLLER"],
            'dpid': '1'
        }
        hash_str = json.dumps(target_hash_fields, sort_keys=True)

        flow_hash = str(hashlib.md5(hash_str.encode('utf-8')).hexdigest())

        expected_result = {
            flow_hash : {
                        "priority": 65535,
                        "cookie": 0,
                        "idle_timeout": 0,
                        "hard_timeout": 0,
                        "actions": [
                            "OUTPUT:CONTROLLER"
                        ],
                        "match": {
                            "dl_dst": "01:80:c2:00:00:0e",
                            "dl_type": 35020
                        },
                        "byte_count": 236520,
                        "packet_count": 3942,
                        "table_id": 0
                    }
                }
        switch_dpid = "1"
        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/stats/flow/{switch_dpid}',
            json = {
                "1": [
                    {
                        "priority": 65535,
                        "cookie": 0,
                        "idle_timeout": 0,
                        "hard_timeout": 0,
                        "actions": [
                            "OUTPUT:CONTROLLER"
                        ],
                        "match": {
                            "dl_dst": "01:80:c2:00:00:0e",
                            "dl_type": 35020
                        },
                        "byte_count": 236520,
                        "duration_sec": 1966,
                        "duration_nsec": 107000000,
                        "packet_count": 3942,
                        "table_id": 0
                    }
                ]
            },
            status=200
        )

        db_creator = NetworkStateFinder()

        result = db_creator.get_installed_flows(switch_dpid)

        self.assertEqual(result, expected_result)
