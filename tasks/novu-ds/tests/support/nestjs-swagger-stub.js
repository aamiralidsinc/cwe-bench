// Minimal stand-ins for the decorator/response helpers the mapped API source imports. They keep
// the preview/mapper modules loadable without the Nest runtime; no product behaviour lives here.
const decorator = () => () => undefined;

module.exports = {
  ApiProperty: decorator,
  ApiPropertyOptional: decorator,
  ApiExtraModels: decorator,
  getSchemaPath: () => ({}),
  PartialType: (base) => base,
  OmitType: (base) => base,
  IntersectionType: (first) => first,
};
