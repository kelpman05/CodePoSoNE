from abc import abstractmethod
from binascii import b2a_hex
from enum import Enum
from typing import List, Optional, Set

from ...queue.manager import Node, some_ids
from ..scene import AbstractScene


class EvilBehaviour(Enum):
    # For Normal nodes
    SendToNoDelegate = 1
    SendToSomeDelegate = 2
    SendToDelegateDifferently = 3

    # For Delegates
    NoForward = 4
    ForwardForge = 5

    # For Leaders
    NoSolving = 6
    IncorrectSolving = 7
    DifferentSolving = 8

    # For Followers
    NoVerification = 9
    IncorrectVerification = 10


class EvilNormalMixIn(AbstractScene):
    behaviour: EvilBehaviour
    delegates_to_forward: Optional[Set[int]]

    def __init__(
        self,
        behaviour: str,
        *args,
        delegates_to_forward: Optional[List[int]] = None,
        **kwargs,
    ) -> None:
        self.behaviour = EvilBehaviour[behaviour]
        assert self.behaviour in {
            EvilBehaviour.SendToNoDelegate,
            EvilBehaviour.SendToSomeDelegate,
            EvilBehaviour.SendToDelegateDifferently,
        }

        self.delegates_to_forward = None
        if self.behaviour in {
            EvilBehaviour.SendToSomeDelegate,
            EvilBehaviour.SendToDelegateDifferently,
        }:
            assert (
                delegates_to_forward is not None
            ), 'delegates_to_forward must be specified to SendToSomeDelegates'
            self.delegates_to_forward = set(delegates_to_forward)
        super(EvilNormalMixIn, self).__init__(*args, **kwargs)

    def normal_send(self):
        data = self.normal_data()
        if self.behaviour == EvilBehaviour.SendToNoDelegate:
            self.logger.info('no data forward to delegates as evil node')
        elif self.behaviour == EvilBehaviour.SendToSomeDelegate:
            assert self.delegates_to_forward is not None
            self.logger.info(
                'data forward to delegates %s exclusively',
                self.delegates_to_forward,
            )
            self.adapter.broadcast(
                data, filter_=some_ids(self.delegates_to_forward)
            )
        else:
            assert self.behaviour == EvilBehaviour.SendToDelegateDifferently
            self.logger.info(
                'data forward to delegates %s normally',
                self.delegates_to_forward,
            )
            assert self.delegates_to_forward is not None
            self.adapter.broadcast(
                data, filter_=some_ids(self.delegates_to_forward)
            )

            for n in self.node_manager.get_delegates():
                assert isinstance(n, Node)
                if n.id in self.delegates_to_forward:
                    continue
                node_data = self.evil_data(n, data)
                self.logger.info(
                    'evil data %r sent to %r', b2a_hex(node_data), n
                )
                self.adapter.send_to(n, node_data)

    @abstractmethod
    def evil_data(self, delegate: Node, normal_data: bytes) -> bytes:
        """ get evil data for a certain delegate

        will be called only when current behaviour is SendToDelegateDifferently
        """
        pass
