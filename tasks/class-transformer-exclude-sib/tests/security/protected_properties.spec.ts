// Security tests: a property the application's classes protect must never be set from
// untrusted input, nor written to output, whichever way it is reached.
// Each test FAILS on the vulnerable library and PASSES once it is fixed.
import 'reflect-metadata';
import { Exclude, Expose, Type, plainToInstance, plainToClassFromExist, instanceToPlain } from 'class-transformer';

// ---------------------------------------------------------------- property-level declarations

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
}

class Order {
  reference: string;

  @Type(() => Account)
  buyer: Account;

  @Type(() => Account)
  approvers: Account[];
}

describe('restricted properties are not set from input', () => {
  it('group-restricted property under its JSON name is not set by a customer call', () => {
    const acc = plainToInstance(Account, { name: 'eve', credit_limit: 50000 }, { groups: ['customer'] });
    expect(acc.name).toBe('eve');
    expect(acc.creditLimit).not.toBe(50000);
  });

  it('group-restricted property under its JSON name is not set by a call without groups', () => {
    const acc = plainToInstance(Account, { name: 'eve', credit_limit: 50000 });
    expect(acc.creditLimit).not.toBe(50000);
  });

  it('property excluded from input is not set under its JSON name', () => {
    const acc = plainToInstance(Account, { name: 'eve', is_admin: true });
    expect(acc.name).toBe('eve');
    expect(acc.isAdmin).not.toBe(true);
  });

  it('version-restricted property under its JSON name is not set by an older-version call', () => {
    const acc = plainToInstance(Account, { name: 'eve', beta_access: true }, { version: 1 });
    expect(acc.betaAccess).not.toBe(true);
  });

  it('group-restricted property is not set when only exposed properties are read', () => {
    const acc = plainToInstance(
      Account,
      { display_name: 'Eve', credit_limit: 50000, is_admin: true },
      { groups: ['customer'], excludeExtraneousValues: true }
    );
    expect(acc.displayName).toBe('Eve');
    expect(acc.creditLimit).not.toBe(50000);
    expect(acc.isAdmin).not.toBe(true);
  });

  it('restricted properties of nested objects and array elements are not set', () => {
    const order = plainToInstance(
      Order,
      {
        reference: 'o-1',
        buyer: { name: 'eve', credit_limit: 50000, is_admin: true },
        approvers: [{ name: 'mallory', credit_limit: 70000, is_admin: true }],
      },
      { groups: ['customer'] }
    );
    expect(order.buyer).toBeInstanceOf(Account);
    expect(order.buyer.creditLimit).not.toBe(50000);
    expect(order.buyer.isAdmin).not.toBe(true);
    expect(order.approvers[0].creditLimit).not.toBe(70000);
    expect(order.approvers[0].isAdmin).not.toBe(true);
  });

  it('restricted property is not changed on an existing object', () => {
    const existing = new Account();
    existing.name = 'eve';
    existing.creditLimit = 100;
    plainToClassFromExist(existing, { name: 'eve2', credit_limit: 50000, is_admin: true }, { groups: ['customer'] });
    expect(existing.name).toBe('eve2');
    expect(existing.creditLimit).toBe(100);
    expect(existing.isAdmin).not.toBe(true);
  });
});

// ------------------------------------------- a subclass declares an inherited property again

class Member {
  name: string;

  @Expose({ name: 'spend_cap' })
  spendCap: number = 100;
}

class ManagedMember extends Member {
  // For managed members only staff may change the cap.
  @Expose({ name: 'spend_cap', groups: ['staff'] })
  spendCap: number = 100;
}

describe("a subclass's own declaration of an inherited property applies", () => {
  it('restricted in the subclass: not set by a customer call', () => {
    const m = plainToInstance(ManagedMember, { name: 'eve', spend_cap: 99999 }, { groups: ['customer'] });
    expect(m.name).toBe('eve');
    expect(m.spendCap).not.toBe(99999);
  });

  it('restricted in the subclass: not set by a call without groups', () => {
    const m = plainToInstance(ManagedMember, { name: 'eve', spend_cap: 99999 });
    expect(m.spendCap).not.toBe(99999);
  });
});

// ------------------------------------------------------- whole class excluded but what it exposes

@Exclude()
class Resource {
  @Expose()
  id: string;

  ownerId: string = 'system';
}

class Document extends Resource {
  @Expose()
  title: string;

  locked: boolean = false;
}

class Contract extends Document {
  @Expose()
  party: string;

  approved: boolean = false;
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
  })
  pinned: Resource;
}

describe('a class excluded as a whole stays excluded in its subclasses', () => {
  it('unexposed properties of a subclass object are not set from input', () => {
    const d = plainToInstance(Document, { id: 'd1', title: 'T', ownerId: 'eve', locked: true });
    expect(d.title).toBe('T');
    expect(d.ownerId).not.toBe('eve');
    expect(d.locked).not.toBe(true);
  });

  it('unexposed properties of a subclass object are not written to output', () => {
    const d = new Document();
    d.id = 'd1';
    d.title = 'T';
    d.ownerId = 'u-42';
    d.locked = true;
    const plain = instanceToPlain(d);
    expect(plain.title).toBe('T');
    expect(plain).not.toHaveProperty('ownerId');
    expect(plain).not.toHaveProperty('locked');
  });

  it('two levels of inheritance: not set from input, not written to output', () => {
    const c = plainToInstance(Contract, { id: 'c1', party: 'ACME', approved: true, ownerId: 'eve' });
    expect(c.party).toBe('ACME');
    expect(c.approved).not.toBe(true);
    expect(c.ownerId).not.toBe('eve');

    const out = new Contract();
    out.id = 'c2';
    out.party = 'ACME';
    out.approved = true;
    const plain = instanceToPlain(out);
    expect(plain.party).toBe('ACME');
    expect(plain).not.toHaveProperty('approved');
    expect(plain).not.toHaveProperty('ownerId');
  });

  it('subclass objects nested in arrays and chosen by a type discriminator are protected', () => {
    const f = plainToInstance(Folder, {
      name: 'f',
      docs: [{ id: 'd1', title: 'T', locked: true, ownerId: 'eve' }],
      pinned: { kind: 'contract', id: 'c1', party: 'ACME', approved: true },
    });
    expect(f.docs[0]).toBeInstanceOf(Document);
    expect(f.docs[0].locked).not.toBe(true);
    expect(f.docs[0].ownerId).not.toBe('eve');
    expect(f.pinned).toBeInstanceOf(Contract);
    expect((f.pinned as Contract).approved).not.toBe(true);
  });

  it('existing subclass object is not changed through unexposed properties', () => {
    const d = new Document();
    d.id = 'd1';
    d.title = 'old';
    plainToClassFromExist(d, { title: 'new', locked: true, ownerId: 'eve' });
    expect(d.title).toBe('new');
    expect(d.locked).toBe(false);
    expect(d.ownerId).toBe('system');
  });
});
