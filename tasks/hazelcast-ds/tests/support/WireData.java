package benchkit;

import com.hazelcast.config.CompactSerializationConfig;
import com.hazelcast.config.SerializationConfig;
import com.hazelcast.internal.serialization.Data;
import com.hazelcast.internal.serialization.InternalSerializationService;
import com.hazelcast.internal.serialization.impl.DefaultSerializationServiceBuilder;
import com.hazelcast.internal.serialization.impl.compact.Schema;
import com.hazelcast.internal.serialization.impl.compact.SchemaService;
import com.hazelcast.nio.serialization.genericrecord.GenericRecord;
import com.hazelcast.nio.serialization.genericrecord.GenericRecordBuilder;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Builds the serialization service a member uses and the binary values a
 * remote peer could send to it.
 */
public final class WireData {

    private WireData() {
    }

    public static InternalSerializationService newService() {
        return newService(new CompactSerializationConfig());
    }

    public static InternalSerializationService newService(CompactSerializationConfig compactConfig) {
        SerializationConfig config = new SerializationConfig().setCompactSerializationConfig(compactConfig);
        return new DefaultSerializationServiceBuilder()
                .setConfig(config)
                .setSchemaService(new MapSchemaService())
                .build();
    }

    /** A value written the way a peer writes one when the schema lives in the schema service. */
    public static Data toData(InternalSerializationService service, Object value) {
        return service.toData(value);
    }

    /** A value written with its schema carried inside the binary. */
    public static Data toDataWithSchema(InternalSerializationService service, Object value) {
        return service.toDataWithSchema(value);
    }

    public static GenericRecord record(String typeName) {
        return GenericRecordBuilder.compact(typeName).build();
    }

    public static Object read(InternalSerializationService service, Data data) {
        return service.toObject(data);
    }

    public static String className(Object value) {
        return value == null ? "null" : value.getClass().getName();
    }

    private static final class MapSchemaService implements SchemaService {

        private final Map<Long, Schema> schemas = new ConcurrentHashMap<>();

        @Override
        public Schema get(long schemaId) {
            return schemas.get(schemaId);
        }

        @Override
        public void put(Schema schema) {
            schemas.putIfAbsent(schema.getSchemaId(), schema);
        }

        @Override
        public void putLocal(Schema schema) {
            put(schema);
        }
    }
}
