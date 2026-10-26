export function tabState(defs: { name: string; typeName: string }[], typeName = "T") {
  return {
    session: { sessionObj: { loading: false, data: {}, error: null } },
    entity: {
      entityData: { entityDefs: [{ name: typeName, attributes: [], attributeDefs: [], superTypes: [], businessAttributeDefs: { bm: defs } }] },
      loading: false
    },
    businessMetaData: {
      loading: false,
      error: null,
      businessMetaData: { businessMetadataDefs: [{ name: "bm", attributeDefs: defs }] }
    },
    classification: { classificationData: { classificationDefs: [] } },
    drawerState: { isOpen: false, activeId: null },
    enum: { enumObj: {} },
    glossary: { glossaryData: [] },
    typeHeader: { typeHeaderData: [] }
  };
}
