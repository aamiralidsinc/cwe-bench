package org.yamcs.tests;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.yamcs.client.Command;
import org.yamcs.client.CommandSubscription;
import org.yamcs.client.ContainerSubscription;
import org.yamcs.client.PacketSubscription;
import org.yamcs.client.YamcsClient;
import org.yamcs.client.base.ResponseObserver;
import org.yamcs.client.processor.ProcessorClient;
import org.yamcs.protobuf.AlgorithmStatus;
import org.yamcs.protobuf.Commanding.CommandHistoryEntry;
import org.yamcs.protobuf.ContainerData;
import org.yamcs.protobuf.GetAlgorithmOverridesRequest;
import org.yamcs.protobuf.GetAlgorithmOverridesResponse;
import org.yamcs.protobuf.ListMdbOverridesRequest;
import org.yamcs.protobuf.ListMdbOverridesResponse;
import org.yamcs.protobuf.MdbOverrideApiClient;
import org.yamcs.protobuf.MdbOverrideInfo;
import org.yamcs.protobuf.SubscribeAlgorithmStatusRequest;
import org.yamcs.protobuf.SubscribeCommandsRequest;
import org.yamcs.protobuf.SubscribeContainersRequest;
import org.yamcs.protobuf.SubscribeMdbChangesRequest;
import org.yamcs.protobuf.SubscribePacketsRequest;
import org.yamcs.protobuf.Table.StreamData;
import org.yamcs.protobuf.Table.SubscribeStreamRequest;
import org.yamcs.protobuf.TmPacketData;
import org.yamcs.protobuf.Yamcs.Value;

/**
 * Hidden security tests: a subscription or override read must not hand out data the
 * caller could not obtain through the corresponding ordinary read.
 */
public class SecuritySubscriptionsTest extends AbstractIntegrationTest {

    private static final String INSTANCE = "instance1";
    private static final String PROCESSOR = "realtime";
    private static final String ROOT_CONTAINER = "/REFMDB/ccsds-default";
    private static final String ALGORITHM = "/REFMDB/SUBSYS1/float_add";
    private static final String ALLOWED_COMMAND = "/REFMDB/SUBSYS1/ONE_INT_ARG_TC";
    private static final String FORBIDDEN_COMMAND = "/REFMDB/SUBSYS1/CRITICAL_TC1";

    @BeforeAll
    public static void beforeClass() throws Exception {
        setupYamcs("HiddenIT", true);
    }

    private YamcsClient as(String user) throws Exception {
        return Support.client(yamcsPort, user, "password");
    }

    private static void awaitRefusal(Support.Capture<?> capture, long timeoutSeconds) throws InterruptedException {
        assertTrue(capture.error.await(timeoutSeconds, TimeUnit.SECONDS),
                "the subscription was accepted for a caller that may not read the data");
    }

    @Test
    public void packetFeedDropsPacketsTheCallerMayNotRead() throws Exception {
        YamcsClient client = as("packetpartial");
        try {
            PacketSubscription sub = client.createPacketSubscription();
            Support.Capture<TmPacketData> capture = new Support.Capture<>();
            sub.addMessageListener(capture);
            sub.sendMessage(SubscribePacketsRequest.newBuilder()
                    .setInstance(INSTANCE).setProcessor(PROCESSOR).build());
            Thread.sleep(500);
            packetGenerator.generate_PKT1_1();
            packetGenerator.generate_PKT1_3();
            Thread.sleep(2000);
            Support.cancel(sub);
            // Packets are labelled with the subscribed container, so judge each one by its content:
            // the role may read PKT1_1 (archived under its own name) but not PKT1_3.
            for (TmPacketData packet : capture.messages) {
                assertNotEquals(packetGenerator.pkt1_3Length, packet.getPacket().size(),
                        "received a packet the role does not authorize (PKT1_3)");
            }
        } finally {
            client.close();
        }
    }

