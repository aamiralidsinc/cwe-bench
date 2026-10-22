<?php declare(strict_types=1);

/*
 * Hidden functional tests: legitimate binaries that live inside the package (plain
 * files, in-package symlinks that resolve inside the package, and packages whose
 * install path is itself a symlink) must keep installing and keep their executable
 * bit. An over-broad fix that rejects every symlinked or every symlink-installed
 * bin fails here. Expected values are computed in the test.
 */

namespace Composer\Test\Functional;

use Composer\Installer\BinaryInstaller;
use Composer\Downloader\FileDownloader;
use Composer\Util\Filesystem;
use Composer\Test\TestCase;

class BinLegitFunctionalTest extends TestCase
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

    private function pkg(array $binaries): \Composer\Package\BasePackage
    {
        $package = self::getPackage('vendor/pkg', '1.0.0');
        $package->setBinaries($binaries);

        return $package;
    }

    // A plain in-package bin installs and gets a vendor/bin proxy.
    public function testPlainInPackageBinInstalls(): void
    {
        $installPath = $this->vendorDir.'/vendor/pkg';
        self::ensureDirectoryExistsAndClear($installPath);
        file_put_contents($installPath.'/run', "#!/usr/bin/env php\n<?php echo 'ok';\n");
        $installer = new BinaryInstaller($this->io, $this->binDir, 'full', $this->fs);
        $installer->installBinaries($this->pkg(['run']), $installPath);
        self::assertFileExists($this->binDir.'/run', 'a legitimate in-package bin must get a proxy');
    }

    // An in-package bin that is a symlink resolving INSIDE the package still installs.
    public function testInPackageSymlinkBinInstalls(): void
    {
        if (!function_exists('symlink')) {
            $this->markTestSkipped('symlink() unavailable');
        }
        $installPath = $this->vendorDir.'/vendor/pkg';
        self::ensureDirectoryExistsAndClear($installPath.'/lib');
        self::ensureDirectoryExistsAndClear($installPath.'/bin');
        file_put_contents($installPath.'/lib/tool.php', "#!/usr/bin/env php\n<?php echo 'ok';\n");
        if (!@symlink('../lib/tool.php', $installPath.'/bin/tool')) {
            $this->markTestSkipped('symlinks not supported here');
        }
        $installer = new BinaryInstaller($this->io, $this->binDir, 'full', $this->fs);
        $installer->installBinaries($this->pkg(['bin/tool']), $installPath);
        self::assertFileExists($this->binDir.'/tool', 'an in-package symlink bin must still get a proxy');
    }

    // A package whose install path is itself a symlink (as with a path repository) still installs its bins.
    public function testSymlinkedInstallPathBinInstalls(): void
    {
        if (!function_exists('symlink')) {
            $this->markTestSkipped('symlink() unavailable');
        }
        $realPkg = $this->root.'/real/pkg';
        self::ensureDirectoryExistsAndClear($realPkg);
        file_put_contents($realPkg.'/run', "#!/usr/bin/env php\n<?php echo 'ok';\n");
        $installPath = $this->vendorDir.'/vendor/pkg';
        self::ensureDirectoryExistsAndClear(dirname($installPath));
        if (!@symlink($realPkg, $installPath)) {
            $this->markTestSkipped('symlinks not supported here');
        }
        $installer = new BinaryInstaller($this->io, $this->binDir, 'full', $this->fs);
        $installer->installBinaries($this->pkg(['run']), $installPath);
        self::assertFileExists($this->binDir.'/run', 'a bin in a symlink-installed package must still get a proxy');
    }

    // The installer refresh path makes a legitimate in-package bin executable.
    public function testInstallerRefreshMakesInPackageBinExecutable(): void
    {
        $installPath = $this->vendorDir.'/vendor/pkg';
        self::ensureDirectoryExistsAndClear($installPath);
        file_put_contents($installPath.'/run', "#!/bin/sh\necho ok\n");
        chmod($installPath.'/run', 0644);
        clearstatcache();
        $installer = new BinaryInstaller($this->io, $this->binDir, 'full', $this->fs);
        $installer->ensureBinariesExecutable($this->pkg(['run']), $installPath);
        clearstatcache();
        self::assertTrue(is_executable($installPath.'/run'), 'a legitimate in-package bin must be made executable');
    }

    // The downloader refresh path makes a legitimate in-package bin executable.
    public function testDownloaderRefreshMakesInPackageBinExecutable(): void
    {
        $installPath = $this->vendorDir.'/vendor/pkg';
        self::ensureDirectoryExistsAndClear($installPath);
        file_put_contents($installPath.'/run', "#!/bin/sh\necho ok\n");
        chmod($installPath.'/run', 0644);
        clearstatcache();
        $httpDownloader = $this->getMockBuilder('Composer\Util\HttpDownloader')->disableOriginalConstructor()->getMock();
        $downloader = new FileDownloader($this->io, $this->getConfig(['vendor-dir' => $this->vendorDir]), $httpDownloader);
        $downloader->ensureBinariesExecutable($this->pkg(['run']), $installPath);
        clearstatcache();
        self::assertTrue(is_executable($installPath.'/run'), 'a legitimate in-package bin must be made executable');
    }
}
