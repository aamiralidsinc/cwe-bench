package benchkit;

import com.hazelcast.internal.serialization.Data;
import com.hazelcast.internal.serialization.InternalSerializationService;
import com.hazelcast.nio.serialization.genericrecord.GenericRecord;
import com.hazelcast.nio.serialization.genericrecord.GenericRecordBuilder;
import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

/**
 * When a value contained in another cannot be delivered as the declared
 * element type, the containing value still has to be delivered as a generic
 * record whenever it has one.
 */
public class SecurityFallbackTest {

    @Test
    public void arrayElementWithEligibleComponentTypeFallsBack() {
        CounterPayload.CONSTRUCTIONS.set(0);
        InternalSerializationService service = WireData.newService();
        GenericRecord element = GenericRecordBuilder.compact(CounterPayload.class.getName()).build();
        GenericRecord value = GenericRecordBuilder.compact(PlainArrayEnvelope.class.getName())
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
        assertNull("reading a value with a contained restricted value must not fail: " + error, error);
        assertTrue("expected a generic record but got " + WireData.className(result), result instanceof GenericRecord);
        GenericRecord record = (GenericRecord) result;
        GenericRecord[] items = record.getArrayOfGenericRecord("items");
        assertNotNull("the fallback generic record lost the array field", items);
        assertEquals("the fallback generic record lost the array elements", 1, items.length);
        assertTrue("the array element was not kept as data: " + WireData.className(items[0]),
                items[0] instanceof GenericRecord);
    }
}
