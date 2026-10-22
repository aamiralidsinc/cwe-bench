package org.yamcs.tests;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.concurrent.CompletableFuture;
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
import org.yamcs.protobuf.Commanding.CommandHistoryAttribute;
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
import org.yamcs.protobuf.Table.GetStreamRequest;
import org.yamcs.protobuf.Table.StreamData;
import org.yamcs.protobuf.Table.StreamInfo;
import org.yamcs.protobuf.Table.SubscribeStreamRequest;
import org.yamcs.protobuf.TableApiClient;
import org.yamcs.protobuf.TmPacketData;
import org.yamcs.protobuf.Yamcs.Value;

/**
 * Hidden functional tests: callers that do hold the privilege keep their live feed.
 */
public class FunctionalSubscriptionsTest extends AbstractIntegrationTest {

    private static final String INSTANCE = "instance1";
    private static final String PROCESSOR = "realtime";
    private static final String ROOT_CONTAINER = "/REFMDB/ccsds-default";
    private static final String ALGORITHM = "/REFMDB/SUBSYS1/float_add";
    private static final String COMMAND = "/REFMDB/SUBSYS1/ONE_INT_ARG_TC";

    @BeforeAll
    public static void beforeClass() throws Exception {
        setupYamcs("HiddenIT", true);
    }

    private YamcsClient as(String user) throws Exception {
        return Support.client(yamcsPort, user, "password");
    }

    @Test
    public void authorizedPacketFeedStillDelivers() throws Exception {
        // A caller authorized for a subset of packets (PKT1_1 only) still receives those packets,
        // labelled as today.
        YamcsClient client = as("packetpartial");
        try {
            PacketSubscription sub = client.createPacketSubscription();
            Support.Capture<TmPacketData> capture = new Support.Capture<>();
            sub.addMessageListener(capture);
            sub.sendMessage(SubscribePacketsRequest.newBuilder()
                    .setInstance(INSTANCE).setProcessor(PROCESSOR).build());
            Thread.sleep(500);
            packetGenerator.generate_PKT1_1();
            assertTrue(capture.awaitAtLeast(1, 6000), "authorized live packets were not delivered");
            Support.cancel(sub);
            for (TmPacketData packet : capture.messages) {
                assertEquals(ROOT_CONTAINER, packet.getId().getName());
                assertEquals(packetGenerator.pkt1_1Length, packet.getPacket().size());
            }
        } finally {
            client.close();
        }
    }

    @Test
    public void authorizedRawPacketStreamStillDelivers() throws Exception {
        YamcsClient client = as("streamtable");
        try {
            PacketSubscription sub = client.createPacketSubscription();
            Support.Capture<TmPacketData> capture = new Support.Capture<>();
            sub.addMessageListener(capture);
            sub.sendMessage(SubscribePacketsRequest.newBuilder()
                    .setInstance(INSTANCE).setStream("tm_realtime").build());
            Thread.sleep(500);
            packetGenerator.generate_PKT1_1();
            assertTrue(capture.awaitAtLeast(1, 6000), "authorized raw stream packets were not delivered");
            Support.cancel(sub);
        } finally {
            client.close();
        }
    }

    @Test
    public void streamDescriptionStillAvailableToStreamReader() throws Exception {
        YamcsClient client = as("streamobj");
        try {
            TableApiClient api = new TableApiClient(client.getMethodHandler());
            CompletableFuture<StreamInfo> future = new CompletableFuture<>();
            api.getStream(null, GetStreamRequest.newBuilder()
                    .setInstance(INSTANCE).setName("tm_realtime").build(), new ResponseObserver<>(future));
            StreamInfo info = future.get(6, TimeUnit.SECONDS);
            assertEquals("tm_realtime", info.getName());
        } finally {
            client.close();
        }
    }

    @Test
    public void authorizedGenericStreamStillDelivers() throws Exception {
        YamcsClient client = as("streamtable");
        try {
            Support.Sub<SubscribeStreamRequest, StreamData> sub =
                    new Support.Sub<>(client, "stream", StreamData.class);
            Support.Capture<StreamData> capture = new Support.Capture<>();
            sub.addMessageListener(capture);
            sub.sendMessage(SubscribeStreamRequest.newBuilder()
                    .setInstance(INSTANCE).setStream("tm_realtime").build());
            Thread.sleep(500);
            packetGenerator.generate_PKT1_1();
            assertTrue(capture.awaitAtLeast(1, 6000), "authorized stream rows were not delivered");
            Support.cancel(sub);
        } finally {
            client.close();
        }
    }

    @Test
    public void authorizedOverrideNotificationsStillDeliver() throws Exception {
        YamcsClient client = as("mdbreader");
        try {
            Support.Sub<SubscribeMdbChangesRequest, MdbOverrideInfo> sub =
                    new Support.Sub<>(client, "mdb-changes", MdbOverrideInfo.class);
            Support.Capture<MdbOverrideInfo> capture = new Support.Capture<>();
            sub.addMessageListener(capture);
            sub.sendMessage(SubscribeMdbChangesRequest.newBuilder()
                    .setInstance(INSTANCE).setProcessor(PROCESSOR).build());
            sub.awaitConfirmation(6, TimeUnit.SECONDS);

            ProcessorClient admin = yamcsClient.createProcessorClient(INSTANCE, PROCESSOR);
            admin.updateAlgorithm(ALGORITHM, "AlgoFloatAdditionJs.value = 1 + f0.value + f1.value")
                    .get(10, TimeUnit.SECONDS);
            assertTrue(capture.awaitAtLeast(1, 6000), "authorized override notifications were not delivered");
            Support.cancel(sub);
        } finally {
            client.close();
        }
    }

