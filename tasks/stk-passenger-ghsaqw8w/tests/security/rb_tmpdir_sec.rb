# Exercise the public temporary-directory helper with a prepared entry.
ws, root = ARGV[0], ARGV[1]
$LOAD_PATH.unshift(File.join(ws, "lib"))
require 'phusion_passenger/utils/tmpdir'
ENV['PASSENGER_TMPDIR'] = root
target = File.join(root, "target")
Dir.mkdir(target) rescue nil
link = File.join(root, "passenger.1.0.#{Process.pid}")
File.symlink(target, link) rescue nil
dir = nil
begin
  dir = PhusionPassenger::Utils.passenger_tmpdir(true)
  File.open(File.join(dir, "probe"), "w") { |f| f.write("x") }
  puts "RETURNED"
rescue Exception => e
  puts "REFUSED #{e.class}"
end
puts "TARGET_PROBE=#{File.exist?(File.join(target, "probe")) ? 'yes' : 'no'}"
if dir
  st = File.lstat(dir)
  puts "RETURNED_IS_DIR=#{st.directory? && st.uid == Process.uid ? 'yes' : 'no'}"
end
