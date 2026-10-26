"""Canned SOAP descriptions and a transport that records every requested location."""
from zeep.settings import Settings

ENTRY = "http://primary.test/service.wsdl"


class RecordingTransport:
    """Serve canned documents and record every location the library asks for."""

    def __init__(self, documents):
        self.documents = dict(documents)
        self.loads = []

    def load(self, url):
        self.loads.append(url)
        if url in self.documents:
            return self.documents[url]
        if "://" not in str(url):
            with open(url, "rb") as fh:
                return fh.read()
        raise KeyError(url)


def forbid_external_settings():
    return Settings(forbid_external=True)


def service_wsdl(types_body="", imports=""):
    """A complete, loadable description with one operation."""
    return (
        '<?xml version="1.0"?>\n'
        '<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"'
        ' xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"'
        ' xmlns:xs="http://www.w3.org/2001/XMLSchema"'
        ' xmlns:tns="http://example.com/svc"'
        ' targetNamespace="http://example.com/svc">'
        + imports
        + "<types>"
        '<xs:schema targetNamespace="http://example.com/svc"'
        ' xmlns:xs="http://www.w3.org/2001/XMLSchema"'
        ' xmlns:tns="http://example.com/svc">'
        + types_body
        + '<xs:element name="ping" type="xs:string"/>'
        "</xs:schema>"
        "</types>"
        '<message name="pingIn"><part name="parameters" element="tns:ping"/></message>'
        '<portType name="P">'
        '<operation name="ping"><input message="tns:pingIn"/></operation>'
        "</portType>"
        '<binding name="B" type="tns:P">'
        '<soap:binding style="document"'
        ' transport="http://schemas.xmlsoap.org/soap/http"/>'
        '<operation name="ping"><soap:operation soapAction="ping"/>'
        '<input><soap:body use="literal"/></input></operation>'
        "</binding>"
        '<service name="S"><port name="p" binding="tns:B">'
        '<soap:address location="http://primary.test/svc"/>'
        "</port></service>"
        "</definitions>"
    )


def secondary_wsdl():
    return (
        '<?xml version="1.0"?>\n'
        '<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"'
        ' targetNamespace="http://secondary.test"/>'
    )


def other_schema():
    return (
        '<?xml version="1.0"?>\n'
        '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"'
        ' targetNamespace="http://other.test">'
        '<xs:element name="other" type="xs:string"/>'
        "</xs:schema>"
    )


def chameleon_schema():
    return (
        '<?xml version="1.0"?>\n'
        '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
        '<xs:element name="included" type="xs:string"/>'
        "</xs:schema>"
    )
