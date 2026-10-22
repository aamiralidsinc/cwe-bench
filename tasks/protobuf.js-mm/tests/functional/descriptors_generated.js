'use strict';
// Coupled behaviour: descriptor import and generated modules keep working.
const {
  loadApp, descriptorOf, assert, assertEqual, assertOwnData, parseType, hasOwn, pbjsStatic,
} = require('../support/lib');

const protobuf = loadApp();
const descriptor = descriptorOf(protobuf);

const SCHEMA = `
syntax = "proto3";
message Note { bool admin = 1; string role = 2; }
message Envelope { map<string, Note> labels = 1; }
`;

module.exports = [
  {
    name: 'ordinary descriptor import builds a working type',
    run() {
      const outer = descriptor.DescriptorProto.create({
        name: 'M',
        nestedType: [{
          name: 'LabelsEntry',
          options: { mapEntry: true },
          field: [
            { name: 'key', number: 1, label: 1, type: 9 },
            { name: 'value', number: 2, label: 1, type: 9 },
          ],
        }],
        field: [{ name: 'labels', number: 1, label: 3, type: 11, typeName: 'M.LabelsEntry' }],
      });
      const type = protobuf.Type.fromDescriptor(outer);
      const field = type.fieldsArray.find((f) => f.name === 'labels');
      assert(field, 'field present');
      assertEqual(field.map, true, 'map field');
      assertEqual(field.keyType, 'string', 'key type');
    },
  },
  {
    name: 'ordinary enum descriptor import builds values and reverse lookup',
    run() {
      const enm = protobuf.Enum.fromDescriptor(
        descriptor.EnumDescriptorProto.create({
          name: 'E',
          value: [{ name: 'OK', number: 0 }, { name: 'OTHER', number: 1 }],
        }),
      );
      assertEqual(enm.values.OK, 0, 'name -> id');
      assertEqual(enm.valuesById[1], 'OTHER', 'id -> name');
    },
  },
  {
    name: 'a repeated field of an ordinary nested type is not a map',
    run() {
      const outer = descriptor.DescriptorProto.create({
        name: 'M',
        nestedType: [{ name: 'Child', field: [{ name: 'x', number: 1, label: 1, type: 9 }] }],
        field: [{ name: 'c', number: 1, label: 3, type: 11, typeName: 'M.Child' }],
      });
      const type = protobuf.Type.fromDescriptor(outer);
      const field = type.fieldsArray.find((f) => f.name === 'c');
      assertEqual(field.map, false, 'not a map');
      assertEqual(field.repeated, true, 'repeated');
    },
  },
  {
    name: 'generated enums keep bidirectional lookup',
    run() {
      const root = pbjsStatic(protobuf, 'syntax="proto3"; enum Kind { OK = 0; OTHER = 1; }');
      assertEqual(root.Kind.OK, 0, 'name -> id');
      assertEqual(root.Kind[1], 'OTHER', 'id -> name');
    },
  },
  {
    name: 'generated enums keep every declared name readable',
    run() {
      const root = pbjsStatic(protobuf, 'syntax="proto3"; enum Kind { first = 0; second = 1; OK = 2; }');
      assertEqual(root.Kind.first, 0, 'first');
      assertEqual(root.Kind.second, 1, 'second');
      assertEqual(root.Kind.OK, 2, 'OK');
      assertEqual(root.Kind[0], 'first', 'reverse');
    },
  },
  {
    name: 'a generated enum table keeps every declared name as own data',
    run() {
      const root = pbjsStatic(protobuf, 'syntax="proto3"; enum Kind { first = 0; second = 1; OK = 2; }');
      assert(hasOwn(root.Kind, 'first'), 'first is own data');
      assert(hasOwn(root.Kind, 'second'), 'second is own data');
      assertEqual(root.Kind[2], 'OK', 'id -> name');
    },
  },
  {
    name: 'merge from text and merge from JSON keep ordinary maps working',
    run() {
      const type = parseType(protobuf, SCHEMA, 'Envelope');
      const a = {};
      type.mergeFromText(a, 'labels { key: "k" value { admin: true } }');
      assertEqual(a.labels.k.admin, true, 'text merge');
      const b = {};
      type.mergeFromJson(b, JSON.parse('{"labels":{"k":{"admin":true}}}'));
      assertEqual(b.labels.k.admin, true, 'json merge');
    },
  },
];
