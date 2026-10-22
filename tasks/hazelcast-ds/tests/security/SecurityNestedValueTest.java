package benchkit;

import com.hazelcast.internal.serialization.Data;
import com.hazelcast.internal.serialization.Data;
import com.hazelcast.internal.serialization.InternalSerializationService;
import com.hazelcast.nio.serialization.genericrecord.GenericRecord;
import com.hazelcast.nio.serialization.genericrecord.GenericRecordBuilder;
import org.junit.Test;

import java.util.List;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

/**
 * The type name of a nested value is chosen by the peer as well, in every
 * position a value can be nested.
 */
public class SecurityNestedValueTest {

    private static GenericRecord nested(String typeName) {
        return GenericRecordBuilder.compact(typeName).build();
    }

    @Test
    public void nestedInterfaceFieldIsNotInstantiated() {
        InternalSerializationService service = WireData.newService();
        GenericRecord value = GenericRecordBuilder.compact(PlainEnvelope.class.getName())
                .setGenericRecord("payload", nested("java.io.File"))
                .setString("label", "x")
                .build();

        Object result = WireData.read(service, WireData.toData(service, value));

        assertTrue("expected a generic record but got " + WireData.className(result), result instanceof GenericRecord);
        GenericRecord record = (GenericRecord) result;
        assertEquals("the fallback generic record lost a field", "x", record.getString("label"));
        assertTrue("the fallback generic record lost the nested value",
                record.getGenericRecord("payload") instanceof GenericRecord);
    }

    @Test
    public void nestedConcreteFieldIsReadAsGenericRecord() {
        InternalSerializationService service = WireData.newService();
        GenericRecord value = GenericRecordBuilder.compact(ConcreteEnvelope.class.getName())
                .setGenericRecord("payload", nested(SerializablePayload.class.getName()))
                .build();

        Object result = WireData.read(service, WireData.toData(service, value));

        assertTrue("expected a generic record but got " + WireData.className(result), result instanceof GenericRecord);
    }

    @Test
    public void nestedCounterFieldIsNotConstructed() {
        CounterPayload.CONSTRUCTIONS.set(0);
        InternalSerializationService service = WireData.newService();
        GenericRecord value = GenericRecordBuilder.compact(CounterEnvelope.class.getName())
                .setGenericRecord("payload", nested(CounterPayload.class.getName()))
                .build();

        Object result = null;
        Throwable error = null;
        try {
            result = WireData.read(service, WireData.toData(service, value));
        } catch (Throwable t) {
            error = t;
        }

        assertEquals("a restricted nested field was constructed", 0, CounterPayload.CONSTRUCTIONS.get());
        assertNull("reading a restricted nested value must not fail: " + error, error);
        assertTrue("expected a generic record but got " + WireData.className(result), result instanceof GenericRecord);
    }

    @Test
    public void listElementIsNotInstantiated() {
        CounterPayload.CONSTRUCTIONS.set(0);
        InternalSerializationService service = WireData.newService();
        GenericRecord value = GenericRecordBuilder.compact(DataListEnvelope.class.getName())
                .setArrayOfGenericRecord("items", new GenericRecord[]{nested(CounterPayload.class.getName())})
                .build();

        Object result = null;
        Throwable error = null;
        try {
            result = WireData.read(service, WireData.toData(service, value));
        } catch (Throwable t) {
            error = t;
        }

        assertEquals("a restricted list element was constructed", 0, CounterPayload.CONSTRUCTIONS.get());
        if (error == null) {
            if (result instanceof DataListEnvelope envelope) {
                List<Data> items = envelope.getItems();
                assertNotNull("the typed value was delivered with its elements dropped", items);
                assertEquals("the typed value was delivered with its elements dropped", 1, items.size());
                for (Object item : items) {
                    assertTrue("a restricted list element was returned as an instance: " + WireData.className(item),
                            item instanceof GenericRecord);
                }
            } else {
                assertTrue("expected a generic record but got " + WireData.className(result),
                        result instanceof GenericRecord);
            }
        }
    }

