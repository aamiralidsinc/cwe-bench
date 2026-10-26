ws, root = ARGV[0], ARGV[1]
$LOAD_PATH.unshift(File.join(ws, "lib"))
require 'phusion_passenger/utils/tmpdir'
ENV['PASSENGER_TMPDIR'] = root
PhusionPassenger::Utils.passenger_tmpdir = nil
d = PhusionPassenger::Utils.passenger_tmpdir(false)
puts "PATH=#{d}"
puts "EXISTS=#{File.exist?(d)}"
