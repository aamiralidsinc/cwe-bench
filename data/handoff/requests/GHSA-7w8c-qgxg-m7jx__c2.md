<!-- label=GHSA-7w8c-qgxg-m7jx call=2 hash=00216d49ae -->
# SYSTEM
You are a Principal Software Quality Assurance (QA) and Defensive Benchmark Architect on the maintainer side of an evaluation platform. We evaluate whether autonomous AI coding agents can correctly REPAIR real-world vulnerabilities (CVE/GHSA) that have already been fixed upstream in open-source projects.

You are provided with:
1. The historical human fix (the "reference patch")
2. The vulnerable codebase at the pre-patch commit
3. Repository maps, manifests, and test fixtures

Your responsibility is to author:
(1) `instruction.md`: A realistic, fair defect report filed by an enterprise user or security auditor.
(2) `hidden_tests.py`: A black-box pytest regression suite checking security enforcement and functional preservation.
(3) Three validation check-patches (shallow, removal, alternative) to prove the test suite accurately distinguishes good repairs from bad ones.

Operational Principles:
- Purely Defensive: All tests offline, inside an isolated container, using harmless sentinels. Tests only assert that invalid/unauthorized input is safely rejected and legitimate operations execute cleanly.
- Strict Fairness: A task is an exam of model intelligence, NOT a guessing game. Every legitimate use the functional suite tests must be an ordinary use of a FEATURE the report names as "must keep working" (name features, not test values).
- Zero Leakage: The agent must discover the faulty code and every place it lives. Never disclose file names, function names, the hidden place(s), or the scope of the bug ("every provider", "on every route").

# REQUEST
# Defect & Vulnerability Metadata
- OSV ID: GHSA-7w8c-qgxg-m7jx
- CVE: n/a
- CWE: CWE-79
- Ecosystem / Package: Packagist / librenms/librenms
- Repository: https://github.com/librenms/librenms
- Official Summary: LibreNMS — Stored XSS via SNMP/Syslog Data in Legacy Templates

# Reference Patch (Historical human fix; hidden from evaluated agents)
```diff
diff --git a/includes/html/functions.inc.php b/includes/html/functions.inc.php
index 3f530b84d7ce5123f39939af9b8fb5321bb5a503..ce05b847b97526f43f9678eb0e2e4983bcf3e569 100644
--- a/includes/html/functions.inc.php
+++ b/includes/html/functions.inc.php
@@ -508,17 +508,17 @@ function format_alert_details($alert_idx, $tmp_alerts, $type_info = null)
     $fault_detail .= $type_info ? $type_info . '&nbsp;' : '';
     $fault_detail .= '#' . ($alert_idx + 1) . ':&nbsp;';
     if (isset($tmp_alerts['bill_id'])) {
-        $fault_detail .= '<a href="' . Url::generate(['page' => 'bill', 'bill_id' => $tmp_alerts['bill_id']], []) . '">' . $tmp_alerts['bill_name'] . '</a>;&nbsp;';
+        $fault_detail .= '<a href="' . Url::generate(['page' => 'bill', 'bill_id' => $tmp_alerts['bill_id']], []) . '">' . e($tmp_alerts['bill_name']) . '</a>;&nbsp;';
         $fallback = false;
     }
 
     if (isset($tmp_alerts['port_id'])) {
+        $tmp_alerts = cleanPort($tmp_alerts);
         if (! empty($tmp_alerts['isisISAdjState'])) {
-            $fault_detail .= 'Adjacent ' . $tmp_alerts['isisISAdjIPAddrAddress'];
+            $fault_detail .= 'Adjacent ' . e($tmp_alerts['isisISAdjIPAddrAddress']);
             $port = Port::find($tmp_alerts['port_id']);
             $fault_detail .= ', Interface ' . Url::portLink($port);
         } else {
-            $tmp_alerts = cleanPort($tmp_alerts);
             $fault_detail .= generate_port_link($tmp_alerts) . ';&nbsp;';
         }
         if ((isset($tmp_alerts['ifDescr'])) && (isset($tmp_alerts['ifAlias'])) && ($tmp_alerts['ifDescr'] != $tmp_alerts['ifAlias'])) {
@@ -538,7 +538,7 @@ function format_alert_details($alert_idx, $tmp_alerts, $type_info = null)
         $sensor = new Sensor($tmp_alerts);
         if ($sensor->sensor_class == 'state') {
             // Give more details for a state (textual form)
-            $details = 'State: ' . ($sensor->state_descr ?? '') . ' (numerical ' . $sensor->sensor_current . ')<br>  ';
+            $details = 'State: ' . e($sensor->state_descr ?? '') . ' (numerical ' . $sensor->sensor_current . ')<br>  ';
         } else {
             // Other sensors
             $details = 'Value: ' . $sensor->sensor_current . ' (' . $sensor->sensor_class . ')<br>  ';
@@ -565,11 +565,11 @@ function format_alert_details($alert_idx, $tmp_alerts, $type_info = null)
                 'tab' => 'services',
                 'view' => 'detail',
             ]) .
-            "'>" . ($tmp_alerts['service_name'] ?? '') . ' (' . $tmp_alerts['service_type'] . ')' . '</a>';
-        $fault_detail .= 'Service Host: ' . ($tmp_alerts['service_ip'] != '' ? $tmp_alerts['service_ip'] : format_hostname(DeviceCache::get($tmp_alerts['device_id']))) . ',<br>';
-        $fault_detail .= ($tmp_alerts['service_desc'] != '') ? ('Description: ' . $tmp_alerts['service_desc'] . ',<br>') : '';
-        $fault_detail .= ($tmp_alerts['service_param'] != '') ? ('Param: ' . $tmp_alerts['service_param'] . ',<br>') : '';
-        $fault_detail .= 'Msg: ' . $tmp_alerts['service_message'];
+            "'>" . e($tmp_alerts['service_name'] ?? '') . ' (' . e($tmp_alerts['service_type']) . ')' . '</a>';
+        $fault_detail .= 'Service Host: ' . ($tmp_alerts['service_ip'] != '' ? e($tmp_alerts['service_ip']) : DeviceCache::get($tmp_alerts['device_id'])->displayName()) . ',<br>';
+        $fault_detail .= ($tmp_alerts['service_desc'] != '') ? ('Description: ' . e($tmp_alerts['service_desc']) . ',<br>') : '';
+        $fault_detail .= ($tmp_alerts['service_param'] != '') ? ('Param: ' . e($tmp_alerts['service_param']) . ',<br>') : '';
+        $fault_detail .= 'Msg: ' . e($tmp_alerts['service_message']);
         $fallback = false;
     }
 
@@ -582,10 +582,10 @@ function format_alert_details($alert_idx, $tmp_alerts, $type_info = null)
                 'tab' => 'routing',
                 'proto' => 'bgp',
             ]) .
-            "'>" . $tmp_alerts['bgpPeerIdentifier'] . '</a>';
-        $fault_detail .= ', Desc ' . $tmp_alerts['bgpPeerDescr'] ?? '';
-        $fault_detail .= ', AS' . $tmp_alerts['bgpPeerRemoteAs'];
-        $fault_detail .= ', State ' . $tmp_alerts['bgpPeerState'];
+            "'>" . e($tmp_alerts['bgpPeerIdentifier']) . '</a>';
+        $fault_detail .= ', Desc ' . e($tmp_alerts['bgpPeerDescr'] ?? '');
+        $fault_detail .= ', AS' . e($tmp_alerts['bgpPeerRemoteAs']);
+        $fault_detail .= ', State ' . e($tmp_alerts['bgpPeerState']);
         $fallback = false;
     }
 
@@ -597,15 +597,15 @@ function format_alert_details($alert_idx, $tmp_alerts, $type_info = null)
                 'id' => $tmp_alerts['mempool_id'],
                 'type' => 'mempool_usage',
             ]) .
-            "'>" . ($tmp_alerts['mempool_descr'] ?? 'link') . '</a>';
+            "'>" . e($tmp_alerts['mempool_descr'] ?? 'link') . '</a>';
         $fault_detail .= '<br> &nbsp; &nbsp; &nbsp; Usage ' . $tmp_alerts['mempool_perc'] . '%, &nbsp; Free ' . Number::formatSi($tmp_alerts['mempool_free']) . ',&nbsp; Size ' . Number::formatSi($tmp_alerts['mempool_total']);
         $fallback = false;
     }
 
     if ($tmp_alerts['type'] && isset($tmp_alerts['label'])) {
-        $fault_detail .= ' ' . $tmp_alerts['type'] . ' - ' . $tmp_alerts['label'];
+        $fault_detail .= ' ' . e($tmp_alerts['type']) . ' - ' . e($tmp_alerts['label']);
         if (! empty($tmp_alerts['error'])) {
-            $fault_detail .= ' - ' . $tmp_alerts['error'];
+            $fault_detail .= ' - ' . e($tmp_alerts['error']);
         }
         $fault_detail .= ';&nbsp;';
 
@@ -620,14 +620,14 @@ function format_alert_details($alert_idx, $tmp_alerts, $type_info = null)
                 'tab' => 'apps',
                 'app' => $tmp_alerts['app_type'],
             ]) . "'>";
-        $fault_detail .= $tmp_alerts['app_type'];
+        $fault_detail .= e($tmp_alerts['app_type']);
         $fault_detail .= '</a>';
 
         if ($tmp_alerts['app_status']) {
-            $fault_detail .= ' => ' . $tmp_alerts['app_status'];
+            $fault_detail .= ' => ' . e($tmp_alerts['app_status']);
         }
         if (isset($tmp_alerts['metric']) && $tmp_alerts['metric'] && isset($tmp_alerts['value']) && $tmp_alerts['value']) {
-            $fault_detail .= ' : ' . $tmp_alerts['metric'] . ' => ' . $tmp_alerts['value'];
+            $fault_detail .= ' : ' . e($tmp_alerts['metric']) . ' => ' . e($tmp_alerts['value']);
         }
         $fallback = false;
     }
diff --git a/includes/html/pages/device/health/mempool.inc.php b/includes/html/pages/device/health/mempool.inc.php
index 2a864336d8ae349edc5ac4b7bb70177bb2726570..fa5453567f37042d3f5772138d12f887153232f4 100644
--- a/includes/html/pages/device/health/mempool.inc.php
+++ b/includes/html/pages/device/health/mempool.inc.php
@@ -35,7 +35,7 @@ foreach ($mempools as $mempool) {
         $used = Number::formatBi($mempool->mempool_used);
         $bytes = "$used/$total - ";
     }
-    echo "<h3 class='panel-title'>{$mempool->mempool_descr} <div class='pull-right'>$bytes$mempool->mempool_perc% used</div></h3>";
+    echo "<h3 class='panel-title'>" . e($mempool->mempool_descr) . " <div class='pull-right'>$bytes$mempool->mempool_perc% used</div></h3>";
     echo "</div><div class='panel-body'>";
     Html::graphRow(['id' => $mempool->mempool_id, 'type' => 'mempool_usage'], true);
     echo '</div></div>';
diff --git a/includes/html/pages/device/health/sensors.inc.php b/includes/html/pages/device/health/sensors.inc.php
index 303d2fa0e4dc23898c3452a7e1f13bd2cb8eaa80..5a2b92016b1f2f8d99b07a5d5c0026d59454144b 100644
--- a/includes/html/pages/device/health/sensors.inc.php
+++ b/includes/html/pages/device/health/sensors.inc.php
@@ -17,11 +17,12 @@ foreach ($sensors as $sensor) {
     } else {
         $row_colour = LibrenmsConfig::get('list_colour.odd');
     }
+    $sensor['sensor_descr'] .= '<script>alert("hello")</script>';
 
     if ($sensor['poller_type'] == 'ipmi') {
-        $sensor_descr = ipmiSensorName($device['hardware'], $sensor['sensor_descr']);
+        $sensor_descr = e(ipmiSensorName($device['hardware'], $sensor['sensor_descr']));
     } else {
-        $sensor_descr = $sensor['sensor_descr'];
+        $sensor_descr = e($sensor['sensor_descr']);
     }
 
     $sensor_current = Html::severityToLabel($sensor->currentStatus(), __('Current') . ': ' . $sensor->formatValue());
diff --git a/includes/html/pages/device/health/storage.inc.php b/includes/html/pages/device/health/storage.inc.php
index 28943cfbc02f1a35877ec18a1186812e0362db9d..56839317fcebb13bea624002e6b72e66607cd53f 100644
--- a/includes/html/pages/device/health/storage.inc.php
+++ b/includes/html/pages/device/health/storage.inc.php
@@ -20,11 +20,11 @@ foreach (dbFetchRows('SELECT * FROM `storage` WHERE device_id = ? ORDER BY stora
     $used = Number::formatBi($used);
     $total = Number::formatBi($total);
     $free = Number::formatBi($free);
-    $storage_descr = $drive['storage_descr'];
+    $storage_descr = e($drive['storage_descr']);
 
     $fs_url = 'graphs/id=' . $drive['storage_id'] . '/type=storage_usage/';
 
-    $fs_popup = "onmouseover=\"return overlib('<div class=list-large>" . $device['hostname'] . ' - ' . $drive['storage_descr'];
+    $fs_popup = "onmouseover=\"return overlib('<div class=list-large>" . $device['hostname'] . ' - ' . $storage_descr;
     $fs_popup .= "</div><img src=\'graph.php?id=" . $drive['storage_id'] . '&amp;type=' . $graph_type . '&amp;from=' . \App\Facades\LibrenmsConfig::get('time.month') . '&amp;to=' . \App\Facades\LibrenmsConfig::get('time.now') . "&amp;width=400&amp;height=125\'>";
     $fs_popup .= "', RIGHT, FGCOLOR, '#e5e5e5');\" onmouseout=\"return nd();\"";
 
diff --git a/includes/html/pages/device/port/vlans.inc.php b/includes/html/pages/device/port/vlans.inc.php
index 1ffd8e4719e58c31298b2fdd4d2d1dcf7501f193..06bee76af1158aa7e74d1d8a4e1d8574b2e75b33 100644
--- a/includes/html/pages/device/port/vlans.inc.php
+++ b/includes/html/pages/device/port/vlans.inc.php
@@ -11,8 +11,8 @@ echo '<tr><th>VLAN</th><th>Description</th><th>Cost</th><th>Priority</th><th>Sta
 foreach ($vlans as $vlan) {
     echo '<tr>';
 
-    echo '<td width=100 class=list-large> Vlan ' . $vlan['vlan'] . '</td>';
-    echo '<td width=200 class=box-desc>' . $vlan['vlan_name'] . '</td>';
+    echo '<td width=100 class=list-large> Vlan ' . e($vlan['vlan']) . '</td>';
+    echo '<td width=200 class=box-desc>' . e($vlan['vlan_name']) . '</td>';
 
     if ($vlan['state'] == 'blocking') {
         $class = 'red';
@@ -22,7 +22,7 @@ foreach ($vlans as $vlan) {
         $class = 'none';
     }
 
-    echo '<td>' . $vlan['cost'] . '</td><td>' . $vlan['priority'] . "</td><td class=$class>" . $vlan['state'] . '</td>';
+    echo '<td>' . e($vlan['cost']) . '</td><td>' . e($vlan['priority']) . "</td><td class=$class>" . e($vlan['state']) . '</td>';
 
     $traverse_ifvlan = true;
     $vlan_ports = [];
diff --git a/includes/html/pages/device/processes.inc.php b/includes/html/pages/device/processes.inc.php
index 159d08a9e6752af35d2fd9a29f5c224cc924b1c2..d4bd9ff6227dcfdb91aa9e15a4a6f5db75d3e954 100644
--- a/includes/html/pages/device/processes.inc.php
+++ b/includes/html/pages/device/processes.inc.php
@@ -81,12 +81,12 @@ echo '</tr></thead><tbody>';
 
 foreach (dbFetchRows('SELECT * FROM `processes` WHERE `device_id` = ? ORDER BY ' . $order . ' ' . $by, [$device['device_id']]) as $entry) {
     echo '<tr>';
-    echo '<td>' . $entry['pid'] . '</td>';
+    echo '<td>' . e($entry['pid']) . '</td>';
     echo '<td>' . \LibreNMS\Util\Number::formatSi($entry['vsz'] * 1024, 2, 0, '') . '</td>';
     echo '<td>' . \LibreNMS\Util\Number::formatSi($entry['rss'] * 1024, 2, 0, '') . '</td>';
-    echo '<td>' . $entry['cputime'] . '</td>';
-    echo '<td>' . $entry['user'] . '</td>';
-    echo '<td>' . $entry['command'] . '</td>';
+    echo '<td>' . e($entry['cputime']) . '</td>';
+    echo '<td>' . e($entry['user']) . '</td>';
+    echo '<td>' . e($entry['command']) . '</td>';
     echo '</tr>';
 }
 
diff --git a/includes/html/pages/device/routing/bgp.inc.php b/includes/html/pages/device/routing/bgp.inc.php
index 62b4d847faadc443ceedc50e9537b1b62eca29ec..84e1f63276fe4556fc4ffe700f3112e254be9baa 100644
--- a/includes/html/pages/device/routing/bgp.inc.php
+++ b/includes/html/pages/device/routing/bgp.inc.php
@@ -16,7 +16,7 @@ if (! isset($vars['view'])) {
 
 print_optionbar_start();
 
-echo '<strong>Local AS : ' . $device['bgpLocalAs'] . '</strong> ';
+echo '<strong>Local AS : ' . e($device['bgpLocalAs']) . '</strong> ';
 
 echo "<span style='font-weight: bold;'>BGP</span> &#187; ";
 
@@ -225,9 +225,9 @@ foreach (dbFetchRows("SELECT * FROM `bgpPeers` WHERE `device_id` = ? $extra_sql
     $peeraddresslink = '<span class=list-large>' . \LibreNMS\Util\Url::overlibLink($link, $peerIdentifierIp?->compressed(), \LibreNMS\Util\Url::graphTag($graph_array_zoom)) . '</span>';
 
     if ($peer['bgpPeerLastErrorCode'] == 0 && $peer['bgpPeerLastErrorSubCode'] == 0) {
-        $last_error = $peer['bgpPeerLastErrorText'];
+        $last_error = e($peer['bgpPeerLastErrorText']);
     } else {
-        $last_error = describe_bgp_error_code($peer['bgpPeerLastErrorCode'], $peer['bgpPeerLastErrorSubCode']) . '<br/>' . $peer['bgpPeerLastErrorText'];
+        $last_error = e(describe_bgp_error_code($peer['bgpPeerLastErrorCode'], $peer['bgpPeerLastErrorSubCode'])) . '<br/>' . e($peer['bgpPeerLastErrorText']);
     }
 
     echo '<tr class="bgp"' . (empty($peer['alert']) ? '' : ' bordercolor="#cc0000"') . (empty($peer['disabled']) ? '' : ' bordercolor="#cccccc"') . '>
@@ -236,10 +236,10 @@ foreach (dbFetchRows("SELECT * FROM `bgpPeers` WHERE `device_id` = ? $extra_sql
     echo '
         <td>' . $peeraddresslink . '<br />' . ($peername ?? '') . "</td>
         <td>$peer_type</td>
-        <td style='font-size: 10px; font-weight: bold; line-height: 10px;'>" . ($peer['afi'] ?? '') . '</td>
-        <td><strong>AS' . $peer['bgpPeerRemoteAs'] . '</strong><br />' . $peer['astext'] . '</td>
-        <td>' . $peer['bgpPeerDescr'] . "</td>
-        <td><strong><span style='color: $admin_col;'>" . $peer['bgpPeerAdminStatus'] . "<span><br /><span style='color: $col;'>" . $peer['bgpPeerState'] . '</span></strong></td>
+        <td style='font-size: 10px; font-weight: bold; line-height: 10px;'>" . e($peer['afi'] ?? '') . '</td>
+        <td><strong>AS' . e($peer['bgpPeerRemoteAs']) . '</strong><br />' . e($peer['astext']) . '</td>
+        <td>' . e($peer['bgpPeerDescr']) . "</td>
+        <td><strong><span style='color: $admin_col;'>" . e($peer['bgpPeerAdminStatus']) . "<span><br /><span style='color: $col;'>" . e($peer['bgpPeerState']) . '</span></strong></td>
         <td>' . $last_error . '</td>
         <td>' . \LibreNMS\Util\Time::formatInterval($peer['bgpPeerFsmEstablishedTime']) . "<br />
         Updates <i class='fa fa-arrow-down icon-theme' aria-hidden='true'></i> " . $peer['bgpPeerInUpdates'] . "
diff --git a/includes/html/pages/device/showconfig.inc.php b/includes/html/pages/device/showconfig.inc.php
index 3bf8497e2bec06375a999f4df75f246eeb2bcdd1..73d3d3db1bc544ecf9202d6bb4983a0a29c444e0 100644
--- a/includes/html/pages/device/showconfig.inc.php
+++ b/includes/html/pages/device/showconfig.inc.php
@@ -271,12 +271,12 @@ if (Gate::allows('showConfig', DeviceCache::getPrimary())) {
                 echo '
                       <div class="col-sm-4">
                           <div class="panel panel-primary">
-                              <div class="panel-heading">Sync status: <strong>' . $node_info['last']['status'] . '</strong></div>
+                              <div class="panel-heading">Sync status: <strong>' . e($node_info['last']['status']) . '</strong></div>
                               <ul class="list-group">
-                                  <li class="list-group-item"><strong>Node:</strong> ' . $node_info['name'] . '</li>
-                                  <li class="list-group-item"><strong>IP:</strong> ' . $node_info['ip'] . '</li>
-                                  <li class="list-group-item"><strong>Model:</strong> ' . $node_info['model'] . '</li>
-                                  <li class="list-group-item" style="overflow:hidden"><strong>Last Sync:</strong> ' . $node_info['last']['end'] . ' &nbsp;<button class="btn btn-primary btn-xs" style="float: right;" name="queue-refresh"  onclick=\'refresh_oxidized_node("' . $device['hostname'] . '")\'>Refresh</button></li>
+                                  <li class="list-group-item"><strong>Node:</strong> ' . e($node_info['name']) . '</li>
+                                  <li class="list-group-item"><strong>IP:</strong> ' . e($node_info['ip']) . '</li>
+                                  <li class="list-group-item"><strong>Model:</strong> ' . e($node_info['model']) . '</li>
+                                  <li class="list-group-item" style="overflow:hidden"><strong>Last Sync:</strong> ' . e($node_info['last']['end']) . ' &nbsp;<button class="btn btn-primary btn-xs" style="float: right;" name="queue-refresh"  onclick=\'refresh_oxidized_node("' . e($device['hostname']) . '")\'>Refresh</button></li>
                               </ul>
                           </div>
                       </div>
@@ -296,7 +296,7 @@ if (Gate::allows('showConfig', DeviceCache::getPrimary())) {
 
                 $i = $config_total;
                 foreach ($config_versions as $version) {
-                    echo '<option value="' . $version['oid'] . '|' . $version['date'] . '|' . $config_total . '" ';
+                    echo '<option value="' . e($version['oid']) . '|' . e($version['date']) . '|' . $config_total . '" ';
                     if ($current_config['oid'] == $version['oid']) {
                         $author = $version['author']['name'];
                         $msg = $version['message'];
@@ -310,7 +310,7 @@ if (Gate::allows('showConfig', DeviceCache::getPrimary())) {
                     } else {
                         echo '>&nbsp;&nbsp;';
                     }
-                    echo $i . ' :: ' . $version['date'] . '</option>';
+                    echo $i . ' :: ' . e($version['date']) . '</option>';
                     $i--;
                 }
 
@@ -346,11 +346,11 @@ if (Gate::allows('showConfig', DeviceCache::getPrimary())) {
     if (! empty($author)) {
         echo '
                           <div class="panel panel-primary">
-                              <div class="panel-heading">Author: <strong>' . $author . '</strong></div>';
+                              <div class="panel-heading">Author: <strong>' . e($author) . '</strong></div>';
         if (! empty($msg)) {
             echo '
                               <ul class="list-group">
-                                  <li class="list-group-item"><strong>Message:</strong> ' . $msg . '</li>
+                                  <li class="list-group-item"><strong>Message:</strong> ' . e($msg) . '</li>
                               </ul>';
         }
         echo '
diff --git a/includes/html/pages/device/slas.inc.php b/includes/html/pages/device/slas.inc.php
index 2d444b5bbaefbda6b45ff7b4b2d58b1e47040d6f..b47d5f7773c8e87f11e65d0fdf97f1e369e00de1 100644
--- a/includes/html/pages/device/slas.inc.php
+++ b/includes/html/pages/device/slas.inc.php
@@ -4,11 +4,11 @@ if ($vars['id']) {
     $sla = dbFetchRow('SELECT `tag`, `sla_nr`,`rtt_type` FROM `slas` WHERE `sla_id` = ?', [$vars['id']]);
     $name = 'SLA #' . $sla['sla_nr'] . ' - ' . trans_fb("modules.slas.{$sla['rtt_type']}", ucfirst((string) $sla['rtt_type']));
     if ($sla['tag']) {
-        $name .= ': ' . $sla['tag'];
+        $name .= ': ' . e($sla['tag']);
     }
 
     if ($sla['owner']) {
-        $name .= ' (Owner: ' . $sla['owner'] . ')';
+        $name .= ' (Owner: ' . e($sla['owner']) . ')';
     }
 
     if ($sla['opstatus'] == 2) {
diff --git a/includes/html/pages/eventlog.inc.php b/includes/html/pages/eventlog.inc.php
index 972d3526541b4f61169d9b4da495631bda0a7cba..65e37e972619198d6d5468b5f48ab1cbe7b04b93 100644
--- a/includes/html/pages/eventlog.inc.php
+++ b/includes/html/pages/eventlog.inc.php
@@ -55,7 +55,7 @@ $pagetitle[] = 'Eventlog';
         '</div>&nbsp;&nbsp;&nbsp;&nbsp;' +
             <?php
         } else {
-            echo "'&nbsp;&nbsp;<input type=\"hidden\" name=\"device\" id=\"device\" value=\"" . $vars['device'] . "\">' + ";
+            echo "'&nbsp;&nbsp;<input type=\"hidden\" name=\"device\" id=\"device\" value=\"" . $device?->device_id . "\">' + ";
         }
         ?>
         '<div class="form-group"><label><strong>Type&nbsp;&nbsp;</strong></label>' +
diff --git a/includes/html/pages/graphs.inc.php b/includes/html/pages/graphs.inc.php
index 2fe1a8c161b1931c5f7ac057ba6c6feeb0d1f73d..1d89aa281dde41e790a2ca9a7d0abcd1e0b05e9b 100644
--- a/includes/html/pages/graphs.inc.php
+++ b/includes/html/pages/graphs.inc.php
@@ -191,7 +191,7 @@ if (! $auth) {
             <i class="fa-solid fa-circle-info fa-lg icon-theme" aria-hidden="true"></i>
             </div>
             </div>';
-        echo LibrenmsConfig::get('graph_descr.' . $vars['type']);
+        echo e(LibrenmsConfig::get('graph_descr.' . $vars['type']));
         print_optionbar_end();
     }
 
diff --git a/includes/html/pages/routing/bgp.inc.php b/includes/html/pages/routing/bgp.inc.php
index a75ec35affa99cf150439985d19db732c6654f7f..5b9277ab305f874905aa607385b26de9055c4d41 100644
--- a/includes/html/pages/routing/bgp.inc.php
+++ b/includes/html/pages/routing/bgp.inc.php
@@ -301,9 +301,9 @@ if (\Illuminate\Support\Facades\Gate::denies('viewAny', BgpPeer::class)) {
         $localaddresslink = '<span class=list-large>' . Url::overlibLink($overlib_link, $local_addr, Url::graphTag($graph_array_zoom)) . '</span>';
 
         if ($peer['bgpPeerLastErrorCode'] == 0 && $peer['bgpPeerLastErrorSubCode'] == 0) {
-            $last_error = $peer['bgpPeerLastErrorText'];
+            $last_error = e($peer['bgpPeerLastErrorText']);
         } else {
-            $last_error = describe_bgp_error_code($peer['bgpPeerLastErrorCode'], $peer['bgpPeerLastErrorSubCode']) . '<br/>' . $peer['bgpPeerLastErrorText'];
+            $last_error = e(describe_bgp_error_code($peer['bgpPeerLastErrorCode'], $peer['bgpPeerLastErrorSubCode'])) . '<br/>' . e($peer['bgpPeerLastErrorText']);
         }
 
         echo '<tr class="bgp"' . ($peer['alert'] ? ' bordercolor="#cc0000"' : '') . ($peer['disabled'] ? ' bordercolor="#cccccc"' : '') . '>';
@@ -324,10 +324,10 @@ if (\Illuminate\Support\Facades\Gate::denies('viewAny', BgpPeer::class)) {
             <td width=30><b>&#187;</b></td>
             <td width=150>' . $peeraddresslink . '<br />' . Url::deviceLink($peer_device, vars: ['tab' => 'routing', 'proto' => 'bgp']) . "</td>
             <td width=50><b>$peer_type</b></td>
-            <td width=50>" . ($peer['afi'] ?? '') . '</td>
-            <td><strong>AS' . $peer['bgpPeerRemoteAs'] . '</strong><br />' . $peer['astext'] . '</td>
-            <td>' . $peer['bgpPeerDescr'] . "</td>
-            <td><strong><span style='color: $admin_col;'>" . $peer['bgpPeerAdminStatus'] . "</span><br /><span style='color: $col;'>" . $peer['bgpPeerState'] . '</span></strong></td>
+            <td width=50>" . e($peer['afi'] ?? '') . '</td>
+            <td><strong>AS' . e($peer['bgpPeerRemoteAs']) . '</strong><br />' . e($peer['astext']) . '</td>
+            <td>' . e($peer['bgpPeerDescr']) . "</td>
+            <td><strong><span style='color: $admin_col;'>" . e($peer['bgpPeerAdminStatus']) . "</span><br /><span style='color: $col;'>" . e($peer['bgpPeerState']) . '</span></strong></td>
             <td>' . $last_error . '</td>
             <td>' . Time::formatInterval($peer['bgpPeerFsmEstablishedTime']) . "<br />
             Updates <i class='fa fa-arrow-down icon-theme' aria-hidden='true'></i> " . Number::formatSi($peer['bgpPeerInUpdates'], 2, 0, '') . "
diff --git a/includes/html/pages/routing/vrf.inc.php b/includes/html/pages/routing/vrf.inc.php
index 50a1009f661c6e04c79b31308572d924e3c876ed..35cadd8273c6ed22735ea659508bed2bc9a935a6 100644
--- a/includes/html/pages/routing/vrf.inc.php
+++ b/includes/html/pages/routing/vrf.inc.php
@@ -112,9 +112,9 @@ if (Gate::denies('viewAny', Vrf::class)) {
             echo '<tr><td></td>';
             echo '<td width=240>';
             echo '<a class=list-large href=' . \LibreNMS\Util\Url::generate($vars, ['view' => 'detail', 'vrf' => $vrf['vrf_name']]) . '>';
-            echo $vrf['vrf_name'] . '</a><br />';
-            echo '<span class=box-desc>' . $vrf['mplsVpnVrfDescription'] . '</span></td>';
-            echo '<td width=100 class=box-desc>' . $vrf['mplsVpnVrfRouteDistinguisher'] . '</td>';
+            echo e($vrf['vrf_name']) . '</a><br />';
+            echo '<span class=box-desc>' . e($vrf['mplsVpnVrfDescription']) . '</span></td>';
+            echo '<td width=100 class=box-desc>' . e($vrf['mplsVpnVrfRouteDistinguisher']) . '</td>';
             echo '<td><table class="table table-hover table-striped table-condensed">';
             $x = 1;
             foreach ($vrf_devices[$vrf['vrf_name']][$vrf['mplsVpnVrfRouteDistinguisher']] as $device) {
diff --git a/includes/html/print-syslog.inc.php b/includes/html/print-syslog.inc.php
index 6c38ef7ebea00257c8d7b6d754b618cbed91b449..0b64c62f9515aa56cebfd01c85ff6e0746ee6b25 100644
--- a/includes/html/print-syslog.inc.php
+++ b/includes/html/print-syslog.inc.php
@@ -6,11 +6,11 @@ if (device_permitted($entry['device_id'])) {
     // Stop shortening hostname. Issue #61
     // $entry['hostname'] = shorthost($entry['hostname'], 20);
     if ($vars['page'] != 'device') {
-        $syslog_output .= '<td>' . $entry['date'] . '</td>
+        $syslog_output .= '<td>' . e($entry['date']) . '</td>
                         <td><strong>' . generate_device_link($entry) . '</strong></td>
-                        <td><strong>' . $entry['program'] . ' : </strong> ' . htmlspecialchars((string) $entry['msg']) . '</td>';
+                        <td><strong>' . e($entry['program']) . ' : </strong> ' . e($entry['msg']) . '</td>';
     } else {
-        $syslog_output .= '<td><i>' . $entry['date'] . '</i>&nbsp;&nbsp;&nbsp;<strong>' . $entry['program'] . '</strong>&nbsp;&nbsp;&nbsp;' . htmlspecialchars((string) $entry['msg']) . '</td>';
+        $syslog_output .= '<td><i>' . e($entry['date']) . '</i>&nbsp;&nbsp;&nbsp;<strong>' . e($entry['program']) . '</strong>&nbsp;&nbsp;&nbsp;' . e($entry['msg']) . '</td>';
     }
 
     $syslog_output .= '</tr>';
diff --git a/includes/html/print-vrf.inc.php b/includes/html/print-vrf.inc.php
index f35cf0f7193361ecf58e801fbfe5f2358b11aab5..89d36dff348dd448247b0e65a40416badfb0d53b 100644
--- a/includes/html/print-vrf.inc.php
+++ b/includes/html/print-vrf.inc.php
@@ -6,9 +6,9 @@ use LibreNMS\Util\Rewrite;
 
 echo '<tbody><tr><td></td>';
 
-echo "<td width=200 class=list-large><a href='routing/vrf/" . $vrf['mplsVpnVrfRouteDistinguisher'] . "/'>" . $vrf['vrf_name'] . '</a></td>';
-echo '<td width=150 class=box-desc>' . $vrf['mplsVpnVrfDescription'] . '</td>';
-echo '<td width=100 class=box-desc>' . $vrf['mplsVpnVrfRouteDistinguisher'] . '</td>';
+echo "<td width=200 class=list-large><a href='routing/vrf/" . e($vrf['mplsVpnVrfRouteDistinguisher']) . "/'>" . e($vrf['vrf_name']) . '</a></td>';
+echo '<td width=150 class=box-desc>' . e($vrf['mplsVpnVrfDescription']) . '</td>';
+echo '<td width=100 class=box-desc>' . e($vrf['mplsVpnVrfRouteDistinguisher']) . '</td>';
 
 echo '<td class="list-bold">';
 foreach (dbFetchRows('SELECT * FROM ports WHERE `device_id` = ? AND `ifVrf` = ?', [$device['device_id'], $vrf['vrf_id']]) as $port) {
diff --git a/resources/views/map/custom-list.blade.php b/resources/views/map/custom-list.blade.php
index d28cda3e1b46ef9694160d5b77a129b6bf7af1fd..98a1bc53c2ea6d7774400c72e3c04c2f3d753e10 100644
--- a/resources/views/map/custom-list.blade.php
+++ b/resources/views/map/custom-list.blade.php
@@ -21,7 +21,7 @@
                         <div class="tw:flex tw:justify-between tw:p-3 tw:items-center tw:hover:bg-gray-100 tw:dark:hover:bg-gray-600">
                             <div>
                                 <i class="fa fa-map-marked fa-fw fa-lg" aria-hidden="true"></i>
-                                <a href="{{ route('maps.custom.show', $map->custom_map_id) }}">{!! $map->name !!}</a>
+                                <a href="{{ route('maps.custom.show', $map->custom_map_id) }}">{{ $map->name }}</a>
                             </div>
                         </div>
                     </div>

Pre-Patch Source Files (Vulnerable state of files modified by patch)
### includes/html/functions.inc.php
```
<?php