    @Test
    public void packetFeedDeliversNoPacketOutsideTheCallersPacketNames() throws Exception {
        // ReadPacket on the root container name only. PKT1_1 is archived under its own name, so the
        // ordinary packet reads never return it to this role; the live feed must not either.
        // (PKT1_3 has no archive partition of its own and is archived under the root name.)
        YamcsClient client = as("packetroot");
        try {
            PacketSubscription sub = client.createPacketSubscription();
            Support.Capture<TmPacketData> capture = new Support.Capture<>();
            sub.addMessageListener(capture);
            sub.sendMessage(SubscribePacketsRequest.newBuilder()
                    .setInstance(INSTANCE).setProcessor(PROCESSOR).build());
            Thread.sleep(500);
            packetGenerator.generate_PKT1_1();
            packetGenerator.generate_PKT1_3();
            Thread.sleep(2000);
            Support.cancel(sub);
            for (TmPacketData packet : capture.messages) {
                assertNotEquals(packetGenerator.pkt1_1Length, packet.getPacket().size(),
                        "received a packet the caller may not read through the ordinary packet reads (PKT1_1)");
            }
        } finally {
            client.close();
        }
    }

    @Test
    public void rawPacketStreamRefusedWithoutTablePrivilege() throws Exception {
        YamcsClient client = as("streamobj");
        try {
            PacketSubscription sub = client.createPacketSubscription();
            Support.Capture<TmPacketData> capture = new Support.Capture<>();
            sub.addMessageListener(capture);
            sub.sendMessage(SubscribePacketsRequest.newBuilder()
                    .setInstance(INSTANCE).setStream("tm_realtime").build());
            awaitRefusal(capture, 6);
            packetGenerator.generate_PKT1_1();
            Thread.sleep(500);
            Support.cancel(sub);
            assertTrue(capture.messages.isEmpty(), "raw packets were delivered without the table privilege");
        } finally {
            client.close();
        }
    }

    @Test
    public void overrideNotificationsRefusedWithoutMissionDatabasePrivilege() throws Exception {
        YamcsClient client = as("nopriv");
        try {
            Support.Sub<SubscribeMdbChangesRequest, MdbOverrideInfo> sub =
                    new Support.Sub<>(client, "mdb-changes", MdbOverrideInfo.class);
            Support.Capture<MdbOverrideInfo> capture = new Support.Capture<>();
            sub.addMessageListener(capture);
            sub.sendMessage(SubscribeMdbChangesRequest.newBuilder()
                    .setInstance(INSTANCE).setProcessor(PROCESSOR).build());
            awaitRefusal(capture, 6);
            Thread.sleep(300);
            Support.cancel(sub);
            assertTrue(capture.messages.isEmpty(), "override notifications were delivered");
        } finally {
            client.close();
        }
    }

    @Test
    public void algorithmStatusRefusedWithoutAlgorithmPrivilege() throws Exception {
        YamcsClient client = as("nopriv");
        try {
            Support.Sub<SubscribeAlgorithmStatusRequest, AlgorithmStatus> sub =
                    new Support.Sub<>(client, "algorithm-status", AlgorithmStatus.class);
            Support.Capture<AlgorithmStatus> capture = new Support.Capture<>();
            sub.addMessageListener(capture);
            sub.sendMessage(SubscribeAlgorithmStatusRequest.newBuilder()
                    .setInstance(INSTANCE).setProcessor(PROCESSOR).setName(ALGORITHM).build());
            awaitRefusal(capture, 6);
            Thread.sleep(300);
            Support.cancel(sub);
            assertTrue(capture.messages.isEmpty(), "algorithm status was delivered");
        } finally {
            client.close();
        }
    }

    @Test
    public void genericStreamRefusedWithoutTablePrivilege() throws Exception {
        YamcsClient client = as("streamobj");
        try {
            Support.Sub<SubscribeStreamRequest, StreamData> sub =
                    new Support.Sub<>(client, "stream", StreamData.class);
            Support.Capture<StreamData> capture = new Support.Capture<>();
            sub.addMessageListener(capture);
            sub.sendMessage(SubscribeStreamRequest.newBuilder()
                    .setInstance(INSTANCE).setStream("tm_realtime").build());
            awaitRefusal(capture, 6);
            packetGenerator.generate_PKT1_1();
            Thread.sleep(500);
            Support.cancel(sub);
            assertTrue(capture.messages.isEmpty(), "stream rows were delivered without the table privilege");
        } finally {
            client.close();
        }
    }

