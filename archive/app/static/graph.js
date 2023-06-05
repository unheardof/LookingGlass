const VALUE_SET_PATTERN = /\{(('.*'),?)+}/;
var nodes = null;
var edges = null;
var network = null;
var seed = 2; // Want the nodes to be rendered the same way every time (rather than based off a random seed)
var data = {};
var currGraphVersion = 0;
var keepGraphUpToDate = true;

var options = {
    locale: 'en',
    interaction: {
	multiselect: true,
    },
    physics:{
	enabled: true,
	stabilization: {
	    enabled: true,
	    iterations: 500 // default is 1000; decreasing iterations to improve performance
	},
	hierarchicalRepulsion: {
	    centralGravity: 0.5,
	    springLength: 10,
	    springConstant: 1.5,
	    nodeDistance: 300,
	    damping: 0.9
	},
	solver: 'hierarchicalRepulsion'
    },
    layout: {
	randomSeed: seed,
	improvedLayout: true,
	hierarchical: {
	    enabled: false
	}
    },
    nodes: {
	color: '#03fc45',
	font: {
	    size: 14, //px
	    face: 'courier',
	    color: '#03fc45',
	    multi: 'html',
	    background: 'black'
	},
	labelHighlightBold: true,
	shape: 'image',
    },
    edges: {
	color: '#03fc45',
	font: {
	    size: 14, //px
	    face: 'courier',
	    color: '#03fc45',
	    background: 'black',
	    strokeWidth: 0
	},
	smooth: {
	    enabled: false
	},
	width: 2,
	hoverWidth: function (width) {return width+1;}
    },
    groups: {
	ops_box: {
	    image: 'static/images/hacker-icon.ico',
	},
	staging_server: {
	    image: 'static/images/staging-server-icon.png',
	},
	redirect: {
	    image: 'static/images/redirector-icon.png',
	},
	beacon: {
	    image: 'static/images/beacon-icon.ico',
	},
	windows_host: {
	    image: 'static/images/windows-icon.png',
	},
	linux_host: {
	    image: 'static/images/linux-icon.png',
	},
	router: {
	    image: 'static/images/router_icon.png',
	},
	network_switch: {
	    image: 'static/images/switch_icon.png',
	},
	nic: {
	    image: 'static/images/ethernet_port_icon.png',
	},
	wan: {
	    image: 'static/images/wan_icon.png',
	},
	other: {
	    image: 'static/images/generic-host.png',
	}
    },
    manipulation: {
	addNode: function (data, callback) {
	    // filling in the popup DOM elements
	    document.getElementById('operation').innerHTML = "Add Node";
	    document.getElementById('node-ip').value = data.title;
	    document.getElementById('node-hostname').value = data.hostname;
	    document.getElementById('saveButton').onclick =  saveNode.bind(this, data, callback);
	    document.getElementById('cancelButton').onclick = clearNodePopUp.bind();
	    document.getElementById('node-popUp').style.display = 'block';
	},
	editNode: function (data, callback) {
	    // filling in the popup DOM elements
	    document.getElementById('operation').innerHTML = "Edit Node";
	    document.getElementById('node-ip').value = data.title;
	    document.getElementById('node-hostname').value = data.hostname;
	    document.getElementById('node-type').value = data.group;
	    document.getElementById('saveButton').onclick =  saveNode.bind(this, data, callback);

	    document.getElementById('cancelButton').onclick = cancelNodeEdit.bind(this, callback);
	    document.getElementById('node-popUp').style.display = 'block';
	},
	addEdge: function (data, callback) {
	    data.options = { label: '' };

	    if (data.from == data.to) {
		var r = confirm("Do you want to connect the node to itself?");
		if (r == true) {
		    saveEdge(data);
		    callback(data);
		}
	    }
	    else {
		saveEdge(data);
		callback(data);
	    }
	},
	editEdge: function (data, callback) {
	    selected_edge = network.body.edges[data.id];
	    data['previous_source_node'] = selected_edge['fromId'];
	    data['previous_destination_node'] = selected_edge['toId'];
	    
	    if (data.from == data.to) {
		var r = confirm("Do you want to connect the node to itself?");
		if (r == true) {
		    saveEdge(data);
		    callback(data);
		}
	    }
	    else {
		saveEdge(data);
		callback(data);
	    }
	},
	deleteNode: function (data, callback) {
	    removeNode(data);
	    callback(data);
	},
	deleteEdge: function (data, callback) {
	    removeEdge(data);
	    callback(data);
	}
    }
};

