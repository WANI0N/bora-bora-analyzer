
const plusSign = document.getElementById('plusSign')
const plusSignPressMessage = document.getElementById('plusSignPressMessage')

plusSignBlock = false
plusSign.addEventListener('click', async () => {
  if (plusSignBlock){
    return
  }  
  
  if (jsPayload['tmp_token']){
    let location, url, settings
    location = window.location.hostname;
    // url = `http://${location}:5000/api/addAlert/`
    url = `https://${location}/api/addAlert/`
    settings = {
        method: 'POST',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            "token":jsPayload.tmp_token,
            "product_id":jsPayload.product_id,
            "innitial_state":(graphData.tableData[0].active == true) ? false : true
        })
    }
    try{
      const response = await fetch(url,settings)
      const jsonResp = await response.json()
      if (!jsonResp.addAlertStatus){
        if (jsonResp.reason){
          plusSignPressMessage.innerText = "Maximum number of alerts has been reached."  
        }else{
          plusSignPressMessage.innerText = "Something went wrong, please refresh the page and try again."  
        }
      }
    }catch{
      plusSignPressMessage.innerText = "Something went wrong, please refresh the page and try again."
    }
  }
  plusSign.classList.remove('sign-active')
  plusSignPressMessage.style.display = "block"
  plusSignBlock = true
})

let canv=document.getElementById("testCanvas");
myGraph = new Graph(canv,graphData['data'],graphData['title']);

myGraph.drawBase()
myGraph.drawPrices()
myGraph.drawDates()
myGraph.drawData()

let rect, offsetX, offsetY
let i, hide
function reOffset(){
  rect = document.getElementById("testCanvas").getBoundingClientRect();
  rectWidth=rect.right-rect.left
  rectHeight=rect.bottom-rect.top
  offsetX=rect.left
  offsetY=rect.top   
}

window.onscroll=function(e){ reOffset(); }
window.onresize=function(e){ reOffset(); }


reOffset()



let mouseX, mouseY, diff, xDiff, yDiff, diffSum, targetIndex
document.addEventListener('mousemove', (event) => {  
  // console.log(`Mouse X: ${event.clientX}, Mouse Y: ${event.clientY}`);
  if (event.clientX > rect.left && event.clientX < rect.right && event.clientY > rect.top && event.clientY < rect.bottom){
    myGraph.drawBase()
    myGraph.drawPrices()
    myGraph.drawDates()
    myGraph.drawData()
    
    mouseX = event.clientX-offsetX
    mouseY = event.clientY-offsetY
    diff = 10000
    for(i = 0;i < myGraph.dataPointsCoor.length;i++){
      xDiff = Math.abs(rectWidth*myGraph.dataPointsCoor[i]['x']-mouseX)
      yDiff = Math.abs(rectHeight*myGraph.dataPointsCoor[i]['y']-mouseY)
      diffSum = xDiff+yDiff
      if (diffSum < diff){
        diff = diffSum
        targetIndex = i
      }
    }
    myGraph.markDataPoint(targetIndex)
  }
  else{
    myGraph.drawBase()
    myGraph.drawPrices()
    myGraph.drawDates()
    myGraph.drawData()
  }
});