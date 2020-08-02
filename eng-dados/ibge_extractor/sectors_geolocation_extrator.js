// Acess https://censo2010.ibge.gov.br/sinopseporsetores/?nivel=st
// Debug cartograma.js in line 9
// Select the desired city
// Execute the code bellow on console
// Save the console history in a file in ../../volume_***/maps/sectors_***.log

var MyShapes = {};
var id = nml_polygon.getId();
var situacao = nml_polygon.getSituation();
var paths = nml_polygon.getMyPaths();
console.log(id)
var polyCoords = [];
for (var i in paths) {
    polyCoords.push(paths[i]);
    for (var j in paths[i]){
        console.log(paths[i][j]['lat'],paths[i][j]['lng'])
    }
}
MyShapes[id] = JSON.stringify(polyCoords);
while (nml_polygon != null) {
    var id = nml_polygon.getId();
    var situacao = nml_polygon.getSituation();
    var paths = nml_polygon.getMyPaths();
    console.log(id)
    var polyCoords = [];
    for (var i in paths) {
        polyCoords.push(paths[i]);
        for (var j in paths[i]){
            console.log(paths[i][j]['lat'],paths[i][j]['lng'])
        }
    }
    MyShapes[id] = polyCoords;
    nml_polygon = nml.googleExport();
}