    @Test
    public void overrideListDoesNotExposeOverridesToUnauthorizedCaller() throws Exception {
        yamcsClient.createProcessorClient(INSTANCE, PROCESSOR)
                .updateAlgorithm(ALGORITHM, "AlgoFloatAdditionJs.value = 3 + f0.value + f1.value")
                .get(10, TimeUnit.SECONDS);
        YamcsClient client = as("nopriv");
        try {
            MdbOverrideApiClient api = new MdbOverrideApiClient(client.getMethodHandler());
            var future = new java.util.concurrent.CompletableFuture<ListMdbOverridesResponse>();
            api.listMdbOverrides(null, ListMdbOverridesRequest.newBuilder()
                    .setInstance(INSTANCE).setProcessor(PROCESSOR).build(), new ResponseObserver<>(future));
            try {
                ListMdbOverridesResponse response = future.get(6, TimeUnit.SECONDS);
                assertEquals(0, response.getOverridesCount(),
                        "the override list was returned to a caller without the mission-database privilege");
            } catch (ExecutionException expected) {
                // A clean refusal is equally correct.
            }
        } finally {
            client.close();
        }
    }

    @Test
    public void algorithmOverrideTextNotExposedToUnauthorizedCaller() throws Exception {
        yamcsClient.createProcessorClient(INSTANCE, PROCESSOR)
                .updateAlgorithm(ALGORITHM, "AlgoFloatAdditionJs.value = 4 + f0.value + f1.value")
                .get(10, TimeUnit.SECONDS);
        YamcsClient client = as("nopriv");
        try {
            MdbOverrideApiClient api = new MdbOverrideApiClient(client.getMethodHandler());
            var future = new java.util.concurrent.CompletableFuture<GetAlgorithmOverridesResponse>();
            api.getAlgorithmOverrides(null, GetAlgorithmOverridesRequest.newBuilder()
                    .setInstance(INSTANCE).setProcessor(PROCESSOR).setName(ALGORITHM).build(),
                    new ResponseObserver<>(future));
            try {
                GetAlgorithmOverridesResponse response = future.get(6, TimeUnit.SECONDS);
                assertFalse(response.hasTextOverride(),
                        "algorithm override text was returned to an unauthorized caller");
            } catch (ExecutionException expected) {
                // A clean refusal is equally correct.
            }
        } finally {
            client.close();
        }
    }

    @Test
    public void containerSubscriptionDeliversNoContainerTheCallerMayNotRead() throws Exception {
        YamcsClient client = as("nopriv");
        try {
            ContainerSubscription sub = client.createContainerSubscription();
            Support.Capture<ContainerData> capture = new Support.Capture<>();
            sub.addMessageListener(capture);
            sub.sendMessage(SubscribeContainersRequest.newBuilder()
                    .setInstance(INSTANCE).setProcessor(PROCESSOR)
                    .addNames(ROOT_CONTAINER).build());
            Thread.sleep(500);
            packetGenerator.generate_PKT1_1();
            Thread.sleep(1500);
            Support.cancel(sub);
            assertTrue(capture.messages.isEmpty(),
                    "container bytes were delivered to a caller without the packet privilege");
        } finally {
            client.close();
        }
    }

    @Test
    public void commandUpdatesAreFilteredPerCommand() throws Exception {
        YamcsClient client = as("cmdpartial");
        try {
            CommandSubscription sub = client.createCommandSubscription();
            Support.Capture<CommandHistoryEntry> capture = new Support.Capture<>();
            sub.addMessageListener(capture);
            sub.sendMessage(SubscribeCommandsRequest.newBuilder()
                    .setInstance(INSTANCE).setProcessor(PROCESSOR)
                    .setIgnorePastCommands(true).build());
            sub.awaitConfirmation(6, TimeUnit.SECONDS);

            ProcessorClient admin = yamcsClient.createProcessorClient(INSTANCE, PROCESSOR);
            Command command = admin.prepareCommand(FORBIDDEN_COMMAND)
                    .withArgument("p1", 2)
                    .issue().get(10, TimeUnit.SECONDS);
            admin.updateCommand(command.getName(), command.getId(), "hiddenProbeKey",
                    Value.newBuilder().setType(Value.Type.STRING)
                            .setStringValue("hiddenProbeValue").build())
                    .get(10, TimeUnit.SECONDS);
            Thread.sleep(2500);
            Support.cancel(sub);
            for (CommandHistoryEntry entry : capture.messages) {
                assertNotEquals(FORBIDDEN_COMMAND, entry.getCommandName(),
                        "a command-history entry was delivered for a command the caller may not read");
            }
        } finally {
            client.close();
        }
    }
}
