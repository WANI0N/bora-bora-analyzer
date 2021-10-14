

let canv=document.getElementById("dbGraphCanvas");
myGraph = new DB_Graph(canv,dbGraphCanvasData);

let rect, offsetX, offsetY, rectWidth, rectHeight



contentWrapper = document.getElementById("content-wrapper")

rect = document.getElementById("dbGraphCanvas").getBoundingClientRect();
function reOffset(){
    
    rectWidth=rect.right-rect.left
    rectHeight=rect.bottom-rect.top
    offsetX=rect.left
    offsetY=rect.top   
    myGraph.drawBase()
    myGraph.drawDataToAxis()
    myGraph.drawDataToChart()
}
reOffset();
if (window.screen.width < 500){ // has to be after rect declaration
    statsSwitchTab("table")
}
window.onscroll=function(e){ reOffset(); }
window.onresize=function(e){ reOffset(); }


let i

// var descriptor = document.getElementById('graphDescription');

function addDescriptor(data = false){
	let str
	if (!data){
		str = "Graph displays how each of the last 6 days (Comparands) compares to data retreived on: " + dbGraphCanvasData[0]['key'] + " (Main)"
		str += ".\n"
		str += "The difference is calculated by comparing mean prices of products between two days (Main and Comparand)"
		str += ".\n"
		str += "Accuracy of the calculation depends on number of matched products between the two days"
		str += "."
	}else if (data.meanComparand !== "n/a"){
		let w1 = (data.difference > 0) ? "more expensive" : "cheaper"
		str = "On " + data.key + " the prices were " + w1 + "(" + data.difference + "%)" + " than on " + dbGraphCanvasData[0]['key']
		str += ".\n"
		str += "Out of " + dbGraphCanvasData[0]['productCount'] + " products found on " + dbGraphCanvasData[0]['key'] + ", " + data.matchCount + " were also present on " + data.key
		str += ".\n"
		str += "Mean price of all matched products is " + data.meanComparand + " for Comparand (" + data.key + ") vs " + data.meanMain + " for Main (" + dbGraphCanvasData[0]['key'] + ")"
		str += "."
	}else{
		str = 'Blue circle indicates most recent product pull'
		str += ".\n"
		str += "Difference is equal to 0"
		str += ".\n"
		str += dbGraphCanvasData[0]['productCount'] + " products were found"
		str += "."
	}
	return str
}

// descriptor.innerText = addDescriptor()
var targetOffset = rectWidth/450
let str,adjustedMouseX,adjustedMouseY,pointX,pointY, currentLinePointer

contentWrapper.scroll({
	left: myGraph.canv.width
})

document.addEventListener('mousemove', (event) => { 
    // if (event.clientX > rect.left && event.clientX < rect.right && event.clientY > rect.top && event.clientY < rect.bottom){
    if (event.pageX > rect.left && event.pageX < rect.right && event.pageY > rect.top && event.pageY < rect.bottom){
		myGraph.drawBase()
		myGraph.drawDataToAxis()
		myGraph.drawDataToChart()
		// myGraph.drawLinePointer(currentLinePointer)
		for (i = 0;i < myGraph.dataPointsCoor.length;i++){
            // adjustedMouseX = event.clientX-offsetX
            // adjustedMouseY = event.clientY-offsetY
            adjustedMouseX = event.pageX-offsetX
            adjustedMouseY = event.pageY-offsetY
            // pointX = rectWidth*myGraph.dataPointsCoor[i]['x']
            pointX = rectWidth*myGraph.dataPointsCoor[i]['x']-contentWrapper.scrollLeft
            pointY = rectHeight*myGraph.dataPointsCoor[i]['y']
            if (Math.abs(adjustedMouseX-pointX) < targetOffset && Math.abs(adjustedMouseY-pointY) < targetOffset){
            // if (Math.abs((rectWidth*myGraph.dataPointsCoor[i]['x'] + offsetX) - event.clientX) < targetOffset && Math.abs((rectHeight*myGraph.dataPointsCoor[i]['y'] + offsetY) - event.clientY) < targetOffset){

				// indicator.classList.remove("hidden");
                // indicator.classList.add("visible");
				// descriptor.innerText = addDescriptor(myGraph.dataPointsCoor[i].data)
                
                // hide = false
				myGraph.statsPoint(i)
				// currentLinePointer = i
				// myGraph.drawLinePointer(currentLinePointer)
				break
            }
        }
        // if (hide){
		// 	// descriptor.innerText = addDescriptor()
		// 	// myGraph.drawBase()
		// 	// myGraph.drawDataToAxis()
		// 	// myGraph.drawDataToChart()
        //     // indicator.classList.add("hidden");
        //     // indicator.classList.remove("visible");
        // }
    
    }else{
		currentLinePointer = 0
	}
})

