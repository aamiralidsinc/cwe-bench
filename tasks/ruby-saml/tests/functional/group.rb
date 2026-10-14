# Functional tests: the legitimate SAML features must keep working. A fix that
# over-blocks or disables signature validation / message decoding fails these.
# These PASS on both the vulnerable and the fixed code.
require_relative '../lib/harness'
require 'onelogin/ruby-saml'
require 'base64'
require 'zlib'
require 'openssl'
SamlTestEnv.silence_logger

g = TestGroup.new('functional')

cert_pem = SamlTestEnv.fixture('ruby-saml.crt')
fingerprint = OpenSSL::Digest::SHA1.new(OpenSSL::X509::Certificate.new(cert_pem).to_der).hexdigest
r3 = SamlTestEnv.fixture('response_with_signed_assertion_3.xml')
rmsg = SamlTestEnv.fixture('response_with_signed_message_and_assertion.xml')

def doc_for(xml)
  OneLogin::RubySaml::Response.new(Base64.encode64(xml)).document
end

g.test('a legitimately signed assertion verifies') do
  g.assert(doc_for(r3).validate_document(fingerprint, true) == true,
           'a validly signed SAML Response was rejected')
end

g.test('a legitimately signed message-and-assertion response verifies') do
  g.assert(doc_for(rmsg).validate_document(fingerprint, true) == true,
           'a validly signed SAML Response (message signature) was rejected')
end

g.test('full relying-party validation accepts a valid signed response') do
  settings = OneLogin::RubySaml::Settings.new
  settings.idp_cert = cert_pem
  opts = { settings: settings, skip_conditions: true, skip_subject_confirmation: true,
           skip_authnstatement: true, skip_destination: true, skip_audience: true,
           skip_recipient_check: true, allowed_clock_drift: 1 }
  resp = OneLogin::RubySaml::Response.new(Base64.encode64(r3), opts)
  g.assert(resp.is_valid? == true, "is_valid? returned false (errors: #{resp.errors.inspect})")
end

g.test('the signed response exposes the expected NameID') do
  resp = OneLogin::RubySaml::Response.new(Base64.encode64(r3))
  g.assert(resp.name_id == 'someone@example.org', "unexpected NameID: #{resp.name_id.inspect}")
end

g.test('a normal compressed redirect-binding message decodes') do
  xml = %(<samlp:LogoutRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" ) +
        %(xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" ID="_abc" Version="2.0" ) +
        %(IssueInstant="2024-01-01T00:00:00Z"><saml:Issuer>idp.example.com</saml:Issuer>) +
        %(<saml:NameID>user@example.com</saml:NameID></samlp:LogoutRequest>)
  blob = Base64.strict_encode64(Zlib::Deflate.deflate(xml, 9)[2..-5])
  slo = OneLogin::RubySaml::SloLogoutrequest.new(blob)
  g.assert(slo.name_id == 'user@example.com', "normal compressed message mis-decoded: #{slo.name_id.inspect}")
end

g.test('a normal base64 message is processed') do
  xml = %(<samlp:LogoutResponse xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" ) +
        %(xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" ID="_r1" Version="2.0" ) +
        %(IssueInstant="2024-01-01T00:00:00Z" InResponseTo="_abc"><saml:Issuer>idp.example.com</saml:Issuer>) +
        %(<samlp:Status><samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/></samlp:Status></samlp:LogoutResponse>)
  resp = OneLogin::RubySaml::Logoutresponse.new(Base64.strict_encode64(xml))
  g.assert(resp.in_response_to == '_abc', "normal base64 message mis-processed: #{resp.in_response_to.inspect}")
end

g.write('/logs/verifier/functional/results.xml')