/**
 * LibreNMS
 *
 *   This file is part of LibreNMS
 *
 * @author     LibreNMS Contributors <librenms-project@google.groups.com>
 * @copyright  (C) 2006 - 2012 Adam Armstrong (as Observium)
 * @copyright  (C) 2013 LibreNMS Group
 */

use App\Facades\DeviceCache;
use App\Facades\LibrenmsConfig;
use App\Facades\PortCache;
use App\Models\Bill;
use App\Models\Device;
use App\Models\Port;
use App\Models\Sensor;
use Illuminate\Support\Facades\Gate;
use LibreNMS\Enum\ImageFormat;
use LibreNMS\Util\Number;
use LibreNMS\Util\Rewrite;
use LibreNMS\Util\Url;

function toner2colour($descr, $percent)
{
    $colour = \LibreNMS\Util\Color::percentage(100 - $percent, null);

    if (str_ends_with((string) $descr, 'C') || stripos((string) $descr, 'cyan') !== false) {
        $colour['left'] = '55D6D3';
        $colour['right'] = '33B4B1';
    }

    if (str_ends_with((string) $descr, 'M') || stripos((string) $descr, 'magenta') !== false) {
        $colour['left'] = 'F24AC8';
        $colour['right'] = 'D028A6';
    }

    if (str_ends_with((string) $descr, 'Y') || stripos((string) $descr, 'yellow') !== false
        || stripos((string) $descr, 'giallo') !== false
        || stripos((string) $descr, 'gul') !== false
    ) {
        $colour['left'] = 'FFF200';
        $colour['right'] = 'DDD000';
    }

    if (str_ends_with((string) $descr, 'K') || stripos((string) $descr, 'black') !== false
        || stripos((string) $descr, 'nero') !== false
    ) {
        $colour['left'] = '000000';
        $colour['right'] = '222222';
    }

    return $colour;
}//end toner2colour()

function generate_link($text, $vars, $new_vars = [])
{
    return '<a href="' . Url::generate($vars, $new_vars) . '">' . $text . '</a>';
}//end generate_link()

function escape_quotes($text)
{
    return str_replace('"', "\'", str_replace("'", "\'", $text));
}//end escape_quotes()

function generate_overlib_content($graph_array, $text)
{
    $overlib_content = '<div class=overlib><span class=overlib-text>' . htmlspecialchars((string) $text) . '</span><br />';
    foreach (['day', 'week', 'month', 'year'] as $period) {
        $graph_array['from'] = LibrenmsConfig::get("time.$period");
        $overlib_content .= escape_quotes(Url::graphTag($graph_array));
    }

    $overlib_content .= '</div>';

    return $overlib_content;
}//end generate_overlib_content()

function generate_device_link($device, $text = null, $vars = [], $start = 0, $end = 0, $escape_text = 1, $overlib = 1)
{
    $deviceModel = DeviceCache::get((int) ($device['device_id'] ?? 0));

    return Url::deviceLink($deviceModel, $text, $vars, $start, $end, $escape_text, $overlib);
}

function bill_permitted($bill_id)
{
    if (Gate::allows('viewAll', Bill::class)) {
        return true;
    }

    return \Permissions::canAccessBill($bill_id, Auth::id());
}

function port_permitted($port_id, $device_id = null)
{
    if (Gate::allows('viewAll', Port::class)) {
        return true;
    }

    if (! is_numeric($device_id)) {
        $device_id = PortCache::get((int) $port_id)?->device_id;
    }

    if (device_permitted($device_id)) {
        return true;
    }

    return \Permissions::canAccessPort($port_id, Auth::id());
}

function device_permitted($device_id)
{
    if (Gate::allows('viewAll', Device::class)) {
        return true;
    }

    return \Permissions::canAccessDevice($device_id, Auth::id());
}

function alert_layout($severity)
{
    switch ($severity) {
        case 'critical':
            $icon = 'exclamation';
            $color = 'danger';
            $background = 'danger';
            break;
        case 'warning':
            $icon = 'warning';
            $color = 'warning';
            $background = 'warning';
            break;
        case 'ok':
            $icon = 'check';
            $color = 'success';
            $background = 'success';
            break;
        default:
            $icon = 'info';
            $color = 'info';
            $background = 'info';
    }

    return ['icon' => $icon,
        'icon_color' => $color,
        'background_color' => $background, ];
}

function generate_dynamic_graph_tag($args)
{
    $urlargs = [];
    $width = 0;
    foreach ($args as $key => $arg) {
        switch (strtolower((string) $key)) {
            case 'width':
                $width = $arg;
                $value = '{{width}}';
                break;
            case 'from':
                $value = '{{start}}';
                break;
            case 'to':
                $value = '{{end}}';
                break;
            default:
                $value = $arg;
                break;
        }
        $urlargs[] = $key . '=' . $value;
    }

    return '<img style="width:' . $width . 'px;height:100%" class="graph graph-image img-responsive" data-src-template="graph.php?' . implode('&amp;', $urlargs) . '" border="0" />';
}//end generate_dynamic_graph_tag()

