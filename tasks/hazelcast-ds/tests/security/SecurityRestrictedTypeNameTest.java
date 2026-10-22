package benchkit;

import com.hazelcast.internal.serialization.Data;
import com.hazelcast.internal.serialization.InternalSerializationService;
import com.hazelcast.nio.serialization.genericrecord.GenericRecord;
import com.hazelcast.nio.serialization.genericrecord.GenericRecordBuilder;
import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

/**
 * A peer chooses the type name carried by a compact value. Reading such a value
 * must not load and construct an arbitrary class on the member.
 */
public class SecurityRestrictedTypeNameTest {

    private static final String HEAP_DATA = "com.hazelcast.internal.serialization.impl.HeapData";
    private static final String PACKET = "com.hazelcast.internal.nio.Packet";
    private static final String UNSAFE_INPUT = "com.hazelcast.internal.serialization.impl.UnsafeObjectDataInput";

    @Test
    public void serializableTypeNameIsNotConstructed() {
        CounterPayload.CONSTRUCTIONS.set(0);
        InternalSerializationService service = WireData.newService();
        GenericRecord value = GenericRecordBuilder.compact(CounterPayload.class.getName())
                .setInt32("value", 7)
                .build();
        Data data = WireData.toData(service, value);

        Object result = null;
        Throwable error = null;
        try {
            result = WireData.read(service, data);
        } catch (Throwable t) {
            error = t;
        }

        assertEquals("a class that is serialized by another mechanism was constructed",
                0, CounterPayload.CONSTRUCTIONS.get());
        assertNull("reading a restricted value must not fail: " + error, error);
        assertTrue("expected a generic record but got " + WireData.className(result), result instanceof GenericRecord);
        assertEquals("the fallback generic record lost the value's fields",
                7, ((GenericRecord) result).getInt32("value"));
    }

    @Test
    public void jdkTypeNameIsNotInstantiated() {
        InternalSerializationService service = WireData.newService();
        Data data = WireData.toData(service, WireData.record("java.io.File"));

        Object result = WireData.read(service, data);

        assertTrue("expected a generic record but got " + WireData.className(result), result instanceof GenericRecord);
    }

    @Test
    public void internalTransferTypeIsNotInstantiated() {
        InternalSerializationService service = WireData.newService();
        Data data = WireData.toData(service, WireData.record(HEAP_DATA));

        Object result = WireData.read(service, data);

        assertTrue("expected a generic record but got " + WireData.className(result), result instanceof GenericRecord);
    }

    @Test
    public void internalOutboundFrameTypeIsNotInstantiated() {
        InternalSerializationService service = WireData.newService();
        Data data = WireData.toData(service, WireData.record(PACKET));

        Object result = WireData.read(service, data);

        assertTrue("expected a generic record but got " + WireData.className(result), result instanceof GenericRecord);
    }

    @Test
    public void unsafeInputTypeIsNotInstantiated() {
        InternalSerializationService service = WireData.newService();
        Data data = WireData.toData(service, WireData.record(UNSAFE_INPUT));

        Object result = WireData.read(service, data);

        assertTrue("expected a generic record but got " + WireData.className(result), result instanceof GenericRecord);
    }

    @Test
    public void schemaCarriedInTheBinaryIsAlsoRestricted() {
        InternalSerializationService service = WireData.newService();
        Data data = WireData.toDataWithSchema(service, WireData.record(HEAP_DATA));

        Object result = WireData.read(service, data);

        assertTrue("expected a generic record but got " + WireData.className(result), result instanceof GenericRecord);
    }
}
