// Functional tests: legitimate transformations keep working exactly as today.
// All of these PASS on the vulnerable library and must keep passing after the fix.
import 'reflect-metadata';
import { Exclude, Expose, Type, plainToInstance, plainToClassFromExist, instanceToPlain } from 'class-transformer';

class Account {
  name: string;

  @Expose({ name: 'display_name' })
  displayName: string;

  @Expose({ name: 'credit_limit', groups: ['staff'] })
  creditLimit: number = 0;

  @Expose({ name: 'is_admin' })
  @Exclude({ toClassOnly: true })
  isAdmin: boolean = false;

  @Expose({ name: 'beta_access', since: 2 })
  betaAccess: boolean = false;

  @Exclude({ toPlainOnly: true })
  password: string;
}

class Order {
  reference: string;

  @Type(() => Account)
  buyer: Account;

  @Type(() => Account)
  approvers: Account[];
}

describe('renamed and restricted properties', () => {
  it('unrestricted renamed property is read from and written to its JSON name', () => {
    const acc = plainToInstance(Account, { name: 'eve', display_name: 'Eve E.' }, { groups: ['customer'] });
    expect(acc).toBeInstanceOf(Account);
    expect(acc.displayName).toBe('Eve E.');
    const plain = instanceToPlain(acc, { groups: ['customer'] });
    expect(plain.display_name).toBe('Eve E.');
    expect(plain.name).toBe('eve');
  });

  it('group-restricted renamed property is read for a call with that group', () => {
    const acc = plainToInstance(Account, { name: 'sam', credit_limit: 50000 }, { groups: ['staff'] });
    expect(acc.creditLimit).toBe(50000);
    const order = plainToInstance(
      Order,
      { buyer: { credit_limit: 10 }, approvers: [{ credit_limit: 20 }] },
      { groups: ['staff'] }
    );
    expect(order.buyer.creditLimit).toBe(10);
    expect(order.approvers[0].creditLimit).toBe(20);
  });

  it('version-restricted renamed property is read for a recent-version call', () => {
    const acc = plainToInstance(Account, { beta_access: true }, { version: 2 });
    expect(acc.betaAccess).toBe(true);
  });

  it('exposed properties are read when only exposed properties are read', () => {
    const acc = plainToInstance(
      Account,
      { display_name: 'Eve', credit_limit: 7, unknown: 1 },
      { groups: ['staff'], excludeExtraneousValues: true }
    );
    expect(acc.displayName).toBe('Eve');
    expect(acc.creditLimit).toBe(7);
    expect((acc as any).unknown).toBeUndefined();
  });

  it('output keeps its JSON names, groups and one-direction exclusions', () => {
    const acc = new Account();
    acc.name = 'eve';
    acc.creditLimit = 300;
    acc.isAdmin = true;
    acc.password = 'secret';
    const staff = instanceToPlain(acc, { groups: ['staff'] });
    expect(staff.credit_limit).toBe(300);
    expect(staff.is_admin).toBe(true);
    expect(staff).not.toHaveProperty('password');
    const customer = instanceToPlain(acc, { groups: ['customer'] });
    expect(customer).not.toHaveProperty('credit_limit');
    expect(customer.is_admin).toBe(true);
    const plain = instanceToPlain(acc);
    expect(plain).not.toHaveProperty('credit_limit');
  });

  it('input naming a restricted property is still transformed: no error, other values set', () => {
    let acc: Account;
    expect(() => {
      acc = plainToInstance(
        Account,
        { name: 'eve', display_name: 'Eve', credit_limit: 50000, is_admin: true, password: 'pw' },
        { groups: ['customer'] }
      );
    }).not.toThrow();
    expect(acc.name).toBe('eve');
    expect(acc.displayName).toBe('Eve');
    expect(acc.password).toBe('pw');
  });

  it('existing object is updated through its unrestricted properties', () => {
    const existing = new Account();
    existing.name = 'eve';
    existing.creditLimit = 100;
    plainToClassFromExist(existing, { display_name: 'New', credit_limit: 500 }, { groups: ['staff'] });
    expect(existing.displayName).toBe('New');
    expect(existing.creditLimit).toBe(500);
  });
});

class Member {
  name: string;

  @Expose({ name: 'spend_cap' })
  spendCap: number = 100;
}

class ManagedMember extends Member {
  @Expose({ name: 'spend_cap', groups: ['staff'] })
  spendCap: number = 100;
}

