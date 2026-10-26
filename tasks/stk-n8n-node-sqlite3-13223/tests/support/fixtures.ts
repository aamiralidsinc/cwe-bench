import fs from 'fs';
import os from 'os';
import path from 'path';

/** A unique, real directory outside the product tree for one case; the case removes it. */
export function makeCaseDir(): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'sqlite-path-guard-'));
}

export function removeCaseDir(dir: string): void {
  fs.rmSync(dir, { recursive: true, force: true });
}

export function makeFile(file: string, content = 'fixture'): string {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content);
  return file;
}
