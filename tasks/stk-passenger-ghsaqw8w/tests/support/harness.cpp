// Neutral driver for the product's public server-instance-directory API.
#include <ServerInstanceDir.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <pwd.h>
#include <grp.h>
#include <cerrno>
#include <cstring>
#include <string>
#include <iostream>

using namespace Passenger;
using namespace std;

static string userName() {
    struct passwd *p = getpwuid(geteuid());
    return p ? string(p->pw_name) : string("nobody");
}
static string groupName() {
    struct group *g = getgrgid(getegid());
    return g ? string(g->gr_name) : string("nogroup");
}
static int refused(const string &msg) {
    cout << "RESULT=refused\nMSG=" << msg << "\n";
    return 3;
}
static int ok(const string &msg) {
    cout << "RESULT=ok\nMSG=" << msg << "\n";
    return 0;
}
static void makeGeneration(ServerInstanceDir &dir) {
    ServerInstanceDir::GenerationPtr g =
        dir.newGeneration(false, userName(), groupName(), geteuid(), getegid());
    g->detach();
}

int main(int argc, char **argv) {
    if (argc < 2) { cout << "RESULT=error\nMSG=usage\n"; return 2; }
    string mode = argv[1];
    try {
        if (mode == "construct" && argc == 3) {
            ServerInstanceDir dir(argv[2]);
            return ok(dir.getPath());
        } else if (mode == "gen" && argc == 3) {
            ServerInstanceDir dir(argv[2]);
            makeGeneration(dir);
            return ok("generation created");
        } else if (mode == "swapgen" && argc == 4) {
            string inst = argv[2], target = argv[3];
            ServerInstanceDir dir(inst);
            dir.detach();
            if (rmdir(inst.c_str()) != 0) { cout << "RESULT=error\nMSG=rmdir:" << strerror(errno) << "\n"; return 2; }
            if (symlink(target.c_str(), inst.c_str()) != 0) { cout << "RESULT=error\nMSG=symlink:" << strerror(errno) << "\n"; return 2; }
            makeGeneration(dir);
            return ok("generation created");
        } else if (mode == "swapdestroy" && argc == 4) {
            string inst = argv[2], target = argv[3];
            ServerInstanceDir dir(inst);
            if (rmdir(inst.c_str()) != 0) { cout << "RESULT=error\nMSG=rmdir:" << strerror(errno) << "\n"; return 2; }
            if (symlink(target.c_str(), inst.c_str()) != 0) { cout << "RESULT=error\nMSG=symlink:" << strerror(errno) << "\n"; return 2; }
            try {
                dir.destroy();
            } catch (const std::exception &e) {
                dir.detach();
                return refused(e.what());
            }
            dir.detach();
            return ok("destroy returned");
        }
        cout << "RESULT=error\nMSG=unknown mode\n";
        return 2;
    } catch (const std::exception &e) {
        return refused(e.what());
    }
}
