let graphHandle=document.getElementById("tab-graph");
let tableHandle=document.getElementById("tab-table");
let graph=document.getElementById("dbGraphCanvas");
let table=document.getElementById("dbTableCanvas");
function statsSwitchTab(target){
    if (target == "graph"){
        graphHandle.classList.add("tab-selector-item-active");
        tableHandle.classList.remove("tab-selector-item-active");

        graph.classList.remove("content-hidden");
        graph.classList.add("content-visible");
        
        table.classList.remove("content-visible");
        table.classList.add("content-hidden");
    }
    if (target == "table"){
        tableHandle.classList.add("tab-selector-item-active");
        graphHandle.classList.remove("tab-selector-item-active");

        table.classList.remove("content-hidden");
        table.classList.add("content-visible");
        
        graph.classList.remove("content-visible");
        graph.classList.add("content-hidden");
    }
}




// function to retrieve an image
function loadImage(url) {
    return new Promise((fulfill, reject) => {
      let imageObj = new Image();
      imageObj.onload = () => fulfill(imageObj);
      imageObj.src = url;
    });
}

class DB_Graph2{
    constructor(canvas,data){
        this.canv = canvas
        this.data = data
        this.ctx = this.canv.getContext("2d")
        let wrapper=document.getElementById("content-wrapper");
        this.canv.width = wrapper.offsetWidth
        this.canv.height = data.length*101
        this.ctx.clearRect(0, 0, this.canv.width, this.canv.height);
        
    }
    draw(){
        Promise.all([
            loadImage('static/images/arrow-up.png'),
            loadImage('static/images/arrow-down.png'),
            loadImage('static/images/equal-sign.png')
        ])
        .then((images) => {
            this.arrowUpImg = images[0]
            this.arrowDownImg = images[1]
            this.equalSignImg = images[2]
            let x, y, w, h, pricePrefix, rowData, img
            
            this.ctx.fillStyle = "rgba(202, 199, 31, 0.63)"
            x = 0
            y = 0
            w = this.canv.width
            h = 100
            let gradient, c
            for(var i = 0; i < this.data.length; i++) {
                rowData = this.data[i]
                img = (rowData.diff_perc > 0) ? this.arrowUpImg : (rowData.diff_perc < 0) ? this.arrowDownImg : this.equalSignImg


                gradient = this.ctx.createLinearGradient(0,0,w,0);
                gradient.addColorStop(0, 'rgba(197, 188, 188, 0.739)')
                c = (rowData.diff_perc > 0) ? 'rgba(68, 71, 117, 0.976)' : 'rgba(117, 68, 68, 0.976)'
                gradient.addColorStop(.25, c)
                gradient.addColorStop(1, 'rgba(0,0,0)')
                
                this.ctx.fillStyle = gradient
                this.ctx.fillRect(x,y,w,h);

                this.ctx.fillStyle = "rgba(202, 199, 31, 0.63)"

                this.ctx.drawImage(img, x, y, w/3.6, h);
                pricePrefix = ''
                if (rowData.diff_perc > 0){
                    pricePrefix = '+'
                }
                //date
                this.ctx.textAlign = "left";
                this.ctx.font = "bold " + Math.floor(this.canv.width/15.6 ).toString() + "px Arial";
                // this.ctx.fillText(rowData.date,x+w/4.1,y+h/4.5);
                this.ctx.fillText(rowData.date,x+w/3.8,y+h/4.5);
                
                //tags
                this.ctx.textAlign = "right";
                this.ctx.font = "italic " + Math.floor(this.canv.width/25 ).toString() + "px Arial";
                this.ctx.fillText('difference to mean: ',x+w/1.5,y+h/2.6);

                this.ctx.textAlign = "right";
                this.ctx.font = "italic " + Math.floor(this.canv.width/25 ).toString() + "px Arial";
                this.ctx.fillText('products on day: ',x+w/1.5,y+h/1.9);
                
                this.ctx.textAlign = "right";
                this.ctx.font = "italic " + Math.floor(this.canv.width/25 ).toString() + "px Arial";
                this.ctx.fillText('products total: ',x+w/1.5,y+h/1.4);
                
                this.ctx.textAlign = "right";
                this.ctx.font = "italic " + Math.floor(this.canv.width/25 ).toString() + "px Arial";
                this.ctx.fillText('% of all products: ',x+w/1.5,y+h/1.1);

                //data
                this.ctx.textAlign = "left";
                this.ctx.font = "bold " + Math.floor(this.canv.width/23 ).toString() + "px Arial";
                this.ctx.fillText(rowData.count,x+w/1.5,y+h/1.9);
                
                this.ctx.textAlign = "left";
                this.ctx.font = "bold " + Math.floor(this.canv.width/23 ).toString() + "px Arial";
                this.ctx.fillText(rowData.total,x+w/1.5,y+h/1.4);
                
                this.ctx.textAlign = "left";
                this.ctx.font = "bold " + Math.floor(this.canv.width/23 ).toString() + "px Arial";
                this.ctx.fillText(rowData.perCent + '%',x+w/1.5,y+h/1.1);

                //difference
                this.ctx.textAlign = "left";
                this.ctx.font = "bold " + Math.floor(this.canv.width/13.3 ).toString() + "px Arial";
                this.ctx.fillText(pricePrefix + rowData.diff_perc + '%',x+w/1.5,y+h/2.9);
                y += h+1
            }
        })
    }
}

let canv2=document.getElementById("dbTableCanvas");
myGraph2 = new DB_Graph2(canv2,dbGraphCanvasData);


myGraph2.draw()