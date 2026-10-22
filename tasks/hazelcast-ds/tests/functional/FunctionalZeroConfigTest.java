package benchkit;

import com.hazelcast.config.CompactSerializationConfig;
import com.hazelcast.internal.serialization.Data;
import com.hazelcast.internal.serialization.InternalSerializationService;
import com.hazelcast.nio.serialization.genericrecord.GenericRecord;
import com.hazelcast.nio.serialization.genericrecord.GenericRecordBuilder;
import org.junit.Test;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

/**
 * Zero-configuration compact serialization keeps working for ordinary user
 * values, and explicit registrations keep overriding other mechanisms.
 */
public class FunctionalZeroConfigTest {

    @Test
    public void plainValueRoundTrip() {
        InternalSerializationService service = WireData.newService();
        PlainPayload value = new PlainPayload(7);

        Object result = WireData.read(service, WireData.toData(service, value));

        assertTrue(WireData.className(result), result instanceof PlainPayload);
        assertEquals(7, ((PlainPayload) result).value());
    }

    @Test
    public void nestedInterfaceFieldRoundTrip() {
        InternalSerializationService service = WireData.newService();
        PlainEnvelope value = new PlainEnvelope(new PlainPayload(3), "label");

        Object result = WireData.read(service, WireData.toData(service, value));

        assertTrue(WireData.className(result), result instanceof PlainEnvelope);
        PlainEnvelope envelope = (PlainEnvelope) result;
        assertEquals("label", envelope.getLabel());
        assertTrue(WireData.className(envelope.getPayload()), envelope.getPayload() instanceof PlainPayload);
        assertEquals(3, envelope.getPayload().value());
    }

    @Test
    public void nestedConcreteFieldRoundTrip() {
        InternalSerializationService service = WireData.newService();
        ConcretePlainEnvelope value = new ConcretePlainEnvelope(new PlainPayload(4));

        Object result = WireData.read(service, WireData.toData(service, value));

        assertTrue(WireData.className(result), result instanceof ConcretePlainEnvelope);
        assertEquals(4, ((ConcretePlainEnvelope) result).getPayload().value());
    }

    @Test
    public void arrayRoundTrip() {
        InternalSerializationService service = WireData.newService();
        ArrayEnvelope value = new ArrayEnvelope(new Payload[]{new PlainPayload(1), new PlainPayload(2)});

        Object result = WireData.read(service, WireData.toData(service, value));

        assertTrue(WireData.className(result), result instanceof ArrayEnvelope);
        Payload[] items = ((ArrayEnvelope) result).getItems();
        assertEquals(2, items.length);
        assertEquals(1, items[0].value());
        assertEquals(2, items[1].value());
    }

    @Test
    public void plainConcreteArrayRoundTrip() {
        InternalSerializationService service = WireData.newService();
        PlainArrayEnvelope value = new PlainArrayEnvelope(
                new PlainPayload[]{new PlainPayload(31), new PlainPayload(32)});

        Object result = WireData.read(service, WireData.toData(service, value));

        assertTrue(WireData.className(result), result instanceof PlainArrayEnvelope);
        PlainPayload[] items = ((PlainArrayEnvelope) result).getItems();
        assertEquals(2, items.length);
        assertEquals(31, items[0].value());
        assertEquals(32, items[1].value());
    }

    @Test
    public void listRoundTrip() {
        InternalSerializationService service = WireData.newService();
        List<Payload> items = new ArrayList<>();
        items.add(new PlainPayload(5));
        items.add(new PlainPayload(6));

        Object result = WireData.read(service, WireData.toData(service, new ListEnvelope(items)));

        assertTrue(WireData.className(result), result instanceof ListEnvelope);
        List<Payload> read = ((ListEnvelope) result).getItems();
        assertEquals(2, read.size());
        assertEquals(5, read.get(0).value());
        assertEquals(6, read.get(1).value());
    }

