package org.apache.catalina.tribes.group.interceptors;

import org.junit.Assert;
import org.junit.Test;

import org.apache.catalina.tribes.Channel;
import org.apache.catalina.tribes.ChannelMessage;
import org.apache.catalina.tribes.Member;
import org.apache.catalina.tribes.group.ChannelInterceptorBase;
import org.apache.catalina.tribes.group.InterceptorPayload;
import org.apache.catalina.tribes.io.ChannelData;
import org.apache.catalina.tribes.io.XByteBuffer;

public class SecEncryptInterceptorIntegrityTest {

    private static final String KEY = "cafebabedeadbeefbeefcafecafebabe";
    private static final byte[] PLAIN = "The quick brown fox jumps over the lazy dog.".getBytes();

    public static class Capture extends ChannelInterceptorBase {
        byte[] value;
        @Override
        public void sendMessage(Member[] d, ChannelMessage m, InterceptorPayload p) {
            value = m.getMessage().getBytes();
        }
        @Override
        public void messageReceived(ChannelMessage m) {
            value = m.getMessage().getBytes();
        }
    }

    private static byte[] encrypt(String algorithm, byte[] plain) throws Exception {
        EncryptInterceptor src = new EncryptInterceptor();
        src.setEncryptionKey(KEY);
        if (algorithm != null) {
            src.setEncryptionAlgorithm(algorithm);
        }
        Capture cap = new Capture();
        src.setNext(cap);
        src.start(Channel.SND_TX_SEQ);
        ChannelData msg = new ChannelData(false);
        msg.setMessage(new XByteBuffer(plain, false));
        src.sendMessage(null, msg, null);
        return cap.value;
    }

    private static byte[] deliver(String algorithm, byte[] wire) throws Exception {
        EncryptInterceptor dest = new EncryptInterceptor();
        dest.setEncryptionKey(KEY);
        if (algorithm != null) {
            dest.setEncryptionAlgorithm(algorithm);
        }
        Capture cap = new Capture();
        dest.setPrevious(cap);
        dest.start(Channel.SND_TX_SEQ);
        ChannelData msg = new ChannelData(false);
        msg.setMessage(new XByteBuffer(wire, false));
        dest.messageReceived(msg);
        return cap.value;
    }

    @Test
    public void defaultConfigIvTamperRejected() throws Exception {
        byte[] wire = encrypt(null, PLAIN);
        byte[] tampered = wire.clone();
        tampered[0] ^= 1;
        Assert.assertNull("a message tampered in transit was accepted", deliver(null, tampered));
    }

    @Test
    public void defaultConfigCiphertextTamperRejected() throws Exception {
        byte[] wire = encrypt(null, PLAIN);
        byte[] tampered = wire.clone();
        tampered[16] ^= 1;
        Assert.assertNull("a message tampered in transit was accepted", deliver(null, tampered));
    }

    @Test
    public void ofbTamperRejected() throws Exception {
        String alg = "AES/OFB/PKCS5Padding";
        byte[] wire = encrypt(alg, PLAIN);
        byte[] tampered = wire.clone();
        tampered[16] ^= 1;
        Assert.assertNull("a message tampered in transit was accepted", deliver(alg, tampered));
    }

    @Test
    public void cfbTamperRejected() throws Exception {
        String alg = "AES/CFB/PKCS5Padding";
        byte[] wire = encrypt(alg, PLAIN);
        byte[] tampered = wire.clone();
        tampered[16] ^= 1;
        Assert.assertNull("a message tampered in transit was accepted", deliver(alg, tampered));
    }
}
