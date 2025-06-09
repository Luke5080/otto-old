import unittest
from unittest.mock import patch

import mongomock
from pymongo.errors import PyMongoError

from otto.exceptions import NetworkDatabaseException
from otto.ryu.network_state_db.network_db_operator import NetworkDbOperator


class TestNetworkDbOperator(unittest.TestCase):

    def setUp(self):
        self.mock_client = mongomock.MongoClient()

        self.nw_db = NetworkDbOperator.get_instance()

        self.nw_db._MongoConnector = self.mock_client

        self.nw_db._network_state_db = self.mock_client["topology"]

        self.nw_db._switch_collection = self.nw_db._network_state_db["switches"]

    @mongomock.patch(servers=(('localhost', 27017),))
    def test_put_switch_to_db__success(self):
        document = {
            "name": "0000000000000001",
            "ports": [
                {
                    "port_no": "00000001",
                    "hw_addr": "4e:40:af:2c:d3:ab",
                    "name": "s1-eth1"
                },
                {
                    "port_no": "00000002",
                    "hw_addr": "06:52:39:09:aa:b8",
                    "name": "s1-eth2"
                },
                {
                    "port_no": "00000003",
                    "hw_addr": "c2:15:a7:20:aa:5b",
                    "name": "s1-eth3"
                }
            ],
            "portMappings": {
                "s1-eth3": "s5-eth1",
                "s1-eth2": "s2-eth2"
            },
            "connectedHosts": {
                "s1-eth1": {
                    "mac": "00:00:aa:bb:cc:01",
                    "ipv4": [],
                    "ipv6": ["fe80::200:aaff:febb:cc01"]
                }
            },
            "installedFlows": {
                "4b87a365b25521845771719ad28f5633": {
                    "priority": 65535,
                    "cookie": 0,
                    "idle_timeout": 0,
                    "hard_timeout": 0,
                    "actions": ["OUTPUT:CONTROLLER"],
                    "match": {
                        "dl_dst": "01:80:c2:00:00:0e",
                        "dl_type": 35020
                    },
                    "byte_count": 12120,
                    "packet_count": 202,
                    "table_id": 0
                }
            }
        }

        d_id = self.nw_db.put_switch_to_db(document)

        self.assertEqual(self.nw_db.object_ids[document["name"]], d_id)

    @mongomock.patch(servers=(('localhost', 27017),))
    def test_put_switch_to_db__exception(self):
        document = {
            "name": "0000000000000001",
            "ports": [
                {
                    "port_no": "00000001",
                    "hw_addr": "4e:40:af:2c:d3:ab",
                    "name": "s1-eth1"
                },
                {
                    "port_no": "00000002",
                    "hw_addr": "06:52:39:09:aa:b8",
                    "name": "s1-eth2"
                },
                {
                    "port_no": "00000003",
                    "hw_addr": "c2:15:a7:20:aa:5b",
                    "name": "s1-eth3"
                }
            ],
            "portMappings": {
                "s1-eth3": "s5-eth1",
                "s1-eth2": "s2-eth2"
            },
            "connectedHosts": {
                "s1-eth1": {
                    "mac": "00:00:aa:bb:cc:01",
                    "ipv4": [],
                    "ipv6": ["fe80::200:aaff:febb:cc01"]
                }
            },
            "installedFlows": {
                "4b87a365b25521845771719ad28f5633": {
                    "priority": 65535,
                    "cookie": 0,
                    "idle_timeout": 0,
                    "hard_timeout": 0,
                    "actions": ["OUTPUT:CONTROLLER"],
                    "match": {
                        "dl_dst": "01:80:c2:00:00:0e",
                        "dl_type": 35020
                    },
                    "byte_count": 12120,
                    "packet_count": 202,
                    "table_id": 0
                }
            }
        }

        with patch.object(self.nw_db._switch_collection, 'insert_one') as mock_insert:
            mock_insert.side_effect = PyMongoError('Error putting document into collection')

            with self.assertRaises(NetworkDatabaseException):
                self.nw_db.put_switch_to_db(document)

    @mongomock.patch(servers=(('localhost', 27017),))
    def test_modify_switch_document__success(self):
        switch_dpid = "0000000000000005"

        switch_document = {
            "name": "0000000000000005",
            "ports": [
                {
                    "port_no": "00000001",
                    "hw_addr": "4e:40:af:2c:d3:ab",
                    "name": "s1-eth1"
                },
                {
                    "port_no": "00000002",
                    "hw_addr": "06:52:39:09:aa:b8",
                    "name": "s1-eth2"
                },
                {
                    "port_no": "00000003",
                    "hw_addr": "c2:15:a7:20:aa:5b",
                    "name": "s1-eth3"
                }
            ],
            "portMappings": {
                "s1-eth3": "s5-eth1",
                "s1-eth2": "s2-eth2"
            },
            "connectedHosts": {
                "s1-eth1": {
                    "mac": "00:00:aa:bb:cc:01",
                    "ipv4": [],
                    "ipv6": ["fe80::200:aaff:febb:cc01"]
                }
            },
            "installedFlows": {
                "4b87a365b25521845771719ad28f5633": {
                    "priority": 65535,
                    "cookie": 0,
                    "idle_timeout": 0,
                    "hard_timeout": 0,
                    "actions": ["OUTPUT:CONTROLLER"],
                    "match": {
                        "dl_dst": "01:80:c2:00:00:0e",
                        "dl_type": 35020
                    },
                    "byte_count": 12120,
                    "packet_count": 202,
                    "table_id": 0
                }
            }
        }

        expected_document = switch_document

        expected_document["portMappings"]["s1-eth3"] = "s6-eth1"

        d_id = self.nw_db._switch_collection.insert_one(switch_document)

        self.nw_db.object_ids[switch_dpid] = d_id.inserted_id

        print(self.nw_db._switch_collection.find_one({"_id": self.nw_db.object_ids[switch_dpid]}))
        change = {
            "$set": {"portMappings.s1-eth3": "s6-eth1"}
        }

        self.nw_db.modify_switch_document(switch_dpid, change)
        print(self.nw_db._switch_collection.find_one({"_id": self.nw_db.object_ids[switch_dpid]}))

        self.assertEqual(self.nw_db._switch_collection.find_one({"_id": self.nw_db.object_ids[switch_dpid]}),
                         expected_document)

    @mongomock.patch(servers=(('localhost', 27017),))
    def test_modify_switch_document__exception(self):
        switch_dpid = "000000000000000f"

        switch_document = {
            "name": "000000000000000f",
            "ports": [
                {
                    "port_no": "00000001",
                    "hw_addr": "4e:40:af:2c:d3:ab",
                    "name": "s1-eth1"
                },
                {
                    "port_no": "00000002",
                    "hw_addr": "06:52:39:09:aa:b8",
                    "name": "s1-eth2"
                },
                {
                    "port_no": "00000003",
                    "hw_addr": "c2:15:a7:20:aa:5b",
                    "name": "s1-eth3"
                }
            ],
            "portMappings": {
                "s1-eth3": "s5-eth1",
                "s1-eth2": "s2-eth2"
            },
            "connectedHosts": {
                "s1-eth1": {
                    "mac": "00:00:aa:bb:cc:01",
                    "ipv4": [],
                    "ipv6": ["fe80::200:aaff:febb:cc01"]
                }
            },
            "installedFlows": {
                "4b87a365b25521845771719ad28f5633": {
                    "priority": 65535,
                    "cookie": 0,
                    "idle_timeout": 0,
                    "hard_timeout": 0,
                    "actions": ["OUTPUT:CONTROLLER"],
                    "match": {
                        "dl_dst": "01:80:c2:00:00:0e",
                        "dl_type": 35020
                    },
                    "byte_count": 12120,
                    "packet_count": 202,
                    "table_id": 0
                }
            }
        }

        d_id = self.nw_db._switch_collection.insert_one(switch_document)

        self.nw_db.object_ids[switch_dpid] = d_id.inserted_id

        change = {
            "$set": {"connectedHosts.ipv4": "10.0.0.1"}
        }

        self.nw_db.modify_switch_document(switch_dpid, change)

        with patch.object(self.nw_db._switch_collection, 'update_one') as mock_insert:
            mock_insert.side_effect = PyMongoError('Error putting document into collection')

            with self.assertRaises(NetworkDatabaseException):
                self.nw_db.modify_switch_document(switch_dpid, change)

    @mongomock.patch(servers=(('localhost', 27017),))
    def test_remove_switch_document__success(self):
        switch_dpid = "000000000000000a"

        switch_document = {
            "name": "000000000000000a",
            "ports": [
                {
                    "port_no": "00000001",
                    "hw_addr": "4e:40:af:2c:d3:ab",
                    "name": "s1-eth1"
                },
                {
                    "port_no": "00000002",
                    "hw_addr": "06:52:39:09:aa:b8",
                    "name": "s1-eth2"
                },
                {
                    "port_no": "00000003",
                    "hw_addr": "c2:15:a7:20:aa:5b",
                    "name": "s1-eth3"
                }
            ],
            "portMappings": {
                "s1-eth3": "s5-eth1",
                "s1-eth2": "s2-eth2"
            },
            "connectedHosts": {
                "s1-eth1": {
                    "mac": "00:00:aa:bb:cc:01",
                    "ipv4": [],
                    "ipv6": ["fe80::200:aaff:febb:cc01"]
                }
            },
            "installedFlows": {
                "4b87a365b25521845771719ad28f5633": {
                    "priority": 65535,
                    "cookie": 0,
                    "idle_timeout": 0,
                    "hard_timeout": 0,
                    "actions": ["OUTPUT:CONTROLLER"],
                    "match": {
                        "dl_dst": "01:80:c2:00:00:0e",
                        "dl_type": 35020
                    },
                    "byte_count": 12120,
                    "packet_count": 202,
                    "table_id": 0
                }
            }
        }

        d_id = self.nw_db._switch_collection.insert_one(switch_document)

        self.nw_db.object_ids[switch_dpid] = d_id.inserted_id

        self.nw_db.remove_switch_document(switch_dpid)

        self.assertTrue(d_id not in self.nw_db.object_ids)

        self.assertEqual(self.nw_db._switch_collection.find_one({"_id": d_id}), None)

    @mongomock.patch(servers=(('localhost', 27017),))
    def test_remove_switch_document__exception(self):
        with patch.object(self.nw_db._switch_collection, 'delete_one') as mock_insert:
            mock_insert.side_effect = PyMongoError('Error removing document from collection')

            with self.assertRaises(NetworkDatabaseException):
                self.nw_db.remove_switch_document("000000000000000a")

    @mongomock.patch(servers=(('localhost', 27017),))
    def test_get_switch__success(self):
        ...
