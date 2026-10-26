'use strict';
// Test double for better-sqlite3. It records every database the product opens (and the options it
// passes) so a suite can assert which file the product actually used, without loading a native
// module. The functional suites assert the legitimate values still arrive here unchanged.
const records = [];

class FakeDatabase {
  constructor(file, options) {
    this.file = file;
    this.options = options || {};
    records.push({ file, options: this.options });
  }

  prepare() {
    return {
      all: () => [{ ok: 1 }],
      get: () => ({ ok: 1 }),
      run: () => ({ changes: 1, lastInsertRowid: 1 }),
    };
  }

  exec() {
    return this;
  }

  close() {
    return this;
  }
}

FakeDatabase.__records = records;
FakeDatabase.__reset = () => {
  records.length = 0;
};

module.exports = FakeDatabase;
module.exports.default = FakeDatabase;
module.exports.__records = records;
module.exports.__reset = FakeDatabase.__reset;
