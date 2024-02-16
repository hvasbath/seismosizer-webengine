from seismosizer_webengine.remote import CommunicationTarget
from pyrocko.gf import Target


def test_target():
    ctarget = CommunicationTarget.from_pyrocko(Target())
    print(ctarget.to_pyrocko())

