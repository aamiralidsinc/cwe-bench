package org.apache.catalina.tribes.group.interceptors;

import java.util.Arrays;

import org.junit.Assert;
import org.junit.Test;

import org.apache.catalina.tribes.Channel;
import org.apache.catalina.tribes.ChannelException;
import org.apache.catalina.tribes.ChannelMessage;
import org.apache.catalina.tribes.Member;
import org.apache.catalina.tribes.group.ChannelInterceptorBase;
import org.apache.catalina.tribes.group.InterceptorPayload;
import org.apache.catalina.tribes.io.ChannelData;
import org.apache.catalina.tribes.io.XByteBuffer;
import org.apache.catalina.tribes.membership.MemberImpl;

public class SecEncryptInterceptorBypassTest {

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
    public void peerMessageCannotSkipEncryption() throws Exception {
        EncryptInterceptor enc = new EncryptInterceptor();
        enc.setEncryptionKey(KEY);

        TcpPingInterceptor ping = new TcpPingInterceptor();
        ping.setUseThread(false);

        MemberImpl member = new MemberImpl();
        Capture wire = new Capture();
        wire.members = new Member[] { member };
        wire.local = member;

        enc.setNext(ping);
        ping.setNext(wire);

        try {
            enc.start(Channel.SND_TX_SEQ);
        } catch (ChannelException | RuntimeException refused) {
            return; // refused configuration: the message cannot skip encryption
        }

        ping.heartbeat();
        Assert.assertNotNull("the peer produced no message", wire.value);
        Assert.assertFalse("a peer message reached the wire in plaintext",
                Arrays.equals(TcpPingInterceptor.TCP_PING_DATA, wire.value));

        EncryptInterceptor dec = new EncryptInterceptor();
        dec.setEncryptionKey(KEY);
        Capture delivered = new Capture();
        dec.setPrevious(delivered);
        dec.start(Channel.SND_TX_SEQ);
        ChannelData msg = new ChannelData(false);
        msg.setMessage(new XByteBuffer(wire.value, false));
        dec.messageReceived(msg);

        Assert.assertNotNull("a peer message travelled without being encrypted", delivered.value);
        Assert.assertArrayEquals("a peer message travelled without being encrypted",
                TcpPingInterceptor.TCP_PING_DATA, delivered.value);
    }
}
