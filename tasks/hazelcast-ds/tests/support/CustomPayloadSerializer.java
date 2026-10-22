package benchkit;

import com.hazelcast.nio.serialization.compact.CompactReader;
import com.hazelcast.nio.serialization.compact.CompactSerializer;
import com.hazelcast.nio.serialization.compact.CompactWriter;

/** An explicitly registered serializer for {@link CustomPayload}. */
public class CustomPayloadSerializer implements CompactSerializer<CustomPayload> {

    @Override
    public CustomPayload read(CompactReader reader) {
        return new CustomPayload(reader.readInt32("value"));
    }

    @Override
    public void write(CompactWriter writer, CustomPayload object) {
        writer.writeInt32("value", object.value());
    }

    @Override
    public String getTypeName() {
        return "benchkit.custom.CustomPayload";
    }

    @Override
    public Class<CustomPayload> getCompactClass() {
        return CustomPayload.class;
    }
}
