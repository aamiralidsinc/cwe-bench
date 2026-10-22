<?php declare(strict_types=1);

/*
 * Hidden security tests for the bin-path containment property. Each test drives a
 * real public install/download entry point with a package whose declared binary
 * resolves OUTSIDE its own install directory, and asserts the operation has no
 * side effect on the out-of-package file (its mode is untouched) and creates no
 * vendor/bin proxy for it. They fail on the vulnerable code and pass on a correct
 * fix. The expected values and clean-up are computed here, not in product code.
 */

namespace Composer\Test\Security;

use Composer\Installer\BinaryInstaller;
use Composer\Downloader\FileDownloader;
use Composer\Util\Filesystem;
use Composer\Util\Http\Response;
use Composer\Test\TestCase;

class BinEscapeSecurityTest extends TestCase
{
    /** @var Filesystem */
    private $fs;
    /** @var string */
    private $root;
    /** @var string */
    private $vendorDir;
    /** @var string */
    private $binDir;
    /** @var \Composer\IO\IOInterface&\PHPUnit\Framework\MockObject\MockObject */
    private $io;

    protected function setUp(): void
    {
        $this->fs = new Filesystem();
        $this->root = self::getUniqueTmpDirectory();
        $this->vendorDir = $this->root.'/vendor';
        $this->binDir = $this->root.'/vendor/bin';
        self::ensureDirectoryExistsAndClear($this->vendorDir);
        self::ensureDirectoryExistsAndClear($this->binDir);
        $this->io = $this->getMockBuilder('Composer\IO\IOInterface')->getMock();
    }

    protected function tearDown(): void
    {
        parent::tearDown();
        $this->fs->removeDirectory($this->root);
    }

    private function makeVictim(): array
    {
        $victim = $this->root.'/outside_victim';
        file_put_contents($victim, "#!/bin/sh\necho x\n");
        chmod($victim, 0600);
        clearstatcache();

        return [$victim, fileperms($victim)];
    }

    private function assertUntouched(string $victim, int $modeBefore, string $proxyName): void
    {
        clearstatcache();
        self::assertSame($modeBefore, fileperms($victim), 'an out-of-package bin must not be chmod\'d');
        self::assertFileDoesNotExist($this->binDir.'/'.$proxyName, 'no vendor/bin proxy may be created for an out-of-package bin');
    }

    private function pkg(array $binaries): \Composer\Package\BasePackage
    {
        $package = self::getPackage('attacker/pkg', '1.0.0');
        $package->setBinaries($binaries);

        return $package;
    }

    // L1: an in-package bin that is a symlink pointing outside the package.
    public function testInstallBinariesRejectsSymlinkEscapingPackage(): void
    {
        if (!function_exists('symlink')) {
            $this->markTestSkipped('symlink() unavailable');
        }
        [$victim, $mode] = $this->makeVictim();
        $installPath = $this->vendorDir.'/attacker/pkg';
        self::ensureDirectoryExistsAndClear($installPath.'/bin');
        if (!@symlink($victim, $installPath.'/bin/tool')) {
            $this->markTestSkipped('symlinks not supported here');
        }
        $installer = new BinaryInstaller($this->io, $this->binDir, 'full', $this->fs);
        $installer->installBinaries($this->pkg(['bin/tool']), $installPath);
        $this->assertUntouched($victim, $mode, 'tool');
    }

    // L2: a ".." bin string that reaches the installer without the solver-time check
    // (e.g. a reinstall built straight from installed.json).
    public function testInstallBinariesRejectsTraversingMetadata(): void
    {
        [$victim, $mode] = $this->makeVictim();
        $installPath = $this->vendorDir.'/attacker/pkg';
        self::ensureDirectoryExistsAndClear($installPath);
        $installer = new BinaryInstaller($this->io, $this->binDir, 'full', $this->fs);
        $installer->installBinaries($this->pkg(['../../../outside_victim']), $installPath);
        $this->assertUntouched($victim, $mode, 'outside_victim');
    }

    // L3: the single-file downloader chmods a package's bins itself.
    public function testFileDownloaderDoesNotChmodBinOutsidePackage(): void
    {
        [$victim, $mode] = $this->makeVictim();
        $installPath = $this->vendorDir.'/attacker/pkg';

        $package = $this->pkg(['../../../outside_victim']);
        $package->setDistUrl('http://example.com/script.js');

        $httpDownloader = $this->getMockBuilder('Composer\Util\HttpDownloader')->disableOriginalConstructor()->getMock();
        $httpDownloader->expects($this->any())->method('addCopy')
            ->will($this->returnValue(\React\Promise\resolve(new Response(['url' => 'http://example.org/'], 200, [], 'file~'))));
        $downloader = new FileDownloader($this->io, $this->getConfig(['vendor-dir' => $this->vendorDir]), $httpDownloader);

        $method = new \ReflectionMethod($downloader, 'getFileName');
        (\PHP_VERSION_ID < 80100) and $method->setAccessible(true);
        $tmpFile = $method->invoke($downloader, $package, $installPath);
        $this->fs->ensureDirectoryExists(dirname($tmpFile));
        file_put_contents($tmpFile, 'downloaded');

        $downloader->install($package, $installPath, false);

        clearstatcache();
        self::assertSame($mode, fileperms($victim), 'an out-of-package bin must not be chmod\'d by the downloader');
    }

    // S1: the installer's standalone "refresh executable bit" path.
    public function testEnsureBinariesExecutableInstallerRejectsEscape(): void
    {
        if (!function_exists('symlink')) {
            $this->markTestSkipped('symlink() unavailable');
        }
        [$victim, $mode] = $this->makeVictim();
        $installPath = $this->vendorDir.'/attacker/pkg';
        self::ensureDirectoryExistsAndClear($installPath.'/bin');
        if (!@symlink($victim, $installPath.'/bin/tool')) {
            $this->markTestSkipped('symlinks not supported here');
        }
        $installer = new BinaryInstaller($this->io, $this->binDir, 'full', $this->fs);
        $installer->ensureBinariesExecutable($this->pkg(['bin/tool']), $installPath);
        clearstatcache();
        self::assertSame($mode, fileperms($victim), 'an out-of-package bin must not be chmod\'d on refresh');
    }

    // S2: the downloader's standalone "refresh executable bit" path (path-repository installs).
    public function testEnsureBinariesExecutableDownloaderRejectsEscape(): void
    {
        [$victim, $mode] = $this->makeVictim();
        $installPath = $this->vendorDir.'/attacker/pkg';
        self::ensureDirectoryExistsAndClear($installPath);

        $httpDownloader = $this->getMockBuilder('Composer\Util\HttpDownloader')->disableOriginalConstructor()->getMock();
        $downloader = new FileDownloader($this->io, $this->getConfig(['vendor-dir' => $this->vendorDir]), $httpDownloader);
        $downloader->ensureBinariesExecutable($this->pkg(['../../../outside_victim']), $installPath);

        clearstatcache();
        self::assertSame($mode, fileperms($victim), 'an out-of-package bin must not be chmod\'d on refresh');
    }
}
