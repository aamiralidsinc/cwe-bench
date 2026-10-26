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
import org.apache.catalina.tribes.membership.MemberImpl;

public class FuncEncryptInterceptorChainTest {

    private static final String KEY = "cafebabedeadbeefbeefcafecafebabe";

    public static class Capture extends ChannelInterceptorBase {
        byte[] value;
        Member[] members;
        Member local;

        @Override
        public void sendMessage(Member[] d, ChannelMessage m, InterceptorPayload p) {
            value = m.getMessage().getBytes();
        }
        @Override
        public void messageReceived(ChannelMessage m) {
            value = m.getMessage().getBytes();
        }
        @Override
        public Member[] getMembers() {
            return members;
        }
        @Override
        public Member getLocalMember(boolean incAlive) {
            return local;
        }
    }

    @Test
    public void peerComponentAboveEncryptionKeepsWorking() throws Exception {
        EncryptInterceptor enc = new EncryptInterceptor();
        enc.setEncryptionKey(KEY);

        TcpPingInterceptor ping = new TcpPingInterceptor();
        ping.setUseThread(false);

        MemberImpl member = new MemberImpl();
        Capture wire = new Capture();
        wire.members = new Member[] { member };
        wire.local = member;

        ping.setNext(enc);
        enc.setNext(wire);
        enc.setPrevious(ping);
        ping.setPrevious(null);

        enc.start(Channel.SND_TX_SEQ);
        ping.heartbeat();

        Assert.assertNotNull("the documented interceptor order stopped sending peer messages", wire.value);

        EncryptInterceptor dec = new EncryptInterceptor();
        dec.setEncryptionKey(KEY);
        Capture delivered = new Capture();
        dec.setPrevious(delivered);
        dec.start(Channel.SND_TX_SEQ);
        ChannelData msg = new ChannelData(false);
        msg.setMessage(new XByteBuffer(wire.value, false));
        dec.messageReceived(msg);

        Assert.assertArrayEquals("peer messages stopped round-tripping through encryption",
                TcpPingInterceptor.TCP_PING_DATA, delivered.value);
    }

    @Test
    public void validPayloadRoundTrips() throws Exception {
        byte[] payload = "The quick brown fox jumps over the lazy dog.".getBytes("UTF-8");
        EncryptInterceptor src = new EncryptInterceptor();
        src.setEncryptionKey(KEY);
        Capture wire = new Capture();
        src.setNext(wire);
        src.start(Channel.SND_TX_SEQ);
        ChannelData msg = new ChannelData(false);
        msg.setMessage(new XByteBuffer(payload, false));
        src.sendMessage(null, msg, null);

        EncryptInterceptor dest = new EncryptInterceptor();
        dest.setEncryptionKey(KEY);
        Capture delivered = new Capture();
        dest.setPrevious(delivered);
        dest.start(Channel.SND_TX_SEQ);
        ChannelData msg2 = new ChannelData(false);
        msg2.setMessage(new XByteBuffer(wire.value, false));
        dest.messageReceived(msg2);

        Assert.assertArrayEquals(payload, delivered.value);
    }
}
