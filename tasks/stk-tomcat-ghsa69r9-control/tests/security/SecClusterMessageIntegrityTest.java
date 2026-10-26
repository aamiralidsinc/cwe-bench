/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
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

/**
 * The default configuration of the protected channel must reject a message that was changed on
 * the wire. Each case damages a different part of the transport encoding, so a fix that only
 * notices one kind of change does not close the report.
 */
public class SecClusterMessageIntegrityTest {

    private static final String KEY = "cafebabedeadbeefbeefcafecafebabe";
    private static final byte[] PLAIN =
            "The quick brown fox jumps over the lazy dog and keeps on running today.".getBytes();

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

    private static byte[] encrypt(byte[] plain) throws Exception {
        EncryptInterceptor src = new EncryptInterceptor();
        src.setEncryptionKey(KEY);
        Capture cap = new Capture();
        src.setNext(cap);
        src.start(Channel.SND_TX_SEQ);
        ChannelData msg = new ChannelData(false);
        msg.setMessage(new XByteBuffer(plain, false));
        src.sendMessage(null, msg, null);
        return cap.value;
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
    public void ivFirstByteTamperRejected() throws Exception {
        byte[] wire = encrypt(PLAIN);
        wire[0] ^= 1;
        Assert.assertNull("a message changed on the wire was accepted", deliver(wire));
    }

    @Test
    public void ivLastByteTamperRejected() throws Exception {
        byte[] wire = encrypt(PLAIN);
        wire[15] ^= 1;
        Assert.assertNull("a message changed on the wire was accepted", deliver(wire));
    }

    @Test
    public void firstCiphertextBlockTamperRejected() throws Exception {
        byte[] wire = encrypt(PLAIN);
        wire[16] ^= 1;
        Assert.assertNull("a message changed on the wire was accepted", deliver(wire));
    }

    @Test
    public void secondCiphertextBlockTamperRejected() throws Exception {
        byte[] wire = encrypt(PLAIN);
        wire[32] ^= 1;
        Assert.assertNull("a message changed on the wire was accepted", deliver(wire));
    }
}
