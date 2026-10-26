package bench.ewm;

import hudson.model.Fingerprint;
import hudson.model.Result;
import hudson.model.Run;
import jenkins.model.Jenkins;
import org.jenkinsci.plugins.ewm.actions.ExwsAllocateActionImpl;
import org.jenkinsci.plugins.ewm.definitions.Disk;
import org.jenkinsci.plugins.ewm.definitions.DiskPool;
import org.jenkinsci.plugins.ewm.facets.WorkspaceBrowserFacet;
import org.jenkinsci.plugins.ewm.model.ExternalWorkspace;
import org.jenkinsci.plugins.ewm.nodes.ExternalWorkspaceProperty;
import org.jenkinsci.plugins.ewm.nodes.NodeDisk;
import org.jenkinsci.plugins.ewm.nodes.NodeDiskPool;
import org.jenkinsci.plugins.ewm.steps.ExwsAllocateStep;
import org.jenkinsci.plugins.ewm.steps.ExwsStep;
import org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition;
import org.jenkinsci.plugins.workflow.job.WorkflowJob;
import org.jenkinsci.plugins.workflow.job.WorkflowRun;
import org.junit.After;
import org.junit.Before;
import org.junit.Rule;
import org.junit.rules.TemporaryFolder;
import org.jvnet.hudson.test.JenkinsRule;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Collections;
import java.util.Random;

/**
 * Fixture shared by the behavioural suites: a live Jenkins controller, one disk pool whose
 * master and node mount points are the same temporary directory, and helpers that drive the
 * product's real Pipeline steps and HTTP endpoints.
 *
 * <p>Workspace records that an earlier (pre-fix) allocation could have written are re-created by
 * serialising a legitimate value and changing the stored path in the serialized form, which
 * exercises the same deserialization path the controller uses on reload and does not depend on
 * any path helper the submitted fix may harden.</p>
 */
public abstract class EwmBase {

    protected static final String POOL_ID = "disk-pool-1";
    protected static final String DISK_ID = "disk-1";
    protected static final String SECRET = "OUTSIDE-SECRET-9f2c41";
    protected static final String ATTACK_FILE = "leaked.txt";

    @Rule
    public JenkinsRule j = new JenkinsRule();

    @Rule
    public TemporaryFolder tmp = new TemporaryFolder();

    protected File mount;
    protected File outside;
    protected File sibling;

    private int counter;

    @Before
    public void setUpFixture() throws Exception {
        mount = tmp.newFolder("mount");
        outside = tmp.newFolder("outside");
        sibling = tmp.newFolder("sibling");
        j.jenkins.setCrumbIssuer(null);
        configurePool(null);
        addNodeDisks();
    }

    @After
    public void tearDownFixture() throws Exception {
        configurePool(null);
        setTemplates(Collections.<org.jenkinsci.plugins.ewm.definitions.Template>emptyList());
        j.jenkins.getNodeProperties().removeAll(ExternalWorkspaceProperty.class);
    }

    // ------------------------------------------------------------------ configuration

    /** Replaces the single disk pool; a non-null template becomes its workspace template. */
    protected void configurePool(String workspaceTemplate) {
        Disk disk = new Disk(DISK_ID, null, mount.getAbsolutePath(), null, null);
        DiskPool pool = new DiskPool(POOL_ID, null, null, workspaceTemplate, null, null,
                Collections.singletonList(disk));
        ExwsAllocateStep.DescriptorImpl descriptor =
                (ExwsAllocateStep.DescriptorImpl) j.jenkins.getDescriptor(ExwsAllocateStep.class);
        descriptor.setDiskPools(Collections.singletonList(pool));
    }

    protected void setTemplates(java.util.List<org.jenkinsci.plugins.ewm.definitions.Template> templates) {
        ExwsStep.DescriptorImpl descriptor =
                (ExwsStep.DescriptorImpl) j.jenkins.getDescriptor(ExwsStep.class);
        descriptor.setTemplates(templates);
    }

    private void addNodeDisks() {
        NodeDisk nodeDisk = new NodeDisk(DISK_ID, mount.getAbsolutePath());
        NodeDiskPool nodeDiskPool = new NodeDiskPool(POOL_ID, Collections.singletonList(nodeDisk));
        j.jenkins.getNodeProperties().add(
                new ExternalWorkspaceProperty(Collections.singletonList(nodeDiskPool)));
    }