describe('subclasses that declare an inherited property again', () => {
  it('the base class keeps its own declaration', () => {
    const m = plainToInstance(Member, { name: 'eve', spend_cap: 250 }, { groups: ['customer'] });
    expect(m.spendCap).toBe(250);
    const n = plainToInstance(Member, { spend_cap: 300 });
    expect(n.spendCap).toBe(300);
    expect(instanceToPlain(n).spend_cap).toBe(300);
  });

  it('the subclass property is read for a call with the right group', () => {
    const m = plainToInstance(ManagedMember, { name: 'sam', spend_cap: 900 }, { groups: ['staff'] });
    expect(m.name).toBe('sam');
    expect(m.spendCap).toBe(900);
    expect(instanceToPlain(m, { groups: ['staff'] }).spend_cap).toBe(900);
  });
});

@Exclude()
class Resource {
  @Expose()
  id: string;

  ownerId: string = 'system';
}

class Document extends Resource {
  @Expose()
  title: string;

  @Expose({ name: 'page_count' })
  pageCount: number;

  locked: boolean = false;
}

class Contract extends Document {
  @Expose()
  party: string;
}

class Folder {
  name: string;

  @Type(() => Document)
  docs: Document[];

  @Type(() => Resource, {
    discriminator: {
      property: 'kind',
      subTypes: [
        { value: Document, name: 'document' },
        { value: Contract, name: 'contract' },
      ],
    },
    keepDiscriminatorProperty: false,
  })
  pinned: Resource;
}

class Note {
  id: string;
  text: string;
  internal: string;
}

class Memo extends Note {
  author: string;
}

describe('classes excluded as a whole and their subclasses', () => {
  it('the excluded class itself reads and writes only what it exposes', () => {
    const r = plainToInstance(Resource, { id: 'r1', ownerId: 'eve' });
    expect(r.id).toBe('r1');
    expect(r.ownerId).toBe('system');
    expect(instanceToPlain(r)).toEqual({ id: 'r1' });
  });

  it('subclass objects read and write every property exposed along the way', () => {
    const c = plainToInstance(Contract, { id: 'c1', title: 'T', page_count: 3, party: 'ACME' });
    expect(c).toBeInstanceOf(Contract);
    expect(c.id).toBe('c1');
    expect(c.title).toBe('T');
    expect(c.pageCount).toBe(3);
    expect(c.party).toBe('ACME');
    const plain = instanceToPlain(c);
    expect(plain.id).toBe('c1');
    expect(plain.title).toBe('T');
    expect(plain.page_count).toBe(3);
    expect(plain.party).toBe('ACME');
  });

  it('nested and discriminated subclass objects keep their exposed properties', () => {
    const f = plainToInstance(Folder, {
      name: 'f',
      docs: [{ id: 'd1', title: 'T1' }],
      pinned: { kind: 'contract', id: 'c1', title: 'C', party: 'ACME' },
    });
    expect(f.name).toBe('f');
    expect(f.docs[0]).toBeInstanceOf(Document);
    expect(f.docs[0].title).toBe('T1');
    expect(f.pinned).toBeInstanceOf(Contract);
    expect((f.pinned as Contract).party).toBe('ACME');
    expect((f.pinned as Contract).title).toBe('C');
  });

  it('existing subclass object is updated through exposed properties', () => {
    const d = new Document();
    d.id = 'd1';
    d.title = 'old';
    plainToClassFromExist(d, { title: 'new', page_count: 9 });
    expect(d.title).toBe('new');
    expect(d.pageCount).toBe(9);
  });

  it('classes that are not excluded as a whole, and their subclasses, read and write everything', () => {
    const m = plainToInstance(Memo, { id: 'm1', text: 'hi', internal: 'x', author: 'eve' });
    expect(m).toBeInstanceOf(Memo);
    expect(m.internal).toBe('x');
    expect(m.author).toBe('eve');
    expect(instanceToPlain(m)).toEqual({ id: 'm1', text: 'hi', internal: 'x', author: 'eve' });
  });

  it('the excludeAll strategy option keeps working for any class', () => {
    const m = plainToInstance(Memo, { id: 'm1', text: 'hi' }, { strategy: 'excludeAll' });
    expect(m.id).toBeUndefined();
    const n = new Memo();
    n.id = 'x';
    expect(instanceToPlain(n, { strategy: 'excludeAll' })).toEqual({});
  });
});
