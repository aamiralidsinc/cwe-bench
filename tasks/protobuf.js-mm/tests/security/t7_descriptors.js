'use strict';
// T7 — names taken from an imported descriptor must be treated as own data of
// the objects the import builds. They must never reach the inherited shape of
// a lookup table, and an imported name that coincides with an inherited member
// is an ordinary name.
const {
  loadApp, descriptorOf, assert, assertEqual, hasOwn,
} = require('../support/lib');

const protobuf = loadApp();
const descriptor = descriptorOf(protobuf);

function enumWithProtoValue() {
  return descriptor.EnumDescriptorProto.create({
    name: 'E',
    value: [
      { name: '__proto__', number: 0, options: { deprecated: true } },
      { name: 'OK', number: 1 },
    ],
  });
}

function typeWithNested(name, fieldLabel, fieldTypeName) {
  return descriptor.DescriptorProto.create({
    name: 'M',
    nestedType: [{ name: name, field: [{ name: 'x', number: 1, label: 1, type: 9 }] }],
    field: [{ name: 'c', number: 1, label: fieldLabel, type: 11, typeName: fieldTypeName }],
  });
}

module.exports = [
  {
    name: 'an imported enum value named __proto__ does not leak options through the prototype',
    run() {
      const enm = protobuf.Enum.fromDescriptor(enumWithProtoValue());
      const vo = enm.valuesOptions;
      if (vo != null) {
        assert(
          !hasOwn(vo, 'deprecated') && vo.deprecated === undefined,
          'option of a __proto__-named value must not be readable on the options container',
        );
        assert(
          Object.getPrototypeOf(vo) === Object.prototype,
          'options container must keep an ordinary prototype',
        );
      }
      // the ordinary value is still there
      assertEqual(enm.values.OK, 1, 'ordinary imported value');
    },
  },
  {
    name: 'an imported enum value named __proto__ does not leak options onto a sibling lookup',
    run() {
      // A second import that shares no state with the first must still not see
      // the option of the __proto__-named value through any lookup table.
      const enm = protobuf.Enum.fromDescriptor(enumWithProtoValue());
      assert(enm.valuesOptions == null || enm.valuesOptions.deprecated === undefined,
        'option of a __proto__-named value must not be reachable');
      assert(enm.values['deprecated'] === undefined,
        'option name must not surface as a value');
      assertEqual(enm.values[1], 'OK', 'id -> name lookup intact');
    },
  },
  {
    name: 'an imported nested type named toString is not mistaken for a group',
    run() {
      const type = protobuf.Type.fromDescriptor(typeWithNested('toString', 1, 'M.toString'));
      const nested = type.nestedArray.find((t) => t.name === 'toString');
      assert(nested, 'nested type must be present');
      assert(nested.group !== true, 'a nested message named toString must not be marked as a group');
    },
  },
  {
    name: 'an imported nested type named constructor is not mistaken for a group',
    run() {
      const type = protobuf.Type.fromDescriptor(typeWithNested('constructor', 1, 'M.constructor'));
      const nested = type.nestedArray.find((t) => t.name === 'constructor');
      assert(nested, 'nested type must be present');
      assert(nested.group !== true, 'a nested message named constructor must not be marked as a group');
    },
  },
  {
    name: 'a repeated field of an imported type named constructor is not read as a map entry',
    run() {
      // label 3 = repeated. A map-field probe must not resolve the name against
      // an inherited member of the entry table.
      let type = null;
      let threw = null;
      try {
        type = protobuf.Type.fromDescriptor(typeWithNested('constructor', 3, 'M.constructor'));
      } catch (e) {
        threw = e;
      }
      if (threw) {
        assert(
          !/invalid map entry descriptor:\s*(Object|toString|Function)/i.test(String(threw.message || threw)),
          'rejection must not come from an inherited member: ' + String(threw.message || threw),
        );
        return;
      }
      const field = type.fieldsArray.find((f) => f.name === 'c');
      assert(field, 'field must be present');
      assert(field.map !== true, 'a repeated message field is not a map field');
      assertEqual(field.repeated, true, 'field stays repeated');
    },
  },
  {
    name: 'a repeated field of an imported type named toString is not read as a map entry',
    run() {
      let type = null;
      let threw = null;
      try {
        type = protobuf.Type.fromDescriptor(typeWithNested('toString', 3, 'M.toString'));
      } catch (e) {
        threw = e;
      }
      if (threw) {
        assert(
          !/invalid map entry descriptor:\s*(Object|toString|Function)/i.test(String(threw.message || threw)),
          'rejection must not come from an inherited member: ' + String(threw.message || threw),
        );
        return;
      }
      const field = type.fieldsArray.find((f) => f.name === 'c');
      assert(field, 'field must be present');
      assert(field.map !== true, 'a repeated message field is not a map field');
    },
  },
];