    // ------------------------------------------------------------------ Pipeline

    protected WorkflowRun runScript(String script) throws Exception {
        String name = "job-" + (++counter) + "-" + Math.abs(new Random().nextInt(1000000));
        WorkflowJob job = j.jenkins.createProject(WorkflowJob.class, name);
        job.setDefinition(new CpsFlowDefinition(script));
        return job.scheduleBuild2(0).get();
    }

    protected static boolean succeeded(WorkflowRun run) {
        return run.getResult() == Result.SUCCESS;
    }

    /** The script that allocates through the reported step parameter and writes in the workspace. */
    protected String allocateWithPathAndWrite(String path) {
        return "def ext = exwsAllocate diskPoolId: '" + POOL_ID + "', path: '" + path + "'\n"
                + "node {\n"
                + "  exws(ext) {\n"
                + "    writeFile file: '" + ATTACK_FILE + "', text: 'x'\n"
                + "  }\n"
                + "}\n";
    }

    // ------------------------------------------------------------------ stored records

    /**
     * Builds the workspace a pre-fix allocation could have recorded: a legitimate value is
     * serialised and deserialised with the stored path replaced. Returns {@code null} when the
     * product refuses to load the record (a valid place to stop the value).
     */
    protected ExternalWorkspace storedWorkspace(String pathOnDisk) {
        try {
            ExternalWorkspace legit = new ExternalWorkspace(POOL_ID, DISK_ID,
                    mount.getAbsolutePath(), "placeholder/inside");
            String xml = Jenkins.XSTREAM2.toXML(legit);
            if (xml == null || !xml.contains("placeholder/inside")) {
                return null;
            }
            xml = xml.replace("placeholder/inside", pathOnDisk);
            return (ExternalWorkspace) Jenkins.XSTREAM2.fromXML(xml);
        } catch (Throwable t) {
            return null;
        }
    }

    protected boolean registerFingerprint(Run<?, ?> owner, ExternalWorkspace workspace) {
        try {
            Fingerprint fingerprint = j.jenkins.getFingerprintMap()
                    .getOrCreate(owner, workspace.getDisplayName(), workspace.getId());
            if (fingerprint.getFacet(WorkspaceBrowserFacet.class) == null) {
                fingerprint.getFacets().add(
                        new WorkspaceBrowserFacet(fingerprint, System.currentTimeMillis(), workspace));
            }
            fingerprint.save();
            return true;
        } catch (Throwable t) {
            return false;
        }
    }

    protected boolean attachStoredAllocation(Run<?, ?> owner, ExternalWorkspace workspace) {
        try {
            ExwsAllocateActionImpl action = new ExwsAllocateActionImpl();
            action.addAllocatedWorkspace(workspace);
            owner.addAction(action);
            owner.save();
            return true;
        } catch (Throwable t) {
            return false;
        }
    }

    // ------------------------------------------------------------------ files and HTTP

    protected void writeMarker(File directory, String name) throws IOException {
        Files.writeString(new File(directory, name).toPath(), SECRET, StandardCharsets.UTF_8);
    }

    protected static boolean exists(File directory, String name) {
        return new File(directory, name).exists();
    }

    protected static final class HttpResult {
        public final int status;
        public final String body;

        HttpResult(int status, String body) {
            this.status = status;
            this.body = body;
        }
    }

    protected HttpResult http(String method, String path) throws IOException {
        HttpURLConnection connection =
                (HttpURLConnection) new URL(j.getURL(), path).openConnection();
        connection.setRequestMethod(method);
        connection.setInstanceFollowRedirects(false);
        connection.setConnectTimeout(20000);
        connection.setReadTimeout(60000);
        if ("POST".equals(method)) {
            connection.setDoOutput(true);
            try (OutputStream out = connection.getOutputStream()) {
                out.write(new byte[0]);
            }
        }
        int status = connection.getResponseCode();
        InputStream in = status >= 400 ? connection.getErrorStream() : connection.getInputStream();
        String body = "";
        if (in != null) {
            try (InputStream input = in; ByteArrayOutputStream buffer = new ByteArrayOutputStream()) {
                byte[] chunk = new byte[8192];
                int read;
                while ((read = input.read(chunk)) != -1) {
                    buffer.write(chunk, 0, read);
                }
                body = new String(buffer.toByteArray(), StandardCharsets.UTF_8);
            }
        }
        connection.disconnect();
        return new HttpResult(status, body);
    }
}