    @Test
    public void mapRoundTrip() {
        InternalSerializationService service = WireData.newService();
        Map<String, Payload> items = new HashMap<>();
        items.put("a", new PlainPayload(8));

        Object result = WireData.read(service, WireData.toData(service, new MapEnvelope(items)));

        assertTrue(WireData.className(result), result instanceof MapEnvelope);
        Map<String, Payload> read = ((MapEnvelope) result).getItems();
        assertEquals(1, read.size());
        assertEquals(8, read.get("a").value());
    }

    @Test
    public void recordRoundTrip() {
        InternalSerializationService service = WireData.newService();
        RecordEnvelope value = new RecordEnvelope(new PlainPayload(9), "rec");

        Object result = WireData.read(service, WireData.toData(service, value));

        assertTrue(WireData.className(result), result instanceof RecordEnvelope);
        RecordEnvelope record = (RecordEnvelope) result;
        assertEquals("rec", record.label());
        assertTrue(WireData.className(record.payload()), record.payload() instanceof PlainPayload);
        assertEquals(9, record.payload().value());
    }

    @Test
    public void unknownTypeNameRoundTrip() {
        InternalSerializationService service = WireData.newService();
        GenericRecord value = GenericRecordBuilder.compact("benchkit.NotOnTheClasspath")
                .setInt32("number", 42)
                .setString("text", "hello")
                .build();

        Object result = WireData.read(service, WireData.toData(service, value));

        assertTrue(WireData.className(result), result instanceof GenericRecord);
        GenericRecord record = (GenericRecord) result;
        assertEquals(42, record.getInt32("number"));
        assertEquals("hello", record.getString("text"));
    }

    @Test
    public void registeredClassOverridesOtherMechanism() {
        CompactSerializationConfig compact = new CompactSerializationConfig();
        compact.addClass(SerializablePayload.class);
        InternalSerializationService service = WireData.newService(compact);
        SerializablePayload value = new SerializablePayload(11);

        Object result = WireData.read(service, WireData.toData(service, value));

        assertTrue(WireData.className(result), result instanceof SerializablePayload);
        assertEquals(11, ((SerializablePayload) result).value());
    }

    @Test
    public void nestedRegisteredClassRoundTrip() {
        CompactSerializationConfig compact = new CompactSerializationConfig();
        compact.addClass(SerializablePayload.class);
        InternalSerializationService service = WireData.newService(compact);
        ConcreteEnvelope value = new ConcreteEnvelope(new SerializablePayload(12));

        Object result = WireData.read(service, WireData.toData(service, value));

        assertTrue(WireData.className(result), result instanceof ConcreteEnvelope);
        assertEquals(12, ((ConcreteEnvelope) result).getPayload().value());
    }

    @Test
    public void explicitSerializerRoundTrip() {
        CompactSerializationConfig compact = new CompactSerializationConfig();
        compact.addSerializer(new CustomPayloadSerializer());
        InternalSerializationService service = WireData.newService(compact);
        CustomPayload value = new CustomPayload(13);

        Object result = WireData.read(service, WireData.toData(service, value));

        assertTrue(WireData.className(result), result instanceof CustomPayload);
        assertEquals(13, ((CustomPayload) result).value());
    }

    @Test
    public void genericRecordValueRoundTrip() {
        InternalSerializationService service = WireData.newService();
        GenericRecord value = GenericRecordBuilder.compact("benchkit.NoSuchType")
                .setInt64("id", 123456789L)
                .setString("name", "value")
                .build();

        Data data = WireData.toData(service, value);
        Object result = WireData.read(service, data);

        assertNotNull(result);
        assertTrue(WireData.className(result), result instanceof GenericRecord);
        assertEquals(123456789L, ((GenericRecord) result).getInt64("id"));
    }

    @Test
    public void javaSerializationIsUnaffected() {
        InternalSerializationService service = WireData.newService();
        SerializablePayload value = new SerializablePayload(21);

        Object result = WireData.read(service, WireData.toData(service, value));

        assertTrue(WireData.className(result), result instanceof SerializablePayload);
        assertEquals(21, ((SerializablePayload) result).value());
    }
}
