


class DB_Graph{
    constructor(canvas,data){
        this.canv = canvas
        this.data = data
        this.ctx = this.canv.getContext("2d")
        this.strokeStyle = "rgb(195,195,195)"
        
        this.fillStyle = "rgb(46,46,46)";
        this.ctx.strokeStyle = this.strokeStyle
        this.yMarkCount = 5;
        // this.xMarkCount = 7;
        this.ctx.fillStyle = this.fillStyle;
        var img = new Image();   // Create new img element
        img.src = 'static/images/arrow-up.png'; // Set source path
        this.arrowUpImg = img
        var img = new Image();   // Create new img element
        img.src = 'static/images/arrow-down.png'; // Set source path
        this.arrowDownImg = img
        var img = new Image();   // Create new img element
        img.src = 'static/images/equal-sign.png'; // Set source path
        this.equalSignImg = img
    }
    drawBase(){
        this.ctx.clearRect(0, 0, this.canv.width, this.canv.height);
        // this.ctx.fillRect(0,0,this.canv.width,this.canv.height);
        // this.ctx.fillStyle = this.strokeStyle;
        this.ctx.lineWidth = 1;
        //drawing y axis, vertical
        this.ctx.beginPath();
        // this.ctx.moveTo(this.canv.width*0.04, this.canv.height*0.12);
        this.ctx.moveTo(this.canv.width*0.04, this.canv.height*0.01);
        this.ctx.lineTo(this.canv.width*0.04, this.canv.height*0.86);
        this.ctx.stroke();
        //drawing x axis, horizontal
        this.ctx.beginPath();
        this.ctx.moveTo(this.canv.width*0.04, this.canv.height*0.86);
        this.ctx.lineTo(this.canv.width*0.96, this.canv.height*0.86);
        this.ctx.stroke();
        //declare axis positioning
        this.xAxisRange = [this.canv.width*0.04,this.canv.width*0.96];
        // this.yAxisRange = [this.canv.height*0.12,this.canv.height*0.86];
        this.yAxisRange = [this.canv.height*0.01,this.canv.height*0.86];
        this.ctx.fillStyle = this.strokeStyle;
        this.ctx.textAlign = "center";
        //insert title
        // this.ctx.font = Math.floor(this.canv.width/71.6 ).toString() + "px Arial";
        // this.ctx.fillText(this.title, this.canv.width*0.5, this.canv.height*0.1);
    }
    drawDataToAxis(){
        //y axis
        this.ctx.font = Math.floor(this.canv.width/81.6 ).toString() + "px Arial";
        let xAxisOffSet = this.canv.width/55;
        
        let xCoor = this.xAxisRange[0]-xAxisOffSet;
        // let diff = this.canv.height/5.57;
        let diff = (this.yAxisRange[1]-this.yAxisRange[0])/4.3;

        this.priceIndicators = this.convertPriceData()
        
        for(var i = 0; i < this.yMarkCount; i++){
            this.ctx.fillText(this.priceIndicators[i], xCoor, this.yAxisRange[1]-diff*i);
            this.ctx.fillText(this.priceIndicators[i], this.xAxisRange[1]+xAxisOffSet, this.yAxisRange[1]-diff*i);
        }
        
        //x axis
        
        xAxisOffSet = canv.width/31;
        
        let pixelRange = Math.abs(this.xAxisRange[0]-this.xAxisRange[1]-xAxisOffSet);
        
        this.daysRange = MyDate.getDiff([this.data[0]['date'],this.data[ this.data.length-1 ]['date']]);
        
        let xMarkCount, lastDate, lastDate2, dayDiff, ckDate
        xMarkCount = 10
        dayDiff = Math.ceil(this.daysRange/(xMarkCount-1));
        lastDate = this.data[ 0 ]['date']
        for (i = 0;i < 5;i++){
            lastDate2 = MyDate.addDays(this.data[ this.data.length-1 ]['date'],dayDiff*(xMarkCount-1),false)
            ckDate = MyDate.getDiff([lastDate,lastDate2],false)
            if (ckDate < 0){
                break
            }
            xMarkCount += -1
        }
        // dayDiff = Math.ceil(this.daysRange/(xMarkCount-1));
        this.xMarkCount = xMarkCount+1
        dayDiff = Math.ceil(this.daysRange/(this.xMarkCount-1));




        // this.xMarkCount = 10
        // let dayDiff = Math.ceil(this.daysRange/(this.xMarkCount-1));
        
        
        
        let pixelDiff = pixelRange/this.xMarkCount;
        
        
        // let backWardsIndex
        let yAxisOffSet = canv.height/10;
        let yCoor = this.yAxisRange[1]+yAxisOffSet
        let text, onGraphDayStart, onGraphDayEnd
        
        for(i = 0;i < this.xMarkCount;i++){
            // backWardsIndex = this.data.length-1-i
            text = MyDate.addDays(this.data[ this.data.length-1 ]['date'],dayDiff*i,false)
            if (i == 0){
                onGraphDayStart = text
            }else if (i == this.xMarkCount-1){
                onGraphDayEnd = text
            }
            this.ctx.fillText(text, this.xAxisRange[0]+(pixelDiff*i)+xAxisOffSet, yCoor);
        }
        this.daysRangeGraph = MyDate.getDiff([onGraphDayStart,onGraphDayEnd]);
        
        
    }
    convertPriceData(){
        let values = [];
        for(var i = 0; i < this.data.length; i++) {
            values.push(this.data[i]['diff_perc']);
        }
        let maxPrice = Math.max(...values);
        let minPrice = Math.min(...values);
        this.priceRange = Math.abs(maxPrice-minPrice)
        let diff;
        let returnArr = [];
        if (maxPrice > minPrice){
            diff = (maxPrice-minPrice)/3;
            let middle = (maxPrice-minPrice)/2+minPrice;
            returnArr = [
                middle-diff*2,
                middle-diff*1,
                middle,
                middle+diff*1,
                middle+diff*2,
            ];
        }else{
            diff = maxPrice/2;
            returnArr = [
                maxPrice-diff*2,
                maxPrice-diff,
                maxPrice,
                maxPrice+diff,
                maxPrice+diff*2
            ];
        }
        returnArr.forEach(function (item, index) {
            returnArr[index] = item.toFixed(2);
        });
        return returnArr
    }
    drawDataToChart(){
        // this.xAxisRange = [this.canv.width*0.04,this.canv.width*0.96];
        // this.yAxisRange = [this.canv.height*0.12,this.canv.height*0.86];
        //y Axis
        // this.priceRange
        let pixelRange = Math.abs(this.yAxisRange[1]-this.yAxisRange[0])
        let maxPrice = Math.max(...this.priceIndicators);
        let minPrice = Math.min(...this.priceIndicators);
        let priceRange = Math.abs( maxPrice-minPrice )
        this.priceMid = priceRange/2+minPrice
        let pixelPerAmount = pixelRange/priceRange
        let adjustedPrice, x, y, value, backWardsIndex
        let xAxisOffSet = canv.width/31;
        this.dataPointsCoor = []

        // let xPixelRange = Math.abs( this.xAxisRange[1]-this.xAxisRange[0] )
        // xPixelRange = xPixelRange-(xAxisOffSet)
        let xPixelRange = Math.abs( this.xAxisRange[1]-this.xAxisRange[0]-xAxisOffSet )
        
        // let pixelPerDay = xPixelRange/(this.data.length )
        let pixelPerDay = xPixelRange/(this.daysRangeGraph+1 )
        
        //draw 0 line + gradient
        adjustedPrice = 0-minPrice
        y = adjustedPrice*pixelPerAmount
        y = this.yAxisRange[1]-y
        let w = this.xAxisRange[1]-this.xAxisRange[0]
        let h = this.yAxisRange[1]-this.yAxisRange[0]
        var gradient = this.ctx.createLinearGradient(0,y-(h/2),0,y+(h/2));
        gradient.addColorStop(0, 'rgba(56, 33, 33, 0.976)');
        gradient.addColorStop(.5, 'rgba(33, 35, 56, 0.976)');
        gradient.addColorStop(1, 'rgba(33, 56, 33, 0.976)');
        this.ctx.fillStyle = gradient
        this.ctx.fillRect(this.xAxisRange[0],this.yAxisRange[0],w,h);
        //0 line
        this.ctx.strokeStyle = "blue"
        this.ctx.fillStyle = "blue"
        this.ctx.beginPath();
        this.ctx.moveTo(this.xAxisRange[0], y);
        this.ctx.lineTo(this.xAxisRange[1], y);
        this.ctx.stroke();
        this.ctx.closePath();
        this.ctx.strokeStyle = this.strokeStyle
        this.ctx.fillStyle = this.fillStyle;
        
        //draw data line
        this.ctx.strokeStyle = "yellow"
        this.ctx.beginPath();
        let arcRadius = canv.width/450
        for(var i = 0; i < this.data.length; i++) {
            backWardsIndex = this.data.length-1-i
            value = this.data[backWardsIndex]['diff_perc']
            adjustedPrice = value-minPrice
            y = adjustedPrice*pixelPerAmount
            y = this.yAxisRange[1]-y
            x = this.xAxisRange[0]+(pixelPerDay*i)+xAxisOffSet
            x = x*0.985 // no idea why there's incrementing offset, but this fixed it
            
            if (i == 0){
                this.ctx.moveTo(x, y);
            }else{
                this.ctx.lineTo(x, y);
            }
            this.dataPointsCoor.push({
                "x":x/this.canv.width,
                "y":y/this.canv.height,
                "_x":x,
                "_y":y,
                "data":this.data[backWardsIndex]
            })
        }
        this.ctx.stroke();
        this.ctx.closePath();
        this.ctx.fillStyle = this.fillStyle;
        
        for(i = 0; i < this.dataPointsCoor.length; i++){
            backWardsIndex = this.data.length-1-i
            value = this.data[backWardsIndex]['diff_perc']
            if (value > 0){
                this.ctx.fillStyle = "green";
                this.ctx.strokeStyle = "green";
            }else if (value < 0){
                this.ctx.fillStyle = "red";
                this.ctx.strokeStyle = "red";
            } else {
                this.ctx.fillStyle = "blue";
                this.ctx.strokeStyle = "blue";
            }
            this.ctx.beginPath();
            this.ctx.arc(this.dataPointsCoor[i]['_x'],this.dataPointsCoor[i]['_y'],arcRadius,0, 2 * Math.PI)
            this.ctx.fill();
            this.ctx.stroke();
        }
        this.ctx.strokeStyle = this.strokeStyle

    }
    drawLinePointer(n = 0){
        this.currentPointer = n
        if (this.currentPointer == 0){
            return
        }
        let data = this.dataPointsCoor[n]
        this.ctx.beginPath();
        // console.log( data["_x"],data["_y"],this.yAxisRange[1] )
        this.ctx.moveTo(data["_x"], data["_y"]);
        this.ctx.lineTo(data["_x"], this.yAxisRange[1]);
        this.ctx.stroke();
        this.ctx.closePath();
    }
    statsPoint(n){
        let obj = this.dataPointsCoor[n]
        let data = obj['data']
        // let primaryProductCount = this.dataPointsCoor[this.dataPointsCoor.length-1].data.productCount
        let x, y, w, h, img, pricePrefix
        
        y = obj['_y']
        w = this.canv.width/8
        let xVector = (obj['_x']+w+5 > this.canv.width*.9) ? "-" : "+"
        x = (xVector == "+") ? obj['_x']+this.canv.width/340 : obj['_x']-this.canv.width/7.8
        h = this.canv.height/3
        if (data['diff_perc'] < this.priceMid){
            y += -h
        }
        pricePrefix = ''
        if (data['diff_perc'] > 0){
            pricePrefix = '+'
        }
        img = (data['diff_perc'] > 0) ? this.arrowUpImg : (data['diff_perc'] < 0) ? this.arrowDownImg : this.equalSignImg
        
        //drawing rectanle
        this.ctx.fillStyle = "rgb(150,150,150)"
        let rectCoor = {
            "x":x,
            "y":y,
            "w":w,
            "h":h,
        }
        this.ctx.beginPath();
        this.ctx.rect(x, y, w, h);
        
        this.ctx.fill();
        this.ctx.stroke();
        // this.ctx.closePath();
        //drawing pointer
        

        //drawing image
        
        y += h/20
        w = w/8
        h = h/3
        // x = (xVector == "+") ? x+w/3 : x-w/3
        x = x+w/3
        this.ctx.drawImage(img, x, y, w, h);
        //drawing data
        let fonts = {
            'top':{
                'tag':"italic " + Math.floor(this.canv.width/101.6 ).toString() + "px Arial",
                'value':"bold " + Math.floor(this.canv.width/91.6 ).toString() + "px Arial"
            },
            'bottom':{
                'tag':"italic " + Math.floor(this.canv.width/121.6 ).toString() + "px Arial",
                'value':"bold " + Math.floor(this.canv.width/101.6 ).toString() + "px Arial"
            }
        }
        
        //drawing top data tags
        this.ctx.fillStyle = this.fillStyle
        x = rectCoor['x']+rectCoor['w']/1.8
        // x = (xVector == "+") ? rectCoor['x']+rectCoor['w']/1.8 : rectCoor['x']-rectCoor['w']/1.8
        
        y = rectCoor['y']+rectCoor['h']/5
        this.ctx.textAlign = "right";
        this.ctx.font = fonts.top.tag
        this.ctx.fillText('date: ',x,y)
        y += rectCoor['h']/5
        this.ctx.fillText('difference: ',x,y)
        
        //drawing top data values
        y = rectCoor['y']+rectCoor['h']/5
        this.ctx.textAlign = "left";
        this.ctx.font = fonts.top.value
        this.ctx.fillText(data['date'],x,y)
        y += rectCoor['h']/5
        this.ctx.fillText(pricePrefix + data['diff_perc'] + '%',x,y)
        
        //drawing bottom data tags
        // x = (xVector == "+") ? rectCoor['x']+rectCoor['w']/1.8 : rectCoor['x']-rectCoor['w']/1.8
        x = rectCoor['x']+rectCoor['w']/1.8
        y = rectCoor['y']+rectCoor['h']/1.62
        this.ctx.textAlign = "right";
        this.ctx.font = fonts.bottom.tag
        this.ctx.fillText('products on day: ',x,y)
        y += rectCoor['h']/6
        this.ctx.fillText('products total: ',x,y)
        y += rectCoor['h']/6
        this.ctx.fillText('% of all prod: ',x,y)
        //drawing bottom data values
        y = rectCoor['y']+rectCoor['h']/1.62
        this.ctx.textAlign = "left";
        this.ctx.font = fonts.bottom.value
        this.ctx.fillText(data.count,x,y)
        y += rectCoor['h']/6
        this.ctx.fillText(data.total,x,y)
        y += rectCoor['h']/6
        this.ctx.fillText(data.perCent + '%',x,y)

    }
}