    @Test
    public void authorizedAlgorithmStatusStillDelivers() throws Exception {
        YamcsClient client = as("algreader");
        try {
            Support.Sub<SubscribeAlgorithmStatusRequest, AlgorithmStatus> sub =
                    new Support.Sub<>(client, "algorithm-status", AlgorithmStatus.class);
            Support.Capture<AlgorithmStatus> capture = new Support.Capture<>();
            sub.addMessageListener(capture);
            sub.sendMessage(SubscribeAlgorithmStatusRequest.newBuilder()
                    .setInstance(INSTANCE).setProcessor(PROCESSOR).setName(ALGORITHM).build());
            assertTrue(capture.awaitAtLeast(1, 8000), "authorized algorithm status was not delivered");
            Support.cancel(sub);
        } finally {
            client.close();
        }
    }

    @Test
    public void authorizedOverrideReadersStillWork() throws Exception {
        ProcessorClient admin = yamcsClient.createProcessorClient(INSTANCE, PROCESSOR);
        admin.updateAlgorithm(ALGORITHM, "AlgoFloatAdditionJs.value = 2 + f0.value + f1.value")
                .get(10, TimeUnit.SECONDS);

        YamcsClient mdb = as("mdbreader");
        try {
            MdbOverrideApiClient api = new MdbOverrideApiClient(mdb.getMethodHandler());
            CompletableFuture<ListMdbOverridesResponse> future = new CompletableFuture<>();
            api.listMdbOverrides(null, ListMdbOverridesRequest.newBuilder()
                    .setInstance(INSTANCE).setProcessor(PROCESSOR).build(), new ResponseObserver<>(future));
            ListMdbOverridesResponse response = future.get(6, TimeUnit.SECONDS);
            assertTrue(response.getOverridesCount() >= 1, "the active override was not listed");
        } finally {
            mdb.close();
        }

        YamcsClient alg = as("algreader");
        try {
            MdbOverrideApiClient api = new MdbOverrideApiClient(alg.getMethodHandler());
            CompletableFuture<GetAlgorithmOverridesResponse> future = new CompletableFuture<>();
            api.getAlgorithmOverrides(null, GetAlgorithmOverridesRequest.newBuilder()
                    .setInstance(INSTANCE).setProcessor(PROCESSOR).setName(ALGORITHM).build(),
                    new ResponseObserver<>(future));
            GetAlgorithmOverridesResponse response = future.get(6, TimeUnit.SECONDS);
            assertTrue(response.hasTextOverride(), "the algorithm override text was not returned");
            assertEquals(ALGORITHM, response.getTextOverride().getAlgorithm());
        } finally {
            alg.close();
        }
    }

    @Test
    public void authorizedContainerSubscriptionStillDelivers() throws Exception {
        YamcsClient client = as("packetroot");
        try {
            ContainerSubscription sub = client.createContainerSubscription();
            Support.Capture<ContainerData> capture = new Support.Capture<>();
            sub.addMessageListener(capture);
            sub.sendMessage(SubscribeContainersRequest.newBuilder()
                    .setInstance(INSTANCE).setProcessor(PROCESSOR)
                    .addNames(ROOT_CONTAINER).build());
            Thread.sleep(500);
            packetGenerator.generate_PKT1_1();
            assertTrue(capture.awaitAtLeast(1, 6000), "authorized container data was not delivered");
            Support.cancel(sub);
            assertEquals(ROOT_CONTAINER, capture.messages.get(0).getName());
        } finally {
            client.close();
        }
    }

    @Test
    public void authorizedCommandFeedStillDeliversUpdates() throws Exception {
        YamcsClient client = as("cmdfull");
        try {
            CommandSubscription sub = client.createCommandSubscription();
            Support.Capture<CommandHistoryEntry> capture = new Support.Capture<>();
            sub.addMessageListener(capture);
            sub.sendMessage(SubscribeCommandsRequest.newBuilder()
                    .setInstance(INSTANCE).setProcessor(PROCESSOR)
                    .setIgnorePastCommands(true).build());
            sub.awaitConfirmation(6, TimeUnit.SECONDS);

            ProcessorClient admin = yamcsClient.createProcessorClient(INSTANCE, PROCESSOR);
            Command command = admin.prepareCommand(COMMAND)
                    .withArgument("uint32_arg", 1000)
                    .issue().get(10, TimeUnit.SECONDS);
            admin.updateCommand(command.getName(), command.getId(), "hiddenProbeKey",
                    Value.newBuilder().setType(Value.Type.STRING)
                            .setStringValue("hiddenProbeValue").build())
                    .get(10, TimeUnit.SECONDS);

            long deadline = System.currentTimeMillis() + 8000;
            boolean created = false;
            boolean updated = false;
            while (System.currentTimeMillis() < deadline && !(created && updated)) {
                for (CommandHistoryEntry entry : capture.messages) {
                    if (COMMAND.equals(entry.getCommandName())) {
                        created = true;
                        for (CommandHistoryAttribute attr : entry.getAttrList()) {
                            if ("hiddenProbeKey".equals(attr.getName())) {
                                updated = true;
                            }
                        }
                    }
                }
                if (!(created && updated)) {
                    Thread.sleep(50);
                }
            }
            Support.cancel(sub);
            assertTrue(created, "the authorized creation entry was not delivered");
            assertTrue(updated, "the authorized update entry was not delivered");
            assertNotNull(command.getId());
        } finally {
            client.close();
        }
    }
}
