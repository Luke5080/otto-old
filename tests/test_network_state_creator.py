import unittest
from unittest.mock import MagicMock
import responses
from pymongo.errors import PyMongoError
from exceptions import (
    SwitchRetrievalException, PortRetrievalException,
    PortMappingException, FlowRetrievalException,
    HostRetrievalException, NetworkDatabaseException
)
from otto.network_state_db.network_state_finder import NetworkStateFinder


class TestNetworkStateCreator(unittest.TestCase):

    @responses.activate
    def test_get_switches__requests_exceptions(self):
        responses.add(
            responses.GET,
            'http://127.0.0.1:8080/stats/switches',
            body=RuntimeError("Error")
        )

        with self.assertRaises(SwitchRetrievalException):
            db_creator = NetworkStateFinder()

            db_creator._get_switches()

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

            db_creator._get_switches()

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

            db_creator._get_ports(switch_dpid)

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

            db_creator._get_ports(switch_dpid)

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

        result = db_creator._get_ports(switch_dpid)

        self.assertEqual(result, {})

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

            db_creator._get_port_mappings(switch_dpid)

    @responses.activate
    def test_get_port_mappings__non_200(self):

        switch_dpid = "0000000000000001"
        responses.add(
            responses.GET,
            f'http://127.0.0.1:8080/v1.0/topology/links/{switch_dpid}',
            json = {'error': 'not found'},
            status=400
        )

        with self.assertRaises(PortMappingException):
            db_creator = NetworkStateFinder()

            db_creator._get_port_mappings(switch_dpid)

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

        result = db_creator._get_port_mappings(switch_dpid)

        self.assertEqual(result, {})

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

            db_creator._get_connected_hosts(switch_dpid)

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

            db_creator._get_connected_hosts(switch_dpid)

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

        result = db_creator._get_connected_hosts(switch_dpid)

        self.assertEqual(result, {})

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

            db_creator._get_installed_flows(switch_dpid)

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

            db_creator._get_installed_flows(switch_dpid)