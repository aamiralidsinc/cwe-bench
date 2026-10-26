"""Reading descriptions keeps working exactly as it does today."""
from zeep import Client
from zeep.settings import Settings

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


def test_entry_document_still_loads_when_external_references_are_forbidden():
    transport = _transport()
    client = Client(ENTRY, transport=transport, settings=forbid_external_settings())
    assert client.get_element("{http://example.com/svc}ping") is not None
    assert transport.loads == [ENTRY]


def test_default_configuration_loads_a_multi_document_description():
    transport = _transport(
        imports='<wsdl:import %s namespace="http://secondary.test"'
        ' location="http://secondary.test/secondary.wsdl"/>' % WSDL_NS,
        types_body='<xs:import namespace="http://other.test"'
        ' schemaLocation="http://other.test/types.xsd"/>',
        documents={
            "http://secondary.test/secondary.wsdl": secondary_wsdl(),
            "http://other.test/types.xsd": other_schema(),
        },
    )
    client = Client(ENTRY, transport=transport, settings=Settings())
    assert "http://secondary.test/secondary.wsdl" in transport.loads
    assert "http://other.test/types.xsd" in transport.loads
    assert client.get_element("{http://example.com/svc}ping") is not None


def test_default_configuration_resolves_a_relative_include():
    transport = _transport(
        types_body='<xs:include schemaLocation="included.xsd"/>',
        documents={"http://primary.test/included.xsd": chameleon_schema()},
    )
    client = Client(ENTRY, transport=transport, settings=Settings())
    assert "http://primary.test/included.xsd" in transport.loads
    assert client.get_element("{http://example.com/svc}included") is not None


def test_a_local_entry_document_still_loads_when_external_references_are_forbidden(
    tmp_path,
):
    path = tmp_path / "local.wsdl"
    path.write_text(service_wsdl())
    transport = RecordingTransport({})
    client = Client(str(path), transport=transport, settings=forbid_external_settings())
    assert client.get_element("{http://example.com/svc}ping") is not None
