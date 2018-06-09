var nodes = null;
var edges = null;
var network = null;
var data = {};
var seed = 2;

// TODO: Remove if not used
function get(url)
{
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", url, false ); // false for synchronous request
    xmlHttp.send( null );
    return xmlHttp.responseText;
}

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
    var options = {
	layout: {randomSeed:seed}, // just to make sure the layout is the same when the locale is changed
	locale: 'en',
	layout: {
	    hierarchical: {
		enabled: true,
		levelSeparation: 150,
		nodeSpacing: 100,
		treeSpacing: 200,
		blockShifting: true,
		edgeMinimization: true,
		parentCentralization: true,
		direction: 'DU',        // UD, DU, LR, RL
		sortMethod: 'directed'   // hubsize, directed
	    }
	},
	groups: {
	    ops_box: {
		color: 'grey',
		shape: 'square',
		font: {
		    size: 15,
		    color: '#ffffff'
		}
	    },
	    staging_server: {
		color: 'green',
		shape: 'diamond',
		font: {
		    size: 15,
		    color: '#ffffff'
		}
	    },
	    redirect: {
		color: 'orange',
		shape: 'diamond',
		font: {
		    size: 15,
		    color: '#ffffff'
		}
	    },
	    beacon: {
		color: 'red',
		shape: 'dot',
		font: {
		    size: 15,
		    color: '#ffffff'
		}
	    },
	    target: {
		color: 'blue',
		shape: 'square',
		font: {
		    size: 15,
		    color: '#ffffff'
		}
	    },
	    other: {
		color: 'grey',
		shape: 'dot',
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
		document.getElementById('node-id').value = data.id;
		document.getElementById('node-label').value = data.label;
		document.getElementById('node-type').value = data.group;
		// TODO: Also allow adding metadata, such as IP, protocol, etc.
		document.getElementById('saveButton').onclick = saveData.bind(this, data, callback);
		document.getElementById('cancelButton').onclick = clearPopUp.bind();
		document.getElementById('network-popUp').style.display = 'block';
	    },
	    editNode: function (data, callback) {
		// filling in the popup DOM elements
		document.getElementById('operation').innerHTML = "Edit Node";
		document.getElementById('node-id').value = data.id;
		document.getElementById('node-label').value = data.label;
		document.getElementById('node-type').value = data.group;
		document.getElementById('saveButton').onclick = saveData.bind(this, data, callback);
		document.getElementById('cancelButton').onclick = cancelEdit.bind(this,callback);
		document.getElementById('network-popUp').style.display = 'block';
	    },
	    addEdge: function (data, callback) {
		if (data.from == data.to) {
		    var r = confirm("Do you want to connect the node to itself?");
		    if (r == true) {
			callback(data);
		    }
		}
		else {
		    callback(data);
		}
	    }
	}
    };

    network = new vis.Network(container, data, options);
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

      function saveData(data,callback) {
    // TODO: Post graph data back to the server (and then save it)
    data.id = document.getElementById('node-id').value;
    data.label = document.getElementById('node-label').value;
    data.group = document.getElementById('node-type').value;

    // TODO: Cleanup
    // var xhttp = new XMLHttpRequest();
    // xhttp.open("POST", 'http://127.0.0.1:5000/update', true);
    // xhttp.setRequestHeader("Content-type", "application/json");
    // xhttp.send(JSON.stringify(data));

    clearPopUp();
    callback(data);
}

function objectToArray(obj) {
    return Object.keys(obj).map(function (key) {
        obj[key].id = key;
        return obj[key];
    });
}

function addConnections(elem, index) {
    // need to replace this with a tree of the network, then get child direct children of the element
    elem.connections = network.getConnectedNodes(index);
}

function saveGraph() {
    var nodes = objectToArray(network.getPositions());

    // TODO: Make sure that this data gets incorporated
    //     data.id = document.getElementById('node-id').value;
    //data.label = document.getElementById('node-label').value;
    //data.group = document.getElementById('node-type').value;

    nodes.forEach(addConnections);
    var xhttp = new XMLHttpRequest();
    xhttp.open("POST", 'http://127.0.0.1:5000/update', true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.onreadystatechange = function() {
	if (this.readyState == 4 && this.status == 200) {
	    setTimeout(saveGraph, 1000);
	}
    };
    xhttp.send(JSON.stringify(nodes));
}

function refreshGraph() {
    // TODO: Get working
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", 'http://127.0.0.1:5000/graph_data', false ); // false for synchronous request
    xmlHttp.send( null );
    
    var inputData = JSON.parse(xmlHttp.responseText);

    var data = {
        nodes: getNodeData(inputData),
        edges: getEdgeData(inputData)
    }

      console.log(data);

      
      var container = document.getElementById('mynetwork');

      // TODO: Get working
    //network = new vis.Network(container, data, {});
}

function getNodeData(data) {
    var networkNodes = [];

    data.forEach(function(elem, index, array) {
        networkNodes.push({id: elem.id, label: elem.id, x: elem.x, y: elem.y});
    });

    return new vis.DataSet(networkNodes);
}

function getNodeById(data, id) {
    for (var n = 0; n < data.length; n++) {
        if (data[n].id == id) {  // double equals since id can be numeric or string
            return data[n];
        }
    };

    throw 'Can not find id \'' + id + '\' in data';
}

function getEdgeData(data) {
    var networkEdges = [];

    data.forEach(function(node) {
        // add the connection
        node.connections.forEach(function(connId, cIndex, conns) {
            networkEdges.push({from: node.id, to: connId});
            let cNode = getNodeById(data, connId);

            var elementConnections = cNode.connections;

            // remove the connection from the other node to prevent duplicate connections
            var duplicateIndex = elementConnections.findIndex(function(connection) {
                return connection == node.id; // double equals since id can be numeric or string
            });


            if (duplicateIndex != -1) {
                elementConnections.splice(duplicateIndex, 1);
            };
        });
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
    setTimeout(saveGraph, 1000);
}



