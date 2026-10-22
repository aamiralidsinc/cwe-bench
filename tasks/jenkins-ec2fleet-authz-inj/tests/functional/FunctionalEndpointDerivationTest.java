package com.amazon.jenkins.ec2fleet;

import com.amazon.jenkins.ec2fleet.aws.EC2Api;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

/** The region-to-endpoint derivation for real AWS regions must keep working. */
class FunctionalEndpointDerivationTest {

    @Test
    void derivesStandardAndChinaEndpoints() {
        final EC2Api api = new EC2Api();
        assertEquals("https://ec2.us-east-1.amazonaws.com", api.getEndpoint("us-east-1", null));
        assertEquals("https://ec2.cn-north-1.amazonaws.com.cn", api.getEndpoint("cn-north-1", null));
        assertEquals("https://ec2.us-gov-west-1.amazonaws.com", api.getEndpoint("us-gov-west-1", null));
    }

    @Test
    void blankRegionYieldsNoEndpoint() {
        final EC2Api api = new EC2Api();
        assertNull(api.getEndpoint(null, null));
        assertNull(api.getEndpoint("", null));
    }

    @Test
    void explicitEndpointIsReturnedAsIs() {
        final EC2Api api = new EC2Api();
        assertEquals("https://ec2.eu-west-1.amazonaws.com",
                api.getEndpoint("us-east-1", "https://ec2.eu-west-1.amazonaws.com"));
    }
}
