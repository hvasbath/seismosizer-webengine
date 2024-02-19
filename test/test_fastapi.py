from seismosizer_webengine.remote import CommunicationTarget, CommunicationSource
from pyrocko.gf import Target, source_classes, CombiSource


def test_target():
    ctarget = CommunicationTarget.from_pyrocko(Target())
    ctarget.to_pyrocko()


def test_source():
    for source in source_classes:
        if source.__name__ != CombiSource.__name__:
            pyrocko_source = source()
            shash = pyrocko_source._hash()

            csource = CommunicationSource.from_pyrocko(pyrocko_source)
            recsource = csource.to_pyrocko()
            assert shash == recsource._hash()
            