    @Test
    public void mapValueIsNotInstantiated() {
        CounterPayload.CONSTRUCTIONS.set(0);
        InternalSerializationService service = WireData.newService();
        GenericRecord value = GenericRecordBuilder.compact(DataMapEnvelope.class.getName())
                .setArrayOfString("items!keys", new String[]{"k"})
                .setArrayOfGenericRecord("items!values", new GenericRecord[]{nested(CounterPayload.class.getName())})
                .build();

        Object result = null;
        Throwable error = null;
        try {
            result = WireData.read(service, WireData.toData(service, value));
        } catch (Throwable t) {
            error = t;
        }

        assertEquals("a restricted map value was constructed", 0, CounterPayload.CONSTRUCTIONS.get());
        if (error == null) {
            if (result instanceof DataMapEnvelope envelope) {
                Map<String, Data> items = envelope.getItems();
                assertNotNull("the typed value was delivered with its entries dropped", items);
                assertEquals("the typed value was delivered with its entries dropped", 1, items.size());
                for (Object item : items.values()) {
                    assertTrue("a restricted map value was returned as an instance: " + WireData.className(item),
                            item instanceof GenericRecord);
                }
            } else {
                assertTrue("expected a generic record but got " + WireData.className(result),
                        result instanceof GenericRecord);
            }
        }
    }

    @Test
    public void mapKeyIsNotInstantiated() {
        CounterPayload.CONSTRUCTIONS.set(0);
        InternalSerializationService service = WireData.newService();
        GenericRecord value = GenericRecordBuilder.compact(KeyedMapEnvelope.class.getName())
                .setArrayOfGenericRecord("items!keys",
                        new GenericRecord[]{nested(CounterPayload.class.getName())})
                .setArrayOfGenericRecord("items!values",
                        new GenericRecord[]{nested(PlainPayload.class.getName())})
                .build();

        Object result = null;
        Throwable error = null;
        try {
            result = WireData.read(service, WireData.toData(service, value));
        } catch (Throwable t) {
            error = t;
        }

        assertEquals("a restricted map key was constructed", 0, CounterPayload.CONSTRUCTIONS.get());
        if (error == null) {
            if (result instanceof KeyedMapEnvelope envelope) {
                Map<Payload, Data> items = envelope.getItems();
                assertNotNull("the typed value was delivered with its entries dropped", items);
                assertEquals("the typed value was delivered with its entries dropped", 1, items.size());
                for (Object key : items.keySet()) {
                    assertTrue("a restricted map key was returned as an instance: " + WireData.className(key),
                            key instanceof GenericRecord);
                }
            } else {
                assertTrue("expected a generic record but got " + WireData.className(result),
                        result instanceof GenericRecord);
            }
        }
    }

    @Test
    public void recordComponentIsNotInstantiated() {
        CounterPayload.CONSTRUCTIONS.set(0);
        InternalSerializationService service = WireData.newService();
        GenericRecord value = GenericRecordBuilder.compact(RecordEnvelope.class.getName())
                .setGenericRecord("payload", nested(CounterPayload.class.getName()))
                .setString("label", "x")
                .build();

        Object result = null;
        Throwable error = null;
        try {
            result = WireData.read(service, WireData.toData(service, value));
        } catch (Throwable t) {
            error = t;
        }

        assertEquals("a restricted record component was constructed", 0, CounterPayload.CONSTRUCTIONS.get());
        assertNull("reading a restricted record must not fail: " + error, error);
        assertTrue("expected a generic record but got " + WireData.className(result), result instanceof GenericRecord);
    }

    @Test
    public void recordConcreteComponentIsReadAsGenericRecord() {
        InternalSerializationService service = WireData.newService();
        GenericRecord value = GenericRecordBuilder.compact(ConcreteRecord.class.getName())
                .setGenericRecord("payload", nested(SerializablePayload.class.getName()))
                .build();

        Object result = WireData.read(service, WireData.toData(service, value));

        assertTrue("expected a generic record but got " + WireData.className(result), result instanceof GenericRecord);
    }
}
