package benchkit;

import com.hazelcast.internal.serialization.Data;
import com.hazelcast.internal.serialization.InternalSerializationService;
import com.hazelcast.nio.serialization.genericrecord.GenericRecord;
import com.hazelcast.nio.serialization.genericrecord.GenericRecordBuilder;
import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

/**
 * Elements of an array are nested values read through their own accessor; the
 * type name of every element is chosen by the peer.
 */
public class SecurityArrayElementTest {

    @Test
    public void arrayElementIsNotInstantiated() {
        CounterPayload.CONSTRUCTIONS.set(0);
        InternalSerializationService service = WireData.newService();
        GenericRecord element = GenericRecordBuilder.compact(CounterPayload.class.getName()).build();
        GenericRecord value = GenericRecordBuilder.compact(ArrayEnvelope.class.getName())
                .setArrayOfGenericRecord("items", new GenericRecord[]{element})
                .build();

        Object result = null;
        Throwable error = null;
        try {
            result = WireData.read(service, WireData.toData(service, value));
        } catch (Throwable t) {
            error = t;
        }

        assertEquals("a restricted array element was constructed", 0, CounterPayload.CONSTRUCTIONS.get());
        if (error == null) {
            if (result instanceof ArrayEnvelope envelope) {
                Payload[] items = envelope.getItems();
                assertNotNull("the typed value was delivered with its elements dropped", items);
                assertEquals("the typed value was delivered with its elements dropped", 1, items.length);
                for (Object item : items) {
                    assertTrue("a restricted array element was returned as an instance: " + WireData.className(item),
                            item instanceof GenericRecord);
                }
            } else {
                assertTrue("expected a generic record but got " + WireData.className(result),
                        result instanceof GenericRecord);
            }
        }
    }
}
