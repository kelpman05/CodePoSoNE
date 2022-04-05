#!/usr/bin/env python

"""Tests for `distributed_consensus` package."""


import unittest

from distributed_consensus.core.node import Node
from distributed_consensus.core.node_manager import (
    default_manager,
    replace_default_manager,
    NodeManager,
)


class TestNode(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, if any."""
        replace_default_manager(NodeManager())

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_auto_register(self):
        """Test the auto registration."""
        manager = NodeManager()
        node1 = Node(1, '192.168.1.1', 1111, None, None, manager=manager)
        assert node1 in manager._all
        assert manager._by_id.get(1) is node1
        del node1
        node1 = None  # noqa
        assert len(manager._all) == 0
        assert len(manager._by_id) == 0

    def test_default_manager(self):
        """Test the auto registration."""
        node1 = Node(1, '192.168.1.1', 1111, None, None)
        node2 = Node(999, '192.168.1.1', 999, None, None) # noqa
        assert node1 in default_manager()._all
        assert default_manager()._by_id.get(1) is node1
        assert len(default_manager()._all) == 2
        assert len(default_manager()._by_id) == 2
