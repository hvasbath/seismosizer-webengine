from remote import CommunicationTarget
from pyrocko.gf import Target


def test_target():
    ctarget = CommunicationTarget.from_pyrocko(Target())
    ctarget.to_pyrocko()

