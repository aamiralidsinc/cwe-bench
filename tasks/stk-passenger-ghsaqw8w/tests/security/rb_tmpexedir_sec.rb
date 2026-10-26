# Exercise the public executable-directory helper with a prepared entry.
ws, root = ARGV[0], ARGV[1]
ENV['TMPDIR'] = root
$LOAD_PATH.unshift(File.join(ws, "lib"))
require 'phusion_passenger'
PhusionPassenger.locate_directories
require 'phusion_passenger/platform_info'
target = File.join(root, "victim")
File.open(target, "w") { |f| f.write("ORIGINAL") }
File.chmod(0644, target)
name = "test-exe.#{Process.pid}.#{Thread.current.object_id}"
File.symlink(target, File.join(root, name)) rescue nil
begin
  PhusionPassenger::PlatformInfo.tmpexedir
rescue Exception => e
  puts "REFUSED #{e.class}"
end
puts "TARGET=#{File.read(target)}"
puts "MODE=#{(File.stat(target).mode & 07777).to_s(8)}"
