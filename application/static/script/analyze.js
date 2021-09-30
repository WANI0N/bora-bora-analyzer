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
  for(i = 0;i < maskElementsHandles.length;i++){
    // maskElementsHandles[i].classList.remove("visible");
    maskElementsHandles[i].classList.add("hidden");
  }      
}

window.onscroll=function(e){ reOffset(); }
window.onresize=function(e){ reOffset(); }

var priceIndicator = document.getElementById('priceIndicator');
var XLine = document.getElementById('XLine');
var dateIndicator = document.getElementById('dateIndicator');
var YLine = document.getElementById('YLine');

var maskElementsHandles = [
  priceIndicator,
  XLine,
  dateIndicator,
  YLine
]

reOffset()




document.addEventListener('mousemove', (event) => {  
  // console.log(`Mouse X: ${event.clientX}, Mouse Y: ${event.clientY}`);
  if (event.clientX > rect.left && event.clientX < rect.right && event.clientY > rect.top && event.clientY < rect.bottom){
    hide = true
    for(i = 0;i < myGraph.dataPointsCoor.length;i++){
      if (Math.abs(event.clientX - (rectWidth*myGraph.dataPointsCoor[i]['x'] + offsetX)) < rectWidth/150 && Math.abs(event.clientY - (rectHeight*myGraph.dataPointsCoor[i]['y'] + offsetY)) < rectHeight/150){
        // priceIndicator.style.top = (event.clientY-20) + 'px';
        priceIndicator.style.top = (event.clientY-(rectHeight/30)) + 'px';
        priceIndicator.style.left = (offsetX + rectWidth*0.01 ) + 'px';
        priceIndicator.innerText = myGraph.dataPointsCoor[i]['price']
        
        dateIndicator.style.left = (event.clientX-(rectWidth/30)) + 'px';
        dateIndicator.style.top = (offsetY + rectHeight*0.92) + 'px';
        dateIndicator.innerText = myGraph.dataPointsCoor[i]['date'].substring(5, 10)
        
        priceIndicator.style['font-size'] = rectWidth/30 + 'px';
        dateIndicator.style['font-size'] = rectWidth/30 + 'px';

        XLine.style.left = offsetX+rectWidth*0.08 + 'px';
        XLine.style.top = event.clientY + 'px';
        XLine.style.width = rectWidth*myGraph.dataPointsCoor[i]['x']-rectWidth*0.084 + 'px';

        // YLine.style.top = event.clientY + 'px';
        YLine.style.top = rectHeight*myGraph.dataPointsCoor[i]['y'] + offsetY + 'px';
        YLine.style.left = event.clientX + 'px';
        YLine.style.height = rectHeight*0.892-rectHeight*myGraph.dataPointsCoor[i]['y'] + 'px';

        for(var ci = 0;ci < maskElementsHandles.length;ci++){
          maskElementsHandles[ci].classList.remove("hidden");
          maskElementsHandles[ci].classList.add("visible");
        }
        hide = false
      break
      }
    }
    if (hide){
      for(i = 0;i < maskElementsHandles.length;i++){
        maskElementsHandles[i].classList.remove("visible");
        maskElementsHandles[i].classList.add("hidden");
      }
    }
  }
});