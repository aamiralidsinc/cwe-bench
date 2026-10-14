# Minimal, dependency-free test harness that emits JUnit XML.
# Tests run against the ruby-saml source under /app (the solver's code).
# Fixtures live under /tests/fixtures and are never read from /app, so a
# solver cannot influence the tests by editing the repository.
require 'fileutils'

$LOAD_PATH.unshift('/app/lib')

module SamlTestEnv
  FIX = File.expand_path(File.join(__dir__, '..', 'fixtures'))

  def self.silence_logger
    require 'onelogin/ruby-saml/logging'
    require 'logger'
    require 'stringio'
    OneLogin::RubySaml::Logging.logger = Logger.new(StringIO.new)
  rescue StandardError
    nil
  end

  def self.fixture(name)
    File.read(File.join(FIX, name))
  end
end

class AssertionError < StandardError; end

class TestGroup
  Result = Struct.new(:name, :status, :message, :time)

  def initialize(group)
    @group = group
    @results = []
  end

  def test(name)
    started = Time.now
    begin
      yield
      @results << Result.new(name, :pass, nil, Time.now - started)
      warn "  PASS #{name}"
    rescue AssertionError => e
      @results << Result.new(name, :fail, e.message, Time.now - started)
      warn "  FAIL #{name}: #{e.message}"
    rescue StandardError => e
      @results << Result.new(name, :error, "#{e.class}: #{e.message}", Time.now - started)
      warn "  ERROR #{name}: #{e.class}: #{e.message}"
    end
  end

  def assert(cond, msg = 'assertion failed')
    raise AssertionError, msg unless cond
  end

  def write(path)
    FileUtils.mkdir_p(File.dirname(path))
    failures = @results.count { |r| r.status != :pass }
    xml = +%(<?xml version="1.0" encoding="UTF-8"?>\n)
    xml << %(<testsuite name="#{@group}" tests="#{@results.size}" failures="#{failures}">\n)
    @results.each do |r|
      xml << %(  <testcase classname="#{@group}" name="#{esc(r.name)}" time="#{'%.3f' % r.time}">)
      if r.status == :fail
        xml << %(\n    <failure message="#{esc(r.message)}">#{esc(r.message)}</failure>\n  )
      elsif r.status == :error
        xml << %(\n    <error message="#{esc(r.message)}">#{esc(r.message)}</error>\n  )
      end
      xml << %(</testcase>\n)
    end
    xml << %(</testsuite>\n)
    File.write(path, xml)
    warn "wrote #{path} (#{@results.size} tests, #{failures} failing)"
  end

  private

  def esc(s)
    s.to_s.gsub('&', '&amp;').gsub('<', '&lt;').gsub('>', '&gt;').gsub('"', '&quot;')
  end
end
