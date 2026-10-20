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
  "unrelated_files": [],
  "test_justifications": {
    "test_security_syslog_program_not_markup": "A program name that arrived with a message from that device was written into the page as markup, and the browser ran it.",
    "test_security_alert_wording_not_markup": "Wording that was not written as page markup must be shown as text, while markup the product itself creates must stay markup.",
    "test_security_device_peer_row_not_markup": "Wording that was not written as page markup must be shown as text, while markup the product itself creates must stay markup.",
    "test_security_routing_peer_row_not_markup": "Wording that was not written as page markup must be shown as text, while markup the product itself creates must stay markup.",
    "test_security_config_backup_labels_not_markup": "Wording that was not written as page markup must be shown as text, while markup the product itself creates must stay markup.",
    "test_security_vrf_labels_not_markup": "Wording that was not written as page markup must be shown as text, while markup the product itself creates must stay markup.",
    "test_security_map_title_not_markup": "Wording that was not written as page markup must be shown as text, while markup the product itself creates must stay markup.",
    "test_functional_syslog_row_shows_text": "A normal syslog row must still show the time, the program name, and the message, and the device must still be a real link that the product itself draws.",
    "test_functional_syslog_keeps_device_link": "Making the program name safe must not drop the row, blank the message, or turn that device link into plain text.",
    "test_functional_syslog_punctuation_readable": "A program name or message that is only text, including an ampersand, a quote, or a less-than sign used as wording, must stay readable rather than being stripped out."
  }
}
</task_metadata_json>
<check_patches_json>
{
  "shallow": [
    {
      "file": "includes/html/print-syslog.inc.php",
      "search": "    if ($vars['page'] != 'device') {\n        $syslog_output .= '<td>' . $entry['date'] . '</td>\n                        <td><strong>' . generate_device_link($entry) . '</strong></td>\n                        <td><strong>' . $entry['program'] . ' : </strong> ' . htmlspecialchars((string) $entry['msg']) . '</td>';\n    } else {\n        $syslog_output .= '<td><i>' . $entry['date'] . '</i>&nbsp;&nbsp;&nbsp;<strong>' . $entry['program'] . '</strong>&nbsp;&nbsp;&nbsp;' . htmlspecialchars((string) $entry['msg']) . '</td>';\n    }",
      "replace": "    if ($vars['page'] != 'device') {\n        $syslog_output .= '<td>' . e($entry['date']) . '</td>\n                        <td><strong>' . generate_device_link($entry) . '</strong></td>\n                        <td><strong>' . e($entry['program']) . ' : </strong> ' . e($entry['msg']) . '</td>';\n    } else {\n        $syslog_output .= '<td><i>' . e($entry['date']) . '</i>&nbsp;&nbsp;&nbsp;<strong>' . e($entry['program']) . '</strong>&nbsp;&nbsp;&nbsp;' . e($entry['msg']) . '</td>';\n    }"
    }
  ],
  "removal": [
    {
      "file": "includes/html/print-syslog.inc.php",
      "search": "    if ($vars['page'] != 'device') {\n        $syslog_output .= '<td>' . $entry['date'] . '</td>\n                        <td><strong>' . generate_device_link($entry) . '</strong></td>\n                        <td><strong>' . $entry['program'] . ' : </strong> ' . htmlspecialchars((string) $entry['msg']) . '</td>';\n    } else {\n        $syslog_output .= '<td><i>' . $entry['date'] . '</i>&nbsp;&nbsp;&nbsp;<strong>' . $entry['program'] . '</strong>&nbsp;&nbsp;&nbsp;' . htmlspecialchars((string) $entry['msg']) . '</td>';\n    }",
      "replace": "    if ($vars['page'] != 'device') {\n        $syslog_output .= '<td></td>\n                        <td></td>\n                        <td></td>';\n    } else {\n        $syslog_output .= '<td></td>';\n    }"
    }
  ],
  "alternative": [
    {
      "file": "includes/html/print-syslog.inc.php",
      "search": "    if ($vars['page'] != 'device') {\n        $syslog_output .= '<td>' . $entry['date'] . '</td>\n                        <td><strong>' . generate_device_link($entry) . '</strong></td>\n                        <td><strong>' . $entry['program'] . ' : </strong> ' . htmlspecialchars((string) $entry['msg']) . '</td>';\n    } else {\n        $syslog_output .= '<td><i>' . $entry['date'] . '</i>&nbsp;&nbsp;&nbsp;<strong>' . $entry['program'] . '</strong>&nbsp;&nbsp;&nbsp;' . htmlspecialchars((string) $entry['msg']) . '</td>';\n    }",
      "replace": "    if ($vars['page'] != 'device') {\n        $syslog_output .= '<td>' . htmlspecialchars((string) ($entry['date']), ENT_QUOTES, 'UTF-8') . '</td>\n                        <td><strong>' . generate_device_link($entry) . '</strong></td>\n                        <td><strong>' . htmlspecialchars((string) ($entry['program']), ENT_QUOTES, 'UTF-8') . ' : </strong> ' . htmlspecialchars((string) ($entry['msg']), ENT_QUOTES, 'UTF-8') . '</td>';\n    } else {\n        $syslog_output .= '<td><i>' . htmlspecialchars((string) ($entry['date']), ENT_QUOTES, 'UTF-8') . '</i>&nbsp;&nbsp;&nbsp;<strong>' . htmlspecialchars((string) ($entry['program']), ENT_QUOTES, 'UTF-8') . '</strong>&nbsp;&nbsp;&nbsp;' . htmlspecialchars((string) ($entry['msg']), ENT_QUOTES, 'UTF-8') . '</td>';\n    }"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": ". '\">' . $tmp_alerts['bill_name'] . '</a>;&nbsp;'",
      "replace": ". '\">' . htmlspecialchars((string) ($tmp_alerts['bill_name']), ENT_QUOTES, 'UTF-8') . '</a>;&nbsp;'"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": "$fault_detail .= 'Adjacent ' . $tmp_alerts['isisISAdjIPAddrAddress'];",
      "replace": "$fault_detail .= 'Adjacent ' . htmlspecialchars((string) ($tmp_alerts['isisISAdjIPAddrAddress']), ENT_QUOTES, 'UTF-8');"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": "$details = 'State: ' . ($sensor->state_descr ?? '') . ' (numerical ' . $sensor->sensor_current . ')<br>  ';",
      "replace": "$details = 'State: ' . htmlspecialchars((string) ($sensor->state_descr ?? ''), ENT_QUOTES, 'UTF-8') . ' (numerical ' . $sensor->sensor_current . ')<br>  ';"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": "($tmp_alerts['service_name'] ?? '') . ' (' . $tmp_alerts['service_type'] . ')'",
      "replace": "htmlspecialchars((string) ($tmp_alerts['service_name'] ?? ''), ENT_QUOTES, 'UTF-8') . ' (' . htmlspecialchars((string) ($tmp_alerts['service_type']), ENT_QUOTES, 'UTF-8') . ')'"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": "'Service Host: ' . ($tmp_alerts['service_ip'] != '' ? $tmp_alerts['service_ip'] : format_hostname(DeviceCache::get($tmp_alerts['device_id'])))",
      "replace": "'Service Host: ' . ($tmp_alerts['service_ip'] != '' ? htmlspecialchars((string) ($tmp_alerts['service_ip']), ENT_QUOTES, 'UTF-8') : format_hostname(DeviceCache::get($tmp_alerts['device_id'])))"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": "('Description: ' . $tmp_alerts['service_desc'] . ',<br>')",
      "replace": "('Description: ' . htmlspecialchars((string) ($tmp_alerts['service_desc']), ENT_QUOTES, 'UTF-8') . ',<br>')"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": "('Param: ' . $tmp_alerts['service_param'] . ',<br>')",
      "replace": "('Param: ' . htmlspecialchars((string) ($tmp_alerts['service_param']), ENT_QUOTES, 'UTF-8') . ',<br>')"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": "'Msg: ' . $tmp_alerts['service_message'];",
      "replace": "'Msg: ' . htmlspecialchars((string) ($tmp_alerts['service_message']), ENT_QUOTES, 'UTF-8');"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": "$tmp_alerts['bgpPeerIdentifier'] . '</a>';",
      "replace": "htmlspecialchars((string) ($tmp_alerts['bgpPeerIdentifier']), ENT_QUOTES, 'UTF-8') . '</a>';"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": "', Desc ' . $tmp_alerts['bgpPeerDescr'] ?? '';",
      "replace": "', Desc ' . htmlspecialchars((string) ($tmp_alerts['bgpPeerDescr'] ?? ''), ENT_QUOTES, 'UTF-8');"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": "', AS' . $tmp_alerts['bgpPeerRemoteAs'];",
      "replace": "', AS' . htmlspecialchars((string) ($tmp_alerts['bgpPeerRemoteAs']), ENT_QUOTES, 'UTF-8');"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": "', State ' . $tmp_alerts['bgpPeerState'];",
      "replace": "', State ' . htmlspecialchars((string) ($tmp_alerts['bgpPeerState']), ENT_QUOTES, 'UTF-8');"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": "($tmp_alerts['mempool_descr'] ?? 'link')",
      "replace": "htmlspecialchars((string) ($tmp_alerts['mempool_descr'] ?? 'link'), ENT_QUOTES, 'UTF-8')"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": "' ' . $tmp_alerts['type'] . ' - ' . $tmp_alerts['label'];",
      "replace": "' ' . htmlspecialchars((string) ($tmp_alerts['type']), ENT_QUOTES, 'UTF-8') . ' - ' . htmlspecialchars((string) ($tmp_alerts['label']), ENT_QUOTES, 'UTF-8');"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": "' - ' . $tmp_alerts['error'];",
      "replace": "' - ' . htmlspecialchars((string) ($tmp_alerts['error']), ENT_QUOTES, 'UTF-8');"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": "$fault_detail .= $tmp_alerts['app_type'];",
      "replace": "$fault_detail .= htmlspecialchars((string) ($tmp_alerts['app_type']), ENT_QUOTES, 'UTF-8');"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": "' => ' . $tmp_alerts['app_status'];",
      "replace": "' => ' . htmlspecialchars((string) ($tmp_alerts['app_status']), ENT_QUOTES, 'UTF-8');"
    },
    {
      "file": "includes/html/functions.inc.php",
      "search": "' : ' . $tmp_alerts['metric'] . ' => ' . $tmp_alerts['value'];",
      "replace": "' : ' . htmlspecialchars((string) ($tmp_alerts['metric']), ENT_QUOTES, 'UTF-8') . ' => ' . htmlspecialchars((string) ($tmp_alerts['value']), ENT_QUOTES, 'UTF-8');"
    },
    {
      "file": "includes/html/pages/device/health/mempool.inc.php",
      "search": "echo \"<h3 class='panel-title'>{$mempool->mempool_descr} <div class='pull-right'>$bytes$mempool->mempool_perc% used</div></h3>\";",
      "replace": "echo \"<h3 class='panel-title'>\" . htmlspecialchars((string) ($mempool->mempool_descr), ENT_QUOTES, 'UTF-8') . \" <div class='pull-right'>$bytes$mempool->mempool_perc% used</div></h3>\";"
    },
    {
      "file": "includes/html/pages/device/health/sensors.inc.php",
      "search": "    } else {\n        $sensor_descr = $sensor['sensor_descr'];\n    }\n\n    $sensor_current = Html::severityToLabel($sensor->currentStatus(), __('Current') . ': ' . $sensor->formatValue());",
      "replace": "    if ($sensor['poller_type'] == 'ipmi') {\n        $sensor_descr = htmlspecialchars((string) (ipmiSensorName($device['hardware'], $sensor['sensor_descr'])), ENT_QUOTES, 'UTF-8');\n    } else {\n        $sensor_descr = htmlspecialchars((string) ($sensor['sensor_descr']), ENT_QUOTES, 'UTF-8');\n    }"
    },
    {
      "file": "includes/html/pages/device/health/storage.inc.php",
      "search": "$storage_descr = $drive['storage_descr'];",
      "replace": "$storage_descr = htmlspecialchars((string) ($drive['storage_descr']), ENT_QUOTES, 'UTF-8');"
    },
    {
      "file": "includes/html/pages/device/health/storage.inc.php",
      "search": "$device['hostname'] . ' - ' . $drive['storage_descr'];",
      "replace": "$device['hostname'] . ' - ' . $storage_descr;"
    },
    {
      "file": "includes/html/pages/device/port/vlans.inc.php",
      "search": "'<td width=100 class=list-large> Vlan ' . $vlan['vlan'] . '</td>';",
      "replace": "'<td width=100 class=list-large> Vlan ' . htmlspecialchars((string) ($vlan['vlan']), ENT_QUOTES, 'UTF-8') . '</td>';"
    },
    {
      "file": "includes/html/pages/device/port/vlans.inc.php",
      "search": "'<td width=200 class=box-desc>' . $vlan['vlan_name'] . '</td>';",
      "replace": "'<td width=200 class=box-desc>' . htmlspecialchars((string) ($vlan['vlan_name']), ENT_QUOTES, 'UTF-8') . '</td>';"
    },
    {
      "file": "includes/html/pages/device/port/vlans.inc.php",
      "search": "'<td>' . $vlan['cost'] . '</td><td>' . $vlan['priority'] . \"</td><td class=$class>\" . $vlan['state'] . '</td>';",
      "replace": "'<td>' . htmlspecialchars((string) ($vlan['cost']), ENT_QUOTES, 'UTF-8') . '</td><td>' . htmlspecialchars((string) ($vlan['priority']), ENT_QUOTES, 'UTF-8') . \"</td><td class=$class>\" . htmlspecialchars((string) ($vlan['state']), ENT_QUOTES, 'UTF-8') . '</td>';"
    },
    {
      "file": "includes/html/pages/device/processes.inc.php",
      "search": "    echo '<td>' . $entry['pid'] . '</td>';\n    echo '<td>' . \\LibreNMS\\Util\\Number::formatSi($entry['vsz'] * 1024, 2, 0, '') . '</td>';\n    echo '<td>' . \\LibreNMS\\Util\\Number::formatSi($entry['rss'] * 1024, 2, 0, '') . '</td>';\n    echo '<td>' . $entry['cputime'] . '</td>';\n    echo '<td>' . $entry['user'] . '</td>';\n    echo '<td>' . $entry['command'] . '</td>';",
      "replace": "    echo '<td>' . htmlspecialchars((string) ($entry['pid']), ENT_QUOTES, 'UTF-8') . '</td>';\n    echo '<td>' . \\LibreNMS\\Util\\Number::formatSi($entry['vsz'] * 1024, 2, 0, '') . '</td>';\n    echo '<td>' . \\LibreNMS\\Util\\Number::formatSi($entry['rss'] * 1024, 2, 0, '') . '</td>';\n    echo '<td>' . htmlspecialchars((string) ($entry['cputime']), ENT_QUOTES, 'UTF-8') . '</td>';\n    echo '<td>' . htmlspecialchars((string) ($entry['user']), ENT_QUOTES, 'UTF-8') . '</td>';\n    echo '<td>' . htmlspecialchars((string) ($entry['command']), ENT_QUOTES, 'UTF-8') . '</td>';"
    },
    {
      "file": "includes/html/pages/device/routing/bgp.inc.php",
      "search": "    if ($peer['bgpPeerLastErrorCode'] == 0 && $peer['bgpPeerLastErrorSubCode'] == 0) {\n        $last_error = $peer['bgpPeerLastErrorText'];\n    } else {\n        $last_error = describe_bgp_error_code($peer['bgpPeerLastErrorCode'], $peer['bgpPeerLastErrorSubCode']) . '<br/>' . $peer['bgpPeerLastErrorText'];\n    }",
      "replace": "    if ($peer['bgpPeerLastErrorCode'] == 0 && $peer['bgpPeerLastErrorSubCode'] == 0) {\n        $last_error = htmlspecialchars((string) ($peer['bgpPeerLastErrorText']), ENT_QUOTES, 'UTF-8');\n    } else {\n        $last_error = htmlspecialchars((string) (describe_bgp_error_code($peer['bgpPeerLastErrorCode'], $peer['bgpPeerLastErrorSubCode'])), ENT_QUOTES, 'UTF-8') . '<br/>' . htmlspecialchars((string) ($peer['bgpPeerLastErrorText']), ENT_QUOTES, 'UTF-8');\n    }"
    },
    {
      "file": "includes/html/pages/device/routing/bgp.inc.php",
      "search": "        <td style='font-size: 10px; font-weight: bold; line-height: 10px;'>\" . ($peer['afi'] ?? '') . '</td>\n        <td><strong>AS' . $peer['bgpPeerRemoteAs'] . '</strong><br />' . $peer['astext'] . '</td>\n        <td>' . $peer['bgpPeerDescr'] . \"</td>\n        <td><strong><span style='color: $admin_col;'>\" . $peer['bgpPeerAdminStatus'] . \"<span><br /><span style='color: $col;'>\" . $peer['bgpPeerState'] . '</span></strong></td>",
      "replace": "        <td style='font-size: 10px; font-weight: bold; line-height: 10px;'>\" . htmlspecialchars((string) ($peer['afi'] ?? ''), ENT_QUOTES, 'UTF-8') . '</td>\n        <td><strong>AS' . htmlspecialchars((string) ($peer['bgpPeerRemoteAs']), ENT_QUOTES, 'UTF-8') . '</strong><br />' . htmlspecialchars((string) ($peer['astext']), ENT_QUOTES, 'UTF-8') . '</td>\n        <td>' . htmlspecialchars((string) ($peer['bgpPeerDescr']), ENT_QUOTES, 'UTF-8') . \"</td>\n        <td><strong><span style='color: $admin_col;'>\" . htmlspecialchars((string) ($peer['bgpPeerAdminStatus']), ENT_QUOTES, 'UTF-8') . \"<span><br /><span style='color: $col;'>\" . htmlspecialchars((string) ($peer['bgpPeerState']), ENT_QUOTES, 'UTF-8') . '</span></strong></td>"
    },
    {
      "file": "includes/html/pages/device/showconfig.inc.php",
      "search": "Sync status: <strong>' . $node_info['last']['status'] . '</strong>",
      "replace": "Sync status: <strong>' . htmlspecialchars((string) ($node_info['last']['status']), ENT_QUOTES, 'UTF-8') . '</strong>"
    },
    {
      "file": "includes/html/pages/device/showconfig.inc.php",
      "search": "<strong>Node:</strong> ' . $node_info['name'] . '</li>",
      "replace": "<strong>Node:</strong> ' . htmlspecialchars((string) ($node_info['name']), ENT_QUOTES, 'UTF-8') . '</li>"
    },
    {
      "file": "includes/html/pages/device/showconfig.inc.php",
      "search": "<strong>IP:</strong> ' . $node_info['ip'] . '</li>",
      "replace": "<strong>IP:</strong> ' . htmlspecialchars((string) ($node_info['ip']), ENT_QUOTES, 'UTF-8') . '</li>"
    },
    {
      "file": "includes/html/pages/device/showconfig.inc.php",
      "search": "<strong>Model:</strong> ' . $node_info['model'] . '</li>",
      "replace": "<strong>Model:</strong> ' . htmlspecialchars((string) ($node_info['model']), ENT_QUOTES, 'UTF-8') . '</li>"
    },
    {
      "file": "includes/html/pages/device/showconfig.inc.php",
      "search": "Last Sync:</strong> ' . $node_info['last']['end'] . ' &nbsp;<button class=\"btn btn-primary btn-xs\" style=\"float: right;\" name=\"queue-refresh\"  onclick=\\'refresh_oxidized_node(\"' . $device['hostname'] . '\")\\'>Refresh</button>",
      "replace": "Last Sync:</strong> ' . htmlspecialchars((string) ($node_info['last']['end']), ENT_QUOTES, 'UTF-8') . ' &nbsp;<button class=\"btn btn-primary btn-xs\" style=\"float: right;\" name=\"queue-refresh\"  onclick=\\'refresh_oxidized_node(\"' . htmlspecialchars((string) ($device['hostname']), ENT_QUOTES, 'UTF-8') . '\")\\'>Refresh</button>"
    },
    {
      "file": "includes/html/pages/device/showconfig.inc.php",
      "search": "'<option value=\"' . $version['oid'] . '|' . $version['date'] . '|' . $config_total . '\" ';",
      "replace": "'<option value=\"' . htmlspecialchars((string) ($version['oid']), ENT_QUOTES, 'UTF-8') . '|' . htmlspecialchars((string) ($version['date']), ENT_QUOTES, 'UTF-8') . '|' . $config_total . '\" ';"
    },
    {
      "file": "includes/html/pages/device/showconfig.inc.php",
      "search": "echo $i . ' :: ' . $version['date'] . '</option>';",
      "replace": "echo $i . ' :: ' . htmlspecialchars((string) ($version['date']), ENT_QUOTES, 'UTF-8') . '</option>';"
    },
    {
      "file": "includes/html/pages/device/showconfig.inc.php",
      "search": "Author: <strong>' . $author . '</strong>",
      "replace": "Author: <strong>' . htmlspecialchars((string) ($author), ENT_QUOTES, 'UTF-8') . '</strong>"
    },
    {
      "file": "includes/html/pages/device/showconfig.inc.php",
      "search": "<strong>Message:</strong> ' . $msg . '</li>",
      "replace": "<strong>Message:</strong> ' . htmlspecialchars((string) ($msg), ENT_QUOTES, 'UTF-8') . '</li>"
    },
    {
      "file": "includes/html/pages/device/slas.inc.php",
      "search": "    $name = 'SLA #' . $sla['sla_nr'] . ' - ' . trans_fb(\"modules.slas.{$sla['rtt_type']}\", ucfirst((string) $sla['rtt_type']));\n    if ($sla['tag']) {\n        $name .= ': ' . $sla['tag'];\n    }\n\n    if ($sla['owner']) {\n        $name .= ' (Owner: ' . $sla['owner'] . ')';\n    }",
      "replace": "    $name = 'SLA #' . $sla['sla_nr'] . ' - ' . trans_fb(\"modules.slas.{$sla['rtt_type']}\", ucfirst((string) $sla['rtt_type']));\n    if ($sla['tag']) {\n        $name .= ': ' . htmlspecialchars((string) ($sla['tag']), ENT_QUOTES, 'UTF-8');\n    }\n\n    if ($sla['owner']) {\n        $name .= ' (Owner: ' . htmlspecialchars((string) ($sla['owner']), ENT_QUOTES, 'UTF-8') . ')';\n    }"
    },
    {
      "file": "includes/html/pages/eventlog.inc.php",
      "search": "echo \"'&nbsp;&nbsp;<input type=\\\"hidden\\\" name=\\\"device\\\" id=\\\"device\\\" value=\\\"\" . $vars['device'] . \"\\\">' + \";",
      "replace": "echo \"'&nbsp;&nbsp;<input type=\\\"hidden\\\" name=\\\"device\\\" id=\\\"device\\\" value=\\\"\" . htmlspecialchars((string) ($vars['device']), ENT_QUOTES, 'UTF-8') . \"\\\">' + \";"
    },
    {
      "file": "includes/html/pages/graphs.inc.php",
      "search": "echo LibrenmsConfig::get('graph_descr.' . $vars['type']);",
      "replace": "echo htmlspecialchars((string) (LibrenmsConfig::get('graph_descr.' . $vars['type'])), ENT_QUOTES, 'UTF-8');"
    },
    {
      "file": "includes/html/pages/routing/bgp.inc.php",
      "search": "        if ($peer['bgpPeerLastErrorCode'] == 0 && $peer['bgpPeerLastErrorSubCode'] == 0) {\n            $last_error = $peer['bgpPeerLastErrorText'];\n        } else {\n            $last_error = describe_bgp_error_code($peer['bgpPeerLastErrorCode'], $peer['bgpPeerLastErrorSubCode']) . '<br/>' . $peer['bgpPeerLastErrorText'];\n        }",
      "replace": "        if ($peer['bgpPeerLastErrorCode'] == 0 && $peer['bgpPeerLastErrorSubCode'] == 0) {\n            $last_error = htmlspecialchars((string) ($peer['bgpPeerLastErrorText']), ENT_QUOTES, 'UTF-8');\n        } else {\n            $last_error = htmlspecialchars((string) (describe_bgp_error_code($peer['bgpPeerLastErrorCode'], $peer['bgpPeerLastErrorSubCode'])), ENT_QUOTES, 'UTF-8') . '<br/>' . htmlspecialchars((string) ($peer['bgpPeerLastErrorText']), ENT_QUOTES, 'UTF-8');\n        }"
    },
    {
      "file": "includes/html/pages/routing/bgp.inc.php",
      "search": "            <td width=50>\" . ($peer['afi'] ?? '') . '</td>\n            <td><strong>AS' . $peer['bgpPeerRemoteAs'] . '</strong><br />' . $peer['astext'] . '</td>\n            <td>' . $peer['bgpPeerDescr'] . \"</td>\n            <td><strong><span style='color: $admin_col;'>\" . $peer['bgpPeerAdminStatus'] . \"</span><br /><span style='color: $col;'>\" . $peer['bgpPeerState'] . '</span></strong></td>",
      "replace": "            <td width=50>\" . htmlspecialchars((string) ($peer['afi'] ?? ''), ENT_QUOTES, 'UTF-8') . '</td>\n            <td><strong>AS' . htmlspecialchars((string) ($peer['bgpPeerRemoteAs']), ENT_QUOTES, 'UTF-8') . '</strong><br />' . htmlspecialchars((string) ($peer['astext']), ENT_QUOTES, 'UTF-8') . '</td>\n            <td>' . htmlspecialchars((string) ($peer['bgpPeerDescr']), ENT_QUOTES, 'UTF-8') . \"</td>\n            <td><strong><span style='color: $admin_col;'>\" . htmlspecialchars((string) ($peer['bgpPeerAdminStatus']), ENT_QUOTES, 'UTF-8') . \"</span><br /><span style='color: $col;'>\" . htmlspecialchars((string) ($peer['bgpPeerState']), ENT_QUOTES, 'UTF-8') . '</span></strong></td>"
    },
    {
      "file": "includes/html/pages/routing/vrf.inc.php",
      "search": "echo $vrf['vrf_name'] . '</a><br />';",
      "replace": "echo htmlspecialchars((string) ($vrf['vrf_name']), ENT_QUOTES, 'UTF-8') . '</a><br />';"
    },
    {
      "file": "includes/html/pages/routing/vrf.inc.php",
      "search": "'<span class=box-desc>' . $vrf['mplsVpnVrfDescription'] . '</span></td>';",
      "replace": "'<span class=box-desc>' . htmlspecialchars((string) ($vrf['mplsVpnVrfDescription']), ENT_QUOTES, 'UTF-8') . '</span></td>';"
    },
    {
      "file": "includes/html/pages/routing/vrf.inc.php",
      "search": "'<td width=100 class=box-desc>' . $vrf['mplsVpnVrfRouteDistinguisher'] . '</td>';",
      "replace": "'<td width=100 class=box-desc>' . htmlspecialchars((string) ($vrf['mplsVpnVrfRouteDistinguisher']), ENT_QUOTES, 'UTF-8') . '</td>';"
    },
    {
      "file": "includes/html/print-vrf.inc.php",
      "search": "echo \"<td width=200 class=list-large><a href='routing/vrf/\" . $vrf['mplsVpnVrfRouteDistinguisher'] . \"/'>\" . $vrf['vrf_name'] . '</a></td>';\necho '<td width=150 class=box-desc>' . $vrf['mplsVpnVrfDescription'] . '</td>';\necho '<td width=100 class=box-desc>' . $vrf['mplsVpnVrfRouteDistinguisher'] . '</td>';",
      "replace": "echo \"<td width=200 class=list-large><a href='routing/vrf/\" . htmlspecialchars((string) ($vrf['mplsVpnVrfRouteDistinguisher']), ENT_QUOTES, 'UTF-8') . \"/'>\" . htmlspecialchars((string) ($vrf['vrf_name']), ENT_QUOTES, 'UTF-8') . '</a></td>';\necho '<td width=150 class=box-desc>' . htmlspecialchars((string) ($vrf['mplsVpnVrfDescription']), ENT_QUOTES, 'UTF-8') . '</td>';\necho '<td width=100 class=box-desc>' . htmlspecialchars((string) ($vrf['mplsVpnVrfRouteDistinguisher']), ENT_QUOTES, 'UTF-8') . '</td>';"
    },
    {
      "file": "resources/views/map/custom-list.blade.php",
      "search": "{!! $map->name !!}",
      "replace": "{!! e($map->name) !!}"
    }
  ]
}
</check_patches_json>
