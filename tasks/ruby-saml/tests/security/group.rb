# Security (exploit) tests. Each drives a real public ruby-saml entry point as a
# relying party would and asserts the malicious input is BLOCKED.
# On vulnerable code these FAIL (the attack succeeds); on fixed code they PASS.
require_relative '../lib/harness'
require 'onelogin/ruby-saml'
require 'base64'
require 'zlib'
require 'openssl'
SamlTestEnv.silence_logger

g = TestGroup.new('security')

cert_pem = SamlTestEnv.fixture('ruby-saml.crt')
fingerprint = OpenSSL::Digest::SHA1.new(OpenSSL::X509::Certificate.new(cert_pem).to_der).hexdigest
base = SamlTestEnv.fixture('response_with_signed_assertion_3.xml')
signed_id = 'pfx7fca52d6-8991-5d99-3147-4f9d7c278d78' # ID of the legitimately signed assertion in the fixture

# A relying party verifying the signature on a received SAML Response document.
def verifies?(xml, fingerprint)
  OneLogin::RubySaml::Response.new(Base64.encode64(xml)).document.validate_document(fingerprint, true)
rescue StandardError
  false
end

# True when the given oversized/compressed message is refused by the size guard.
def size_rejected?
  yield
  false
rescue OneLogin::RubySaml::ValidationError => e
  e.message =~ /exceed/i ? true : false
rescue StandardError
  false
end

# ---- Signature wrapping: a stolen IdP-signed assertion is replayed alongside an
# attacker-controlled element that carries the same signed identifier. The
# signature must not be accepted for such an ambiguous document. ----

g.test('wrapping: duplicate signed identifier on a second assertion is rejected') do
  real = base[/<saml:Assertion.*<\/saml:Assertion>/m]
  forged = real.sub('someone@example.org', 'attacker@evil.example')
  payload = base.sub(real, real + forged)
  g.assert(!verifies?(payload, fingerprint),
           'signature accepted for a response with two elements sharing the signed identifier')
end

g.test('wrapping: duplicate signed identifier on an injected element is rejected') do
  decoy = %(<Decoy xmlns="urn:example:decoy" ID="#{signed_id}">x</Decoy>)
  payload = base.sub('</samlp:Response>', decoy + '</samlp:Response>')
  g.assert(!verifies?(payload, fingerprint),
           'signature accepted for a response where the signed identifier appears on more than one element')
end

# ---- Resource exhaustion: a tiny compressed message that inflates to a huge one
# must be refused before it is expanded/processed. ----

def bomb_blob(inflated_bytes = 600_000)
  xml = '<a>' + ('A' * inflated_bytes) + '</a>'
  Base64.strict_encode64(Zlib::Deflate.deflate(xml, 9)[2..-5])
end

g.test('resource: decompression bomb via a redirect-binding message is rejected') do
  blob = bomb_blob
  g.assert(size_rejected? { OneLogin::RubySaml::SloLogoutrequest.new(blob) },
           'a small compressed message that expands past the configured limit was processed')
end

g.test('resource: decompression bomb via a response message is rejected') do
  blob = bomb_blob
  settings = OneLogin::RubySaml::Settings.new
  g.assert(size_rejected? { OneLogin::RubySaml::Response.new(blob, settings: settings) },
           'a small compressed response that expands past the configured limit was processed')
end

# ---- Resource exhaustion: an oversized message must be refused regardless of
# whether it is base64-encoded, before expensive scanning/parsing. ----

g.test('resource: oversized message is rejected before expensive processing') do
  oversized = '<x>' + ('m \t<>' * 60_000) + '</x>' # > default limit, not base64
  g.assert(size_rejected? { OneLogin::RubySaml::SloLogoutrequest.new(oversized) },
           'an oversized message was accepted/processed instead of being rejected by the size guard')
end

g.write('/logs/verifier/security/results.xml')