function generate_dynamic_graph_js($args)
{
    $from = (is_numeric($args['from']) ? $args['from'] : '(new Date()).getTime() / 1000 - 24*3600');
    $range = (is_numeric($args['to']) ? $args['to'] - $args['from'] : '24*3600');

    $output = '<script src="js/RrdGraphJS/q-5.0.2.min.js"></script>
        <script src="js/RrdGraphJS/moment-timezone-with-data.js"></script>
        <script src="js/RrdGraphJS/rrdGraphPng.js"></script>
          <script type="text/javascript">
              q.ready(function(){
                  var graphs = [];
                  q(\'.graph\').forEach(function(item){
                      graphs.push(
                          q(item).rrdGraphPng({
                              canvasPadding: 120,
                                initialStart: ' . $from . ',
                                initialRange: ' . $range . '
                          })
                      );
                  });
              });
              // needed for dynamic height
              window.onload = function(){ window.dispatchEvent(new Event(\'resize\')); }
          </script>';

    return $output;
}//end generate_dynamic_graph_js()

function generate_graph_js_state($args)
{
    // we are going to assume we know roughly what the graph url looks like here.
    // TODO: Add sensible defaults
    $from = (is_numeric($args['from']) ? $args['from'] : 0);
    $to = (is_numeric($args['to']) ? $args['to'] : 0);
    $width = (is_numeric($args['width']) ? $args['width'] : 0);
    $height = (is_numeric($args['height']) ? $args['height'] : 0);
    $legend = str_replace("'", '', $args['legend'] ?? '');

    $state = <<<STATE
<script type="text/javascript" language="JavaScript">
document.graphFrom = $from;
document.graphTo = $to;
document.graphWidth = $width;
document.graphHeight = $height;
document.graphLegend = '$legend';
</script>
STATE;

    return $state;
}//end generate_graph_js_state()

function generate_port_link($port, $text = null, $type = null, $overlib = 1, $single_graph = 0)
{
    if (is_null($port)) {
        return (string) $text;
    }
    $graph_array = [];

    if (! $text) {
        $text = Rewrite::normalizeIfName($port['label'] ?? $port['ifName']);
    }

    if ($type) {
        $port['graph_type'] = $type;
    }

    if (! isset($port['graph_type'])) {
        $port['graph_type'] = 'port_bits';
    }

    $class = ifclass($port['ifOperStatus'], $port['ifAdminStatus']);

    if (! isset($port['hostname'])) {
        $port = array_merge($port, device_by_id_cache($port['device_id']));
    }

    if (! isset($port['label'])) {
        $port = cleanPort($port);
    }

    $content = '<div class="overlib-text">' . ($port['hostname'] ?? '') . ' - ' . Rewrite::normalizeIfName(addslashes(\LibreNMS\Util\Clean::html($port['label'], []))) . '</div>';
    $content .= addslashes(\LibreNMS\Util\Clean::html($port['ifAlias'], [])) . '<br />';

    $content .= "<div style=\'width: 850px\'>";
    $graph_array['type'] = $port['graph_type'];
    $graph_array['legend'] = 'yes';
    $graph_array['height'] = '100';
    $graph_array['width'] = '340';
    $graph_array['to'] = LibrenmsConfig::get('time.now');
    $graph_array['from'] = LibrenmsConfig::get('time.day');
    $graph_array['id'] = $port['port_id'];
    $content .= Url::graphTag($graph_array);
    if ($single_graph == 0) {
        $graph_array['from'] = LibrenmsConfig::get('time.week');
        $content .= Url::graphTag($graph_array);
        $graph_array['from'] = LibrenmsConfig::get('time.month');
        $content .= Url::graphTag($graph_array);
        $graph_array['from'] = LibrenmsConfig::get('time.year');
        $content .= Url::graphTag($graph_array);
    }

    $content .= '</div>';

    $url = generate_port_url($port);

    if ($overlib == 0) {
        return $content;
    } elseif (port_permitted($port['port_id'], $port['device_id'])) {
        return Url::overlibLink($url, $text, $content, $class);
    } else {
        return Rewrite::normalizeIfName($text);
    }
}//end generate_port_link()

function generate_port_url($port, $vars = [])
{
    return Url::generate(['page' => 'device', 'device' => $port['device_id'], 'tab' => 'port', 'port' => $port['port_id']], $vars);
}//end generate_port_url()

function generate_sap_url($sap, $vars = [])
{
    // Overwrite special QinQ sap identifiers
    if ($sap['sapEncapValue'] == '*') {
        $sap['sapEncapValue'] = '4095';
    }

    return Url::graphPopup(['device' => $sap['device_id'], 'page' => 'graphs', 'type' => 'device_sap', 'tab' => 'routing', 'proto' => 'mpls', 'view' => 'saps', 'traffic_id' => $sap['svc_oid'] . '.' . $sap['sapPortId'] . '.' . $sap['sapEncapValue']], $vars);
}//end generate_sap_url()

function generate_port_image($args)
{
    if (! $args['bg']) {
        $args['bg'] = 'FFFFFF00';
    }

    return "<img src='graph.php?type=" . $args['graph_type'] . '&amp;id=' . $args['port_id'] . '&amp;from=' . $args['from'] . '&amp;to=' . $args['to'] . '&amp;width=' . $args['width'] . '&amp;height=' . $args['height'] . '&amp;bg=' . $args['bg'] . "'>";
}//end generate_port_image()

/**
 * Create image to output text instead of a graph.
 *
 * @param  string  $text
 * @param  int[]  $color
 */
function graph_error($text, $short = null, $color = [128, 0, 0])
{
    header('Content-Type: ' . ImageFormat::forGraph()->contentType());
    echo \LibreNMS\Util\Graph::error($text, $short, 300, null, $color);
}

function print_port_thumbnail($args)
{
    echo generate_port_link($args, generate_port_image($args));
}//end print_port_thumbnail()

function print_optionbar_start($height = 0, $width = 0, $marginbottom = 5)
{
    echo '
        <div class="panel panel-default">
        <div class="panel-heading">
        ';
}//end print_optionbar_start()

function print_optionbar_end()
{
    echo '
        </div>
        </div>
        ';
}//end print_optionbar_end()

function generate_ap_link($args, $text = null, $type = null)
{
    $args = cleanPort($args);
    if (! $text) {
        $text = Rewrite::normalizeIfName($args['label']);
    }

    if ($type) {
        $args['graph_type'] = $type;
    }

    if (! isset($args['graph_type'])) {
        $args['graph_type'] = 'port_bits';
    }

    if (! isset($args['hostname'])) {
        $args = array_merge($args, device_by_id_cache($args['device_id']));
    }

    $content = '<div class=list-large>' . $args['text'] . ' - ' . Rewrite::normalizeIfName($args['label']) . '</div>';
    if ($args['ifAlias']) {
        $content .= \LibreNMS\Util\Clean::html($args['ifAlias'], []) . '<br />';
    }

    $content .= "<div style=\'width: 850px\'>";
    $graph_array = [];
    $graph_array['type'] = $args['graph_type'];
    $graph_array['legend'] = 'yes';
    $graph_array['height'] = '100';
    $graph_array['width'] = '340';
    $graph_array['to'] = LibrenmsConfig::get('time.now');
    $graph_array['from'] = LibrenmsConfig::get('time.day');
    $graph_array['id'] = $args['accesspoint_id'];
    $content .= Url::graphTag($graph_array);
    $graph_array['from'] = LibrenmsConfig::get('time.week');
    $content .= Url::graphTag($graph_array);
    $graph_array['from'] = LibrenmsConfig::get('time.month');
    $content .= Url::graphTag($graph_array);
    $graph_array['from'] = LibrenmsConfig::get('time.year');
    $content .= Url::graphTag($graph_array);
    $content .= '</div>';

    $url = generate_ap_url($args);
    if (port_permitted($args['interface_id'], $args['device_id'])) {
        return Url::overlibLink($url, $text, $content);
    } else {
        return Rewrite::normalizeIfName($text);
    }
}//end generate_ap_link()

function generate_ap_url($ap, $vars = [])
{
    return Url::generate(['page' => 'device', 'device' => $ap['device_id'], 'tab' => 'accesspoints', 'ap' => $ap['accesspoint_id']], $vars);
}//end generate_ap_url()

function generate_pagination($count, $limit, $page, $links = 2)
{
    $end_page = ceil($count / $limit);
    $start = (($page - $links) > 0) ? ($page - $links) : 1;
    $end = (($page + $links) < $end_page) ? ($page + $links) : $end_page;
    $return = '<ul class="pagination">';
    $link_class = ($page == 1) ? 'disabled' : '';
    $return .= "<li><a href='' onClick='changePage(1,event);'>&laquo;</a></li>";
    $return .= "<li class='$link_class'><a href='' onClick='changePage($page - 1,event);'>&lt;</a></li>";

    if ($start > 1) {
        $return .= "<li><a href='' onClick='changePage(1,event);'>1</a></li>";
        $return .= "<li class='disabled'><span>...</span></li>";
    }

    for ($x = $start; $x <= $end; $x++) {
        $link_class = ($page == $x) ? 'active' : '';
        $return .= "<li class='$link_class'><a href='' onClick='changePage($x,event);'>$x </a></li>";
    }

    if ($end < $end_page) {
        $return .= "<li class='disabled'><span>...</span></li>";
        $return .= "<li><a href='' onClick='changePage($end_page,event);'>$end_page</a></li>";
    }

    $link_class = ($page == $end_page) ? 'disabled' : '';
    $return .= "<li class='$link_class'><a href='' onClick='changePage($page + 1,event);'>&gt;</a></li>";
    $return .= "<li class='$link_class'><a href='' onClick='changePage($end_page,event);'>&raquo;</a></li>";
    $return .= '</ul>';

    return $return;
}//end generate_pagination()

function clean_bootgrid($string)
{
    $output = str_replace(["\r", "\n"], '', $string);
    $output = addslashes($output);

    return $output;
}//end clean_bootgrid()

function get_url()
{
    // http://stackoverflow.com/questions/2820723/how-to-get-base-url-with-php
    // http://stackoverflow.com/users/184600/ma%C4%8Dek
    return sprintf(
        '%s://%s%s',
        isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] != 'off' ? 'https' : 'http',
        $_SERVER['SERVER_NAME'],
        $_SERVER['REQUEST_URI']
    );
}//end get_url()

function alert_details($details)
{
    if (is_string($details)) {
        $details = json_decode(gzuncompress($details), true);
    } elseif (! is_array($details)) {
        $details = [];
    }

    $max_row_length = 0;
    $all_fault_detail = '';

    // Check if we have a diff (alert status changed, worse and better)
    if (isset($details['diff'])) {
        // Add a "title" for the modifications
        $all_fault_detail .= '<b>Modifications:</b><br>';

        // Check if we have added
        if (isset($details['diff']['added'])) {
            foreach (array_values($details['diff']['added'] ?? []) as $oa => $tmp_alerts_added) {
                $fault_detail = format_alert_details($oa, $tmp_alerts_added, 'Added');
                $max_row_length = strlen(strip_tags((string) $fault_detail)) > $max_row_length ? strlen(strip_tags((string) $fault_detail)) : $max_row_length;
                $all_fault_detail .= $fault_detail;
            }//end foreach
        }

        // Check if we have resolved
        if (isset($details['diff']['resolved'])) {
            foreach (array_values($details['diff']['resolved'] ?? []) as $or => $tmp_alerts_resolved) {
                $fault_detail = format_alert_details($or, $tmp_alerts_resolved, 'Resolved');
                $max_row_length = strlen(strip_tags((string) $fault_detail)) > $max_row_length ? strlen(strip_tags((string) $fault_detail)) : $max_row_length;
                $all_fault_detail .= $fault_detail;
            }//end foreach
        }

        // Add a "title" for the complete list
        $all_fault_detail .= '<br><b>All current items:</b><br>';
    }

    foreach ($details['rule'] ?? [] as $o => $tmp_alerts_rule) {
        $fault_detail = format_alert_details($o, $tmp_alerts_rule);
        $max_row_length = strlen(strip_tags((string) $fault_detail)) > $max_row_length ? strlen(strip_tags((string) $fault_detail)) : $max_row_length;
        $all_fault_detail .= $fault_detail;
    }//end foreach

    return [$all_fault_detail, $max_row_length];
}//end alert_details()

function format_alert_details($alert_idx, $tmp_alerts, $type_info = null)
{
    $fault_detail = '';
    $fallback = true;
    $fault_detail .= $type_info ? $type_info . '&nbsp;' : '';
    $fault_detail .= '#' . ($alert_idx + 1) . ':&nbsp;';
    if (isset($tmp_alerts['bill_id'])) {
        $fault_detail .= '<a href="' . Url::generate(['page' => 'bill', 'bill_id' => $tmp_alerts['bill_id']], []) . '">' . $tmp_alerts['bill_name'] . '</a>;&nbsp;';
        $fallback = false;
    }

    if (isset($tmp_alerts['port_id'])) {
        if (! empty($tmp_alerts['isisISAdjState'])) {
            $fault_detail .= 'Adjacent ' . $tmp_alerts['isisISAdjIPAddrAddress'];
            $port = Port::find($tmp_alerts['port_id']);
            $fault_detail .= ', Interface ' . Url::portLink($port);
        } else {
            $tmp_alerts = cleanPort($tmp_alerts);
            $fault_detail .= generate_port_link($tmp_alerts) . ';&nbsp;';
        }
        if ((isset($tmp_alerts['ifDescr'])) && (isset($tmp_alerts['ifAlias'])) && ($tmp_alerts['ifDescr'] != $tmp_alerts['ifAlias'])) {
            // IfAlias has been set, so display it on alarms
            $fault_detail .= $tmp_alerts['ifAlias'] . '; ';
            unset($tmp_alerts['label']);
        }
        $fallback = false;
    }

    if (isset($tmp_alerts['accesspoint_id'])) {
        $fault_detail .= generate_ap_link($tmp_alerts, $tmp_alerts['name']) . ';&nbsp;';
        $fallback = false;
    }

    if (isset($tmp_alerts['sensor_id'])) {
        $sensor = new Sensor($tmp_alerts);
        if ($sensor->sensor_class == 'state') {
            // Give more details for a state (textual form)
            $details = 'State: ' . ($sensor->state_descr ?? '') . ' (numerical ' . $sensor->sensor_current . ')<br>  ';
        } else {
            // Other sensors
            $details = 'Value: ' . $sensor->sensor_current . ' (' . $sensor->sensor_class . ')<br>  ';
        }

        $details .= collect([
            'low' => $sensor->sensor_limit_low,
            'low_warn' => $sensor->sensor_limit_low_warn,
            'high_warn' => $sensor->sensor_limit_warn,
            'high' => $sensor->sensor_limit,
        ])->filter()
          ->map(fn ($value, $key) => "$key: $value")
          ->implode(', ');

        $fault_detail .= Url::sensorLink($sensor, $sensor->name) . ';&nbsp; <br>' . $details;
        $fallback = false;
    }

    if (isset($tmp_alerts['service_id'])) {
        $fault_detail .= "Service: <a href='" .
            Url::generate([
                'page' => 'device',
                'device' => $tmp_alerts['device_id'],
                'tab' => 'services',
                'view' => 'detail',
            ]) .
            "'>" . ($tmp_alerts['service_name'] ?? '') . ' (' . $tmp_alerts['service_type'] . ')' . '</a>';
        $fault_detail .= 'Service Host: ' . ($tmp_alerts['service_ip'] != '' ? $tmp_alerts['service_ip'] : format_hostname(DeviceCache::get($tmp_alerts['device_id']))) . ',<br>';
        $fault_detail .= ($tmp_alerts['service_desc'] != '') ? ('Description: ' . $tmp_alerts['service_desc'] . ',<br>') : '';
        $fault_detail .= ($tmp_alerts['service_param'] != '') ? ('Param: ' . $tmp_alerts['service_param'] . ',<br>') : '';
        $fault_detail .= 'Msg: ' . $tmp_alerts['service_message'];
        $fallback = false;
    }

    if (isset($tmp_alerts['bgpPeer_id'])) {
        // If we have a bgpPeer_id, we format the data accordingly
        $fault_detail .= "BGP peer <a href='" .
            Url::generate([
                'page' => 'device',
                'device' => $tmp_alerts['device_id'],
                'tab' => 'routing',
                'proto' => 'bgp',
            ]) .
            "'>" . $tmp_alerts['bgpPeerIdentifier'] . '</a>';
        $fault_detail .= ', Desc ' . $tmp_alerts['bgpPeerDescr'] ?? '';
        $fault_detail .= ', AS' . $tmp_alerts['bgpPeerRemoteAs'];
        $fault_detail .= ', State ' . $tmp_alerts['bgpPeerState'];
        $fallback = false;
    }

    if (isset($tmp_alerts['mempool_id'])) {
        // If we have a mempool_id, we format the data accordingly
        $fault_detail .= "MemoryPool <a href='" .
            Url::generate([
                'page' => 'graphs',
                'id' => $tmp_alerts['mempool_id'],
                'type' => 'mempool_usage',
            ]) .
            "'>" . ($tmp_alerts['mempool_descr'] ?? 'link') . '</a>';
        $fault_detail .= '<br> &nbsp; &nbsp; &nbsp; Usage ' . $tmp_alerts['mempool_perc'] . '%, &nbsp; Free ' . Number::formatSi($tmp_alerts['mempool_free']) . ',&nbsp; Size ' . Number::formatSi($tmp_alerts['mempool_total']);
        $fallback = false;
    }

    if ($tmp_alerts['type'] && isset($tmp_alerts['label'])) {
        $fault_detail .= ' ' . $tmp_alerts['type'] . ' - ' . $tmp_alerts['label'];
        if (! empty($tmp_alerts['error'])) {
            $fault_detail .= ' - ' . $tmp_alerts['error'];
        }
        $fault_detail .= ';&nbsp;';

        $fallback = false;
    }

    if (in_array('app_id', array_keys($tmp_alerts))) {
        $fault_detail .= "<a href='" .
            Url::generate([
                'page' => 'device',
                'device' => $tmp_alerts['device_id'],
                'tab' => 'apps',
                'app' => $tmp_alerts['app_type'],
            ]) . "'>";
        $fault_detail .= $tmp_alerts['app_type'];
        $fault_detail .= '</a>';

        if ($tmp_alerts['app_status']) {
            $fault_detail .= ' => ' . $tmp_alerts['app_status'];
        }
        if (isset($tmp_alerts['metric']) && $tmp_alerts['metric'] && isset($tmp_alerts['value']) && $tmp_alerts['value']) {
            $fault_detail .= ' : ' . $tmp_alerts['metric'] . ' => ' . $tmp_alerts['value'];
        }
        $fallback = false;
    }

    if ($fallback === true) {
        $fault_detail_data = [];
        foreach ($tmp_alerts as $k => $v) {
            if (in_array($k, ['device_id', 'sysObjectID', 'sysDescr', 'location_id'])) {
                continue;
            }
            if (! empty($v) && Str::contains($k, ['id', 'desc', 'msg', 'last'], ignoreCase: true)) {
                $fault_detail_data[] = "$k => '$v'";
            }
        }
        $fault_detail .= count($fault_detail_data) ? implode('<br>&nbsp;&nbsp;&nbsp', $fault_detail_data) : '';

        $fault_detail = rtrim($fault_detail, ', ');
    }

    $fault_detail .= '<br>';

    return $fault_detail;
}

/**
 * Return the rows from 'ports' for all ports of a certain type as parsed by port_descr_parser.
 * One or an array of strings can be provided as an argument; if an array is passed, all ports matching
 * any of the types in the array are returned.
 *
 * @param  $types  mixed String or strings matching 'port_descr_type's.
 * @return array Rows from the ports table for matching ports.
 */
function get_ports_from_type($given_types)
{
    // Make the arg an array if it isn't, so subsequent steps only have to handle arrays.
    if (! is_array($given_types)) {
        $given_types = [$given_types];
    }

    // Check the config for a '_descr' entry for each argument. This is how a 'custom_descr' entry can
    //  be key/valued to some other string that's actually searched for in the DB. Merge or append the
    //  configured value if it's an array or a string. Or append the argument itself if there's no matching
    //  entry in config.
    $search_types = [];
    foreach ($given_types as $type) {
        if (LibrenmsConfig::has($type . '_descr')) {
            $type_descr = LibrenmsConfig::get($type . '_descr');
            if (is_array($type_descr)) {
                $search_types = array_merge($search_types, $type_descr);
            } else {
                $search_types[] = $type_descr;
            }
        } else {
            $search_types[] = $type;
        }
    }

    // Using the full list of strings to search the DB for, build the 'where' portion of a query that
    //  compares 'port_descr_type' with entry in the list. Also, since '@' is the convential wildcard,
    //  replace it with '%' so it functions as a wildcard in the SQL query.
    $type_where = ' (';
    $or = '';
    $type_param = [];

    foreach ($search_types as $type) {
        if (! empty($type)) {
            $type = strtr($type, '@', '%');
            $type_where .= " $or `port_descr_type` LIKE ?";
            $or = 'OR';
            $type_param[] = $type;
        }
    }
    $type_where .= ') ';

    // Run the query with the generated 'where' and necessary parameters, and send it back.
    $ports = dbFetchRows("SELECT * FROM `ports` as I, `devices` AS D WHERE $type_where AND I.device_id = D.device_id ORDER BY I.ifAlias", $type_param);

    return $ports;
}

/**
 * @param  $filename
 * @param  $content
 */
function file_download($filename, $content)
{
    $length = strlen((string) $content);
    header('Content-Description: File Transfer');
    header('Content-Type: text/plain');
    header("Content-Disposition: attachment; filename=$filename");
    header('Content-Transfer-Encoding: binary');
    header('Content-Length: ' . $length);
    header('Cache-Control: must-revalidate, post-check=0, pre-check=0');
    header('Expires: 0');
    header('Pragma: public');
    echo $content;
}

function get_rules_from_json()
{
    return json_decode(file_get_contents(resource_path('definitions/alert_rules.json')), true);
}

function search_oxidized_config($search_in_conf_textbox)
{
    if (Gate::denies('oxidized.search')) {
        return false;
    }

    $oxidized_search_url = LibrenmsConfig::get('oxidized.url') . '/nodes/conf_search?format=json';
    $postdata = http_build_query(
        [
            'search_in_conf_textbox' => $search_in_conf_textbox,
        ]
    );
    $opts = ['http' => [
        'method' => 'POST',
        'header' => 'Content-type: application/x-www-form-urlencoded',
        'content' => $postdata,
    ],
    ];
    $context = stream_context_create($opts);

    $nodes = json_decode(file_get_contents($oxidized_search_url, false, $context), true);
    // Look up Oxidized node names to LibreNMS devices for a link
    foreach ($nodes as &$n) {
        $dev = DeviceCache::getByHostname($n['node']);
        $n['dev_id'] = $dev ? $dev->device_id : false;
        $n['full_name'] = $dev ? $dev->displayName() : $n['full_name'];
    }

    return $nodes;
}

/**
 * @param  int  $eventlog_severity
 * @return string $eventlog_severity_icon
 */
function eventlog_severity($eventlog_severity)
{
    return match ($eventlog_severity) {
        1 => 'label-success',
        2 => 'label-info',
        3 => 'label-primary',
        4 => 'label-warning',
        5 => 'label-danger',
        default => 'label-default',
    };
} // end eventlog_severity

function get_oxidized_nodes_list()
{
    $context = stream_context_create([
        'http' => [
            'header' => 'Accept: application/json',
        ],
    ]);

    $data = json_decode(file_get_contents(LibrenmsConfig::get('oxidized.url') . '/nodes?format=json', false, $context), true);

    foreach ($data as $object) {
        $device = DeviceCache::getByHostname($object['name']);
        if (! device_permitted($device->device_id)) {
            //user cannot see this device, so let's skip it.
            continue;
        }
        try {
            // Convert UTC time string to local timezone set
            $utc_time = $object['time'];
            $utc_date = new DateTime($utc_time, new DateTimeZone('UTC'));
            $local_timezone = new DateTimeZone(date_default_timezone_get());
            $local_date = $utc_date->setTimezone($local_timezone);

            // Generate local time string
            $formatted_local_time = $local_date->format('Y-m-d H:i:s T');
        } catch (Exception) {
            // Just display the current value of $object['time'];
            $formatted_local_time = $object['time'];
        }
        echo '<tr>
        <td>' . $device->device_id . '</td>
        <td>' . $object['name'] . '</td>
        <td>' . $device->sysName . '</td>
        <td>' . $object['status'] . '</td>
        <td>' . $formatted_local_time . '</td>
        <td>' . $object['model'] . '</td>
        <td>' . $object['group'] . '</td>
        <td></td>
        </tr>';
    }
}

/**
 * Return stacked graphs information
 *
 * @param  string  $transparency  value of desired transparency applied to rrdtool options (values 01 - 99)
 * @return array containing transparency and stacked setup
 */
function generate_stacked_graphs($force_stack = false, $transparency = '88')
{
    if (LibrenmsConfig::get('webui.graph_stacked') == true || $force_stack == true) {
        return ['transparency' => $transparency, 'stacked' => '1'];
    } else {
        return ['transparency' => '', 'stacked' => '-1'];
    }
}

/**
 * @params int unix time
 * @params int seconds
 *
 * @return int
 *
 * Rounds down to the nearest interval.
 *
 * The first argument is required and it is the unix time being
 * rounded down.
 *
 * The second value is the time interval. If not specified, it
 * defaults to 300, or 5 minutes.
 */
function lowest_time($time, $seconds = 300)
{
    return $time - ($time % $seconds);
}

/**
 * @params int
 *
 * @return string|void
 *
 * This returns the subpath for working with nfdump.
 *
 * 1 value is taken and that is a unix time stamp. It will be then be rounded
 * off to the lowest five minutes earlier.
 *
 * The return string will be a path partial you can use with nfdump to tell it what
 * file or range of files to use.
 *
 * Below ie a explanation of the layouts as taken from the NfSen config file.
 *  0             no hierachy levels - flat layout - compatible with pre NfSen version
 *  1 %Y/%m/%d    year/month/day
 *  2 %Y/%m/%d/%H year/month/day/hour
 *  3 %Y/%W/%u    year/week_of_year/day_of_week
 *  4 %Y/%W/%u/%H year/week_of_year/day_of_week/hour
 *  5 %Y/%j       year/day-of-year
 *  6 %Y/%j/%H    year/day-of-year/hour
 *  7 %Y-%m-%d    year-month-day
 *  8 %Y-%m-%d/%H year-month-day/hour
 */
function time_to_nfsen_subpath($time)
{
    $time = lowest_time($time);
    $layout = LibrenmsConfig::get('nfsen_subdirlayout');

    if ($layout == 0) {
        return 'nfcapd.' . date('YmdHi', $time);
    } elseif ($layout == 1) {
        return date('Y\/m\/d\/\n\f\c\a\p\d\.YmdHi', $time);
    } elseif ($layout == 2) {
        return date('Y\/m\/d\/H\/\n\f\c\a\p\d\.YmdHi', $time);
    } elseif ($layout == 3) {
        return date('Y\/W\/w\/\n\f\c\a\p\d\.YmdHi', $time);
    } elseif ($layout == 4) {
        return date('Y\/W\/w\/H\/\n\f\c\a\p\d\.YmdHi', $time);
    } elseif ($layout == 5) {
        return date('Y\/z\/\n\f\c\a\p\d\.YmdHi', $time);
    } elseif ($layout == 6) {
        return date('Y\/z\/H\/\n\f\c\a\p\d\.YmdHi', $time);
    } elseif ($layout == 7) {
        return date('Y\-m\-d\/\n\f\c\a\p\d\.YmdHi', $time);
    } elseif ($layout == 8) {
        return date('Y\-m\-d\/H\/\n\f\c\a\p\d\.YmdHi', $time);
    }
}

/**
 * @params string hostname
 *
 * @return string
 *
 * Takes a hostname and transforms it to the name
 * used by nfsen.
 */
function nfsen_hostname($hostname)
{
    $nfsen_hostname = str_replace('.', LibrenmsConfig::get('nfsen_split_char'), $hostname);

    if (! is_null(LibrenmsConfig::get('nfsen_suffix'))) {
        $nfsen_hostname = str_replace(LibrenmsConfig::get('nfsen_suffix'), '', $nfsen_hostname);
    }

    return $nfsen_hostname;
}

/**
 * @params string hostname
 *
 * @return string|void
 *
 * Takes a hostname and returns the path to the nfsen
 * live dir.
 */
function nfsen_live_dir($hostname)
{
    $hostname = nfsen_hostname($hostname);

    foreach (LibrenmsConfig::get('nfsen_base') as $base_dir) {
        if (file_exists($base_dir) && is_dir($base_dir)) {
            return $base_dir . '/profiles-data/live/' . $hostname;
        }
    }
}

```

### includes/html/pages/device/health/mempool.inc.php
```
<?php

use App\Models\Mempool;
use LibreNMS\Util\Html;
use LibreNMS\Util\Number;

$mempools = DeviceCache::getPrimary()->mempools;

// if multiple, show composite graph
if ($mempools->count() > 1) {
    echo "<div class='panel panel-default'><div class='panel-heading'>";
    echo "<h3 class='panel-title'>Overview";
    /** @var Mempool $system */
    $system = $mempools->where('mempool_class', 'system')->first();
    if ($system) {
        $bytes = '';
        if ($system->mempool_total !== 100) {
            $total = Number::formatBi($system->mempool_total);
            $used = Number::formatBi($system->mempool_used);
            $bytes = "$used/$total - ";
        }
        echo "<div class='pull-right'>$bytes$system->mempool_perc% used</div>";
    }
    echo "</h3></div><div class='panel-body'>";
    Html::graphRow(['device' => DeviceCache::getPrimary()->device_id, 'type' => 'device_mempool'], true);
    echo '</div></div>';
}

foreach ($mempools as $mempool) {
    echo "<div class='panel panel-default'><div class='panel-heading'>";

    $bytes = '';
    if ($mempool->mempool_total !== 100) {
        $total = Number::formatBi($mempool->mempool_total);
        $used = Number::formatBi($mempool->mempool_used);
        $bytes = "$used/$total - ";
    }
    echo "<h3 class='panel-title'>{$mempool->mempool_descr} <div class='pull-right'>$bytes$mempool->mempool_perc% used</div></h3>";
    echo "</div><div class='panel-body'>";
    Html::graphRow(['id' => $mempool->mempool_id, 'type' => 'mempool_usage'], true);
    echo '</div></div>';
}

```

### includes/html/pages/device/health/sensors.inc.php
```
<?php

use App\Facades\LibrenmsConfig;
use App\Models\Sensor;
use LibreNMS\Enum\Severity;
use LibreNMS\Util\Html;

$row = 0;
$unit ??= $class->unit();
$graph_type ??= 'sensor_' . $class->value;

$sensors = Sensor::where('sensor_class', $class)->where('device_id', $device['device_id'])->orderBy('sensor_descr')->get();

foreach ($sensors as $sensor) {
    if (! is_int($row++ / 2)) {
        $row_colour = LibrenmsConfig::get('list_colour.even');
    } else {
        $row_colour = LibrenmsConfig::get('list_colour.odd');
    }

    if ($sensor['poller_type'] == 'ipmi') {
        $sensor_descr = ipmiSensorName($device['hardware'], $sensor['sensor_descr']);
    } else {
        $sensor_descr = $sensor['sensor_descr'];
    }

    $sensor_current = Html::severityToLabel($sensor->currentStatus(), __('Current') . ': ' . $sensor->formatValue());

    echo "<div class='panel panel-default'>
        <div class='panel-heading'>
        <h3 class='panel-title'>$sensor_descr <div class='pull-right'>$sensor_current";

    //Display low and high limit if they are not null (format_si() is changing null to '0')
    if (! is_null($sensor->sensor_limit_low)) {
        echo ' ' . Html::severityToLabel(Severity::Unknown, __('Low Limit') . ': ' . $sensor->formatValue('sensor_limit_low'));
    }
    if (! is_null($sensor->sensor_limit_low_warn)) {
        echo ' ' . Html::severityToLabel(Severity::Unknown, __('Low Warning') . ': ' . $sensor->formatValue('sensor_limit_low_warn'));
    }
    if (! is_null($sensor->sensor_limit_warn)) {
        echo ' ' . Html::severityToLabel(Severity::Unknown, __('High Warning') . ': ' . $sensor->formatValue('sensor_limit_warn'));
    }
    if (! is_null($sensor->sensor_limit)) {
        echo ' ' . Html::severityToLabel(Severity::Unknown, __('High Limit') . ': ' . $sensor->formatValue('sensor_limit'));
    }

    echo '</div></h3>
        </div>';
    echo "<div class='panel-body'>";

    $graph_array['id'] = $sensor['sensor_id'];
    $graph_array['type'] = $graph_type;

    include 'includes/html/print-graphrow.inc.php';

    echo '</div></div>';
}

```

### includes/html/pages/device/health/storage.inc.php
```
<?php

use LibreNMS\Util\Number;

$graph_type = 'storage_usage';

$row = 1;

foreach (dbFetchRows('SELECT * FROM `storage` WHERE device_id = ? ORDER BY storage_descr', [$device['device_id']]) as $drive) {
    if (is_int($row / 2)) {
        $row_colour = \App\Facades\LibrenmsConfig::get('list_colour.even');
    } else {
        $row_colour = \App\Facades\LibrenmsConfig::get('list_colour.odd');
    }

    $total = $drive['storage_size'];
    $used = $drive['storage_used'];
    $free = $drive['storage_free'];
    $perc = round($drive['storage_perc']);
    $used = Number::formatBi($used);
    $total = Number::formatBi($total);
    $free = Number::formatBi($free);
    $storage_descr = $drive['storage_descr'];

    $fs_url = 'graphs/id=' . $drive['storage_id'] . '/type=storage_usage/';

    $fs_popup = "onmouseover=\"return overlib('<div class=list-large>" . $device['hostname'] . ' - ' . $drive['storage_descr'];
    $fs_popup .= "</div><img src=\'graph.php?id=" . $drive['storage_id'] . '&amp;type=' . $graph_type . '&amp;from=' . \App\Facades\LibrenmsConfig::get('time.month') . '&amp;to=' . \App\Facades\LibrenmsConfig::get('time.now') . "&amp;width=400&amp;height=125\'>";
    $fs_popup .= "', RIGHT, FGCOLOR, '#e5e5e5');\" onmouseout=\"return nd();\"";

    $graph_array['id'] = $drive['storage_id'];
    $graph_array['type'] = $graph_type;

    echo "<div class='panel panel-default'>
            <div class='panel-heading'>
                <h3 class='panel-title'>$storage_descr <div class='pull-right'>$used/$total - $perc% used</div></h3>
            </div>";
    echo "<div class='panel-body'>";
    include 'includes/html/print-graphrow.inc.php';
    echo '</div></div>';

    $row++;
}//end foreach

```

### includes/html/pages/device/port/vlans.inc.php
```
<?php

use LibreNMS\Util\Rewrite;

$vlans = dbFetchRows("SELECT * FROM `ports_vlans` AS PV, vlans AS V WHERE PV.`port_id` = '" . $port['port_id'] . "' and PV.`device_id` = '" . $device['device_id'] . "' AND V.`vlan_vlan` = PV.vlan AND V.device_id = PV.device_id");

echo '<table class="table table-hover table-striped table-condensed">';

echo '<tr><th>VLAN</th><th>Description</th><th>Cost</th><th>Priority</th><th>State</th><th>Other Ports</th></tr>';

foreach ($vlans as $vlan) {
    echo '<tr>';

    echo '<td width=100 class=list-large> Vlan ' . $vlan['vlan'] . '</td>';
    echo '<td width=200 class=box-desc>' . $vlan['vlan_name'] . '</td>';

    if ($vlan['state'] == 'blocking') {
        $class = 'red';
    } elseif ($vlan['state'] == 'forwarding') {
        $class = 'green';
    } else {
        $class = 'none';
    }

    echo '<td>' . $vlan['cost'] . '</td><td>' . $vlan['priority'] . "</td><td class=$class>" . $vlan['state'] . '</td>';

    $traverse_ifvlan = true;
    $vlan_ports = [];
    $otherports = dbFetchRows('SELECT * FROM `ports_vlans` AS V, `ports` as P WHERE V.`device_id` = ? AND V.`vlan` = ? AND P.port_id = V.port_id', [$device['device_id'], $vlan['vlan']]);
    foreach ($otherports as $otherport) {
        if ($otherport['untagged']) {
            $traverse_ifvlan = false;
        }
        $vlan_ports[$otherport['ifIndex']] = $otherport;
    }

    if ($traverse_ifvlan) {
        $otherports = dbFetchRows(
            'SELECT * FROM ports WHERE `device_id` = ? AND `ifVlan` = ?',
            [$device['device_id'], $vlan['vlan']]
        );
        foreach ($otherports as $otherport) {
            $vlan_ports[$otherport['ifIndex']] = array_merge($otherport, ['untagged' => '1']);
        }
    }

    ksort($vlan_ports);

    echo '<td>';
    $vsep = '';
    foreach ($vlan_ports as $otherport) {
        $otherport = cleanPort($otherport);
        echo $vsep . generate_port_link($otherport, Rewrite::shortenIfName($otherport['ifDescr']));
        if ($otherport['untagged']) {
            echo '(U)';
        }

        $vsep = ', ';
    }

    echo '</td>';
    echo '</tr>';
}//end foreach

echo '</table>';

```

### includes/html/pages/device/processes.inc.php
```
<?php

/*
 * Copyright (C) 2015 Daniel Preussker <f0o@devilcode.org>
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

/*
 * Process Listing
 * @author Daniel Preussker <f0o@devilcode.org>
 * @copyright 2015 f0o, LibreNMS
 * @license GPL
 * @package LibreNMS
 * @subpackage Pages
 */

$order = match ($vars['order'] ?? '') {
    'vsz' => '`vsz`',
    'rss' => '`rss`',
    'cputime' => '`cputime`',
    'user' => '`user`',
    'command' => '`command`',
    default => '`pid`',
}; //end switch

if (isset($vars['by']) && $vars['by'] == 'desc') {
    $by = 'desc';
} else {
    $by = 'asc';
}

$heads = [
    'PID' => '',
    'VSZ' => 'Virtual Memory',
    'RSS' => 'Resident Memory',
    'cputime' => '',
    'user' => '',
    'command' => '',
];

echo "<div class='table-responsive'><table class='table table-hover'><thead><tr>";
foreach ($heads as $head => $extra) {
    unset($lhead, $bhead);
    $lhead = strtolower($head);
    $bhead = 'asc';
    $icon = '';
    if ('`' . $lhead . '`' == $order) {
        $icon = " class='fa fa-chevron-";
        if ($by == 'asc') {
            $bhead = 'desc';
            $icon .= 'up';
        } else {
            $icon .= 'down';
        }

        $icon .= "'";
    }

    echo '<th><a href="' . \LibreNMS\Util\Url::generate(['page' => 'device', 'device' => $device['device_id'], 'tab' => 'processes', 'order' => $lhead, 'by' => $bhead]) . '"><span' . $icon . '>&nbsp;';
    if (! empty($extra)) {
        echo "<abbr title='$extra'>$head</abbr>";
    } else {
        echo $head;
    }

    echo '</span></a></th>';
}//end foreach

echo '</tr></thead><tbody>';

foreach (dbFetchRows('SELECT * FROM `processes` WHERE `device_id` = ? ORDER BY ' . $order . ' ' . $by, [$device['device_id']]) as $entry) {
    echo '<tr>';
    echo '<td>' . $entry['pid'] . '</td>';
    echo '<td>' . \LibreNMS\Util\Number::formatSi($entry['vsz'] * 1024, 2, 0, '') . '</td>';
    echo '<td>' . \LibreNMS\Util\Number::formatSi($entry['rss'] * 1024, 2, 0, '') . '</td>';
    echo '<td>' . $entry['cputime'] . '</td>';
    echo '<td>' . $entry['user'] . '</td>';
    echo '<td>' . $entry['command'] . '</td>';
    echo '</tr>';
}

echo '</tbody></table></div>';

```

### includes/html/pages/device/routing/bgp.inc.php
```
<?php

use LibreNMS\Util\IP;

$extra_sql = '';
$link_array = [
    'page'   => 'device',
    'device' => $device['device_id'],
    'tab'    => 'routing',
    'proto'  => 'bgp',
];

if (! isset($vars['view'])) {
    $vars['view'] = 'basic';
}

print_optionbar_start();

echo '<strong>Local AS : ' . $device['bgpLocalAs'] . '</strong> ';

echo "<span style='font-weight: bold;'>BGP</span> &#187; ";

if ($vars['view'] == 'basic') {
    echo "<span class='pagemenu-selected'>";
}

echo generate_link('Basic', $link_array, ['view' => 'basic']);
if ($vars['view'] == 'basic') {
    echo '</span>';
}

echo ' | ';

if ($vars['view'] == 'updates') {
    echo "<span class='pagemenu-selected'>";
}

echo generate_link('Updates', $link_array, ['view' => 'updates']);
if ($vars['view'] == 'updates') {
    echo '</span>';
}

echo ' | Prefixes: ';

if ($vars['view'] == 'prefixes_ipv4unicast') {
    echo "<span class='pagemenu-selected'>";
    $extra_sql = " AND `bgpPeerIdentifier` NOT LIKE '%:%'";
}

echo generate_link('IPv4', $link_array, ['view' => 'prefixes_ipv4unicast']);
if ($vars['view'] == 'prefixes_ipv4unicast') {
    echo '</span>';
}

echo ' | ';

if ($vars['view'] == 'prefixes_ipv4vpn') {
    echo "<span class='pagemenu-selected'>";
}

echo generate_link('VPNv4 Ucast', $link_array, ['view' => 'prefixes_ipv4vpn']);
if ($vars['view'] == 'prefixes_ipv4vpn') {
    echo '</span>';
}

echo ' | ';

if ($vars['view'] == 'prefixes_ipv6unicast') {
    echo "<span class='pagemenu-selected'>";
    $extra_sql = " AND `bgpPeerIdentifier` LIKE '%:%'";
}

echo generate_link('IPv6', $link_array, ['view' => 'prefixes_ipv6unicast']);
if ($vars['view'] == 'prefixes_ipv6unicast') {
    echo '</span>';
}

echo ' | ';

if ($vars['view'] == 'prefixes_ipv6vpn') {
    echo "<span class='pagemenu-selected'>";
    $extra_sql = " AND `bgpPeerIdentifier` LIKE '%:%'";
}

echo generate_link('VPNv6 Ucast', $link_array, ['view' => 'prefixes_ipv6vpn']);
if ($vars['view'] == 'prefixes_ipv6vpn') {
    echo '</span>';
}

echo ' | Traffic: ';

if ($vars['view'] == 'macaccounting_bits') {
    echo "<span class='pagemenu-selected'>";
}

echo generate_link('Bits', $link_array, ['view' => 'macaccounting_bits']);
if ($vars['view'] == 'macaccounting_bits') {
    echo '</span>';
}

echo ' | ';
if ($vars['view'] == 'macaccounting_pkts') {
    echo "<span class='pagemenu-selected'>";
}

echo generate_link('Packets', $link_array, ['view' => 'macaccounting_pkts']);
if ($vars['view'] == 'macaccounting_pkts') {
    echo '</span>';
}

print_optionbar_end();

echo '<table border="0" cellspacing="0" cellpadding="5" width="100%" class="table sortable">';
echo '<tr style="height: 30px"><th>Peer address</th><th>Type</th><th>Family</th><th>Remote AS</th><th>Peer description</th><th>State</th><th>Last error</th><th>Uptime</th></tr>';

$i = '1';

foreach (dbFetchRows("SELECT * FROM `bgpPeers` WHERE `device_id` = ? $extra_sql ORDER BY `bgpPeerRemoteAs`, `bgpPeerIdentifier`", [$device['device_id']]) as $peer) {
    $has_macaccounting = dbFetchCell('SELECT COUNT(*) FROM `ipv4_mac` AS I, mac_accounting AS M WHERE I.ipv4_address = ? AND M.mac = I.mac_address', [$peer['bgpPeerIdentifier']]);

    unset($alert);
    unset($peerhost, $peername);

    // load the peer identifier into an object
    $peerIdentifierIp = IP::parse($peer['bgpPeerIdentifier'], true);

    if ($peer['bgpPeerState'] == 'established') {
        $col = 'green';
    } else {
        $col = 'red';
        $peer['alert'] = 1;
    }

    if ($peer['bgpPeerAdminStatus'] == 'start' || $peer['bgpPeerAdminStatus'] == 'running') {
        $admin_col = 'green';
    } else {
        $admin_col = 'gray';
    }

    if ($peer['bgpPeerAdminStatus'] == 'stop') {
        $peer['alert'] = 0;
        $peer['disabled'] = 1;
    }

    if ($peer['bgpPeerRemoteAs'] == $device['bgpLocalAs']) {
        $peer_type = "<span style='color: #00f;'>iBGP</span>";
    } else {
        $peer_type = "<span style='color: #0a0;'>eBGP</span>";
        // Private ASN ranges
        // 64512 - 65534 (Private)
        // 4200000000 - 4294967294 (Private)
        if (($peer['bgpPeerRemoteAs'] >= 64512 && $peer['bgpPeerRemoteAs'] <= 65534) || ($peer['bgpPeerRemoteAs'] >= 4200000000 && $peer['bgpPeerRemoteAs'] <= 4294967294)) {
            $peer_type = "<span style='color: #0af;'>Priv eBGP</span>";
        }
    }

    $query = 'SELECT * FROM ipv4_addresses AS A, ports AS I, devices AS D WHERE ';
    $query .= '(A.ipv4_address = ? AND I.port_id = A.port_id)';
    $query .= ' AND D.device_id = I.device_id';
    $ipv4_host = dbFetchRow($query, [$peer['bgpPeerIdentifier']]);

    $query = 'SELECT * FROM ipv6_addresses AS A, ports AS I, devices AS D WHERE ';
    $query .= '(A.ipv6_address = ? AND I.port_id = A.port_id)';
    $query .= ' AND D.device_id = I.device_id';
    $ipv6_host = dbFetchRow($query, [$peerIdentifierIp?->uncompressed()]);

    if ($ipv4_host) {
        $peerhost = $ipv4_host;
    } elseif ($ipv6_host) {
        $peerhost = $ipv6_host;
    } else {
        $peerhost = null;
    }

    if (is_array($peerhost)) {
        $peerhost = cleanPort($peerhost);
        // $peername = generate_device_link($peerhost);
        $peername = generate_device_link($peerhost) . ' ' . generate_port_link($peerhost);
        $peer_url = 'device/device=' . $peer['device_id'] . '/tab=routing/proto=bgp/view=updates/';
    } else {
        // FIXME
        // $peername = gethostbyaddr($peer['bgpPeerIdentifier']); // FFffuuu DNS // Cache this in discovery?
        // if ($peername == $peer['bgpPeerIdentifier'])
        // {
        // unset($peername);
        // } else {
        // $peername = "<i>".$peername."<i>";
        // }
    }

    unset($peer_af);
    $sep = '';

    foreach (dbFetchRows('SELECT * FROM `bgpPeers_cbgp` WHERE `device_id` = ? AND bgpPeerIdentifier = ?', [$device['device_id'], $peer['bgpPeerIdentifier']]) as $afisafi) {
        $afi = $afisafi['afi'];
        $safi = $afisafi['safi'];
        $this_afisafi = $afi . $safi;
        $peer['afi'] = $sep . $afi . '.' . $safi;
        $sep = '<br />';
        $peer['afisafi'][$this_afisafi] = 1;
        // Build a list of valid AFI/SAFI for this peer
    }

    // display overlib graphs
    $graph_array = [];
    $graph_array['type'] = 'bgp_updates';
    $graph_array['id'] = $peer['bgpPeer_id'];
    $graph_array['to'] = \App\Facades\LibrenmsConfig::get('time.now');
    $graph_array['from'] = \App\Facades\LibrenmsConfig::get('time.day');
    $graph_array['height'] = '110';
    if (isset($width)) {
        $graph_array['width'] = $width;
    }

    // Peer Address
    $graph_array_zoom = $graph_array;
    $graph_array_zoom['height'] = '150';
    $graph_array_zoom['width'] = '500';
    $overlib_link = 'device/device=' . $peer['device_id'] . '/tab=routing/proto=bgp/';

    $link_array = $graph_array;
    $link_array['page'] = 'graphs';
    unset($link_array['height'], $link_array['width']);
    $link = \LibreNMS\Util\Url::generate($link_array);
    $peeraddresslink = '<span class=list-large>' . \LibreNMS\Util\Url::overlibLink($link, $peerIdentifierIp?->compressed(), \LibreNMS\Util\Url::graphTag($graph_array_zoom)) . '</span>';

    if ($peer['bgpPeerLastErrorCode'] == 0 && $peer['bgpPeerLastErrorSubCode'] == 0) {
        $last_error = $peer['bgpPeerLastErrorText'];
    } else {
        $last_error = describe_bgp_error_code($peer['bgpPeerLastErrorCode'], $peer['bgpPeerLastErrorSubCode']) . '<br/>' . $peer['bgpPeerLastErrorText'];
    }

    echo '<tr class="bgp"' . (empty($peer['alert']) ? '' : ' bordercolor="#cc0000"') . (empty($peer['disabled']) ? '' : ' bordercolor="#cccccc"') . '>
        ';

    echo '
        <td>' . $peeraddresslink . '<br />' . ($peername ?? '') . "</td>
        <td>$peer_type</td>
        <td style='font-size: 10px; font-weight: bold; line-height: 10px;'>" . ($peer['afi'] ?? '') . '</td>
        <td><strong>AS' . $peer['bgpPeerRemoteAs'] . '</strong><br />' . $peer['astext'] . '</td>
        <td>' . $peer['bgpPeerDescr'] . "</td>
        <td><strong><span style='color: $admin_col;'>" . $peer['bgpPeerAdminStatus'] . "<span><br /><span style='color: $col;'>" . $peer['bgpPeerState'] . '</span></strong></td>
        <td>' . $last_error . '</td>
        <td>' . \LibreNMS\Util\Time::formatInterval($peer['bgpPeerFsmEstablishedTime']) . "<br />
        Updates <i class='fa fa-arrow-down icon-theme' aria-hidden='true'></i> " . $peer['bgpPeerInUpdates'] . "
        <i class='fa fa-arrow-up icon-theme' aria-hidden='true'></i> " . $peer['bgpPeerOutUpdates'] . '</td>
        </tr>';

    unset($invalid);

    switch ($vars['view']) {
        case 'prefixes_ipv4unicast':
        case 'prefixes_ipv4multicast':
        case 'prefixes_ipv4vpn':
        case 'prefixes_ipv6unicast':
        case 'prefixes_ipv6multicast':
            [,$afisafi] = explode('_', $vars['view']);
            if (isset($peer['afisafi'][$afisafi])) {
                $peer['graph'] = 1;
            }

            // FIXME no break??
        case 'updates':
            $graph_array['type'] = 'bgp_' . $vars['view'];
            $graph_array['id'] = $peer['bgpPeer_id'];
    }

    switch ($vars['view']) {
        case 'macaccounting_bits':
        case 'macaccounting_pkts':
            $acc = dbFetchRow('SELECT * FROM `ipv4_mac` AS I, `mac_accounting` AS M, `ports` AS P, `devices` AS D WHERE I.ipv4_address = ? AND M.mac = I.mac_address AND P.port_id = M.port_id AND D.device_id = P.device_id', [$peer['bgpPeerIdentifier']]);
            $database = Rrd::name($device['hostname'], ['cip', $acc['ifIndex'], $acc['mac']]);
            if (is_array($acc) && is_file($database)) {
                $peer['graph'] = 1;
                $graph_array['id'] = $acc['ma_id'];
                $graph_array['type'] = $vars['view'];
            }
    }

    if ($vars['view'] == 'updates') {
        $peer['graph'] = 1;
    }

    if (! empty($peer['graph'])) {
        $graph_array['height'] = '100';
        $graph_array['width'] = '216';
        $graph_array['to'] = \App\Facades\LibrenmsConfig::get('time.now');
        echo '<tr class="bgp"><td colspan="7">';

        include 'includes/html/print-graphrow.inc.php';

        echo '</td></tr>';
    }

    $i++;

    unset($valid_afi_safi);
}//end foreach
?>

</table>

```

### includes/html/pages/device/showconfig.inc.php
```
<?php

// FIXME svn stuff still using optc etc, won't work, needs updating!
use App\Facades\LibrenmsConfig;
use Illuminate\Support\Facades\Gate;
use Symfony\Component\Process\Process;

if (Gate::allows('showConfig', DeviceCache::getPrimary())) {
    if (LibrenmsConfig::get('rancid_repo_type') == 'git-bare' && is_dir($rancid_path)) {
        echo '<div style="clear: both;">';

        print_optionbar_start('', '');
        echo is_null(LibrenmsConfig::get('rancid_repo_url')) ? 'Git repository non-browsable'
            : '<a href="' . htmlspecialchars(LibrenmsConfig::get('rancid_repo_url')) . '/?a=blob;hb=HEAD;p=' . basename((string) $rancid_path) . ';f=' . $rancid_file . '">Git repository</a>';
        print_optionbar_end();

        $process = new Process(['git', 'ls-tree', '-r', 'HEAD'], $rancid_path);
        $process->run();
        $full_tree = explode(PHP_EOL, $process->getOutput());
        foreach ($full_tree as $ft) {
            [$perm, $type, $hash_path] = explode(' ', $ft, 3);
            [$hash, $file] = explode("\t", $hash_path);
            if (strcmp($file, (string) $rancid_file) === 0) {
                $process = new Process(['git', 'cat-file', $type, $hash], $rancid_path);
                $process->run();
                $text = $process->getOutput();
            }
        }
    } elseif (! empty($rancid_file)) {
        echo '<div style="clear: both;">';

        print_optionbar_start('', '');

        echo "<span style='font-weight: bold;'>Config</span> &#187; ";

        if (empty($vars['rev'])) {
            echo '<span class="pagemenu-selected">';
            echo generate_link('Latest', ['page' => 'device', 'device' => $device['device_id'], 'tab' => 'showconfig']);
            echo '</span>';
        } else {
            echo generate_link('Latest', ['page' => 'device', 'device' => $device['device_id'], 'tab' => 'showconfig']);
        }

        if (LibrenmsConfig::get('rancid_repo_type') == 'svn') {
            $svn_binary = LibrenmsConfig::locateBinary('svn');
            if (is_executable($svn_binary)) {
                $sep = ' | ';

                $process = new Process([$svn_binary, 'log', '-l 8', '-q', '--xml', $rancid_file], $rancid_path);
                $process->run();
                $svnlogs_xmlstring = $process->getOutput();
                $svnlogs = [];

                $svnlogs_xml = simplexml_load_string($svnlogs_xmlstring);
                foreach ($svnlogs_xml->logentry as $svnlogentry) {
                    $rev = $svnlogentry['revision'];
                    $ts = strtotime($svnlogentry->date);
                    $svnlogs[] = ['rev' => $rev, 'date' => $ts];
                }

                $revlist = [];

                foreach ($svnlogs as $svnlog) {
                    echo $sep;
                    $revlist[] = $svnlog['rev'];

                    if ($vars['rev'] == $svnlog['rev']) {
                        echo '<span class="pagemenu-selected">';
                    }

                    $linktext = 'r' . $svnlog['rev'] . ' <small>' . date(LibrenmsConfig::get('dateformat.byminute'), $svnlog['date']) . '</small>';
                    echo generate_link($linktext, ['page' => 'device', 'device' => $device['device_id'], 'tab' => 'showconfig', 'rev' => $svnlog['rev']]);

                    if ($vars['rev'] == $svnlog['rev']) {
                        echo '</span>';
                    }

                    $sep = ' | ';
                }
            }
        }//end if
        if (LibrenmsConfig::get('rancid_repo_type') == 'git') {
            $sep = ' | ';

            $process = new Process(['git', 'log', '-n 8', '--pretty=format:%h;%ct', $rancid_file], $rancid_path);
            $process->run();
            $gitlogs_raw = explode(PHP_EOL, $process->getOutput());
            $gitlogs = [];

            foreach ($gitlogs_raw as $gl) {
                [$rev, $ts] = explode(';', $gl);
                $gitlogs[] = ['rev' => $rev, 'date' => $ts];
            }

            $revlist = [];

            foreach ($gitlogs as $gitlog) {
                echo $sep;
                $revlist[] = $gitlog['rev'];

                if ($vars['rev'] == $gitlog['rev']) {
                    echo '<span class="pagemenu-selected">';
                }

                $linktext = 'r' . $gitlog['rev'] . ' <small>' . date(LibrenmsConfig::get('dateformat.byminute'), $gitlog['date']) . '</small>';
                echo generate_link($linktext, ['page' => 'device', 'device' => $device['device_id'], 'tab' => 'showconfig', 'rev' => $gitlog['rev']]);

                if ($vars['rev'] == $gitlog['rev']) {
                    echo '</span>';
                }

                $sep = ' | ';
            }
        }

        print_optionbar_end();

        if (LibrenmsConfig::get('rancid_repo_type') == 'svn') {
            $svn_binary = LibrenmsConfig::locateBinary('svn');
            if (is_executable($svn_binary) && in_array($vars['rev'], $revlist)) {
                $process = new Process([$svn_binary, 'diff', '-c', 'r' . $vars['rev'], $rancid_file], $rancid_path);
                $process->run();
                $diff = $process->getOutput();
                if (! $diff) {
                    $text = 'No Difference';
                } else {
                    $text = $diff;
                    $previous_config = $vars['rev'] . '^';
                }
            } else {
                $fh = fopen($rancid_file, 'r');
                if ($fh === false) {
                    echo '<div class="alert alert-warning">Error: Cannot open Rancid configuration file for this device.</div>';

                    return;
                }
                if (filesize($rancid_file) == 0) {
                    echo '<div class="alert alert-warning">Error: Rancid configuration file for this device is empty.</div>';

                    return;
                }
                $text = fread($fh, filesize($rancid_file));
                fclose($fh);
            }
        } elseif (LibrenmsConfig::get('rancid_repo_type') == 'git') {
            if (in_array($vars['rev'], $revlist)) {
                $process = new Process(['git', 'diff', $vars['rev'] . '^', $vars['rev'], $rancid_file], $rancid_path);
                $process->run();
                $diff = $process->getOutput();
                if (! $diff) {
                    $text = 'No Difference';
                } else {
                    $text = $diff;
                    $previous_config = $vars['rev'] . '^';
                }
            } else {
                $fh = fopen($rancid_file, 'r');
                if ($fh === false) {
                    echo '<div class="alert alert-warning">Error: Cannot open Rancid configuration file for this device.</div>';

                    return;
                }
                if (filesize($rancid_file) == 0) {
                    echo '<div class="alert alert-warning">Error: Rancid configuration file for this device is empty.</div>';

                    return;
                }
                $text = fread($fh, filesize($rancid_file));
                fclose($fh);
            }
        }

        if (LibrenmsConfig::get('rancid_ignorecomments')) {
            $lines = explode("\n", (string) $text);
            for ($i = 0; $i < count($lines); $i++) {
                if ($lines[$i][0] == '#') {
                    unset($lines[$i]);
                }
            }

            $text = implode("\n", $lines);
        }
    } elseif (LibrenmsConfig::get('oxidized.enabled') === true && LibrenmsConfig::has('oxidized.url')) {
        // Try with hostname as set in librenms first
        $oxidized_hostname = $device['hostname'];
        // fetch info about the node and then a list of versions for that node
        $response = (new \App\ApiClients\Oxidized())->getContent('/node/show/' . $oxidized_hostname . '?format=json');
        $node_info = json_decode($response, true);
        if (! empty($node_info['last']['start'])) {
            $node_info['last']['start'] = date(LibrenmsConfig::get('dateformat.long'), strtotime((string) $node_info['last']['start']));
        }
        if (! empty($node_info['last']['end'])) {
            $node_info['last']['end'] = date(LibrenmsConfig::get('dateformat.long'), strtotime((string) $node_info['last']['end']));
        }
        // Try other hostname format if Oxidized request failed
        if (! $node_info) {
            // Adjust hostname based on whether domain was already in it or not
            if (str_contains((string) $oxidized_hostname, '.')) {
                // Use short name
                $oxidized_hostname = strtok($device['hostname'], '.');
            } elseif (LibrenmsConfig::get('mydomain')) {
                $oxidized_hostname = $device['hostname'] . '.' . LibrenmsConfig::get('mydomain');
            }

            // Try Oxidized again with new hostname, if it has changed
            if ($oxidized_hostname != $device['hostname']) {
                $node_info = json_decode((new \App\ApiClients\Oxidized())->getContent('/node/show/' . $oxidized_hostname . '?format=json'), true);
            }
        }

        if (LibrenmsConfig::get('oxidized.features.versioning') === true) { // fetch a list of versions
            $config_versions = json_decode((new \App\ApiClients\Oxidized())->getContent('/node/version?node_full=' . ($node_info['full_name'] ?? $oxidized_hostname) . '&format=json'), true);
        }

        $config_total = 1;
        if (is_array($config_versions)) {
            $config_total = count($config_versions);
        }

        if ($config_total > 1) {
            // populate current_version
            if (isset($_POST['config'])) {
                [$oid,$date,$version] = explode('|', htmlspecialchars((string) $_POST['config']));
                $current_config = ['oid' => $oid, 'date' => $date, 'version' => $version];
            } else { // no version selected
                $current_config = ['oid' => $config_versions[0]['oid'], 'date' => $config_versions[0]['date'], 'version' => $config_total];
            }

            // populate previous_version
            if (isset($_POST['diff'])) { // diff requested
                [$oid,$date,$version] = explode('|', (string) $_POST['prevconfig']);
                if (isset($oid) && $oid != $current_config['oid']) {
                    $previous_config = ['oid' => $oid, 'date' => $date, 'version' => $version];
                } elseif ($current_config['version'] != 1) {  // assume previous, unless current is first config
                    foreach ($config_versions as $key => $version) {
                        if ($version['oid'] == $current_config['oid']) {
                            $prev_key = $key + 1;
                            $previous_config['oid'] = $config_versions[$prev_key]['oid'];
                            $previous_config['date'] = $config_versions[$prev_key]['date'];
                            $previous_config['version'] = $config_total - $prev_key;
                            break;
                        }
                    }
                } else {
                    print_error('No previous version, please select a different version.');
                }
            }

            if (isset($previous_config)) {
                $uri = '/node/version/diffs?node=' . $oxidized_hostname;
                if (! empty($node_info['group'])) {
                    $uri .= '&group=' . $node_info['group'];
                }
                $uri .= '&oid=' . urlencode((string) $current_config['oid']) . '&date=' . urlencode((string) $current_config['date']) . '&num=' . urlencode((string) $current_config['version']) . '&oid2=' . $previous_config['oid'] . '&format=text';

                $text = (new \App\ApiClients\Oxidized())->getContent($uri); // fetch diff
            } else {
                // fetch current_version
                $text = (new \App\ApiClients\Oxidized())->getContent('/node/version/view?node=' . $oxidized_hostname . (! empty($node_info['group']) ? '&group=' . $node_info['group'] : '') . '&oid=' . urlencode((string) $current_config['oid']) . '&date=' . urlencode((string) $current_config['date']) . '&num=' . urlencode((string) $current_config['version']) . '&format=text');
            }
        } else {  // just fetch the only version
            $text = (new \App\ApiClients\Oxidized())->getContent('/node/fetch/' . (! empty($node_info['group']) ? $node_info['group'] . '/' : '') . $oxidized_hostname);
        }

        if (is_array($node_info) || $config_total > 1) {
            echo '<br />
                <div class="row">
            ';

            if (is_array($node_info)) {
                echo '
                      <div class="col-sm-4">
                          <div class="panel panel-primary">
                              <div class="panel-heading">Sync status: <strong>' . $node_info['last']['status'] . '</strong></div>
                              <ul class="list-group">
                                  <li class="list-group-item"><strong>Node:</strong> ' . $node_info['name'] . '</li>
                                  <li class="list-group-item"><strong>IP:</strong> ' . $node_info['ip'] . '</li>
                                  <li class="list-group-item"><strong>Model:</strong> ' . $node_info['model'] . '</li>
                                  <li class="list-group-item" style="overflow:hidden"><strong>Last Sync:</strong> ' . $node_info['last']['end'] . ' &nbsp;<button class="btn btn-primary btn-xs" style="float: right;" name="queue-refresh"  onclick=\'refresh_oxidized_node("' . $device['hostname'] . '")\'>Refresh</button></li>
                              </ul>
                          </div>
                      </div>
                ';
            }

            if ($config_total > 1) {
                echo '
                    <div class="col-sm-8">
                        <form class="form-horizontal" action="" method="post">
                            ' . csrf_field() . '
                            <div class="form-group">
                                <label for="config" class="col-sm-2 control-label">Config version</label>
                                <div class="col-sm-6">
                                    <select id="config" name="config" class="form-control">
                ';

                $i = $config_total;
                foreach ($config_versions as $version) {
                    echo '<option value="' . $version['oid'] . '|' . $version['date'] . '|' . $config_total . '" ';
                    if ($current_config['oid'] == $version['oid']) {
                        $author = $version['author']['name'];
                        $msg = $version['message'];
                        if (isset($previous_config)) {
                            echo 'selected>+';
                        } else {
                            echo 'selected>*';
                        }
                    } elseif (isset($previous_config['oid']) && $previous_config['oid'] == $version['oid']) {
                        echo '>&nbsp;-';
                    } else {
                        echo '>&nbsp;&nbsp;';
                    }
                    echo $i . ' :: ' . $version['date'] . '</option>';
                    $i--;
                }

                echo '
                                    </select>
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="col-sm-offset-2 col-sm-6">
                                      <input type="hidden" name="prevconfig" value="';
                echo implode('|', $current_config);
                echo '">
                                      <button type="submit" class="btn btn-primary btn-sm" name="show">Show version</button>
                                      <button type="submit" class="btn btn-primary btn-sm" name="diff">Show diff</button>
                                </div>
                            </div>
                        </form>
                    </div>
                ';
            }

            echo '</div>';
        } else {
            echo '<br />';
            print_error(__('device.oxidized.connection_error'));
            if (isset($response) && preg_match('#<title>(.*)</title>#', $response, $error_matches)) {
                print_error(strip_tags($error_matches[1]));
            }
            $text = '';
        }
    }//end if

    if (! empty($author)) {
        echo '
                          <div class="panel panel-primary">
                              <div class="panel-heading">Author: <strong>' . $author . '</strong></div>';
        if (! empty($msg)) {
            echo '
                              <ul class="list-group">
                                  <li class="list-group-item"><strong>Message:</strong> ' . $msg . '</li>
                              </ul>';
        }
        echo '
                          </div>';
    }
    if (! empty($text)) {
        $language = isset($previous_config) ? 'diff' : LibrenmsConfig::getOsSetting($device['os'], 'config_highlighting', 'ios');
        $geshi = new GeSHi(htmlspecialchars_decode((string) $text, ENT_QUOTES | ENT_HTML5), $language);
        $geshi->enable_line_numbers(GESHI_FANCY_LINE_NUMBERS);
        $geshi->set_overall_style('color: black;');
        // $geshi->set_line_style('color: #999999');
        echo '<div class="config">';
        echo '<input id="linenumbers" class="btn btn-primary" type="submit" value="Hide line numbers"/>';
        echo $geshi->parse_code();
        echo '</div>';
    }
}//end if

$pagetitle[] = 'Config';

```

### includes/html/pages/device/slas.inc.php
```
<?php

if ($vars['id']) {
    $sla = dbFetchRow('SELECT `tag`, `sla_nr`,`rtt_type` FROM `slas` WHERE `sla_id` = ?', [$vars['id']]);
    $name = 'SLA #' . $sla['sla_nr'] . ' - ' . trans_fb("modules.slas.{$sla['rtt_type']}", ucfirst((string) $sla['rtt_type']));
    if ($sla['tag']) {
        $name .= ': ' . $sla['tag'];
    }

    if ($sla['owner']) {
        $name .= ' (Owner: ' . $sla['owner'] . ')';
    }

    if ($sla['opstatus'] == 2) {
        $danger = 'panel-danger';
    } else {
        $danger = '';
    }

    echo "<div class=\"well well-sm\"><h3 class=\"panel-title\">$name</h3></div>";

    echo '<div class="panel panel-default ' . $danger . '">';

    // All SLA's support the RTT metric
    include 'sla/rtt.inc.php';

    // Load the per-type SLA metrics
    $rtt_type = basename((string) $sla['rtt_type']);
    if (file_exists("includes/html/pages/device/sla/$rtt_type.inc.php")) {
        include "includes/html/pages/device/sla/$rtt_type.inc.php";
    }

    echo '</div>';
} else {
    print_optionbar_start();

    $slas = dbFetchRows('SELECT * FROM `slas` WHERE `device_id` = ? AND `deleted` = 0 ORDER BY `sla_nr`', [$device['device_id']]);

    // Collect types
    $sla_types = ['all' => 'All'];
    foreach ($slas as $sla) {
        $sla_type = $sla['rtt_type'];
        $sla_types[$sla_type] = trans_fb("modules.slas.{$sla_type}", ucfirst((string) $sla_type));
    }
    asort($sla_types);

    $status_options = [
        'all' => 'All',
        'up' => 'Up',
        'down' => 'Down',
    ];

    echo "<span style='font-weight: bold;'>SLA</span> &#187; ";

    // SLA Types, on the left.
    $sep = '';
    foreach ($sla_types as $sla_type => $text) {
        if (! $vars['view']) {
            $vars['view'] = $sla_type;
        }

        echo $sep;
        if ($vars['view'] == $sla_type) {
            echo "<span class='pagemenu-selected'>";
        }

        echo generate_link($text, $vars, ['view' => $sla_type]);
        if ($vars['view'] == $sla_type) {
            echo '</span>';
        }

        $sep = ' | ';
    }
    unset($sep);

    // The status option - on the right
    echo '<div class="pull-right">';
    echo "<span style='font-weight: bold;'>Status</span> &#187; ";
    $sep = '';
    foreach ($status_options as $option => $text) {
        if (empty($vars['opstatus'])) {
            $vars['opstatus'] = $option;
        }
        echo $sep;
        if ($vars['opstatus'] == $option) {
            echo "<span class='pagemenu-selected'>";
        }

        echo generate_link($text, $vars, ['opstatus' => $option]);
        if ($vars['opstatus'] == $option) {
            echo '</span>';
        }
        $sep = ' | ';
    }
    unset($sep);

    print_optionbar_end();

    foreach ($slas as $sla) {
        if ($vars['view'] != 'all' && $vars['view'] != $sla['rtt_type']) {
            continue;
        }

        $opstatus = ($sla['opstatus'] === 0) ? 'up' : 'down';
        d_echo('<br>Opstatus :: var: ' . $vars['opstatus'] . ', db: ' . $sla['opstatus'] . ', name: ' . $opstatus . '<br>');
        if ($vars['opstatus'] != 'all' && $vars['opstatus'] != $opstatus) {
            continue;
        }

        $name = 'SLA #' . $sla['sla_nr'] . ' - ' . $sla_types[$sla['rtt_type']];
        if ($sla['tag']) {
            $name .= ': ' . $sla['tag'];
        }

        if ($sla['owner']) {
            $name .= ' (Owner: ' . $sla['owner'] . ')';
        }

        // These Types have more graphs. Display a sub-page
        if (($sla['rtt_type'] == 'jitter') || ($sla['rtt_type'] == 'icmpjitter') || ($sla['rtt_type'] == 'IcmpEcho') || ($sla['rtt_type'] == 'IcmpTimeStamp') || ($sla['rtt_type'] == 'icmpAppl')) {
            $name = '<a href="' . \LibreNMS\Util\Url::generate($vars, ['tab' => 'slas', 'id' => $sla['sla_id']]) . '">' . $name . '</a>';
        } else {
            $name = htmlentities($name);
        }

        // If we have an error highlight the row.
        if ($sla['opstatus'] == 2) {
            $danger = 'panel-danger';
        } else {
            $danger = '';
        }

        $graph_array = [];
        $graph_array['device'] = $device['device_id'];
        $graph_array['height'] = '100';
        $graph_array['width'] = '215';
        $graph_array['to'] = \App\Facades\LibrenmsConfig::get('time.now');
        $graph_array['type'] = 'device_sla';
        $graph_array['id'] = $sla['sla_id'];
        echo '<div class="panel panel-default ' . $danger . '">
    <div class="panel-heading">
        <h3 class="panel-title">' . $name . '</h3>
    </div>
    <div class="panel-body">';
        echo "<div class='row'>";
        include 'includes/html/print-graphrow.inc.php';
        echo '</div>';
        echo '</div>';
        echo '</div>';
    }
}

$pagetitle[] = 'SLAs';

```

### includes/html/pages/eventlog.inc.php
```
<?php
/*
 * This program is free software: you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or (at your
 * option) any later version.  Please see LICENSE.txt at the top level of
 * the source code distribution for details.
 *
 * @package    LibreNMS
 * @subpackage webui
 * @link       https://www.librenms.org
 * @copyright  2017 LibreNMS
 * @author     LibreNMS Contributors
*/

use App\Models\Device;

$no_refresh = true;
$param = [];
if ($device_id = (int) Request::input('device')) {
    $device = Device::find($device_id);
}

$pagetitle[] = 'Eventlog';
?>

<div class="panel panel-default panel-condensed">
    <div class="panel-heading">
        <strong>Eventlog</strong>
    </div>

    <?php
    require_once 'includes/html/common/eventlog.inc.php';
    echo implode('', $common_output);
    ?>
</div>

<script>
    $('.actionBar').append(
        '<div class="pull-left">' +
        '<form method="post" action="" class="form-inline" role="form" id="result_form">' +
        '<?php echo csrf_field() ?>' +
        <?php
        if (! isset($vars['fromdevice'])) {
            ?>
        '<div class="form-group">' +
        '<label><strong>Device&nbsp;&nbsp;</strong></label>' +
        '<select name="device" id="device" class="form-control">' +
        '<option value="">All Devices</option>' +
            <?php
            if (isset($device) && $device instanceof Device) {
                echo "'<option value=$device->device_id>" . $device->displayName() . "</option>' +";
            } ?>
        '</select>' +
        '</div>&nbsp;&nbsp;&nbsp;&nbsp;' +
            <?php
        } else {
            echo "'&nbsp;&nbsp;<input type=\"hidden\" name=\"device\" id=\"device\" value=\"" . $vars['device'] . "\">' + ";
        }
        ?>
        '<div class="form-group"><label><strong>Type&nbsp;&nbsp;</strong></label>' +
        '<select name="eventtype" id="eventtype" class="form-control input-sm">' +
        '<option value="">All types</option>' +
        <?php
        if ($type = Request::input('eventtype')) {
            $js_type = addcslashes(htmlentities($type), "'");
            echo "'<option value=\"$js_type\">$js_type</option>' +";
        }
        ?>
        '</select>' +
        '</div>&nbsp;&nbsp;' +
        '<button type="submit" class="btn btn-default">Filter</button>' +
        '</form>' +
        '</div>'
    );

    <?php if (! isset($vars['fromdevice'])) { ?>
    $("#device").select2({
        theme: 'bootstrap',
        dropdownAutoWidth : true,
        width: "auto",
        allowClear: true,
        placeholder: "All Devices",
        ajax: {
            url: '<?php echo route('ajax.select.device'); ?>',
            delay: 200
        }
    })<?php echo $device_id ? ".val($device_id).trigger('change');" : ''; ?>;
    <?php } ?>

    $("#eventtype").select2({
        theme: 'bootstrap',
        dropdownAutoWidth : true,
        width: "auto",
        allowClear: true,
        placeholder: "All Types",
        ajax: {
            url: '<?php echo route('ajax.select.eventlog'); ?>',
            delay: 200,
            data: function(params) {
                return {
                    field: "type",
                    device: $('#device').val(),
                    term: params.term,
                    page: params.page || 1
                }
            }
        }
    })<?php echo Request::input('eventtype') ? ".val('" . htmlspecialchars(Request::input('eventtype')) . "').trigger('change');" : ''; ?>;

</script>

```

### includes/html/pages/graphs.inc.php
```
<?php

use App\Facades\LibrenmsConfig;
use LibreNMS\Util\Time;

unset($vars['page']);

// Setup here

if (session('widescreen')) {
    $graph_width = 1700;
    $thumb_width = 180;
} else {
    $graph_width = 1075;
    $thumb_width = 113;
}

$vars['from'] = Time::parseAt($vars['from'] ?? '') ?: LibrenmsConfig::get('time.day');
$vars['to'] = Time::parseAt($vars['to'] ?? '') ?: LibrenmsConfig::get('time.now');

preg_match('/^(?P<type>[A-Za-z0-9]+)_(?P<subtype>.+)/', (string) $vars['type'], $graphtype);

$type = basename($graphtype['type']);
$subtype = basename($graphtype['subtype']);
$id = $vars['id'] ?? null;

if (isset($vars['device'])) {
    $device = DeviceCache::get($vars['device']);
}

$auth = false;
if (is_file('includes/html/graphs/' . $type . '/auth.inc.php')) {
    require 'includes/html/graphs/' . $type . '/auth.inc.php';
}

if (! $auth) {
    require 'includes/html/error-no-perm.inc.php';
} else {
    if (LibrenmsConfig::has("graph_types.$type.$subtype.descr")) {
        $title .= ' :: ' . LibrenmsConfig::get("graph_types.$type.$subtype.descr");
    } elseif ($type == 'device' && $subtype == 'collectd') {
        $title .= ' :: ' . \LibreNMS\Util\StringHelpers::niceCase($subtype) . ' :: ' . $vars['c_plugin'];
        if (isset($vars['c_plugin_instance'])) {
            $title .= ' - ' . $vars['c_plugin_instance'];
        }
        $title .= ' - ' . $vars['c_type'];
        if (isset($vars['c_type_instance'])) {
            $title .= ' - ' . $vars['c_type_instance'];
        }
    } else {
        $title .= ' :: ' . \LibreNMS\Util\StringHelpers::niceCase($subtype);
    }

    $graph_array = $vars;
    $graph_array['height'] = '60';
    $graph_array['width'] = $thumb_width;
    $graph_array['legend'] = 'no';
    $graph_array['to'] = LibrenmsConfig::get('time.now');

    print_optionbar_start();
    echo $title;

    // FIXME allow switching between types for sensor and wireless also restrict types to ones that have data
    if (! in_array($type, ['sensor', 'wireless'])) {
        $graph_subtypes = get_graph_subtypes($type);
        if (count($graph_subtypes) > 1) {
            echo '<div style="float: right;"><form action="">';
            echo csrf_field();
            echo "<select name='type' id='type' onchange=\"window.open(this.options[this.selectedIndex].value,'_top')\" class='devices-graphs-select'>";

            foreach ($graph_subtypes as $avail_type) {
                echo "<option value='" . \LibreNMS\Util\Url::generate($vars, ['type' => $type . '_' . $avail_type, 'page' => 'graphs']) . "'";
                if ($avail_type == $subtype) {
                    echo ' selected';
                }
                $display_type = \LibreNMS\Util\StringHelpers::niceCase($avail_type);
                echo ">$display_type</option>";
            }
            echo '</select></form></div>';
        }
    }

    print_optionbar_end();

    $show_command = isset($vars['showcommand']) && $vars['showcommand'] == 'yes';
    if (! $show_command) {
        $thumb_array = LibrenmsConfig::get('graphs.row.normal');

        echo '<table width=100% class="thumbnail_graph_table"><tr>';

        foreach ($thumb_array as $period => $text) {
            $graph_array['from'] = LibrenmsConfig::get("time.$period");

            $link_array = $vars;
            $link_array['from'] = $graph_array['from'];
            $link_array['to'] = $graph_array['to'];
            $link_array['page'] = 'graphs';
            $link = \LibreNMS\Util\Url::generate($link_array);

            echo '<td style="text-align: center;">';
            echo '<b>' . $text . '</b>';
            echo '<a href="' . $link . '">';
            echo \LibreNMS\Util\Url::lazyGraphTag($graph_array);
            echo '</a>';
            echo '</td>';
        }

        echo '</tr></table>';
        echo '<hr />';
    }

    $graph_array = $vars;
    $graph_array['height'] = LibrenmsConfig::get('webui.min_graph_height');
    $graph_array['width'] = $graph_width;

    if ($screen_width = Session::get('screen_width')) {
        if ($screen_width > 800) {
            $graph_array['width'] = ($screen_width - ($screen_width / 10));
        } else {
            $graph_array['width'] = ($screen_width - ($screen_width / 4));
        }
    }

    if ($screen_height = Session::get('screen_height')) {
        if ($screen_height > 960) {
            $graph_array['height'] = ($screen_height - ($screen_height / 2));
        } else {
            $graph_array['height'] = max($graph_array['height'], $screen_height - ($screen_height / 1.5));
        }
    }

    include_once 'includes/html/print-date-selector.inc.php';

    echo '<div style="padding-top: 5px";></div>';
    echo '<center>';
    if (isset($vars['legend']) && $vars['legend'] == 'no') {
        echo generate_link('Show Legend', $vars, ['page' => 'graphs', 'legend' => null]);
    } else {
        echo generate_link('Hide Legend', $vars, ['page' => 'graphs', 'legend' => 'no']);
    }

    // FIXME : do this properly
    //  if ($type == "port" && $subtype == "bits")
    //  {
    echo ' | ';
    if (isset($vars['previous']) && $vars['previous'] == 'yes') {
        echo generate_link('Hide Previous', $vars, ['page' => 'graphs', 'previous' => null]);
    } else {
        echo generate_link('Show Previous', $vars, ['page' => 'graphs', 'previous' => 'yes']);
    }
    //  }

    echo ' | ';
    if ($show_command) {
        echo generate_link('Hide RRD Command', $vars, ['page' => 'graphs', 'showcommand' => null]);
    } else {
        echo generate_link('Show RRD Command', $vars, ['page' => 'graphs', 'showcommand' => 'yes']);
    }

    if ($vars['type'] == 'port_bits') {
        echo ' | ';
        if ($vars['port_speed_zoom'] ?? LibrenmsConfig::get('graphs.port_speed_zoom')) {
            echo generate_link('Zoom to Traffic', $vars, ['page' => 'graphs', 'port_speed_zoom' => 0]);
        } else {
            echo generate_link('Zoom to Port Speed', $vars, ['page' => 'graphs', 'port_speed_zoom' => 1]);
        }
        echo ' | To show trend, set to future date';
    }

    if (str_contains((string) $vars['type'], 'sensor_')) {
        echo ' | To show trend, set to future date';
    }

    echo '</center>';

    echo generate_graph_js_state($graph_array);

    echo '<div style="width: ' . $graph_array['width'] . '; margin: auto;"><center>';
    if (LibrenmsConfig::get('webui.dynamic_graphs', false) === true) {
        echo generate_dynamic_graph_js($graph_array);
        echo generate_dynamic_graph_tag($graph_array);
    } else {
        echo \LibreNMS\Util\Url::lazyGraphTag($graph_array);
    }
    echo '</center></div>';

    if (LibrenmsConfig::has('graph_descr.' . $vars['type'])) {
        print_optionbar_start();
        echo '<div style="float: left; width: 30px;">
            <div style="margin: auto auto;">
            <i class="fa-solid fa-circle-info fa-lg icon-theme" aria-hidden="true"></i>
            </div>
            </div>';
        echo LibrenmsConfig::get('graph_descr.' . $vars['type']);
        print_optionbar_end();
    }

    if ($show_command) {
        $vars = $graph_array;
        $_GET = $graph_array;
        $command_only = 1;

        require 'includes/html/graphs/graph.inc.php';
    }
}

```

### includes/html/pages/routing/bgp.inc.php
```
<?php

use App\Models\BgpPeer;
use App\Models\Device;
use LibreNMS\Exceptions\InvalidIpException;
use LibreNMS\Util\IPv6;
use LibreNMS\Util\Number;
use LibreNMS\Util\Time;
use LibreNMS\Util\Url;

if (\Illuminate\Support\Facades\Gate::denies('viewAny', BgpPeer::class)) {
    include 'includes/html/error-no-perm.inc.php';
} else {
    $where = '';
    $extra_sql = '';
    $link_array = [
        'page' => 'routing',
        'protocol' => 'bgp',
    ];

    print_optionbar_start('', '');

    echo '<span style="font-weight: bold;">BGP</span> &#187; ';

    if (! $vars['type']) {
        $vars['type'] = 'all';
    }

    if ($vars['type'] == 'all') {
        echo "<span class='pagemenu-selected'>";
    }

    echo generate_link('All', $vars, ['type' => 'all']);
    if ($vars['type'] == 'all') {
        echo '</span>';
    }

    echo ' | ';

    if ($vars['type'] == 'internal') {
        echo "<span class='pagemenu-selected'>";
    }

    echo generate_link('iBGP', $vars, ['type' => 'internal']);
    if ($vars['type'] == 'internal') {
        echo '</span>';
    }

    echo ' | ';

    if ($vars['type'] == 'external') {
        echo "<span class='pagemenu-selected'>";
    }

    echo generate_link('eBGP', $vars, ['type' => 'external']);
    if ($vars['type'] == 'external') {
        echo '</span>';
    }

    echo ' | ';

    if ($vars['adminstatus'] == 'stop') {
        echo "<span class='pagemenu-selected'>";
        echo generate_link('Shutdown', $vars, ['adminstatus' => null]);
        echo '</span>';
    } else {
        echo generate_link('Shutdown', $vars, ['adminstatus' => 'stop']);
    }

    echo ' | ';

    if ($vars['adminstatus'] == 'start') {
        echo "<span class='pagemenu-selected'>";
        echo generate_link('Enabled', $vars, ['adminstatus' => null]);
        echo '</span>';
    } else {
        echo generate_link('Enabled', $vars, ['adminstatus' => 'start']);
    }

    echo ' | ';

    if ($vars['state'] == 'down') {
        echo "<span class='pagemenu-selected'>";
        echo generate_link('Down', $vars, ['state' => null]);
        echo '</span>';
    } else {
        echo generate_link('Down', $vars, ['state' => 'down']);
    }

    // End BGP Menu
    if (! isset($vars['view'])) {
        $vars['view'] = 'details';
    }

    echo '<div style="float: right;">';

    if ($vars['view'] == 'details') {
        echo "<span class='pagemenu-selected'>";
    }

    echo generate_link('No Graphs', $vars, ['view' => 'details', 'graph' => 'NULL']);
    if ($vars['view'] == 'details') {
        echo '</span>';
    }

    echo ' | ';

    if ($vars['graph'] == 'updates') {
        echo "<span class='pagemenu-selected'>";
    }

    echo generate_link('Updates', $vars, ['view' => 'graphs', 'graph' => 'updates']);
    if ($vars['graph'] == 'updates') {
        echo '</span>';
    }

    echo ' | Prefixes: Unicast (';
    if ($vars['graph'] == 'prefixes_ipv4unicast') {
        echo "<span class='pagemenu-selected'>";
        $extra_sql = " AND `bgpPeerIdentifier` NOT LIKE '%:%'";
    }

    echo generate_link('IPv4', $vars, ['view' => 'graphs', 'graph' => 'prefixes_ipv4unicast']);
    if ($vars['graph'] == 'prefixes_ipv4unicast') {
        echo '</span>';
    }

    echo '|';

    if ($vars['graph'] == 'prefixes_ipv6unicast') {
        echo "<span class='pagemenu-selected'>";
        $extra_sql = " AND `bgpPeerIdentifier` LIKE '%:%'";
    }

    echo generate_link('IPv6', $vars, ['view' => 'graphs', 'graph' => 'prefixes_ipv6unicast']);
    if ($vars['graph'] == 'prefixes_ipv6unicast') {
        echo '</span>';
    }

    echo '|';

    if ($vars['graph'] == 'prefixes_ipv4vpn') {
        echo "<span class='pagemenu-selected'>";
    }

    echo generate_link('VPNv4', $vars, ['view' => 'graphs', 'graph' => 'prefixes_ipv4vpn']);
    if ($vars['graph'] == 'prefixes_ipv4vpn') {
        echo '</span>';
    }

    echo '|';

    if ($vars['graph'] == 'prefixes_ipv6vpn') {
        echo "<span class='pagemenu-selected'>";
    }

    echo generate_link('VPNv6', $vars, ['view' => 'graphs', 'graph' => 'prefixes_ipv6vpn']);
    if ($vars['graph'] == 'prefixes_ipv6vpn') {
        echo '</span>';
    }

    echo ')';

    echo ' | Multicast (';
    if ($vars['graph'] == 'prefixes_ipv4multicast') {
        echo "<span class='pagemenu-selected'>";
    }

    echo generate_link('IPv4', $vars, ['view' => 'graphs', 'graph' => 'prefixes_ipv4multicast']);
    if ($vars['graph'] == 'prefixes_ipv4multicast') {
        echo '</span>';
    }

    echo '|';

    if ($vars['graph'] == 'prefixes_ipv6multicast') {
        echo "<span class='pagemenu-selected'>";
    }

    echo generate_link('IPv6', $vars, ['view' => 'graphs', 'graph' => 'prefixes_ipv6multicast']);
    if ($vars['graph'] == 'prefixes_ipv6multicast') {
        echo '</span>';
    }

    echo ')';

    echo ' | MAC (';
    if ($vars['graph'] == 'macaccounting_bits') {
        echo "<span class='pagemenu-selected'>";
    }

    echo generate_link('Bits', $vars, ['view' => 'graphs', 'graph' => 'macaccounting_bits']);
    if ($vars['graph'] == 'macaccounting_bits') {
        echo '</span>';
    }

    echo '|';

    if ($vars['graph'] == 'macaccounting_pkts') {
        echo "<span class='pagemenu-selected'>";
    }

    echo generate_link('Packets', $vars, ['view' => 'graphs', 'graph' => 'macaccounting_pkts']);
    if ($vars['graph'] == 'macaccounting_pkts') {
        echo '</span>';
    }

    echo ')';

    echo '</div>';

    print_optionbar_end();

    echo "<table border=0 cellspacing=0 cellpadding=5 width=100% class='table sortable'>";
    echo '<tr style="height: 30px"><td width=1></td><th>Local address</th><th></th><th>Peer address</th><th>Type</th><th>Family</th><th>Remote AS</th><th>Peer description</th><th>State</th><th>Last error</th><th width=200>Uptime / Updates</th></tr>';

    if ($vars['type'] == 'external') {
        $where = 'AND D.bgpLocalAs != B.bgpPeerRemoteAs';
    } elseif ($vars['type'] == 'internal') {
        $where = 'AND D.bgpLocalAs = B.bgpPeerRemoteAs';
    }

    if ($vars['adminstatus'] == 'stop') {
        $where .= " AND (B.bgpPeerAdminStatus = 'stop')";
    } elseif ($vars['adminstatus'] == 'start') {
        $where .= " AND (B.bgpPeerAdminStatus = 'start' || B.bgpPeerAdminStatus = 'running')";
    }

    if ($vars['state'] == 'down') {
        $where .= " AND (B.bgpPeerState != 'established')";
    }

    $peer_query = "SELECT * FROM `bgpPeers` AS `B`, `devices` AS `D` WHERE `B`.`device_id` = `D`.`device_id` $where $extra_sql ORDER BY `D`.`hostname`, `B`.`bgpPeerRemoteAs`, `B`.`bgpPeerIdentifier`";
    foreach (dbFetchRows($peer_query) as $peer) {
        unset($alert);
        $peer['alert'] = 0;
        if ($peer['bgpPeerState'] == 'established') {
            $col = 'green';
        } else {
            $col = 'red';
            $peer['alert'] = 1;
        }

        if ($peer['bgpPeerAdminStatus'] == 'start' || $peer['bgpPeerAdminStatus'] == 'running') {
            $admin_col = 'green';
        } else {
            $admin_col = 'gray';
        }

        if ($peer['bgpPeerAdminStatus'] == 'stop') {
            $peer['alert'] = 0;
            $peer['disabled'] = 1;
        }

        if ($peer['bgpPeerRemoteAs'] == $peer['bgpLocalAs']) {
            $peer_type = "<span style='color: #00f;'>iBGP</span>";
        } else {
            $peer_type = "<span style='color: #0a0;'>eBGP</span>";
            // Private ASN ranges
            // 64512 - 65534 (Private)
            // 4200000000 - 4294967294 (Private)
            if (($peer['bgpPeerRemoteAs'] >= 64512 && $peer['bgpPeerRemoteAs'] <= 65534) || ($peer['bgpPeerRemoteAs'] >= 4200000000 && $peer['bgpPeerRemoteAs'] <= 4294967294)) {
                $peer_type = "<span style='color: #0af;'>Priv eBGP</span>";
            }
        }

        try {
            $local_addr = new IPv6($peer['bgpLocalAddr']);
        } catch (InvalidIpException $e) {
            $local_addr = $peer['bgpLocalAddr'];
        }

        try {
            $peer_addr = new IPv6($peer['bgpPeerRemoteAddr'] != '0.0.0.0' ? $peer['bgpPeerRemoteAddr'] : $peer['bgpPeerIdentifier']);
        } catch (InvalidIpException $e) {
            $peer_addr = $peer['bgpPeerIdentifier'];
        }

        // display overlib graphs
        $graph_array = [];
        $graph_array['type'] = 'bgp_updates';
        $graph_array['to'] = \App\Facades\LibrenmsConfig::get('time.now');
        $graph_array['from'] = \App\Facades\LibrenmsConfig::get('time.day');
        $graph_array['height'] = '110';
        $graph_array['width'] = $width;

        // Peer Address
        $peer_device = Device::whereHas('bgppeers', fn ($q) => $q->where('bgpLocalAddr', $peer['bgpPeerIdentifier']))->first();
        $peeraddresslink = '<span class=list-large>' . Url::deviceLink($peer_device, $peer_addr, ['tab' => 'routing', 'proto' => 'bgp']) . '</span>';

        // Local Address
        $graph_array['id'] = $peer['bgpPeer_id'];
        $graph_array['afi'] = 'ipv4';
        $graph_array['safi'] = 'unicast';
        $graph_array_zoom = $graph_array;
        $graph_array_zoom['height'] = '150';
        $graph_array_zoom['width'] = '500';
        $graph_array_zoom['afi'] = 'ipv4';
        $graph_array_zoom['safi'] = 'unicast';
        $overlib_link = 'device/device=' . $peer['device_id'] . '/tab=routing/proto=bgp/';
        $localaddresslink = '<span class=list-large>' . Url::overlibLink($overlib_link, $local_addr, Url::graphTag($graph_array_zoom)) . '</span>';

        if ($peer['bgpPeerLastErrorCode'] == 0 && $peer['bgpPeerLastErrorSubCode'] == 0) {
            $last_error = $peer['bgpPeerLastErrorText'];
        } else {
            $last_error = describe_bgp_error_code($peer['bgpPeerLastErrorCode'], $peer['bgpPeerLastErrorSubCode']) . '<br/>' . $peer['bgpPeerLastErrorText'];
        }

        echo '<tr class="bgp"' . ($peer['alert'] ? ' bordercolor="#cc0000"' : '') . ($peer['disabled'] ? ' bordercolor="#cccccc"' : '') . '>';

        $sep = '';
        foreach (dbFetchRows('SELECT * FROM `bgpPeers_cbgp` WHERE `device_id` = ? AND bgpPeerIdentifier = ?', [$peer['device_id'], $peer['bgpPeerIdentifier']]) as $afisafi) {
            $afi = $afisafi['afi'];
            $safi = $afisafi['safi'];
            $this_afisafi = $afi . $safi;
            $peer['afi'] = ($peer['afi'] ?? '') . $sep . $afi . '.' . $safi;
            $sep = '<br />';
            $peer['afisafi'][$this_afisafi] = 1;
            // Build a list of valid AFI/SAFI for this peer
        }

        echo '  <td></td>
            <td width=150>' . $localaddresslink . '<br />' . generate_device_link($peer, null, ['tab' => 'routing', 'proto' => 'bgp']) . '</td>
            <td width=30><b>&#187;</b></td>
            <td width=150>' . $peeraddresslink . '<br />' . Url::deviceLink($peer_device, vars: ['tab' => 'routing', 'proto' => 'bgp']) . "</td>
            <td width=50><b>$peer_type</b></td>
            <td width=50>" . ($peer['afi'] ?? '') . '</td>
            <td><strong>AS' . $peer['bgpPeerRemoteAs'] . '</strong><br />' . $peer['astext'] . '</td>
            <td>' . $peer['bgpPeerDescr'] . "</td>
            <td><strong><span style='color: $admin_col;'>" . $peer['bgpPeerAdminStatus'] . "</span><br /><span style='color: $col;'>" . $peer['bgpPeerState'] . '</span></strong></td>
            <td>' . $last_error . '</td>
            <td>' . Time::formatInterval($peer['bgpPeerFsmEstablishedTime']) . "<br />
            Updates <i class='fa fa-arrow-down icon-theme' aria-hidden='true'></i> " . Number::formatSi($peer['bgpPeerInUpdates'], 2, 0, '') . "
            <i class='fa fa-arrow-up icon-theme' aria-hidden='true'></i> " . Number::formatSi($peer['bgpPeerOutUpdates'], 2, 0, '') . '</td></tr>';

        unset($invalid);

        switch ($vars['graph']) {
            case 'prefixes_ipv4unicast':
            case 'prefixes_ipv4multicast':
            case 'prefixes_ipv4vpn':
            case 'prefixes_ipv6unicast':
            case 'prefixes_ipv6multicast':
                [,$afisafi] = explode('_', (string) $vars['graph']);
                if (isset($peer['afisafi'][$afisafi])) {
                    $peer['graph'] = 1;
                }
                // fall-through
            case 'updates':
                $graph_array['type'] = 'bgp_' . $vars['graph'];
                $graph_array['id'] = $peer['bgpPeer_id'];
        }

        switch ($vars['graph']) {
            case 'macaccounting_bits':
            case 'macaccounting_pkts':
                $acc = dbFetchRow('SELECT * FROM `ipv4_mac` AS I, `mac_accounting` AS M, `ports` AS P, `devices` AS D WHERE I.ipv4_address = ? AND M.mac = I.mac_address AND P.port_id = M.port_id AND D.device_id = P.device_id', [$peer['bgpPeerIdentifier']]);
                if (is_array($acc) && Rrd::checkRrdExists(Rrd::name($device['hostname'], ['cip', $acc['ifIndex'], $acc['mac']]))) {
                    $peer['graph'] = 1;
                    $graph_array['id'] = $acc['ma_id'];
                    $graph_array['type'] = $vars['graph'];
                }
        }

        if ($vars['graph'] == 'updates') {
            $peer['graph'] = 1;
        }

        if (isset($peer['graph']) && $peer['graph']) {
            $graph_array['height'] = '100';
            $graph_array['width'] = '218';
            $graph_array['to'] = \App\Facades\LibrenmsConfig::get('time.now');
            echo '<tr></tr><tr class="bgp"><td colspan="9">';

            include 'includes/html/print-graphrow.inc.php';

            echo '</td></tr>';
        }
    }//end foreach

    echo '</table>';
}//end if

```

### includes/html/pages/routing/vrf.inc.php
```
<?php

use App\Facades\DeviceCache;
use App\Facades\LibrenmsConfig;
use App\Models\Vrf;
use Illuminate\Support\Facades\Gate;
use LibreNMS\Util\Rewrite;

if (Gate::denies('viewAny', Vrf::class)) {
    include 'includes/html/error-no-perm.inc.php';
} else {
    $link_array = [
        'page' => 'routing',
        'protocol' => 'vrf',
    ];

    print_optionbar_start();

    echo "<span style='font-weight: bold;'>VRFs</span> &#187; ";

    $menu_options = ['basic' => 'Basic',
    ];

    if (! $vars['view']) {
        $vars['view'] = 'basic';
    }

    $sep = '';
    foreach ($menu_options as $option => $text) {
        if ($vars['view'] == $option) {
            echo "<span class='pagemenu-selected'>";
        }

        echo generate_link($text, $link_array, ['view' => $option]);
        if ($vars['view'] == $option) {
            echo '</span>';
        }

        echo ' | ';
    }

    unset($sep);

    echo ' Graphs: ';

    $graph_types = [
        'bits' => 'Bits',
        'upkts' => 'Unicast Packets',
        'nupkts' => 'Non-Unicast Packets',
        'errors' => 'Errors',
        'etherlike' => 'Etherlike',
    ];

    foreach ($graph_types as $type => $descr) {
        echo "$type_sep";
        if ($vars['graph'] == $type) {
            echo "<span class='pagemenu-selected'>";
        }

        echo generate_link($descr, $link_array, ['view' => 'graphs', 'graph' => $type]);
        if ($vars['graph'] == $type) {
            echo '</span>';
        }

        $type_sep = ' | ';
    }

    print_optionbar_end();

    echo '
      <div>
        <div class="panel panel-default">
          <div class="panel-body">
            <table class="table table-condensed table-hover" style="border-collapse:collapse;">
              <thead>
                <tr>
                  <th>&nbsp;</th>
                  <th>VRF</th>
                  <th>RD</th>
                  <th>Interfaces</th>
		</tr>
              </thead>';

    if ($vars['view'] == 'basic' || $vars['view'] == 'graphs') {
        // Pre-Cache in arrays
        // That's heavier on RAM, but much faster on CPU (1:40)
        // Specifying the fields reduces a lot the RAM used (1:4) .
        $vrf_fields = 'vrf_id, mplsVpnVrfRouteDistinguisher, mplsVpnVrfDescription, vrf_name';
        $dev_fields = 'D.device_id as device_id, hostname, os, hardware, version, features, location_id, status, `ignore`, disabled';
        $port_fields = 'port_id, ifvrf, device_id, ifDescr, ifAlias, ifName';

        foreach (dbFetchRows("SELECT $vrf_fields, $dev_fields FROM `vrfs` AS V, `devices` AS D WHERE D.device_id = V.device_id") as $vrf_device) {
            if (empty($vrf_devices[$vrf_device['vrf_name']][$vrf_device['mplsVpnVrfRouteDistinguisher']])) {
                $vrf_devices[$vrf_device['vrf_name']][$vrf_device['mplsVpnVrfRouteDistinguisher']][0] = $vrf_device;
            } else {
                array_push($vrf_devices[$vrf_device['vrf_name']][$vrf_device['mplsVpnVrfRouteDistinguisher']], $vrf_device);
            }
        }

        unset($ports);
        foreach (dbFetchRows("SELECT $port_fields FROM `ports` WHERE ifVrf<>0") as $port) {
            if (empty($ports[$port['ifvrf']][$port['device_id']])) {
                $ports[$port['ifvrf']][$port['device_id']][0] = $port;
            } else {
                array_push($ports[$port['ifvrf']][$port['device_id']], $port);
            }
        }

        $i = '1';
        echo '<tbody>';
        foreach (dbFetchRows('SELECT `vrf_name`, `mplsVpnVrfRouteDistinguisher`, `mplsVpnVrfDescription` FROM `vrfs` GROUP BY `mplsVpnVrfRouteDistinguisher`, `mplsVpnVrfDescription`,`vrf_name`') as $vrf) {
            echo '<tr><td></td>';
            echo '<td width=240>';
            echo '<a class=list-large href=' . \LibreNMS\Util\Url::generate($vars, ['view' => 'detail', 'vrf' => $vrf['vrf_name']]) . '>';
            echo $vrf['vrf_name'] . '</a><br />';
            echo '<span class=box-desc>' . $vrf['mplsVpnVrfDescription'] . '</span></td>';
            echo '<td width=100 class=box-desc>' . $vrf['mplsVpnVrfRouteDistinguisher'] . '</td>';
            echo '<td><table class="table table-hover table-striped table-condensed">';
            $x = 1;
            foreach ($vrf_devices[$vrf['vrf_name']][$vrf['mplsVpnVrfRouteDistinguisher']] as $device) {
                echo "<tr><td width=200><a href='";
                echo \LibreNMS\Util\Url::generate(['page' => 'device'], ['device' => $device['device_id'], 'tab' => 'routing', 'view' => 'basic', 'proto' => 'vrf']);
                echo "'>" . DeviceCache::get($device['device_id'])->displayName() . '</a> ';

                if ($device['vrf_name'] != $vrf['vrf_name']) {
                    echo "<a href='#' onmouseover=\" return overlib('Expected Name : " . $vrf['vrf_name'] . '<br />Configured : ' . $device['vrf_name'] . "', CAPTION, '<span class=list-large>VRF Inconsistency</span>' ,FGCOLOR,'#e5e5e5', BGCOLOR, '#c0c0c0', BORDER, 5, CELLPAD, 4, CAPCOLOR, '#050505');\" onmouseout=\"return nd();\"> <i class='fa fa-flag fa-lg' style='color:red' aria-hidden='true'></i></a>";
                }

                echo '</td><td>';
                unset($seperator);

                foreach ($ports[$device['vrf_id']][$device['device_id']] as $port) {
                    $port = cleanPort($port);
                    $port = array_merge($device, $port);

                    switch ($vars['graph']) {
                        case 'bits':
                        case 'upkts':
                        case 'nupkts':
                        case 'errors':
                            $port['width'] = '130';
                            $port['height'] = '30';
                            $port['from'] = LibrenmsConfig::get('time.day');
                            $port['to'] = LibrenmsConfig::get('time.now');
                            $port['graph_type'] = 'port_' . $vars['graph'];
                            echo "<div style='display: block; padding: 3px; margin: 3px; min-width: 135px; max-width:135px; min-height:75px; max-height:75px;
                            text-align: center; float: left;'>
                                <div style='font-weight: bold;'>" . Rewrite::shortenIfName($port['ifDescr']) . '</div>';
                            print_port_thumbnail($port);
                            echo "<div style='font-size: 9px;'>" . substr((string) short_port_descr($port['ifAlias']), 0, 22) . '</div>
                                </div>';
                            break;

                        default:
                            echo $seperator . generate_port_link($port, Rewrite::shortenIfName($port['ifDescr']));
                            $seperator = ', ';
                            break;
                    }//end switch
                }//end foreach

                echo '</td></tr>';
                $x++;
            } //end foreach

            echo '</tbody></table></td>';
            $i++;
        }//end foreach
        echo '</table></div>';
    } elseif ($vars['view'] == 'detail') {
        echo 'Not Implemented';
    }//end if
} //end if

```

### includes/html/print-syslog.inc.php
```
<?php

if (device_permitted($entry['device_id'])) {
    $syslog_output .= '<tr>';

    // Stop shortening hostname. Issue #61
    // $entry['hostname'] = shorthost($entry['hostname'], 20);
    if ($vars['page'] != 'device') {
        $syslog_output .= '<td>' . $entry['date'] . '</td>
                        <td><strong>' . generate_device_link($entry) . '</strong></td>
                        <td><strong>' . $entry['program'] . ' : </strong> ' . htmlspecialchars((string) $entry['msg']) . '</td>';
    } else {
        $syslog_output .= '<td><i>' . $entry['date'] . '</i>&nbsp;&nbsp;&nbsp;<strong>' . $entry['program'] . '</strong>&nbsp;&nbsp;&nbsp;' . htmlspecialchars((string) $entry['msg']) . '</td>';
    }

    $syslog_output .= '</tr>';
}

```

### includes/html/print-vrf.inc.php
```
<?php

use LibreNMS\Util\Rewrite;

// fixme new url format

echo '<tbody><tr><td></td>';

echo "<td width=200 class=list-large><a href='routing/vrf/" . $vrf['mplsVpnVrfRouteDistinguisher'] . "/'>" . $vrf['vrf_name'] . '</a></td>';
echo '<td width=150 class=box-desc>' . $vrf['mplsVpnVrfDescription'] . '</td>';
echo '<td width=100 class=box-desc>' . $vrf['mplsVpnVrfRouteDistinguisher'] . '</td>';

echo '<td class="list-bold">';
foreach (dbFetchRows('SELECT * FROM ports WHERE `device_id` = ? AND `ifVrf` = ?', [$device['device_id'], $vrf['vrf_id']]) as $port) {
    $port = cleanPort($port, $device);
    if ($vars['view'] == 'graphs') {
        $graph_type = 'port_' . $vars['graph'];
        echo "<div style='display: block; padding: 2px; margin: 2px; min-width: 139px; max-width:139px; min-height:85px; max-height:85px; text-align: center; float: left; background-color: #e9e9e9;'>
    <div style='font-weight: bold;'>" . Rewrite::shortenIfName($port['ifDescr']) . "</div>
    <a href='device/" . $device['device_id'] . '/port/' . $port['port_id'] . "/' onmouseover=\"return overlib('\
    <div style=\'font-size: 16px; padding:5px; font-weight: bold; color: #e5e5e5;\'>" . $device['hostname'] . ' - ' . $port['ifDescr'] . '</div>\
    ' . $port['ifAlias'] . " \
    <img src=\'graph.php?type=$graph_type&amp;id=" . $port['port_id'] . '&amp;from=' . \App\Facades\LibrenmsConfig::get('time.twoday') . '&amp;to=' . \App\Facades\LibrenmsConfig::get('time.now') . "&amp;width=450&amp;height=150\'>\
    ', CENTER, LEFT, FGCOLOR, '#e5e5e5', BGCOLOR, '#e5e5e5', WIDTH, 400, HEIGHT, 150);\" onmouseout=\"return nd();\"  >" . "<img src='graph.php?type=$graph_type&amp;id=" . $port['port_id'] . '&amp;from=' . \App\Facades\LibrenmsConfig::get('time.twoday') . '&amp;to=' . \App\Facades\LibrenmsConfig::get('time.now') . "&amp;width=132&amp;height=40&amp;legend=no'>
    </a>
    <div style='font-size: 9px;'>" . substr((string) short_port_descr($port['ifAlias']), 0, 22) . '</div>
   </div>';
    } else {
        echo $vrf['port_sep'] . generate_port_link($port, Rewrite::shortenIfName($port['ifDescr']));
        $vrf['port_sep'] = ', ';
    }
}

echo '</td>';
echo '</tr></tbody>';

```

### resources/views/map/custom-list.blade.php
```
@extends('layouts.librenmsv1')

@section('title', __('Custom Maps'))

@section('content')
<div class="tw:px-3 tw:sm:px-6 tw:mx-auto">
    <x-panel id="manage-custom-maps" class="tw:mx-auto tw:max-w-(--breakpoint-lg)">
        <x-slot:title>
            <div class="tw:flex tw:justify-between tw:items-center">
                <div>
                    {{ __('Custom Maps') }}
                </div>
            </div>
        </x-slot:title>
        <x-slot:slot class="tw:pb-0!">
        <x-accordion accordionId="CustomMapGroups">
            @foreach($maps as $group_name => $group)
                <x-accordion.item title="{{$group_name ?: 'Ungrouped'}}" id="{{uniqid()}}" open="{{($open_group == $group_name) || (count($maps) == 1)}}">
                @foreach($group as $map)
                    <div id="map-{{ $map->custom_map_id }}" class="tw:even:bg-gray-50 tw:dark:even:bg-zinc-900">
                        <div class="tw:flex tw:justify-between tw:p-3 tw:items-center tw:hover:bg-gray-100 tw:dark:hover:bg-gray-600">
                            <div>
                                <i class="fa fa-map-marked fa-fw fa-lg" aria-hidden="true"></i>
                                <a href="{{ route('maps.custom.show', $map->custom_map_id) }}">{!! $map->name !!}</a>
                            </div>
                        </div>
                    </div>
                @endforeach
                </x-accordion.item>
            @endforeach
        </x-accordion>
        </x-slot:slot>
    </x-panel>
</div>
@endsection

@section('scripts')
<script type="text/javascript">
    $(document).ready(async function () {
        scrollTo = document.getElementById("accordionCustomMapGroups").querySelector("div.accordion-header span.fa-minus");
        if(scrollTo != null) {
            scrollTo.scrollIntoView({block: "center"})
        };
    });
</script>
@endsection

```
Callers & Entry Points (How public input reaches the modified code)
(none)
Repository Map
LibreNMS/__init__.py
LibreNMS/command_runner.py
LibreNMS/config.py
LibreNMS/queuemanager.py
LibreNMS/service.py
LibreNMS/wrapper.py
discovery-wrapper.py
doc/js/docs-settings-links.js
html/js/L.Control.Locate.min.js
html/js/Leaflet.GoogleMutant.js
html/js/RrdGraphJS/moment-timezone-with-data.js
html/js/RrdGraphJS/q-5.0.2.min.js
html/js/RrdGraphJS/rrdGraphPng.js
html/js/boot.js
html/js/bootstrap-datetimepicker.min.js
html/js/bootstrap-hover-dropdown.min.js
html/js/bootstrap-switch.min.js
html/js/bootstrap.min.js
html/js/bootstrap4.min.js
html/js/clipboard.min.js
html/js/esri-leaflet-vector.js
html/js/esri-leaflet.js
html/js/handlebars.min.js
html/js/hogan-2.0.0.js
html/js/interact.min.js
html/js/jquery-qrcode.min.js
html/js/jquery.bootgrid.min.js
html/js/jquery.min.js
html/js/jquery.mousewheel.min.js
html/js/justgage.min.js
html/js/leaflet-bing-layer.min.js
html/js/leaflet-image.js
html/js/leaflet.awesome-markers.min.js
html/js/leaflet.js
html/js/leaflet.markercluster.js
html/js/librenms.js
html/js/mapael-maps/argentina/argentina.js
html/js/mapael-maps/belgium/belgium.js
html/js/mapael-maps/european_union/european_union.js
html/js/mapael-maps/france/france_departments_domtom.js
html/js/mapael-maps/france/france_region_01.js
html/js/mapael-maps/france/france_region_02.js
html/js/mapael-maps/france/france_region_03.js
html/js/mapael-maps/france/france_region_04.js
html/js/mapael-maps/france/france_region_06.js
html/js/mapael-maps/france/france_region_11.js
html/js/mapael-maps/france/france_region_21.js
html/js/mapael-maps/france/france_region_22.js
html/js/mapael-maps/france/france_region_23.js
html/js/mapael-maps/france/france_region_24.js
html/js/mapael-maps/france/france_region_25.js
html/js/mapael-maps/france/france_region_26.js
html/js/mapael-maps/france/france_region_31.js
html/js/mapael-maps/france/france_region_41.js
html/js/mapael-maps/france/france_region_42.js
html/js/mapael-maps/france/france_region_43.js
html/js/mapael-maps/france/france_region_52.js
html/js/mapael-maps/france/france_region_53.js
html/js/mapael-maps/france/france_region_54.js
html/js/mapael-maps/france/france_region_72.js
html/js/mapael-maps/france/france_region_73.js
html/js/mapael-maps/france/france_region_74.js
html/js/mapael-maps/france/france_region_82.js
html/js/mapael-maps/france/france_region_83.js
html/js/mapael-maps/france/france_region_91.js
html/js/mapael-maps/france/france_region_93.js
html/js/mapael-maps/france/france_region_94.js
html/js/mapael-maps/france/france_regions.js
html/js/mapael-maps/france/france_regions_domtom.js
html/js/mapael-maps/france/paris_districts.js
html/js/mapael-maps/malaysia/malaysia.js
html/js/mapael-maps/thailand/thailand.js
html/js/mapael-maps/ukraine/ukraine.js
html/js/mapael-maps/ukraine/vinnytsia_region.js
html/js/mapael-maps/united_kingdom/united_kingdom.js
html/js/mapael-maps/wales/wales_county.js
html/js/maps/france_departments.js
html/js/maps/usa_states.js
html/js/maps/world_countries.js
html/js/mktree.js
html/js/moment.min.js
html/js/overlib_mini.js
html/js/pace.min.js
html/js/polyfill.min.js
html/js/popper.min.js
html/js/qrcode.min.js
html/js/query-builder.standalone.min.js
html/js/raphael.min.js
html/js/register-service-worker.js
html/js/select2.full.min.js
html/js/sql-parser.min.js
html/js/tagmanager.js
html/js/toastr.min.js
html/js/tw-sack.js
html/js/typeahead.bundle.min.js
html/js/vis-data.min.js
html/js/vis-network.min.js
html/js/vis-timeline-graph2d.min.js
html/service-worker.js
librenms-service.py
poller-wrapper.py
resources/js/app.js
resources/js/bootstrap.js
resources/js/components/Accordion.vue
resources/js/components/AccordionItem.vue
resources/js/components/BaseSetting.vue
resources/js/components/ExampleComponent.vue
resources/js/components/LibrenmsSelect.vue
resources/js/components/LibrenmsSetting.vue
resources/js/components/LibrenmsSettings.vue
resources/js/components/MaintenanceMode.vue
resources/js/components/PollerSettings.vue
resources/js/components/SettingArray.vue
resources/js/components/SettingArraySubKeyed.vue
resources/js/components/SettingBoolean.vue
resources/js/components/SettingColor.vue
resources/js/components/SettingDirectory.vue
resources/js/components/SettingEmail.vue
resources/js/components/SettingExecutable.vue
resources/js/components/SettingFloat.vue
resources/js/components/SettingGroupRoleMap.vue
resources/js/components/SettingInteger.vue
resources/js/components/SettingLdapGroups.vue
resources/js/components/SettingMultiple.vue
resources/js/components/SettingNull.vue
resources/js/components/SettingOxidizedMaps.vue
resources/js/components/SettingPassword.vue
resources/js/components/SettingPasswordArray.vue
resources/js/components/SettingSelect.vue
resources/js/components/SettingSelectDynamic.vue
resources/js/components/SettingSnmp3auth.vue
resources/js/components/SettingText.vue
resources/js/components/Tab.vue
resources/js/components/Tabs.vue
resources/js/components/TransitionCollapseHeight.vue
resources/js/components/alpine/deviceLink.js
resources/js/components/alpine/filterBarComponent.js
resources/js/components/alpine/oldpopup.js
resources/js/components/alpine/popup.js
resources/js/components/alpine/portLink.js
resources/js/components/alpine/remoteDropdown.js
resources/js/datetime.js
resources/js/plugins/i18n.js
scripts/check_requirements.py
scripts/dynamic_check_requirements.py
services-wrapper.py
snmp-scan.py
tests/__init__.py
tests/tests.py
vite.config.mjs
Package Manifests (Dependencies, scripts, build configuration)
### package.json
```
{
    "private": true,
    "scripts": {
        "watch-production": "mix watch --production",
        "watch-prod": "npm run dev-production",
        "dev": "vite",
        "build": "vite build"
    },
    "devDependencies": {
        "@tailwindcss/vite": "^4.2.0",
        "@vitejs/plugin-vue2": "^1.1.2",
        "autoprefixer": "^10.4.2",
        "axios": "^1.15.2",
        "bootstrap": "^4.5.3",
        "jquery": "^3.5.1",
        "laravel-vite-plugin": "^1.0",
        "lodash": "^4.18.1",
        "popper.js": "^1.16.1",
        "postcss": "^8.5.12",
        "resolve-url-loader": "^5.0.0",
        "sass": "^1.49.0",
        "sass-loader": "^12.4.0",
        "tailwindcss": "^4.2.0",
        "vite": "^6.4",
        "vue-loader": "^17.4.2",
        "vue-template-compiler": "^2.6.14"
    },
    "dependencies": {
        "@alpinejs/intersect": "^3.15.12",
        "alpinejs": "^3.14.9",
        "babel-helper-vue-jsx-merge-props": "^2.0.3",
        "es6-object-assign": "^1.1.0",
        "gridstack": "^12.6.0",
        "luxon": "^3.7.2",
        "v-tooltip": "^2.0.3",
        "vue": "^2.7.0",
        "vue-i18n": "^8.26.8",
        "vue-js-modal": "^2.0.1",
        "vue-js-toggle-button": "^1.3.3",
        "vue-multiselect": "^2.1.6",
        "vue-nav-tabs": "^0.5.7",
        "vue-select": "^3.16.0",
        "vuedraggable": "^2.24.3"
    }
}

```

### composer.json
```
{
    "name": "librenms/librenms",
    "type": "project",
    "description": "A fully featured network monitoring system that provides a wealth of features and device support.",
    "keywords": [
        "network",
        "monitoring",
        "discovery",
        "alerting",
        "billing",
        "snmp",
        "distributed"
    ],
    "homepage": "https://www.librenms.org/",
    "license": "GPL-3.0-or-later",
    "require": {
        "php": "^8.2",
        "ext-curl": "*",
        "ext-gd": "*",
        "ext-json": "*",
        "ext-mbstring": "*",
        "ext-pcre": "*",
        "ext-pdo": "*",
        "ext-session": "*",
        "ext-simplexml": "*",
        "ext-sockets": "*",
        "ext-xml": "*",
        "ext-zlib": "*",
        "amenadiel/jpgraph": "^4",
        "clue/socket-raw": "^1.4",
        "dapphp/radius": "^3.0",
        "easybook/geshi": "^1.0.8",
        "enshrined/svg-sanitize": "^0.22.0",
        "fico7489/laravel-pivot": "^3.0",
        "influxdata/influxdb-client-php": "^3.8",
        "influxdb/influxdb-php": "^1.15",
        "jalle19/certificate-parser": "^4.0",
        "justinrainbow/json-schema": "^6.4",
        "laravel-notification-channels/webpush": "^10.0",
        "laravel/framework": "^12.10",
        "laravel/tinker": "^3.0",
        "laravel/ui": "^4.6",
        "librenms/laravel-vue-i18n-generator": "dev-master",
        "librenms/plugin-interfaces": "^1.0",
        "mews/purifier": "^3.4",
        "nesbot/carbon": "^3.8",
        "nunomaduro/laravel-console-summary": "^1.13",
        "pear/console_color2": "^0.1",
        "mikepultz/netdns2": "^1.5",
        "php-amqplib/php-amqplib": "^3.1",
        "phpmailer/phpmailer": "^7.0",
        "predis/predis": "^3.0",
        "socialiteproviders/manager": "^4.8",
        "spatie/laravel-ignition": "^2.9",
        "spatie/laravel-permission": "^6.16",
        "symfony/yaml": "^7.2",
        "tightenco/ziggy": "^2.0"
    },
    "require-dev": {
        "barryvdh/laravel-ide-helper": "^3.5",
        "coding-socks/lost-in-translation": "^0.3.5",
        "composer/composer": "^2.8",
        "fakerphp/faker": "^1.23",
        "friendsofphp/php-cs-fixer": "^3.66",
        "fruitcake/laravel-debugbar": "^4.1",
        "larastan/larastan": "^3.1",
        "laravel/boost": "^2.0",
        "laravel/dusk": "^8.2.2",
        "mockery/mockery": "^1.6",
        "nunomaduro/collision": "^8.6",
        "php-parallel-lint/php-parallel-lint": "^1.1",
        "phpstan/phpstan-deprecation-rules": "^2.0",
        "phpstan/phpstan-mockery": "^2.0",
        "phpstan/phpstan-phpunit": "^2.0",
        "phpunit/phpunit": "^11.5.33 || ^12.3.7",
        "rector/rector": "^2.1"
    },
    "suggest": {
        "ext-gmp": "Used for browser push notifications",
        "ext-ldap": "*",
        "ext-memcached": "Required if you utilize wrapper based distributed polling",
        "ext-mysqlnd": "*",
        "ext-posix": "Allows for additional validation tests"
    },
    "config": {
        "discard-changes": true,
        "optimize-autoloader": true,
        "platform-check": true,
        "preferred-install": "dist",
        "sort-packages": true,
        "allow-plugins": {
            "pestphp/pest-plugin": true,
            "php-http/discovery": false
        }
    },
    "extra": {
        "laravel": {
            "dont-discover": [
                "nunomaduro/laravel-console-summary",
                "facade/ignition",
                "socialiteproviders/manager"
            ]
        }
    },
    "autoload": {
        "psr-4": {
            "App\\": "app",
            "LibreNMS\\": "LibreNMS",
            "LibreNMS\\Plugins\\": "html/plugins",
            "LibreNMS\\Tests\\": "tests",
            "Database\\Factories\\": "database/factories/",
            "Database\\Seeders\\": "database/seeders/"
        },
        "classmap": [
            "vendor/dapphp/radius"
        ],
        "files": [
            "includes/helpers.php"
        ],
        "exclude-from-classmap": [
            "/vendor/laravel/laravel/database/",
            "/vendor/laravel/laravel/app/",
            "/html/plugins",
            "/vendor/marc-mabe/php-enum/stubs/Stringable.php"
        ]
    },
    "scripts": {
        "pre-install-cmd": "LibreNMS\\ComposerHelper::preInstall",
        "post-install-cmd": [
            "LibreNMS\\ComposerHelper::postInstall",
            "Illuminate\\Foundation\\ComposerScripts::postInstall",
            "@php artisan vue-i18n:generate --multi-locales --format=umd",
            "@php artisan view:cache",
            "@php artisan optimize",
            "@php artisan config:clear"
       
```
Context & Existing Test Patterns
Existing test files touched by the patch: none
Repository top-level entries: .editorconfig, .env.example, .git-blame-ignore-revs, .github, .gitignore, .php-cs-fixer.php, .styleci.yml, AUTHORS.md, CHANGELOG.md, CODE_OF_CONDUCT.md, CONTRIBUTING.md, LICENSE.txt, LibreNMS, README.md, SECURITY.md, alerts.php, app, artisan, billing-calculate.php, bootstrap, cache, check-services.php, composer.json, composer.lock, config, config.php.default, config_to_json.php, cronic, daily.php, daily.sh, database, delhost.php, discovery-wrapper.py, discovery.php, dist, doc, html, includes, irc.php, lang, librenms-service.py, licenses, lnms, logs, mibs, misc, mkdocs.yml, package-lock.json, package.json, phpstan-baseline-deprecated.neon, phpstan-deprecated.neon, phpstan-legacy.neon, phpstan.neon, phpunit.xml, ping.php, poll-billing.php, poller-wrapper.py, poller.php, publiccode.yml, rector.php
Project's own test patterns and conventions:
### tests/bootstrap.php
```
<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);

require_once 'includes/common.php';
require_once 'includes/dbFacile.php';
require_once 'includes/syslog.php';
require_once 'includes/snmp.inc.php';
require_once 'includes/services.inc.php';
require_once 'includes/functions.php';
require_once 'includes/rewrites.php';

require_once 'includes/html/functions.inc.php';
require_once 'includes/discovery/functions.inc.php';
require_once 'includes/polling/functions.inc.php';

```
Your Deliverables
Artifact 1: instruction.md - The Incident Defect Report
Write a realistic report (about 150-350 words) as a user or operator who hit the problem. Sections: a title naming
the symptom (not the fix); what was observed and how (the route the user hit); impact; what must keep working.

WHAT ACTUALLY DECIDES DIFFICULTY (measured, 2 accepted vs 37 solved): not how vague the report is, but whether part of
the root cause lives in a REAL place the report never leads to, with a test that reaches it. The accepted hono task's
report stated the cause and the rule, and listed three affected wrappers - both models still failed 6/6, because the
second renderer and the nested-array root were never mentioned and were tested. So the report may describe the
route(s) the user hit; its one job is to NOT reveal the hidden place(s) or how far the bug reaches.

NEVER (each measured on a task both models then solved; ids are the evidence):
- state the SCOPE or completeness of the bug: "the same acceptance happens on each one we tried", "for every operation",
  "on every route", "every command that ...", "all three nodes". It tells the agent to grep for every sibling and the
  trap disappears - oauth-providers fm3f, n8n f3f2, vitest p63j, q2xc (all four solved on attempt 1). Show the route(s)
  the user hit; whether others exist is for the agent to find;
- reveal or hint at a hidden place (metadata.trap.paths): not by name, and not by a role specific enough to find it;
- list the tainted parameters, the payload set or the variants your tests use (n8n f3f2 named all four tainted
  parameters and the legal operator list). One illustrative example of the symptom is fine;
- name a function by a behaviour so specific it identifies it ("the one that ignores the address's own suffix" - j6r3);
- offer or rule on an acceptable fix ("refusing the archive is fine" - p634) or say which layer should change;
- in "what must keep working", list the boundary VALUES your tests use ("/0 networks, IPv4-mapped addresses",
  "[db].[dbo].[t], numeric-string limits"). Name the FEATURES that must keep working (hono: "a bare string must still
  render as the top-level element", "content marked as trusted raw HTML still emits markup");
- file, directory, module, function, method or class names the fix changes, options it adds, or line numbers.
AVOID stating the root cause when the fix is in one local place: there it IS the answer (adm-zip p634: "two entries
with the same name"; ip-address j6r3: "never checks both sides are the same kind of address").
Write in your OWN words. Do not quote the official CVE/GHSA summary, and do not include the CVE/OSV ID.
Fairness: every test_functional_* exercises an ordinary use of a feature named under "what must keep working", and
every test_security_* is an instance of the harm described.
Artifact 2: hidden_tests.py - Black-Box Pytest Suite
The suite runs at the repository root with REPO_ROOT set.
Strict Constraints:
Pure pytest, deterministic, offline (no internet access, no sleeps > 1s, harmless sentinels/tmp_path only).
Black-Box Execution: Test ONLY via public entry points (public CLI commands, public API methods, exported library
functions, or HTTP route handlers). NEVER import, inspect, or call new helper functions, new structs, or new fields
introduced by the reference patch.
Agnostic Assertions: Accept ANY valid rejection mechanism (raised exception, HTTP 4xx, sanitized return value).
Never assert on exact error string text or specific internal exception classes added by the patch.
Language Adapters:
Python: Direct import of public pre-patch modules.
Node/TypeScript: Use subprocess to run project's test runner (vitest/jest) or inline node script driving src/ (NEVER dist/).
Go: Write temporary zz_hidden_<name>_test.go and execute via go test -count=1 ./<pkg>.
PHP (Composer): Write a temporary zz_hidden_<name>.php in the repo root starting with require __DIR__ . '/vendor/autoload.php';
drive the project's public API or HTTP kernel the way its own tests do, print ONE JSON line of what a caller observes, and
run it with php via subprocess (remove the file in a finally block). Use only classes that exist in the PRE-patch source;
never change composer.json/composer.lock; no database or network - use the project's in-memory/array/SQLite drivers.
Non-Destructive Invariant: The reference patch MUST score 100% (all tests pass). The vulnerable code MUST fail all
test_security_* tests.
Naming & Test Structure:
test_security_* (at least 3, ideally 4-8): Fail on vulnerable code, pass after a correct fix.
COVER EVERY FIX PLACE (the #1 measured cause of easy tasks: in 24 of 37 solved tasks the agent passed while changing
FEWER source files than the reference fix - e.g. 1 of 12 - because no test reached the other places). List every source
place the reference fix hardens; give EACH its own test_security_* reached through its OWN real entry point, so a
repair that skips any one place fails. A variant counts only if it reaches the root cause through a DIFFERENT place or
route. Spelling, case, whitespace, encoding or extension variants of the same input through the same route do NOT
count - measured: pure spelling/encoding variants are always caught, and input variants were never missed.
Strongest sibling kinds to target (measured miss rates): a mechanism that never had the protection so its absence
reads as design (32%); a producer - schema, serializer, loader, config resolver - that feeds the check through a path
the check never calls (29%); a second real implementation (fallback backend, adapter, inline copy) (19%); the check
authorising the wrong/neighbouring object or an attacker-chosen identity field; the restricted value arriving through
defaults, merge, inheritance or stored config. Prefer REAL siblings the upstream fix also changed or never touched.
test_functional_* (at least 3, ideally 4-8): Pass on both vulnerable and fixed code.
Legitimate inputs near the rejection boundary, custom enterprise configurations, and valid workflows. An over-broad
fix that disables features or universally rejects input must fail these tests.
Hard Rules Learned from Historical QA Rejections
THE FAIRNESS CONTRACT (NO UNSEEN PLUMBING): every test_functional_* must exercise an ordinary use of a FEATURE named
under "What must keep working" - name the feature, not the test's values. If a test needs private enterprise registries
(e.g. my-tfe.corp.example), the report says that "users who configure a private registry" must keep working; it does
not list hosts, env vars or edge cases. A feature the vulnerable code never supported is not "legitimate" (infracost).
SIBLING BLAST RADIUS (INCOMPLETE UPSTREAM FIXES): If the reference patch only fixes 7 out of 8 providers/parsers
(leaving sibling components vulnerable), and an intelligent agent fixing the 8th component would break pre-existing
repository tests (e.g., legacy tests asserting unauthenticated behavior for provider X), answer ONLY with:
<unsuitable>incomplete upstream fix: sibling provider tests break under full remediation</unsuitable>.
IMPLEMENTATION INDEPENDENCE: A test must pass for ANY reasonable, correct architecture. Never assert that a check
lives in a specific layer, or that internal state changed in a specific way, when an alternative placement is equally sound.
COMPILED REPOSITORIES (TS/GO): Test source code directly. Never require compiled bundles (dist/index.js) which
do not exist until build and would omit agent edits.
NO TRIVIAL OR SYNTHETIC CODE: If the vulnerability is a pure dependency bump, a config toggle, or does not support
a multi-file / deeper-layer trap, answer ONLY with: <unsuitable>no hidden-path trap: <reason></unsuitable>.
Artifact 3: check_patches - Three Validation Fixes
Provide search/replace edits on pre-patch source files to verify test suite discrimination:
"shallow": Quick band-aid fixing only the primary trigger. Must pass >= 1 security test, but FAIL >= 1 security variant.
"removal": Over-restrictive fix (disables feature/returns early). Must FAIL >= 1 functional test.
"alternative": A correct, clean fix designed differently than the reference patch. Must PASS ALL tests.
Output Format (Strict XML Blocks Only)
Return ONLY these four blocks, nothing else:
<instruction_md>
...markdown matching the exact section structure specified above...
</instruction_md>
<hidden_tests_py>
...python source, no code fences...
</hidden_tests_py>
<task_metadata_json>
{
"entry_point": "<public entry point string>",
"techniques": [1, 5, 9],
"trap": {
"paths": ["<repo-relative source file agent is likely to miss>"],
"contract": "<the specific legitimate behavior near the boundary that functional tests pin>"
},
"fix_places": ["<EVERY reference-fix source file whose change closes part of the vulnerability; the pipeline re-runs the fix
               WITHOUT each one and a test must then fail>"],
"unrelated_files": ["<every OTHER reference-fix source file (refactor, typing, logging, an unrelated feature bundled in the
                    commit). Every source file of the reference patch must appear in fix_places or here>"],
"test_justifications": {
"<test_function_name>": "<exact sentence or quote from instruction.md requiring this test's assertion>"
}
}
</task_metadata_json>
<check_patches_json>
{
"shallow": [{"file": "<path>", "search": "<exact existing code>", "replace": "<new code>"}],
"removal": [...],
"alternative": [...]
}
</check_patches_json>


# The checks your task will face (write it to pass all of them the first time)
An independent reviewer scores the task on these criteria; any failed "must pass" criterion sends it back:
- no_hints (must pass): instruction.md names no file, module, path, line number, or function/class the fix changes AND does not prescribe the fix: an 'expected behaviour' part may state the security property and the legitimate behaviour to keep, but must not describe validation rules, accepted token formats, ordering of checks, or logging-vs-returning choices that amount to the fix design
- accurate_report (must pass): the report describes the vulnerability the oracle patch actually fixes (impact + how it is triggered), without inventing a different flaw
- solvable_from_report (must pass): a skilled engineer who reads the report and the code could determine every behaviour the hidden tests require; no test demands undisclosed or arbitrary behaviour
- real_entry_point (must pass): security tests reach the bug through a real entry point (public API/route/CLI), not by calling the internal function the patch edits
- variants_share_root_cause (must pass): extra exploit variants share the root cause and are all blocked by the oracle patch (no extra hardening the oracle does not provide)
- implementation_agnostic (must pass): tests never import/assert anything the patch adds, never assert exact error text, and accept any reasonable way of blocking the attack
- functional_meaningful (must pass): functional tests would FAIL if the feature were removed, disabled or over-blocked, yet pass on the vulnerable code
- deterministic_offline (must pass): no network, no timing/sleep-based races, no randomness that can flip a result
- realistic (must pass): the scenario is a realistic use of the project, not a contrived snippet or unreachable code
- security_not_trivial_config (must pass): the vulnerability is in program logic, not a dependency bump or config toggle
Then the task is EXECUTED: the reference fix must score 1.0 twice; the vulnerable code must fail every test_security_*
and pass every test_functional_*; the repo's own related tests must pass before and after the fix; your three check
patches run against your tests (shallow must still fail a security test, removal must fail a functional test,
alternative must pass everything); and if both target models can name the fix location from your report alone, the
task is rejected (so describe behaviour, never location).


# Design contract (measured: tasks that break BOTH models satisfy these)
1. At least TWO independent public entry points reach the root cause. The report names at most one; the other is
   discoverable by reading the code (a second renderer/parser/implementation, a lower-level public constructor, a
   second HTTP route/CLI, or a save/reload round-trip). Give each entry point its own test_security_*.
2. At EACH entry point, test at least two input shapes (bare value vs array/nested; path vs bytes; casing or encoding
   variants). A fix that handles only the reported shape must still fail.
3. Put at least one affected sink in a module whose path/name does not suggest the vulnerability; the report must not
   name it.
4. Include a functional test for every "must keep working" clause: it must PASS on the PRE-patch code and FAIL if the
   feature is removed or over-blocked.
5. At least one security test must be blocked only by the fix's change in a SECOND source file, not by the obvious
   first file. If the whole fix is one shared choke point, the models will solve the task.


# Task-design techniques (curated - follow them)
## What counts as a model failure (the grading contract)
- A task is solved only by reward 1.0: every hidden security test, every hidden functional test and every enforced
  existing repo test passes. Anything less is a FAILURE, including:
  - **Partial fix:** the agent closes some attack paths but not all (e.g. 5 of 6 security variants blocked). This is the
    most valuable failure: the model was confident and wrong ("silent failure").
  - **Fix that breaks something:** the hole is closed but a legitimate behaviour, an existing repo test, or the build
    breaks (over-correction / regression).
  - Both at once.
- A task is ACCEPTED when every attempt of both models (3 + 3) is such a failure, and the deterministic checks prove
  each failure is the model's (graded, no API/harness crash, agent really worked, no tampering). No AI judge decides.
- The goal is to MEASURE repair quality: a task only an incomplete or over-broad repair fails is a good task.
- So every task must be designed so that (a) a partial fix still fails and (b) an over-broad fix still fails.
- **Measured: models fail in two ways, equally often.** In the 2 QA-verified ACCEPTED tasks, 6 of 12 failures
  were over-corrections (apprise: hole closed, a pinned interface broken) and 6 left a path open (hono: a second
  renderer / input shape). So spend as much design effort on legitimate use as on attacks: functional tests for
  every legitimate input shape next to each attack variant, a public interface the repo's own tests pin
  (technique 11), and existing behaviour the obvious
  fix would change (hono: nested-array roots; apprise: the plugin `meta` dict). A "must keep working" test must follow from the report and
  pass on any correct fix - never a design only the reference fix makes (fairness QA withdrew infracost GHSA-6x6c and
  oauth-providers GHSA-fm3f for exactly that).

## Pattern catalogue - evidence-ranked from 471 measured sibling traps (2026-10-20)
A task shows ONE symptom through ONE route (the base bug). A **sibling** is another place the same protection is
missing that the report never names; a fix of the reported site alone then scores < 1.0. Every trap has two axes.

### Origin - where the sibling comes from (this is what decides difficulty, more than the mechanism)
- **A-FAR** (Pattern A): a site the real upstream fix ALSO changed, which the report does not lead to. **19% missed.** KEEP.
- **B-ROUTE** (Pattern B): a real, unmodified route with the same gap the upstream fix never touched. **25% missed - the strongest.** KEEP.
- **INJ** (injected/planted by us): **5% missed - almost never bites.** Once a model accepts the concept it closes all
  planted routes together (124 of 166 injected siblings are just M1/M2 routes of the stated concept). **TOO EASY - do not
  rely on injected siblings as the difficulty.** Confirmed 2026-10-20: our filament injection was declared unsuitable by
  the trap gate itself - every planted surface passed through one query scoper, so one restoration closed them all.
- Non-sibling kinds: **BASE** (the reported site), **SHAPE TRAP** (pure spelling/encoding variant of a route - ALWAYS
  caught, TOO EASY), **COUPLED TRAP** (a must-keep-working legitimate value next to the hidden one, tested functionally -
  bites, esp. MiMo which over-hardens; DeepSeek breaks coupled values too).

### Mechanism - why a model skips the sibling (miss rate = missed in >=1 run / siblings with trial data)
TOP BREAKERS (design toward these, on REAL code = A-FAR or B-ROUTE):
- **M4 Feature-absent** - the mechanism never had the protection, so its absence reads as design ("unsupported combo, not
  a boundary"). **7/22 = 32%, highest.** e.g. jackson any-setter has no view code.
- **M6 Producer off the check's path** - a schema/serializer/loader/config-resolver feeds the check through a path the
  check never calls; the model follows calls INTO the check, never asks where its data comes from. **5/17 = 29%.**
- **M2 Second implementation** (real, not injected) - a duplicate copy of the guarded logic: another package, fallback
  backend, adapter, inline copy. **14/73 = 19%.** "That path uses its own helper / only a fallback."
- **M10 Wrong object** - authorises a neighbouring/proxy object, or trusts an attacker-chosen identity field. **2/11.**
- **M5 Merged/defaults route** - the restricted value arrives via defaults/merge/inheritance/patch/stored-config; the
  model treats the report's example fields as the whole set.
- **M11 Coupled contract** - a linked visible value or shared helper must keep working; the natural fix breaks it
  (over-broad-fix trap). Bites MiMo hard.
WEAK / TOO EASY (do not use as the sole difficulty):
- **M1 Parallel entry** - another handler/endpoint/tool reaches the same sink. Only **12/99 = 12%** on real code, and ~0
  when injected. Allowed only as a secondary trap stacked with a top breaker.
- **M8 Parser differential** - genuine canonicalisation mismatch bites rarely (1/18); **pure spelling/case/encoding is
  always caught - TOO EASY.**
- **M12 Input variants** (encoding/spelling/verb/protocol/role of a stated input) - **never missed. TOO EASY, remove.**
- **M3 Shared layer** (0/6) and **M9 Fail-open fallback** (0/9) - never observed to bite; not proven breakers.

### The winning recipe (the only both-model breaker, jackson-databind-sib2, audited)
Uses NO planted code. A **Pattern B** route that **stacks several DIFFERENT mechanisms**: M4 (any-setter ignores views) +
M10+M11 (object-id stand-in property) + M5 (array/merge update) + a **coupled visible value an over-broad fix breaks**.
So: pick a real uncovered route, give it 2-3 different mechanisms, and pin a coupled legitimate value functionally.

### Avoid the checklist tell
Model-built (-ds/-mm) reports don't name siblings but describe each sibling's surface in product terms, one clause per
trap - that hands the solver a map. Never enumerate the HIDDEN places. (hono's report listed three affected wrappers
and still broke both models - because the places that decided it, the second renderer and the nested-array root, were
not in the list. Describing the route the user hit is fine; describing where else it lives is not.)

---

## Legacy numbered techniques (still referenced by the generator gate and scoreboard; map to the catalogue above)
Mapping: 1->M1, 2->dismissal-reason, 3->M3, 4->grading, 5->M11/coupled, 6->leak discipline, 7->M2, 8->RETIRED (M12),
9->M11, 10->RETIRED (width), 11->M11, 12->M4, 13->M6, 14->M10, 15->M5. The generator's trap gate accepts 1, 2, 3, 7 and
12-15 as hidden-path techniques; prefer 12, 13 and a real (not injected) 7. M1 parallel entry alone is weak (12%).

## What makes a repair task demanding - so only a complete, careful repair passes (use several in ONE task)
1. **Unnamed sibling path.** The report describes the reported trigger only. The same root cause is reachable through
   a second entry point, a second code path, or a round-trip (serialize -> store -> parse) that the report never
   names. Give it its own security test. Evidence: DeepSeek missed the schema round-trip variant in 3/3 runs on 6qxp.
2. **Already-protected-looking code.** One path already validates correctly, so the model reads the area as "handled"
   and patches only the path the report mentions (pyload jq7h, 6qxp).
3. **Fix across a layer boundary.** The correct fix must reach from the entry layer into a deeper layer (e.g. a core
   API that cannot see the web session, an SDK helper that cannot see the stored binding). Local guards at the entry
   point are the shallow fix your tests must catch.
4. **One test per fix place.** Each place the reference fix hardens gets its own `test_security_*` reached through its
   own entry point, so a fix that skips one place still scores < 1.0. (Was "one test per variant"; spelling, case and
   encoding variants of one input through one route are always caught and do not count.)
5. **Boundary-hugging functional tests.** Legitimate inputs that look like the attack (same characters, same feature,
   trailing slash, empty/None, legacy unbound data) must keep working, so "reject everything suspicious" fails.
6. **Behavioural report, no localization, no scope.** Describe what a user observes ("an IPv6 client passed our IPv4
   allowlist"), never the function, class, file or the root cause wording that points at the line to change - and
   never how far the bug reaches ("each provider we tried", "on every route"): all 4 evaluated reports with such a
   phrase were solved on attempt 1. Stating the cause is fatal only for a one-place fix; hono stated it and still won.
7. **Parallel implementation.** The project has a second module that re-implements the same feature (a second
   renderer, a second parser, a legacy and a new API). The report describes the behaviour once; the fix must land in
   both. Evidence: hono GHSA-hxh3 (first ACCEPTED task) - in 4 of 6 attempts the second `jsx/dom/server` renderer was
   left unfixed (DeepSeek read it every time but argued a top-level string is "trusted HTML"; MiMo twice never looked);
   the other 2 fixed it for a bare string only and missed a nested-array root. Details: data/knowledge/failure_analyses/.
8. **Input-shape variants (RETIRED - do not use as a difficulty technique).** In 35 of 40 tagged tasks, break rate at
   the 15% baseline: models catch spelling, case, encoding and shape variants of one route. A second public API or
   lower-level constructor that is a REAL separate place is technique 1 or 7, not this one.
9. **A "must keep working" clause that argues against the fix.** DeepSeek uses such a clause (or an existing test that
   passes either way) as permission to leave a sink open; MiMo over-hardens and breaks the legitimate path - test the
   legitimate behaviour in every supported composition order (undici GHSA-vp8m).
10. **Prefer big fixes (RETIRED as a difficulty lever).** Width does not separate hard from easy: 10-21-file fixes
   were solved on attempt 1 (9router changed 1 of 12 fix files and scored 1.0). Tiny local fixes (<= 3 files, <= 35
   lines) are still unusable, so width is a floor, not a lever.
11. **A compatibility contract pinned by an existing repo test.** Pick fixes that add an option or a check next to
   an existing public interface that the project's own tests pin (the exact keys a plugin receives, an output format,
   a default). The obvious fix changes that interface; a careful fix keeps it. Evidence: apprise GHSA-856c
   (ACCEPTED) - in 6 of 6 attempts both models added the new `redirect` key to every plugin's parsed-URL dict "like
   `verify`", saw the repo test `len(meta) == 8` fail, and edited the test instead of their fix; the grader restores
   repo tests, so all 6 scored 0.99. The upstream fix kept the key out unless set. Make sure the existing test is in
   the enforced pass->pass set and the report does not tell the agent to change that interface.
12. **Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22).** A mechanism that never had the
   protection, so its absence reads as design ("unsupported combination, not a boundary"). jackson: the any-setter
   route has no view code at all. Test it through its own entry point.
13. **Producer off the check's path (M6, 5 of 17).** A schema, serializer, loader or config resolver feeds the check
   through a path the check never calls; the model follows calls INTO the check and never asks where its data comes
   from. MCP SDK 6qxp: the schema strips the issuer on reload (DeepSeek missed it 3/3).
14. **Wrong object (M10).** The check authorises a neighbouring or proxy object, or trusts an attacker-chosen identity
   field (seaweedfs: authorises against the ARN's account field; django-cms: parent from POST while the check reads GET).
15. **Merged / defaults route (M5).** The restricted value arrives through defaults, merge, inheritance, a patch or
   stored config; the model treats the report's example fields as the whole set (protobuf.js: inherited options).

## Cover every place the real fix protects (measured)
- In 15 of 27 solved tasks the agent passed while changing FEWER source files than the reference fix: the hidden tests
  did not exercise every place the fix protects, so a partial repair scored 1.0. Before writing tests, list each source
  file / code path the reference fix hardens and give each one at least one security test reached from a real entry
  point. A repair that skips any of those places must fail. (Live numbers: data/knowledge/solved_profile.md.)

## How the pipeline proves the tests are good (your check patches)
- **shallow**: blocks only the reported trigger. At least one security test must still fail on it (technique 1/4).
- **removal**: disables or over-restricts the feature. At least one functional test must fail on it (technique 5).
- **alternative**: a correct fix of a different design. Every test must pass on it (tests are implementation-agnostic).
- **coverage (leave-one-file-out)**: the reference fix is run WITHOUT its change to each file you list in
  `fix_places` (metadata). At least one test must fail every time; otherwise an agent that skips that file solves
  the task and it is sent back. List only files whose change closes part of the vulnerability.
- These are executed in the real environment. A wrong outcome sends the task back with the failing test names.

## Fairness rules (never break these to make a task harder)
- Every hidden test is passed by the reference fix and follows from the report plus a careful reading of the code.
- Tests observe only what a caller can observe at the entry point; never internal state or names the fix adds.
- No timing races, no network, no randomness.
- **Never test a number the report does not state.** The reference fix's internal limits (max length 64, a 1,000,000
  cap, a depth limit) are ONE design; another correct fix may pick another value. (Most common rejection so far:
  pypdf, source-map-js.) For resource-exhaustion bugs: keep the legitimate input small and the attack input orders of
  magnitude larger (e.g. 1x vs 1000x), and assert only that the attack is refused or finishes quickly and bounded -
  never at which exact size it starts being refused. If a boundary matters, the report must state it.
- **Variants must share the reported root cause.** Another bug in the same area (a different slow path, a different
  missing check) is a different task, not a variant (rejected: source-map-js deep nesting, typespec output files).
- **Never map every exception to "blocked".** Catch only the project's own rejection (UnauthorizedException, a 4xx,
  its ValidationError); let any other error fail the test. A catch-all hid a broken fake request in sync-in (the
  guard crashed on a missing `request.url`), so legitimate-use tests failed for no visible reason - and the same
  catch-all lets a security test "pass" when the code under test never ran.
- **"Must keep working" means it works today.** Every functional test must pass on the vulnerable code; never describe
  as legitimate a behaviour the project never had (rejected: undici allow-list caching).

## Answer-key hygiene (the agent must use its own knowledge)
- The agent sees only the report and the repo at the vulnerable commit: no hidden tests, no fix, no git history of
  the fix, no network, no advisory text. Never put fix code, upstream regression tests or exploit inputs into the repo
  or the report. Fixes committed after the models' release dates keep the answer out of their training data.


# Which task types each evaluated agent could not repair completely (measured results)
## Model failure map (deterministic, rebuilt after every evaluation)
Task type = vulnerability family; fix breadth (files / dirs / lines). Timeouts are not failures.
### DeepSeek
- FAILED on (5): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) - partial fix: closed 5 of 6 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: schema_roundtrip_keeps_binding | information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | path / file handling; wide multi-layer fix (10 files / 3 dirs / 236 lines) - partial fix: closed 4 of 5 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: toolbox_symlink_escape | auth / session / credentials; local fix (1 files / 1 dir / 33 lines) - partial fix: closed 6 of 7 attack variants in its run and stopped on its own (it thought it was done); left open every time: exp_at_epoch_boundary
- Timed out on (0): none
- Solved (35), by vulnerability family: resource exhaustion (DoS) x7, auth / session / credentials x7, other x6, path / file handling x3, parsing / type confusion x3, injection (code / command / markup) x2, injection (code / command / markup) + information exposure x1, parsing / type confusion + SSRF / redirect x1, information exposure x1, auth / session / credentials + injection (code / command / markup) x1, auth / session / credentials + path / file handling x1, deserialization / prototype pollution x1, auth / session / credentials + path / file handling + information exposure x1
### MiMo
- FAILED on (3): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | auth / session / credentials; wide multi-layer fix (10 files / 5 dirs / 120 lines) - closed the hole but broke legitimate behaviour (storage_with_custom_lookup_same_host) in its run and stopped on its own (it thought it was done)
- Timed out on (2): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) | auth / session / credentials; wide multi-layer fix (5 files / 4 dirs / 111 lines)
- Solved (7), by vulnerability family: auth / session / credentials x2, parsing / type confusion x2, injection (code / command / markup) x1, path / file handling x1, auth / session / credentials + path / file handling + information exposure x1
### Broke BOTH (replicate this shape): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines)


# Which techniques have broken the evaluated agents so far (measured)
## Technique scoreboard (measured, rebuilt after every evaluation)
How often each curated technique was used in an evaluated task, and the outcome. A technique that keeps appearing in tasks DeepSeek solves on attempt 1 is not enough on its own: combine it with ones that broke a model. Counts are per task.

Baseline: 6 of 40 tagged tasks broke at least one model (15%). A technique is only informative when its break rate differs from that baseline.

| # | Technique | Tasks | Broke both | Broke only DeepSeek | Broke only MiMo | Solved | Read |
|---|---|---|---|---|---|---|---|
| 1 | Unnamed sibling path | 20 | 2 | 2 | 1 | 15 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt, undici) |
| 2 | Already-protected-looking code | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 3 | Fix across a layer boundary | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 4 | One test per fix place | 40 | 2 | 3 | 1 | 34 | BASELINE (in 40/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 5 | Boundary-hugging functional tests | 38 | 2 | 3 | 1 | 32 | BASELINE (in 38/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 6 | Behavioural report, no localization, no scope | 39 | 2 | 3 | 1 | 33 | BASELINE (in 39/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 7 | Parallel implementation | 9 | 2 | 0 | 1 | 6 | USE: 33% break rate vs 15% baseline (apprise, hono, undici) |
| 8 | Input-shape variants (RETIRED - do not use as a difficulty technique) | 35 | 2 | 2 | 1 | 30 | BASELINE (in 35/40 tasks): necessary, not sufficient (apprise, hono, nltk, fast-jwt, undici) |
| 9 | A "must keep working" clause that argues against the fix | 16 | 2 | 2 | 0 | 12 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt) |
| 10 | Prefer big fixes (RETIRED as a difficulty lever) | 2 | 1 | 0 | 0 | 1 | too few uses to judge (but broke both models) (apprise) |
| 11 | A compatibility contract pinned by an existing repo test | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 12 | Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 13 | Producer off the check's path (M6, 5 of 17) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 14 | Wrong object (M10) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 15 | Merged / defaults route (M5) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |

_0 evaluated task(s) have no technique record._


# Task shapes the evaluated agents SOLVED (avoid repeating them; measured)
## Solved-task profile (deterministic, rebuilt after every evaluation)
37 evaluated tasks were solved by at least one model; 35 on the FIRST attempt. Median solve time 13 min. These are the shapes to avoid or to combine with the techniques that broke a model (see the technique scoreboard).
- Median reference-fix size of solved tasks: 6 source files; median number of security tests: 6.
- Solved by vulnerability family: auth / session / credentials x11, resource exhaustion (DoS) x7, path / file handling x6, other x6, injection (code / command / markup) x4, parsing / type confusion x4, information exposure x3, SSRF / redirect x1, deserialization / prototype pollution x1
- In 8 of 37 solves the agent changed every source file of the reference fix: the report led it to all affected places.

### Why solved tasks were too easy (measured; fix the most common first)
- **coverage gap** in 24 of 37 solved tasks -> list every place the reference fix hardens and reach EACH one from its own security test - a repair that skips one place must fail.
- **no hidden path** in 15 of 37 solved tasks -> put part of the root cause in a REAL place the report never leads to - a second implementation, a producer feeding the check, a defaults/merge route - and reach it with its own test (techniques 1, 2, 3, 7, 12-15).
- **small fix** in 12 of 37 solved tasks -> a one-place fix is solved whatever the report says; skip it unless the code has a real second place the fix must also reach (fix width alone does not help: 10-21-file fixes were solved on attempt 1).
- **few security tests** in 9 of 37 solved tasks -> write one security test per fix place, each through its own entry point (spelling and encoding variants of one input do not count: models always catch them).
- **report points at the code** in 7 of 37 solved tasks -> never name the file, function, option or parameter the fix changes, and never state how far the bug reaches ('every provider', 'on every route').

| Task | Family | Fix | Security tests | Techniques used | Solved by | Attempt | Minutes | Why it passed |
|---|---|---|---|---|---|---|---|---|
| 9router | auth / session / credentials | 13 files / 10 dirs / 257 lines | 6 | 1, 4, 5, 6, 8, 9 | DeepSeek | 1 | 2 | coverage gap (1/12 fix files changed) |
| @hono/oauth-providers | auth / session / credentials | 7 files / 7 dirs / 54 lines | 6 | 1, 4, 5, 6, 8, 10 | DeepSeek | 1 | 3 | - |
| msgpack5 | resource exhaustion (DoS) | 2 files / 2 dirs / 40 lines | 7 | 1, 4, 5, 6, 8 | DeepSeek | 1 | 4 | small fix |
| nltk | other | 6 files / 2 dirs / 163 lines | 5 | 4, 5, 6, 8 | DeepSeek | 1 | 4 | coverage gap (1/7 fix files changed); report points at the code: grammar; no hidden path; few security tests |
| ip-address | parsing / type confusion | 3 files / 1 dir / 25 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 5 | small fix; report points at the code: Address4, Address6; no hidden path |
| @xmldom/xmldom | other | 3 files / 2 dirs / 37 lines | 10 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 6 | small fix |
| vibe-trading-ai | auth / session / credentials + path / file handling + information exposure | 17 files / 5 dirs / 618 lines | 6 | 3, 4, 5, 6, 8 | DeepSeek | 1 | 6 | coverage gap (4/23 fix files changed); report points at the code: Settings, service |
| pyload-ng | auth / session / credentials | 2 files / 2 dirs / 9 lines | 4 | 4, 5, 6 | DeepSeek | 1 | 8 | coverage gap (1/2 fix files changed); small fix; no hidden path; few security tests |
| pyload-ng | auth / session / credentials | 4 files / 2 dirs / 58 lines | 7 | 4, 5, 6, 8 | DeepSeek | 1 | 8 | coverage gap (3/5 fix files changed); no hidden path |
| n8n | injection (code / command / markup) | 9 files / 7 dirs / 343 lines | 6 | 1, 4, 5, 8 | DeepSeek | 1 | 8 | coverage gap (5/9 fix files changed); report points at the code: execute |
| @vitest/browser | auth / session / credentials + path / file handling | 8 files / 4 dirs / 104 lines | 4 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 9 | coverage gap (6/8 fix files changed); report points at the code: upload; few security tests |
| pymongo | other | 3 files / 3 dirs / 74 lines | 6 | 4, 5, 6, 7, 8 | DeepSeek | 1 | 10 | small fix |
| adm-zip | parsing / type confusion | 2 files / 2 dirs / 11 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 11 | small fix; no hidden path |
| react-router | other | 8 files / 7 dirs / 113 lines | 5 | 1, 3, 4, 5, 6, 7, 8 | DeepSeek | 1 | 12 | coverage gap (1/6 fix files changed); report points at the code: server; few security tests |
| pyload-ng | auth / session / credentials | 5 files / 4 dirs / 111 lines | 7 | 4, 5, 6 | DeepSeek | 1 | 12 | no hidden path |
| datamodel-code-generator | path / file handling | 1 files / 1 dir / 31 lines | 6 | 4, 5, 6, 9 | DeepSeek | 1 | 13 | small fix; no hidden path |
| @sync-in/server | other | 21 files / 8 dirs / 224 lines | 6 | 1, 4, 5, 6, 7, 8, 9 | DeepSeek | 1 | 13 | coverage gap (12/20 fix files changed) |
| hono | path / file handling | fix size unknown | 4 | 1, 4, 5, 6, 8, 9 | DeepSe


# Why the evaluated agents failed real tasks (curated from their trajectories - design for these)
## GHSA-856c-92hv-3vxx: Verdict: ACCEPTED. Both models failed every run. DeepSeek scored 0.99 on all three attempts and MiMo scored 0.99 on all three. In all six attempts every hidden test passed, including all 16 security and functional tests, so the fix itself worked. Each attempt failed on the same pre-existing test, `tests/test_decorator_notify.py::test_notify_multi_instance_decoration`, which asserts `len(meta) == 8`. The new `redirect` option was copied exactly from how `verify=` is handled, so a `redirect` key now appeared in every parsed-URL result. The agents saw this test fail and changed the expected count to 9. Test edits were restored before grading, so the change did nothing and the test still failed. All six attempts treated a failing existing test as something to update, not as a limit on their design. None of them changed `apprise/asset.py`, which the reference fix did change. That suggests the reference stores the default somewhere other than an always-present `parse_url` key, though the evidence doesn't show exactly how.
#### Weakness profile
- **DeepSeek:**
  - **Strengths:** it explores thoroughly and finds every HTTP call site. It does careful mechanical checks of its own patch, such as AST scans of every `allow_redirects` use.
  - **Weakness:** when an existing test breaks, it assumes the test is out of date, not that its design choice is wrong. It openly concludes the edits are "harmless" because hidden tests "will add new tests".
  - **How it verifies and stops:** it treats "the full suite passes after I edited the tests" as done. It never checks whether the new option could be added without changing what existing public output looks like.
- **MiMo:**
  - **Weakness:** the same habit of editing existing tests, but even stronger. It changes or extends four to six existing test files per attempt, and in attempt 3 it adds assertions that lock in its own side effects.
  - **Less precise coverage:** it touched a TCP-only plugin (attempt 1) and skipped eight HTTP plugins (attempt 2).
  - **Why it stops:** its own tests pass, and it takes that as proof of correctness.
- **Both:** they took "behave exactly like `verify=`" as an order to copy everything about it, including always adding a key to the parsed-URL results. Neither considered that existing callers and tests might depend on that results dict having a fixed size.
#### Task-design lessons
- **Ask for a feature that mirrors an existing option, while existing tests fix the shape of shared output.** Phrase it as "behave exactly like X", while an existing test pins the number of keys, the field list or the serialised form of a shared structure. Agents copy the template wholesale, change the shared structure, then "fix" the pinning test.
- **Keep breakage-detecting tests in files the agent will naturally edit.** Enforce existing tests and restore any test edits before grading. Put the fragile assertion in a test that fails noticeably during the agent's own full-suite run. Both models reliably edit such tests and wrongly believe test changes are "harmless".
- **Make the reference fix put new state somewhere unexpected.** Here that was a central config or defaults object (`asset.py`) instead of the obvious parser. A naive copy of the existing option then visibly breaks backward compatibility, while the reference route does not.
- **Grade the security behaviour on every call site, not a sample.** Use a fan-out change across many near-identical files and run hidden tests over the full set or a random sample of call sites. MiMo attempt 2 skipped eight plugins, and the hidden tests, which only covered json/form/xml/apprise_api/config/attachment, didn't notice.
- **State backward compatibility outright, but leave the danger implicit.** Write "existing behaviour stays as it is today" and nothing more. Agents read that as runtime behaviour only. They don't treat existing API or introspection output, such as a parsed-URL dict, as behaviour too, and that gap is what both models fell into.

## GHSA-hxh3-vqpv-xpqv: ACCEPTED - both models failed all 3 attempts (DeepSeek 0.83/0.83/0.94, MiMo 0.89/0.94/0.89, Claude Code agent), every run stopped on its own (no timeout). All 6 fixed the three wrappers the report names (Suspense, ErrorBoundary, Context.Provider) and all 6 left `renderToString([unsafe, [unsafe]])` unescaped.
#### Weakness profile
- Shared: both treat the report's examples as the complete list of sinks, and fix only the input shape they
  reproduced (a bare string) even when the same parameter accepts arrays, nested arrays and promises.
- DeepSeek: over-reasons about intent - finds the sink, then uses a "keep legitimate behaviour" clause or an existing
  passing test as permission to leave it vulnerable.
- MiMo: under-explores and asserts unverified facts ("that API doesn't exist") instead of searching.
#### Task-design lessons
- Put a **second entry point in a sibling module whose path sounds out of scope** (here `dom/` reads as "client") and
  describe it only vaguely ("a string handed to the renderer directly").
- Add a **"must keep working" clause that plausibly argues against the fix** ("a bare string must still be
  renderable"), backed by an existing test that passes either way (`'Hono'` has nothing to escape).
- **Test input-shape variants at each sink** (array, nested array, promise, number), not only each sink.
- Make **two entry points share the bug but need separate fixes**; agents fix them unevenly and claim full coverage.
- List some sinks "for example" and test more than you list: every agent stopped once the listed items were covered.

## GHSA-6qxp-vccf-f47h: DeepSeek failed 3/3 (0.92 each, Claude Code agent), always closing 5 of 6 attack paths; MiMo only timed out (terminus-2, 2 h), so the task is rejected (a timeout is not a failure).
#### Weakness profile
- DeepSeek traces call graphs well but misses state that crosses a serialization boundary (save -> store -> parse).
- It trusts in-code comments and "intentional" design notes, and reads "must keep working" hints as constraints.
- It stops as soon as self-written tests (which cover only what it already believes) pass.
#### Task-design lessons
- Put one variant on a **data round-trip** (serialize -> persist -> parse through the project's own schema/model
  layer) that the report does not name; the call-path fix then leaves exactly that variant open.
- Let the vulnerable code contain a plausible "intentional" comment or an already-protected entry point near the bug.
- Mention the round-trip only as legitimate behaviour that must keep working; never as an attack path.

## GHSA-p4rw-rvv2-7xwr: DeepSeek failed all 3 attempts (0.93 each, always the toolbox symlink escape left open); MiMo failed 2 (0.87, toolbox + MTE left open) and solved 1. Rejected (MiMo solved). No timeouts; every run stopped on its own.
#### Weakness profile
- DeepSeek: entry-point blindness - treats "reachable through the main class" as the whole attack surface and



# Lessons from previous runs (auto-generated from real DeepSeek/MiMo results - follow them)
## Breaks BOTH models (replicate)
- **hxh3 · hono · CWE-79 · 6 files/3 dirs/156 lines** and **856c · apprise · CWE-200/601** are the accepted tasks (n=2). hono: both models scored 0.83–0.94 and stopped on their own in 3/3 runs, leaving the second `jsx/dom/server` renderer or the nested-array root open every time - places the report never mentioned. apprise: both broke a plugin interface the repo's own test pins (over-correction, 6/6). Check `stream > Should call onAbort` for flakiness before reusing hono.
- **Combine in one task:**
  1. A REAL place the report never leads to - a second implementation, a lower-level API, a round-trip - that the obvious choke point misses. This beat DeepSeek (n=3). Spelling/encoding/shape variants of the same route do not count: they are always caught.
  2. One security test per fix place, each through its own entry point, so a fix that skips one place still fails.
  3. A falsy or boundary variant (`0`, `""`, `[]`). This beat DeepSeek (tentative, n=1: x937).
  4. A test that existing behaviour still works across a composition or ordering boundary. This beat MiMo (tentative, n=1: vp8m).
  5. A path that is already safe, as a decoy. This beat MiMo (tentative, n=1: jq7h).
  6. Fast test suites. A MiMo timeout counts as "too slow", not as a failure (6qxp, vp8m).

## Breaks only DeepSeek (MiMo solves)
- **Stops one variant short (n=4: 6qxp, p4rw, hxh3, x937; scores 0.92–0.95).** It patches the first layer it finds, then declares itself done.
  - **p4rw · nltk · CWE-22/59.** It put the check in `CorpusReader.abspath` and missed the bare-string entry points `StandardFormat.open`, `XMLCorpusView` and `load_ace_file`. MiMo fixed the shared `FileSystemPathPointer`.
  - **x937 · fast-jwt · CWE-613 · 1 file/33 lines.** It fixed the `hasIat` gate the report described, but kept the cache rule that `0` means "no bound". The `exp: 0` case stayed open (13/14 tests passed). MiMo checked whether the claim was present, not whether it was truthy, and compared cached against uncached results.
  - **6qxp.** It saw that the binding is lost on a schema round-trip and stopped anyway.
- **Hiding file names is not enough.** DeepSeek named the fix file in 0 of 38 recall probes, yet solved 21 tasks: the
  reports hid the files but stated the scope, the tainted parameters or the root cause of a one-place fix. What failed
  DeepSeek was a real place the report never led to (hono's second renderer, 6qxp's schema round-trip).

## Breaks only MiMo (DeepSeek solves)
- **vp8m · undici · CWE-346 (tentative).** Security tests reached 1.0, but reuse in `compose(cache(), dns())` broke. MiMo restored the hostname only on the response side, so the lookup key and the store key diverged.
- **jq7h · pyload · CWE-613 (tentative).** MiMo spent its budget on the webui path, which was already correct, and never edited REST.
- **When MiMo succeeds:** it solves tasks where one shared layer covers every variant (p4rw 1/3, x937). It has 3 counted failures.
- **Evidence on MiMo is thin.** Its p90 step time is about 400 s vs about 40 s for DeepSeek. It was ungraded in 13 of 14 stage-5 rows because a DeepSeek solve ends the run.

## Solved by both (avoid)
- **p634, j6r3:** the report gave the root cause, a repro and the API names, and the fix was one local check.
- **pqg4, x33g:** both models named the fix location.
- **DeepSeek solved on the first try, MiMo ungraded (n=21; 35–223 steps, 4–64 min):** j22f, v247, 24ch, 68w4, 9q47, 77xj, 5jq2, 3wxw, hqr4, hmq2, 2q42, qf28, 8fvv, 8xx6, mcm9, w3v8, q2xc, c7q8, gqvv, f65p and PYSEC-3869.
  - Each had one choke point that every variant passed through.
  - Wide fixes didn't help: 7 of them were solved, including qf28 (16 files) and w3v8 (289 lines).

## Task-quality pitfalls (rubric / oracle failures)
- **Run every test on the vulnerable code (n=6).** Security tests must fail there and functional tests must pass.
  - 8r5x crashed before the injection ran.
  - In r4xh and q238, security tests already passed (GEOS rejected nested Multi* at depth 5–6).
  - mcm9 and vp8m had functional tests that required new behaviour.
  - PYSEC-3869 used the mixed rule `S -> S 'a'`, which CNF conversion rejects on both versions.
- **Oracle fails its own tests (n=11):** x6jw, p634, jggr, 68fv, hmq2, 2q42, hqr4, r4xh, 376h, 2q76 and hwr6.
  - If every functional test scores 0.0, the harness or fixture is broken. Regenerating fixed hmq2, 2q42 and hqr4.
  - Drop existing tests that assert the vulnerable behaviour (tentative, n=2: qf28, c4c3).
- **Tests accept only one fix shape (n=9):**
  - 68w4, 9q47, jq7h, qf28.
  - 2q76: required field-level `access` and called functions with a made-up `req`.
  - x78j: rejected raise, `SystemExit` and drop fixes.
  - p63j: aliased `@vitest/browser` to `utils.ts` and used fake contexts.
  - PYSEC-3819: mocked only the module-level `requests.get`.
  - 5vf6: a minimal constructor config crashed fixes that read `flagResolver`.

  Accept reject, raise, drop and sanitize fixes. Test through the public HTTP, CLI or RPC entry point. Mock at the transport layer and import through the package entry.
- **Undisclosed limits or semantics (n=5):** 5jq2 (a cutoff of 64), 68fv (hidden cap), 2q42 (sanitize and still emit), w3v8 (25 s vs the repo's 60 s) and x78j (`splitlines()` instead of cmd.exe rules). State limits in the report or use ≥100× margins, and model the real sink.
- **Weak tests (n=5):** x937, 6qxp, qf28, r4xh and 2q76 (deny-all passed). Assert the output content and make over-blocking fail. Count operations instead of timing them (tentative, n=2).
- **No network in tests (tentative, n=1: 5vf6).** The test resolved a real host's DNS, and the oracle passed only through a hidden `NODE_ENV=test` fallback.
- **Fix visible to the model (n=4):** readable in site-packages or node_modules (8xx6, q2xc, f65p), or already in the vulnerable tree (337j). Uninstall released copies.
- **Bad existing-test files (n=4):** helper, manual and DB-integration files. Exclude them.
- **Infrastructure; retry before rejecting:**
  - no verdict (n=9)
  - host Docker I/O error (n=4)
  - "no usable existing tests" (n=4; f65p passed on retry)
  - `pip install -e .` failed (n=3)
  - environment start timeout, stage-5 incomplete attempts, npm install failed (n=2 each)
- **Report names the code (n=3)**, and **safeguard blocks (n=9)**; Handlebars, q238 and 2q76 were retired.

## Selection hints
- **Prefer:** fixes where a tempting high-level choke point misses a real second place - a second implementation, a lower-level API, a producer feeding the check (n=3; 6–10 files, 120–236 lines). At screening, ask whether one function sees every variant. If it does, skip.
- **Also prefer (tentative):** checks on falsy-sensitive fields (timestamps, counts, empty values), and these CWEs:
  - CWE-79
  - CWE-345/522
  - CWE-613 (broke each model once)
  - CWE-22/59, only if bare-path entries bypass the reader layer
- **Skip:**
  - Fixes of ≤4 files and ≤60 lines (0 usable of 14).
  - DoS CWE-400/407/409/674/1284/1333 (0 usable).
  - CWE-22/73 fixed in one path builder (n=3).
  - CWE-91, URI parsers and SSRF fixes that need DNS (tentative).
  - Code generators.
  - Oracle patches over 80k characters (n=3).
  - Monorepos: payload (5 failures), pydantic-ai, vllm, Flowise, reactpress, mermaid and vitest.
  - PyPI repos where `pip install -e .` fails.
- **pyload:** use only with the real app's test client.
- **Recall:** reject if both models name the fix (n=2). Otherwise recall doesn't predict the outcome.


# Approved design (previous step)
<instruction_md>
# Syslog program names run as page scripts

## What we observed

We opened the syslog list for a switch we monitor. A program name that arrived with a message from that device was written into the page as markup, and the browser ran it. The message text beside that name stayed ordinary readable text. We had not entered the program name in LibreNMS. The row still showed the time, and it still showed a link to the device, both produced by the product rather than by the device.

## Impact

A person who can send syslog to this installation, or who controls a device we already monitor, can run script in the browser of an operator who opens that syslog list. The operator's session is enough to perform the same actions the operator can perform.

## What must keep working

A normal syslog row must still show the time, the program name, and the message, and the device must still be a real link that the product itself draws. Making the program name safe must not drop the row, blank the message, or turn that device link into plain text. A program name or message that is only text, including an ampersand, a quote, or a less-than sign used as wording, must stay readable rather than being stripped out. Wording that was not written as page markup must be shown as text, while markup the product itself creates must stay markup.

</instruction_md>
<task_metadata_json>
{
  "entry_point": "Operator view of one device's syslog list, where each received row is printed into the page",
  "techniques": [
    1,
    2,
    5,
    7,
    9,
    12
  ],
  "trap": {
    "paths": [
      "includes/html/functions.inc.php",
      "includes/html/pages/device/routing/bgp.inc.php",
      "includes/html/pages/routing/bgp.inc.php",
      "includes/html/pages/device/showconfig.inc.php",
      "includes/html/print-vrf.inc.php",
      "resources/views/map/custom-list.blade.php"
    ],
    "contract": "An ordinary syslog row still shows the program name and message as readable text, and the product-drawn device link stays a real anchor."
  },
  "fix_places": [
    "includes/html/functions.inc.php",
    "includes/html/pages/device/health/mempool.inc.php",
    "includes/html/pages/device/health/sensors.inc.php",
    "includes/html/pages/device/health/storage.inc.php",
    "includes/html/pages/device/port/vlans.inc.php",
    "includes/html/pages/device/processes.inc.php",
    "includes/html/pages/device/routing/bgp.inc.php",
    "includes/html/pages/device/showconfig.inc.php",
    "includes/html/pages/device/slas.inc.php",
    "includes/html/pages/eventlog.inc.php",
    "includes/html/pages/graphs.inc.php",
    "includes/html/pages/routing/bgp.inc.php",
    "includes/html/pages/routing/vrf.inc.php",
    "includes/html/print-syslog.inc.php",
    "includes/html/print-vrf.inc.php",
    "resources/views/map/custom-list.blade.php"
  ],
  "unrelated_files": []
}
</task_metadata_json>

# Split generation (this request)
The report, metadata and check patches were approved in the previous step. Return ONLY the `<hidden_tests_py>` block,
following every test constraint above. Keep the suite lean: at most 6 `test_security_*` and 6 `test_functional_*`
tests, each focused and under 60 lines. Do not repeat the instruction, metadata or patches.

