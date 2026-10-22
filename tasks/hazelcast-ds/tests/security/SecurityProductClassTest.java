package benchkit;

import com.hazelcast.internal.serialization.Data;
import com.hazelcast.internal.serialization.InternalSerializationService;
import com.hazelcast.nio.serialization.genericrecord.GenericRecord;
import org.junit.Test;

import static org.junit.Assert.assertTrue;

/**
 * Classes that belong to the platform itself are never user data, even when
 * they are not already serialized by another mechanism.
 */
public class SecurityProductClassTest {

    private static final String MEMBER_PROXY = "com.hazelcast.instance.impl.HazelcastInstanceProxy";
    private static final String DISCOVERY_FILE_READER =
            "com.hazelcast.kubernetes.KubernetesConfig$DefaultFileContentsReader";
    private static final String CONNECTOR_DATA_SOURCE =
            "com.hazelcast.jet.impl.connector.DataSourceFromJdbcUrl";
    private static final String SERIALIZATION_STATISTICS =
            "com.hazelcast.internal.serialization.impl.SerializationServiceStatistics";
    private static final String PLATFORM_NAMESPACE_CLASS = "org.xml.sax.ext.DefaultHandler2";

    private static void assertNotInstantiated(String typeName) {
        InternalSerializationService service = WireData.newService();
        Data data = WireData.toData(service, WireData.record(typeName));

        Object result = WireData.read(service, data);

        assertTrue("expected a generic record but got " + WireData.className(result), result instanceof GenericRecord);
    }

    @Test
    public void memberInternalTypeIsNotInstantiated() {
        assertNotInstantiated(MEMBER_PROXY);
    }

    @Test
    public void discoveryFileReaderTypeIsNotInstantiated() {
        assertNotInstantiated(DISCOVERY_FILE_READER);
    }

    @Test
    public void connectorDataSourceTypeIsNotInstantiated() {
        assertNotInstantiated(CONNECTOR_DATA_SOURCE);
    }

    @Test
    public void serializationStatisticsTypeIsNotInstantiated() {
        assertNotInstantiated(SERIALIZATION_STATISTICS);
    }

    @Test
    public void platformTypeOutsideJavaNamespaceIsNotInstantiated() {
        assertNotInstantiated(PLATFORM_NAMESPACE_CLASS);
    }
}
