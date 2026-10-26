"""A description read by the client must not make it fetch anything it names."""
import asyncio

import pytest

from zeep import Client
from zeep.loader import load_external_async

from support.wire import (
    ENTRY,
    RecordingTransport,
    chameleon_schema,
    forbid_external_settings,
    other_schema,
    secondary_wsdl,
    service_wsdl,
)

WSDL_NS = 'xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"'


def _transport(imports="", types_body="", documents=None):
    docs = dict(documents or {})
    docs[ENTRY] = service_wsdl(types_body=types_body, imports=imports)
    return RecordingTransport(docs)


def test_wsdl_import_of_remote_document_is_refused():
    transport = _transport(
        imports='<wsdl:import %s namespace="http://secondary.test"'
        ' location="http://untrusted.test/secondary.wsdl"/>' % WSDL_NS,
        documents={"http://untrusted.test/secondary.wsdl": secondary_wsdl()},
    )
    with pytest.raises(Exception):
        Client(ENTRY, transport=transport, settings=forbid_external_settings())
    assert "http://untrusted.test/secondary.wsdl" not in transport.loads
    assert transport.loads == [ENTRY]


def test_xsd_import_of_remote_document_is_refused():
    transport = _transport(
        types_body='<xs:import namespace="http://other.test"'
        ' schemaLocation="http://untrusted.test/types.xsd"/>',
        documents={"http://untrusted.test/types.xsd": other_schema()},
    )
    with pytest.raises(Exception):
        Client(ENTRY, transport=transport, settings=forbid_external_settings())
    assert "http://untrusted.test/types.xsd" not in transport.loads
    assert transport.loads == [ENTRY]


def test_relative_include_is_refused():
    transport = _transport(
        types_body='<xs:include schemaLocation="included.xsd"/>',
        documents={"http://primary.test/included.xsd": chameleon_schema()},
    )
    with pytest.raises(Exception):
        Client(ENTRY, transport=transport, settings=forbid_external_settings())
    assert "http://primary.test/included.xsd" not in transport.loads
    assert transport.loads == [ENTRY]


def test_import_namespace_without_location_is_not_fetched():
    transport = _transport(
        types_body='<xs:import namespace="http://untrusted.test/ns"/>',
        documents={"http://untrusted.test/ns": other_schema()},
    )
    with pytest.raises(Exception):
        Client(ENTRY, transport=transport, settings=forbid_external_settings())
    assert "http://untrusted.test/ns" not in transport.loads
    assert transport.loads == [ENTRY]


def test_async_loader_refuses_remote_document():
    transport = RecordingTransport(
        {"http://untrusted.test/types.xsd": other_schema()}
    )
    with pytest.raises(Exception):
        asyncio.run(
            load_external_async(
                "http://untrusted.test/types.xsd",
                transport,
                settings=forbid_external_settings(),
            )
        )
    assert transport.loads == []
