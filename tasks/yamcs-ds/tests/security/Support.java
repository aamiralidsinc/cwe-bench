package org.yamcs.tests;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;

import org.yamcs.client.MessageListener;
import org.yamcs.client.YamcsClient;
import org.yamcs.client.base.AbstractSubscription;

import com.google.protobuf.Message;

/**
 * Small helpers shared by the hidden subscription tests.
 */
final class Support {

    private Support() {
    }

    static YamcsClient client(int port, String user, String password) throws Exception {
        YamcsClient client = YamcsClient.newBuilder("localhost", port)
                .withUserAgent("hidden-it")
                .build();
        client.login(user, password.toCharArray());
        client.connectWebSocket();
        return client;
    }

    static final class Sub<C extends Message, S extends Message> extends AbstractSubscription<C, S> {
        Sub(YamcsClient client, String topic, Class<S> messageClass) {
            super(client.getMethodHandler(), topic, messageClass);
        }
    }

    static final class Capture<S extends Message> implements MessageListener<S> {
        final List<S> messages = new CopyOnWriteArrayList<>();
        final CountDownLatch error = new CountDownLatch(1);

        @Override
        public void onMessage(S message) {
            messages.add(message);
        }

        @Override
        public void onError(Throwable t) {
            error.countDown();
        }

        boolean awaitAtLeast(int count, long timeoutMillis) throws InterruptedException {
            long deadline = System.currentTimeMillis() + timeoutMillis;
            while (System.currentTimeMillis() < deadline) {
                if (messages.size() >= count) {
                    return true;
                }
                Thread.sleep(25);
            }
            return messages.size() >= count;
        }
    }

    static void cancel(AbstractSubscription<?, ?> subscription) {
        try {
            subscription.cancel(true);
        } catch (Exception ignored) {
            // The call may already have failed; cancellation is best effort.
        }
    }
}
