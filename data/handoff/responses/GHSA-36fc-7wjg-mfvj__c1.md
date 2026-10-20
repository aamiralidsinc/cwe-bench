<instruction_md>
# A data-object table field constructed a PHP class while it was loading

## What we observed

An editor opened a data object and one table field did not come back as rows of values. The stored value for that field had been replaced beforehand with a crafted blob. Loading the field constructed a PHP class that is not part of the table, and that class's startup logic ran during the load. This is the read the editor and the export path use to turn the stored table back into rows. One crafted blob was enough; nothing else on the object was changed.

A stored value that should only be plain structured data must not construct a class, and it must not run that class's startup logic, when the application reads it back.

## Impact

Anyone who can replace that stored blob can choose a class to construct the next time the object is read. Unexpected logic then runs inside the application as part of an ordinary load, before anyone sees the rows.

## What must keep working

- A normal table of text and numbers, including several rows and a row made of several cells, still loads as those plain values.
- Cell text is returned unchanged when it merely looks like a class name or an object blob, as long as it is stored as text inside a real row.
- A table whose stored value is missing or empty still loads as an empty table, and the rest of the object still opens.
- When that table is configured with named columns, each reloaded row is keyed by those column names.
- A link field still loads as a link, with the label and the target that were saved. Saved values that are real application objects, such as a link or a stored snapshot of an element, have to come back as those objects. A repair that refuses to restore any object at all makes links and snapshots unusable.
</instruction_md>
<task_metadata_json>
{
  "entry_point": "Public load of a data-object table field from its stored blob, via the field type's resource reader used when an object is opened or exported, and the public read of the on-disk delete history written when a desktop client removes an asset.",
  "techniques": [
    1,
    2,
    5,
    7,
    9,
    12
  ],
  "trap": {
    "paths": [
      "models/Asset/WebDAV/Service.php"
    ],
    "contract": "Plain table rows, including cell text that only looks like an object blob, still load as those values, and a saved link still comes back as a link object with its label and target."
  },
  "fix_places": [
    "lib/Tool/Serialize.php",
    "models/Asset/WebDAV/Service.php",
    "models/DataObject/ClassDefinition/Data/Table.php"
  ],
  "unrelated_files": [
    "models/Asset/WebDAV/Tree.php",
    "models/DataObject/ClassDefinition/CustomLayout/Dao.php",
    "models/DataObject/Service.php",
    "models/Site/Dao.php"
  ],
  "test_justifications": {
    "test_security_table_field_whole_blob": "Loading the field constructed a PHP class that is not part of the table, and that class's startup logic ran during the load.",
    "test_security_table_field_object_in_row": "A stored value that should only be plain structured data must not construct a class, and it must not run that class's startup logic, when the application reads it back.",
    "test_security_plain_store_root_object": "A stored value that should only be plain structured data must not construct a class, and it must not run that class's startup logic, when the application reads it back.",
    "test_security_plain_store_nested_object": "A stored value that should only be plain structured data must not construct a class, and it must not run that class's startup logic, when the application reads it back.",
    "test_functional_table_rows": "A normal table of text and numbers, including several rows and a row made of several cells, still loads as those plain values.",
    "test_functional_table_cell_text_looking_like_object": "Cell text is returned unchanged when it merely looks like a class name or an object blob, as long as it is stored as text inside a real row.",
    "test_functional_table_empty": "A table whose stored value is missing or empty still loads as an empty table, and the rest of the object still opens.",
    "test_functional_table_named_columns": "When that table is configured with named columns, each reloaded row is keyed by those column names.",
    "test_functional_link_field_restores_object": "A link field still loads as a link, with the label and the target that were saved."
  }
}
</task_metadata_json>
<check_patches_json>
{
  "shallow": [
    {
      "file": "models/DataObject/ClassDefinition/Data/Table.php",
      "search": "        $unserializedData = Serialize::unserialize((string) $data);\n",
      "replace": "        $unserializedData = ($data === null || $data === '') ? $data : unserialize((string) $data, ['allowed_classes' => false]);\n"
    }
  ],
  "removal": [
    {
      "file": "lib/Tool/Serialize.php",
      "search": "    public static function unserialize(?string $data = null): mixed\n    {\n        if ($data) {\n            $data = unserialize($data);\n        }\n\n        return $data;\n    }\n",
      "replace": "    public static function unserialize(?string $data = null): mixed\n    {\n        if ($data === null || $data === '') {\n            return $data;\n        }\n\n        return unserialize($data, ['allowed_classes' => false]);\n    }\n"
    }
  ],
  "alternative": [
    {
      "file": "models/DataObject/ClassDefinition/Data/Table.php",
      "search": "        $unserializedData = Serialize::unserialize((string) $data);\n",
      "replace": "        if ($data === null || $data === '') {\n            $unserializedData = $data;\n        } else {\n            $unserializedData = unserialize((string) $data, ['allowed_classes' => false]);\n        }\n"
    },
    {
      "file": "models/Asset/WebDAV/Service.php",
      "search": "            $log = unserialize(file_get_contents(self::getDeleteLogFile()));\n",
      "replace": "            $log = unserialize(file_get_contents(self::getDeleteLogFile()), ['allowed_classes' => false]);\n"
    }
  ]
}
</check_patches_json>
