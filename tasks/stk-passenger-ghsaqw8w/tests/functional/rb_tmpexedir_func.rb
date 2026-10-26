ws, root = ARGV[0], ARGV[1]
ENV['TMPDIR'] = root
$LOAD_PATH.unshift(File.join(ws, "lib"))
require 'phusion_passenger'
PhusionPassenger.locate_directories
require 'phusion_passenger/platform_info'
dir = PhusionPassenger::PlatformInfo.tmpexedir
f = File.join(dir, "check-#{Process.pid}.sh")
File.open(f, "w") { |io| io.puts("#!/bin/sh\nexit 0") }
File.chmod(0755, f)
ok = system(f)
puts "DIR=#{dir}"
puts "EXEC=#{ok ? 'yes' : 'no'}"
puts "DIRWRITABLE=#{File.writable?(dir)}"
