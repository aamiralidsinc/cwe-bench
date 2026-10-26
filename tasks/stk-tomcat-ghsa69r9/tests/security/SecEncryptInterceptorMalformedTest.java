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

public class SecEncryptInterceptorMalformedTest {

    private static final String KEY = "cafebabedeadbeefbeefcafecafebabe";

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

    private static byte[] deliver(byte[] wire) throws Exception {
        EncryptInterceptor dest = new EncryptInterceptor();
        dest.setEncryptionKey(KEY);
        Capture cap = new Capture();
        dest.setPrevious(cap);
        dest.start(Channel.SND_TX_SEQ);
        ChannelData msg = new ChannelData(false);
        msg.setMessage(new XByteBuffer(wire, false));
        dest.messageReceived(msg);
        return cap.value;
    }

    @Test
    public void oneByteFrameDiscarded() throws Exception {
        Assert.assertNull("a truncated frame was accepted", deliver(new byte[] { 1 }));
    }

    @Test
    public void frameShorterThanIvDiscarded() throws Exception {
        Assert.assertNull("a truncated frame was accepted", deliver(new byte[15]));
    }
}
