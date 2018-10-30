var nodes = null;
var edges = null;
var network = null;
var seed = 2; // Want the nodes to be rendered the same way every time (rather than based off a random seed)
var data = {};

var options = {
    locale: 'en',
    interaction: {
        multiselect: true,
    },
    physics:{
	enabled: true,
	hierarchicalRepulsion: {
	    centralGravity: 2.0,
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
            type: "continuous"
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

	    document.getElementById('cancelButton').onclick = cancelEdit.bind(this,callback);
	    document.getElementById('network-popUp').style.display = 'block';
	},
        // TODO: Add support for adding labels to edges -> https://stackoverflow.com/questions/37661543/vis-js-network-add-label-to-edge
	addEdge: function (data, callback) {
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

function clearPopUp() {
    document.getElementById('saveButton').onclick = null;
    document.getElementById('cancelButton').onclick = null;
    document.getElementById('network-popUp').style.display = 'none';
}

function cancelEdit(callback) {
    clearPopUp();
    callback(null);
}

function postGraphData(methodName, data) {
    // TODO: Figure out if this bit is still needed
    data.title = document.getElementById('node-ip').value;
    data.label = document.getElementById('node-hostname').value;
    data.group = document.getElementById('node-type').value;

    var xhttp = new XMLHttpRequest();
    xhttp.open("POST", methodName, true);
    xhttp.setRequestHeader("Content-type", "application/json");

    xhttp.onreadystatechange = function() {
     	if (this.readyState == 4 && this.status == 200) {
	    refreshGraph();
	}
    };

    xhttp.send(JSON.stringify(data, undefined, 2));
}

function saveNode(data, callback) {
    clearPopUp();
    callback(data);
    postGraphData("upsert_node", data);
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

	    // TODO: Populate popupDiv with details of the clicked node before making it visible
	    popupDiv.style.left = properties.pointer.DOM.x + 'px';
     	    popupDiv.style.top = properties.pointer.DOM.y + 'px';
     	    popupDiv.style.display = 'block';
	} else {
	    popupDiv.style.display = 'none'; // Hide the pop-up if it's visible
	}
    });

    //network.on('click', function(params) {
	// Check if you clicked on a node; if so, display the title (if any) in a popup
	//network.interactionHandler._checkShowPopup(params.pointer.DOM);
//alert('HERE!');
    //}

    // for (let nodeId in network.body.nodes) {
    // 	if (nodes.hasOwnProperty(nodeId)) {
    //  	    network.body.nodes[nodeId].on('click', function(params) {
    // 		alert('Node clicked!')
	    
    // 	    // TODO: Get this working
    // 	    var popupDiv = document.getElementById('node-popup');

    // 	    // TODO: Remove
    // 	    params.event = "[original event]";
    // 	    console.log("Pointer: " + JSON.stringify(params.pointer.DOM));
    // 	    popupDiv.style.left = params.pointer.DOM.x + 'px';
    // 	    popupDiv.style.top = params.pointer.DOM.y + 'px';
    // 	    popupDiv.style.visibility='visible';
    // 	    popupDiv.style.display = 'inline-block';
	
    // 	    $(popupDiv).offset({ top: mousePos.y, left: mousePos.x });
    // 	    var ids = properties.nodes;
    // 	    var clickedNodes = data.nodes.get(ids);
    // 	    console.log('clicked nodes:', clickedNodes);
    // 	    }
    //     });
    // }

    //network.on( 'click', function(params) {
	// TODO: Get this working
	// var popupDiv = document.getElementById('node-popup');

	// // TODO: Remove
	// params.event = "[original event]";
	// console.log("Pointer: " + JSON.stringify(params.pointer.DOM));
	// popupDiv.style.left = params.pointer.DOM.x + 'px';
	// popupDiv.style.top = params.pointer.DOM.y + 'px';
	// popupDiv.style.visibility='visible';
	// popupDiv.style.display = 'inline-block';
	
	//$(popupDiv).offset({ top: mousePos.y, left: mousePos.x });
	//var ids = properties.nodes;
	//var clickedNodes = data.nodes.get(ids);
	//console.log('clicked nodes:', clickedNodes);
    //});

    return network;
}

function refreshGraph() {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() {
	// TODO: Add check on if the version number has increased
        if (this.readyState == 4 && this.status == 200) {
            var inputData = JSON.parse(xmlHttp.responseText);

	    var data = {
                nodes: getNodeData(inputData['nodes']),
                edges: getEdgeData(inputData['nodes'])
	    }
		
	    var container = document.getElementById('mynetwork');
	    network = create_network(container, data, options);

	    // TODO: put back once the version check has been added
	    // setTimeout(refreshGraph, 100);
	}
    };

    xmlHttp.open( "GET", "graph_data", true ); // true for asynchronous request
    xmlHttp.send();
}

function getNodeData(data) {
    var networkNodes = [];

    data.forEach(
	function(elem, index, array) {
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
