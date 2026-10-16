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

# Test-only spy on the XML parsers the library can use (REXML and Nokogiri). While armed,
# it records every parse of a source at least `min_bytes` long, so a test can tell
# "refused before parsing" apart from "parsed, then refused". (2026-10-16 repair)
module ParseSpy
  @armed = false
  @min = 0
  @hits = []
  class << self
    attr_reader :hits

    def watch(min_bytes)
      @hits = []
      @min = min_bytes
      @armed = true
      yield
    ensure
      @armed = false
    end

    def seen(src, via)
      return unless @armed
      size = begin
        if src.respond_to?(:bytesize) then src.bytesize
        elsif src.respond_to?(:size) then src.size.to_i
        else 0
        end
      rescue StandardError
        0
      end
      @hits << via if size >= @min
    end
  end
end

module RexmlParseSpy
  def stream=(source)
    ParseSpy.seen(source, 'REXML')
    super
  end
end
REXML::Parsers::BaseParser.prepend(RexmlParseSpy)

module NokogiriParseSpy
  def parse(*args, **kw, &blk)
    ParseSpy.seen(args.first, 'Nokogiri')
    super
  end
end
Nokogiri::XML::Document.singleton_class.prepend(NokogiriParseSpy)

# True when the entry point refuses the message by raising (any error: the instruction
# requires rejection, not a particular error class or wording). Running out of memory
# or being interrupted is not a rejection.
def rejected?
  yield
  false
rescue NoMemoryError, SignalException, SystemExit
  false
rescue Exception # rubocop:disable Lint/RescueException
  true
end

# Runs the entry point with the parse spy armed. Returns [rejected, parsers that
# parsed a source of at least `min_bytes`].
def refused_unparsed(min_bytes, &blk)
  rej = nil
  ParseSpy.watch(min_bytes) { rej = rejected?(&blk) }
  [rej, ParseSpy.hits.uniq]
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
# must be refused rather than processed: the entry point raises, and the expanded
# document is never handed to an XML parser. ----

BOMB_INFLATED = 600_000

def bomb_xml(inflated_bytes = BOMB_INFLATED)
  '<a>' + ('A' * inflated_bytes) + '</a>'
end

def bomb_blob(inflated_bytes = BOMB_INFLATED)
  Base64.strict_encode64(Zlib::Deflate.deflate(bomb_xml(inflated_bytes), 9)[2..-5])
end

g.test('resource: decompression bomb via a redirect-binding message is rejected') do
  blob = bomb_blob
  rej, parsed = refused_unparsed(BOMB_INFLATED) { OneLogin::RubySaml::SloLogoutrequest.new(blob) }
  g.assert(rej, 'a small compressed message that expands past the configured limit was processed')
  g.assert(parsed.empty?, "the expanded message was parsed (#{parsed.join(', ')}) before being rejected")
end

g.test('resource: decompression bomb via a response message is rejected') do
  blob = bomb_blob
  settings = OneLogin::RubySaml::Settings.new
  rej, parsed = refused_unparsed(BOMB_INFLATED) { OneLogin::RubySaml::Response.new(blob, settings: settings) }
  g.assert(rej, 'a small compressed response that expands past the configured limit was processed')
  g.assert(parsed.empty?, "the expanded response was parsed (#{parsed.join(', ')}) before being rejected")
end

# ---- Resource exhaustion: a greatly oversized message must be refused up front,
# whatever its encoding: the entry point raises, never parses it, and spends far
# less than one scanning pass over the input. The input is well-formed XML and not
# base64, so the unfixed library parses it without error. The time bound is relative
# to a whitespace-stripping pass over the same input measured here, so it does not
# depend on machine speed; a size check up front costs microseconds. ----

g.test('resource: oversized message is rejected before expensive processing') do
  require 'benchmark'
  oversized = '<x>' + ("m m\t\n " * 1_400_000) + '</x>' # ~8.4 MB, not base64
  scan_cost = Array.new(3) { Benchmark.realtime { oversized.gsub(/\s/, '') } }.min
  results = Array.new(2) do
    rej = parsed = nil
    t = Benchmark.realtime do
      rej, parsed = refused_unparsed(oversized.bytesize) { OneLogin::RubySaml::SloLogoutrequest.new(oversized) }
    end
    [rej, parsed, t]
  end
  g.assert(results.all? { |r| r[0] },
           'an oversized message was accepted/processed instead of being rejected')
  parsed = results.flat_map { |r| r[1] }.uniq
  g.assert(parsed.empty?, "the oversized message was parsed (#{parsed.join(', ')}) before being rejected")
  best = results.map { |r| r[2] }.min
  g.assert(best < 0.2 * scan_cost,
           format('rejecting the oversized message took %.3f s, not far below one scanning pass ' \
                  'over it (%.3f s): it was scanned/processed before the size limit was applied',
                  best, scan_cost))
end

g.write('/logs/verifier/security/results.xml')