function destroy() {
    if (network !== null) {
	network.destroy();
	network = null;
    }
}

function draw() {
    destroy();
    nodes = [];
    edges = [];

    // create a network
    var container = document.getElementById('mynetwork');

    network = create_network(container, data, options);
}

function openControlPanel() {
    document.getElementById("controlPanel").style.display = "block";
    document.getElementById("openControlPanelSpan").style.display = "none";
}

function closeControlPanel() {
    document.getElementById("controlPanel").style.display = "none";
    document.getElementById("openControlPanelSpan").style.display = "block";
}

function contextPanel() {
    return document.getElementById('contextPanel');
}

function openContextPanel() {
    contextPanel().style.display = "block";
}

function closeContextPanel() {
    contextPanel().style.display = "none";
}

function setContextPanelContent(lines) {
    contextPanel().innerHTML = lines.join('<br>');
}

function clearNodePopUp() {
    document.getElementById('saveButton').onclick = null;
    document.getElementById('cancelButton').onclick = null;
    document.getElementById('node-popUp').style.display = 'none';
}

function cancelNodeEdit(callback) {
    clearNodePopUp();
    callback(null);
}

function cancelEdgeEdit(callback) {
    callback(null);
}

function getCsrfToken() {
    return document.head.querySelector("meta[name='csrf-token']").getAttribute("content");
}

function getUserId() {
    return document.head.querySelector("meta[name='user-id']").getAttribute("content");
}

function getWorkspaceId() {
    workspaceMetaTag = document.head.querySelector("meta[name='workspace-id']")
    if (workspaceMetaTag == null) {
        return null;
    }
    
    return workspaceMetaTag.getAttribute("content");
}

function setWorkspaceId(workspaceId) {
    document.querySelector('meta[name="workspace-id"]').setAttribute("content", workspaceId);
}

function postData(methodName, data = {}, contentType = "application/json") {
    var xhttp = new XMLHttpRequest();
    xhttp.open("POST", methodName, true);
    xhttp.setRequestHeader("Content-type", contentType);
    xhttp.setRequestHeader("X-CSRFToken", getCsrfToken());
    xhttp.setRequestHeader("User-Id", getUserId());
    xhttp.setRequestHeader("Workspace-Id", getWorkspaceId());

    xhttp.onreadystatechange = function() {
	// Wait for the state changes to end before doing anything
	if (this.readyState == 4) {
	    if (this.status == 200) {
		refreshGraph();
	    } else {
		if (xhttp.responseText) {
                    error_details = JSON.parse(xhttp.responseText)

                    if ('message' in error_details) {
                        alert(error_details.message);
		        console.error(error_details.message);
                    } else {
		        alert(xhttp.responseText);
		        console.error(xhttp.responseText);
                    }
		} else {
		    alert('Failed to execute ' + methodName);
		    console.error('Failed to execute ' + methodName);
		}
	    }
	}
    };

    xhttp.send(data);
}

function postJsonData(methodName, data) {
    postData(methodName, JSON.stringify(data, undefined, 2), "application/json");
}

function postNodeData(methodName, data) {
    data.ip = document.getElementById('node-ip').value;
    data.hostname = document.getElementById('node-hostname').value;
    data.group = document.getElementById('node-type').value;
    postJsonData(methodName, data);
}

function postFile(methodName, fileName) {
    var reader = new FileReader();

    reader.onload = function(evt) {
	postJsonData(methodName, evt.target.result);
    };

    reader.readAsText(fileName);
}

function postBinaryFile(methodName, fileName) {
    var reader = new FileReader();

    reader.onload = function(evt) {
	postData(methodName, evt.target.result, 'application/octet-stream');
    };

    reader.readAsArrayBuffer(fileName);
}

