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
    edges: {
	smooth: {
	    enabled: false
	}
    },
    groups: {
	ops_box: {
	    shape: 'image',
	    image: 'static/images/hacker-icon.ico',
	    font: {
		size: 15,
		color: '#ffffff'
	    }
	},
	staging_server: {
	    shape: 'image',
	    image: 'static/images/staging-server-icon.png',
	    font: {
		size: 15,
		color: '#ffffff'
	    }
	},
	redirect: {
	    shape: 'image',
	    image: 'static/images/redirector-icon.png',
	    font: {
		size: 15,
		color: '#ffffff'
	    }
	},
	beacon: {
	    shape: 'image',
	    image: 'static/images/beacon-icon.ico',
	    font: {
		size: 15,
		color: '#ffffff'
	    }
	},
	windows_host: {
	    shape: 'image',
	    image: 'static/images/windows-icon.png',
	    font: {
		size: 15,
		color: '#ffffff'
	    }
	},
	linux_host: {
	    shape: 'image',
	    image: 'static/images/linux-icon.png',
	    font: {
		size: 15,
		color: '#ffffff'
	    }
	},
	other: {
	    shape: 'image',
	    image: 'static/images/generic-host.png',
	    font: {
		size: 15,
		color: '#ffffff'
	    }
	}
    },
    manipulation: {
	addNode: function (data, callback) {
	    // filling in the popup DOM elements
	    document.getElementById('operation').innerHTML = "Add Node";
	    document.getElementById('node-ip').value = data.title;
	    document.getElementById('node-hostname').value = data.label;
	    document.getElementById('node-type').value = data.group;
	    document.getElementById('saveButton').onclick =  saveNode.bind(this, data, callback);
	    document.getElementById('cancelButton').onclick = clearPopUp.bind();
	    document.getElementById('network-popUp').style.display = 'block';
	},
	editNode: function (data, callback) {
	    // filling in the popup DOM elements
	    document.getElementById('operation').innerHTML = "Edit Node";
	    document.getElementById('node-ip').value = data.title;
	    document.getElementById('node-hostname').value = data.label;
	    document.getElementById('node-type').value = data.group;
	    document.getElementById('saveButton').onclick =  saveNode.bind(this, data, callback);

	    document.getElementById('cancelButton').onclick = cancelEdit.bind(this, callback);
	    document.getElementById('network-popUp').style.display = 'block';
	},

	addEdge: function (data, callback) {
	    // At present, edge labels are not used for anything
	    // TODO: Add support for adding labels to edges -> https://stackoverflow.com/questions/37661543/vis-js-network-add-label-to-edge
	    data.label = '';

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

function clearPopUp() {
    document.getElementById('saveButton').onclick = null;
    document.getElementById('cancelButton').onclick = null;
    document.getElementById('network-popUp').style.display = 'none';
}

function cancelEdit(callback) {
    clearPopUp();
    callback(null);
}

function getCsrfToken() {
    return document.head.querySelector("meta[name='csrf-token']").getAttribute("content");
}

function getUserId() {
    return document.head.querySelector("meta[name='user-id']").getAttribute("content");
}

function getWorkspaceId() {
    return document.head.querySelector("meta[name='workspace-id']").getAttribute("content");
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
		    alert(xhttp.responseText);
		    console.error(xhttp.responseText);
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

function postGraphData(methodName, data) {
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

function openNmapFileSelector() {
    nmapFileSelector.click();
}

function openArpFileSelector() {
    arpFileSelector.click();
}

function openPcapFileSelector() {
    pcapFileSelector.click();
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
    alert('This feature is not fully supported at this time; please run the extract_uniq_flows.sh script on the PCAP and then upload the result net-flow file using the Upload Net Flow File option');
    postBinaryFile('upload_pcap_data', files[0]);
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

function saveNode(data, callback) {
    clearPopUp();
    delete_view_specific_data_attrs(data);
    postGraphData("upsert_node", data);
    callback(data);
}

function saveEdge(data) {
    postGraphData("add_edge", data);
}

function removeNode(data) {
    var popupDiv = document.getElementById('node-popup');
    popupDiv.style.display = 'none'; // Hide the pop-up if it's visible
    postGraphData("remove_node", data.nodes[0]);
}

function removeEdge(call_data) {
    edge = network.body.edges[call_data.edges[0]]
    postGraphData("remove_edge", { from: edge.fromId, to: edge.toId });
}

function objectToArray(obj) {
    return Object.keys(obj).map(function (key) {
	obj[key].id = key;
	return obj[key];
    });
}

function create_network(container, data, options) {
    network = new vis.Network(container, data, options);

    // Based on https://stackoverflow.com/questions/35906493/accessing-node-data-in-vis-js-click-handler
    network.on('click', function(properties) {
	var popupDiv = document.getElementById('node-popup');

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

		    displayLines.push('IP: ' + elem['title']);
		    displayLines.push('Hostname: ' + elem['label']);

		    if('device_types' in elem) {
			device_type_list = JSON.parse(elem['device_types']);
			if(device_type_list.length != 0) {
			    displayLines.push('<hr>Device Types:');
			    for(var device in device_type_list) {
				displayLines.push(device);
			    }
			}
		    }

		    if('os_list' in elem && elem['os_list'].length != 0) {
			os_list_str = elem['os_list'].replace(/'/g, "\"");

			os_list = JSON.parse(os_list_str);
			if(os_list.length != 0) {
			    displayLines.push('<hr>OS Info:');
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

			    displayLines.push('<hr>Port Number: ' + portNumber);

			    for (var dataKey in dataForPort) {
				if(dataForPort[dataKey].length != 0) {
				    displayLines.push(dataKey + ': ' + dataForPort[dataKey]);
				}
			    }
			}
		    }

		    // TODO: Add support for interacting with hosts (when there is an agent on the host to interact with); ex: could launch a nmap scan from the console or spawn a serpent shell
		}
	    );

	    document.getElementById('node-popup').innerHTML = displayLines.join('<br>');

	    popupDiv.style.left = properties.pointer.DOM.x + 'px';
	    popupDiv.style.top = properties.pointer.DOM.y + 'px';
	    popupDiv.style.display = 'block';
	} else {
	    popupDiv.style.display = 'none'; // Hide the pop-up if it's visible
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
	// TODO: Add error handling
	if (this.readyState == 4 && keepGraphUpToDate) {
	    var graphData = JSON.parse(xmlHttp.responseText);

	    if (forceRedraw || parseInt(graphData['current_version_number']) > currGraphVersion) {
		// Hide the node data pop-up
		var popupDiv = document.getElementById('node-popup');
		popupDiv.style.display = 'none';

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
	    elem.label = elem.hostname;
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
	    node.connections.forEach(function(connId, cIndex, conns) {
		networkEdges.push({from: node.id, to: connId});
		let cNode = getNodeById(data, connId);

		if(typeof cNode !== 'undefined' && typeof cNode.connections !== 'undefined') {
		    var elementConnections = cNode.connections;

		    // remove the connection from the other node to prevent duplicate connections
		    var duplicateIndex = elementConnections.findIndex(function(connection) {
			return connection == node.id; // double equals since id can be numeric or string
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
}

function logout() {
    // No additional data needs to be send with the logout request
    keepGraphUpToDate = false;
    postJsonData('logout', ''); // TODO: Change to GET if not auth data needs to be explicitly sent
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
	    // TODO: Add error handling
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
			location.reload();
		    }
		}

	    }

	    for (var i = 0; i < workspaces.length; i++) {
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
    document.querySelector('meta[name="workspace-id"]').setAttribute("content", workspaceId);
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
