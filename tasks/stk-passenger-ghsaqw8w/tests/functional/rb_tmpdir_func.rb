ws, root = ARGV[0], ARGV[1]
$LOAD_PATH.unshift(File.join(ws, "lib"))
require 'phusion_passenger/utils/tmpdir'
ENV['PASSENGER_TMPDIR'] = root
PhusionPassenger::Utils.passenger_tmpdir = nil
d1 = PhusionPassenger::Utils.passenger_tmpdir(true)
st = File.lstat(d1)
puts "CREATED=#{d1}"
puts "DIR=#{st.directory?}"
puts "UIDOK=#{st.uid == Process.uid}"
PhusionPassenger::Utils.passenger_tmpdir = nil
d2 = PhusionPassenger::Utils.passenger_tmpdir(true)
puts "REUSED=#{d2 == d1}"
puts "SUBDIRS=#{File.directory?(File.join(d1, 'generation-0'))}"