function setStringToList(str) {
    // Reference: https://stackoverflow.com/questions/23136691/replace-last-occurrence-word-in-javascript/23137090
    var lastClosingBraceIndex = str.lastIndexOf('}');
    str = str.slice(0, lastClosingBraceIndex) + str.slice(lastClosingBraceIndex).replace('}', '');
    str = str.replace('{', '').replace(/'/g, "");
    return str.split(',');
}

function openNmapFileSelector() {
    nmapFileSelector.click();
}

function openArpFileSelector() {
    arpFileSelector.click();
}

function openPcapFileSelector() {
    // TODO: Get PCAP uploads working
    //pcapFileSelector.click();
    alert('This feature is not fully supported at this time; please run the extract_uniq_flows.sh script on the PCAP and then upload the result net-flow file using the Upload Net Flow File option');
}

function openNetflowFileSelector() {
    netflowFileSelector.click();
}

function uploadNmapFile(files) {
    postFile('upload_nmap_data', files[0]);
}

function uploadArpFile(files) {
    postFile('upload_arp_data', files[0]);
}

function uploadPcapFile(files) {
    // TODO: Get this fixed 
    //postBinaryFile('upload_pcap_data', files[0]);
}

function uploadNetflowFile(files) {
    postFile('upload_net_flow_data', files[0])
}

function delete_view_specific_data_attrs(data) {
    delete data.font;
    delete data.color;
    delete data.shapeProperties;
    delete data.y_coordinate;
    delete data.x_coordinate;
    delete data.scaling;
    delete data.y;
    delete data.x;
    delete data.icon;
    delete data.shape;
    delete data.connections;
    delete data.image;
    delete data.shadow;
    delete data.fixed;
    delete data.margin;

    return data;
}

function nodeForIp(ip) {
    if (ip == undefined || ip == 'undefined') {
	return null;
    }
    
    nodes = network.body.nodes;
    for (node_id in nodes) {
	node = nodes[node_id]
        if(node.options.ip == ip) {
            return node;
        }
    }

    return null;
}

function isPrivateIp(ip) {
    // Private IP Ranges:
    // 10.0.0.0/8
    // 172.16.0.0/12 (172.16.0.0-172.31.255.255)
    // 192.168.0.0/16
    
    octets = ip.split('.')
    if (octets[0] == '10') {
	return true;
    }

    if (octets[0] == '172') {
	second_octet = parseInt(octets[1]);
	if (second_octet >= 16 && second_octet <= 31) {
	    return true;
	}
    }

    if (octets[0] == '192' && octets[1] == '168') {
	return true;
    }

    return false;
}

function saveNode(data, callback) {
    ip = document.getElementById('node-popUp').getElementsByTagName('td')[1].children[0].value;
    node = nodeForIp(ip);
    
    if (!isPrivateIp(ip) && node != null && data.id != node.id) {
        alert(`ERROR: Node already exists with IP of ${ip}`);
    } else {
        clearNodePopUp();
        delete_view_specific_data_attrs(data);
        postNodeData("upsert_node", data);
        callback(data);
    }
}

function saveEdge(data) {
    postJsonData("upsert_edge", data);
}

function removeNode(data) {
    closeContextPanel();
    postNodeData("remove_node", data.nodes[0]);
}

function removeEdge(data) {
    edge = network.body.edges[data.edges[0]]
    postJsonData("remove_edge", { from: edge.fromId, to: edge.toId });
}

function objectToArray(obj) {
    return Object.keys(obj).map(function (key) {
	obj[key].id = key;
	return obj[key];
    });
}

function formatIfacesForDisplay(networkInterfaces) {
    displayLines = [];

    for(var i = 0; i < networkInterfaces.length; i++) {
        iface = networkInterfaces[i];

        if('name' in iface && iface['name'] != null) {
            if(networkInterfaces.length > 1) {
                displayLines.push('<b>Network Interface ' + (i + 1) + ' (' + iface['name'] +')</b>');
            } else {
                displayLines.push('<b>Network Interface (' + iface['name'] +')</b>');
            }
        } else {
            if(networkInterfaces.length > 1) {
                displayLines.push('<b>Network Interface ' + (i + 1) + '</b>');
            } else {
                displayLines.push('<b>Network Interface</b>');
            }
        }
        
        if('mac_addr' in iface) {
            displayLines.push('MAC Address: ' + iface['mac_addr']);
        }

        if('hardware_type' in iface) {
            displayLines.push('Type: ' + iface['hardware_type']);
        }

        if('arp_flags' in iface) {
            displayLines.push('ARP Flags: ' + iface['arp_flags']);
        }

        displayLines.push('');
    }

    return displayLines;
}

function create_network(container, data, options) {
    network = new vis.Network(container, data, options);

    // Based on https://stackoverflow.com/questions/35906493/accessing-node-data-in-vis-js-click-handler
    network.on('click', function(properties) {
	if('nodes' in properties && properties.nodes.length != 0) {
	    var ids = properties.nodes;
	    var clickedNodes = data.nodes.get(ids);

	    var displayLines = [];

	    clickedNodes.forEach(
		function(elem, index, array) {
		    // Add separations between data for different nodes if multiple nodes have been selected
		    if(clickedNodes.length > 1) {
			displayLines.push('<hr/>');
		    }

                    if('title' in elem) {
		        displayLines.push('<b><u>IP:</u></b> ' + elem['title']);
                    } else {
                        displayLines.push('<b><u>IP:</u></b> ' + 'UNKNOWN');
                    }

                    if('hostname' in elem) {
		        displayLines.push('<b><u>Hostname:</u></b> ' + elem['hostname']);
                    } else {
                        displayLines.push('<b><u>Hostname:</u></b> ' + 'UNKNOWN');
                    }

                    displayLines.push('');

                    if('network_interfaces' in elem) {
                        displayLines = displayLines.concat(formatIfacesForDisplay(elem['network_interfaces']));
                    }

		    if('device_types' in elem) {
			device_type_list = JSON.parse(elem['device_types']);
			if(device_type_list.length != 0) {
			    displayLines.push('<br><b><u>Device Types:</u></b>');
			    for(var device in device_type_list) {
				displayLines.push(device);
			    }
			}
		    }

		    if('os_list' in elem && elem['os_list'].length != 0) {
			os_list_str = elem['os_list'].replace(/'/g, "\"");

			os_list = JSON.parse(os_list_str);
			if(os_list.length != 0) {
			    displayLines.push('<br><b><u>OS Info:</u></b>');
			    for(var i in os_list) {
				displayLines.push(os_list[i]);
			    }
			}
		    }

		    if('port_data' in elem) {
			port_data_obj_str = elem['port_data'].replace(/'/gi, "\"");
			var portData = JSON.parse(port_data_obj_str);

			for (var portNumber in portData) {
			    var dataForPort = portData[portNumber];

			    displayLines.push('<br><b><u>Port Number:</u></b> ' + portNumber);

			    for (var dataKey in dataForPort) {
                                if(dataKey == 'port_number') {
                                    continue
                                }
                                
				if(dataForPort[dataKey].length != 0) {
				    displayLines.push(dataKey + ': ' + dataForPort[dataKey]);
				}
			    }
			}
		    }

		    var edgeLabels = new Set();
		    var allEdges = network.body.edges;
		    
		    for (var edgeIndex in allEdges) {
			edge = allEdges[edgeIndex];
			if (edge['fromId'] == elem['id'] || edge['toId'] == elem['id']) {
			    if ('options' in edge && 'label' in edge['options']) {
				var label = edge['options']['label'];
				if (label != undefined && label.replace(/^\s+|\s+$/g, '').length > 0) {
				    edgeLabels.add(label);
				}
			    }
			}
		    }

		    if(edgeLabels.size > 0) {
			displayLines.push('<br><b><u>Connected edge labels:</u></b>');
			for (const label of edgeLabels) {
			    displayLines.push(label);
			}
		    }

		    // TODO: Add support for interacting with hosts (when there is an agent on the host to interact with); ex: could launch a nmap scan from the console or spawn a serpent shell
		}
	    );

	    setContextPanelContent(displayLines);
	    openContextPanel();
	} else {
	    closeContextPanel();
	}
    });

    // Reference: https://visjs.github.io/vis-network/docs/network/index.html?keywords=selectEdge#Events
    network.on("doubleClick", function(data) {
	if (data.edges.length > 0) {
	    selected_edge = null;
	    edges = network.body.edges
	    for (edge_id in edges) {
		edge = edges[edge_id];
		if (edge.selected) {
		    selected_edge = edge;
		}
	    }

	    if (selected_edge != null) {
		label = prompt("Please enter edge label", selected_edge.options.label);
		if (label != null) {
		    saveEdge({
			to: selected_edge.toId,
			from: selected_edge.fromId,
			label: label
		    });
		}
	    } else {
		console.log('ERROR: Unable to find selected edge while handling double-click event');
	    }
	}
    });
    
    return network;
}

function refreshGraph(forceRedraw = false) {
    if (!keepGraphUpToDate) {
	return null;
    }

    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() {
	if (this.readyState == 4 && keepGraphUpToDate) {
	    var graphData = JSON.parse(xmlHttp.responseText);

	    if (forceRedraw || parseInt(graphData['current_version_number']) > currGraphVersion) {
		// Hide the node data pop-up
		closeContextPanel();

		currGraphVersion = parseInt(graphData['current_version_number']);

		var data = {
		    nodes: getNodeData(graphData['nodes']),
		    edges: getEdgeData(graphData['nodes'])
		}

		var container = document.getElementById('mynetwork');
		network = create_network(container, data, options);
	    }

	    setTimeout(refreshGraph, 100);
	    refreshWorkspaceTabs();
	}
    };

    params = "user_id=" + getUserId() + "&workspace_id=" + getWorkspaceId();
    xmlHttp.open("GET", "graph_data?" + params, true ); // true for asynchronous request
    xmlHttp.send();
}

function getNodeData(data) {
    var networkNodes = [];

    data.forEach(
	function(elem, index, array) {
	    elem.title = elem.ip;

	    if ((elem.ip == null || elem.ip == 'undefined') && (elem.hostname == null || elem.hostname == 'undefined')) {
		elem.label = '';
	    } else if (elem.hostname == null || elem.hostname == 'undefined') {
		elem.label = elem.ip;
	    } else if (elem.hostname != elem.ip && elem.ip != null && elem.ip != 'undefined') {
		elem.label = elem.hostname + '\n' + elem.ip;
	    } else {
		elem.label = elem.hostname;
	    }
	    
	    networkNodes.push(elem);
	}
    );

    return new vis.DataSet(networkNodes);
}

function getNodeById(data, id) {
    for (var n = 0; n < data.length; n++) {
	if (data[n].id == id) {  // double equals since id can be numeric or string
	    return data[n];
	}
    };

    console.warn('Cannot find node with ID \'' + id + '\' in data; node may have been deleted');
}

function getEdgeData(data) {
    var networkEdges = [];

    data.forEach(function(node) {
	if(typeof node !== 'undefined' && typeof node.connections !== 'undefined') {
	    // add the connection
	    node.connections.forEach(function(edgeData, cIndex, conns) {
		destinationId = edgeData.destination_node_id; 
		
		networkEdges.push({from: node.id, to: destinationId, label: edgeData.label});
		let cNode = getNodeById(data, destinationId);

		if(typeof cNode !== 'undefined' && typeof cNode.connections !== 'undefined') {
		    var elementConnections = cNode.connections;

		    // remove the connection from the other node to prevent duplicate connections
		    var duplicateIndex = elementConnections.findIndex(function(connection) {
			return connection.destinationId == node.id; // double equals since id can be numeric or string
		    });

		    if (duplicateIndex != -1) {
			elementConnections.splice(duplicateIndex, 1);
		    };
		}
	    });
	};
    });

    return new vis.DataSet(networkEdges);
}

function objectToArray(obj) {
    return Object.keys(obj).map(function (key) {
	obj[key].id = key;
	return obj[key];
    });
}

function init() {
    draw();
    refreshGraph(); // Do an initial load of the current graph data

    var currentTab = document.getElementById('workspace-tabs').children[0];
    var currentTabButton = currentTab.children[0];
    currentTabButton.style.backgroundColor = '#03fc45';
    currentTabButton.style.color = 'black';
}

function logout() {
    // No additional data needs to be send with the logout request
    keepGraphUpToDate = false;
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open("GET", "logout", true ); // true for asynchronous request
    xmlHttp.send();
    window.location.href = '/login';
}

function getWorkspaceNameForTab(tabSpan) {
    return tabSpan.children[0].textContent;
}

function getWorkspaceIdForTab(tabSpan) {
    // The workspace ID is stored in a hidden input element within the tab span
    return tabSpan.children[1].value;
}

function tabExists(workspaceName, currentTabs) {
    for (var i = 0; i < currentTabs.length; i++) {
	if (getWorkspaceNameForTab(currentTabs[i]) == workspaceName) {
	    return true;
	}
    }

    return false;
}

function workspaceExists(workspaceName, workspaces) {
    for (var i = 0; i < workspaces.length; i++) {
	if (workspaces[i]['name'] == workspaceName) {
	    return true;
	}
    }

    return false;
}

function refreshWorkspaceTabs() {
    var xmlHttp = new XMLHttpRequest();

    xmlHttp.onreadystatechange = function() {
	if (this.readyState == 4) {
	    var workspaces = JSON.parse(xmlHttp.responseText);

	    var workspaceTabsDiv = document.getElementById('workspace-tabs');
	    var currentTabs = workspaceTabsDiv.children;

	    // Remove any tabs for workspaces which no longer exist (or the user no
	    // longer has permissions for)
	    for (var i = 0; i < currentTabs.length; i++) {
		var tabWorkspaceName = getWorkspaceNameForTab(currentTabs[i]);
		if (!workspaceExists(tabWorkspaceName, workspaces)) {
		    var workspaceId = getWorkspaceIdForTab(currentTabs[i]);
		    workspaceTabsDiv.removeChild(currentTabs[i]);

		    // If the user is currently viewing the workspace that has been removed,
		    // just refresh the page
		    if (workspaceId == getWorkspaceId()) {
                        setWorkspaceId(null);
			location.reload();
		    }
		}

	    }

	    for (var i = 0; i < workspaces.length; i++) {
                if (getWorkspaceId() == null){
                    setWorkspaceId(workspaces[i]['id']);
                }
                
		if (tabExists(workspaces[i]['name'], currentTabs)) {
		    continue;
		} else {
		    var tabButtonHtml = "<button class='tab-buttons' onclick='loadWorkspace(";
		    tabButtonHtml += workspaces[i]['id'];
		    tabButtonHtml += ")' >"
		    tabButtonHtml += workspaces[i]['name'];
		    tabButtonHtml += "</button>";
		    tabButtonHtml += "<input type='hidden' value='";
		    tabButtonHtml += workspaces[i]['id'];
		    tabButtonHtml += "'/>";

		    // Based on answer from https://stackoverflow.com/questions/6956258/adding-onclick-event-to-dynamically-added-button
		    var span = document.createElement("span");
		    span.innerHTML = tabButtonHtml;
		    workspaceTabsDiv.appendChild(span);
		}
	    }
	}
    };

    xmlHttp.open("GET", "workspaces", true ); // true for asynchronous request
    xmlHttp.send();
}

function loadWorkspace(workspaceId) {
    setWorkspaceId(workspaceId);
    var workspaceTabsDiv = document.getElementById('workspace-tabs');
    var tabs = workspaceTabsDiv.children;

    for (var i = 0; i < tabs.length; i++) {
	var tabWorkspaceId = getWorkspaceIdForTab(tabs[i]);
	var tabButton = tabs[i].children[0];

	if (tabWorkspaceId == workspaceId) {
	    tabButton.style.backgroundColor = '#03fc45';
	    tabButton.style.color = 'black';
	} else {
	    tabButton.style.backgroundColor = 'black';
	    tabButton.style.color = '#03fc45';
	}
    }
    
    refreshGraph(true);
}

function createWorkspace() {
    var workspace_name = prompt('Enter name for the new workspace:');

    if (workspace_name) {
	data = {};
	data['workspace_name'] = workspace_name;
	postJsonData('create_workspace', data);
	refreshWorkspaceTabs();
    }
}

function removeWorkspace() {
    var proceed = confirm('Really delete current workspace?')

    if (proceed) {
	postJsonData('delete_workspace', { 'workspace_id': getWorkspaceId() });
        setWorkspaceId(null);
        refreshWorkspaceTabs();
	location.reload();
    }
}

function shareWorkspace() {
    var username = prompt('Who would you like to share this workspace with?');

    data = {};
    data['authorized_user'] = username;
    postJsonData('share_workspace', data);
}

function unshareWorkspace() {
    // TODO: Allow user to select from list of currently authorized users
    //       Would ultimately be good to add a permissions/workspaces management page
    var username = prompt('Who would you like to unshare this workspace with?');

    data = {};
    data['unauthorized_user'] = username;
    postJsonData('unshare_workspace', data);
}
