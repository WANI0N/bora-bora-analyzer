
class MyDate{
    // support class, used only in this module
    static getDiff(dateStringsArr,abs=true){
        let dates = []
        for (let i = 0; i < dateStringsArr.length; i++) {
            var array = dateStringsArr[i].split('-')
            dates.push( new Date(array[0],array[1]-1,array[2]) )
        }
        const diffTime = (abs) ? Math.abs(dates[1] - dates[0]) : dates[1] - dates[0]
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24)); 
    }
    static addDays(dateString,days,trim = true){
        var array = dateString.split('-')
        var date = new Date(array[0],array[1]-1,array[2]);
        date.setDate(date.getDate() + days);
        let a
        if (trim){
            a = [ {month: '2-digit'},{day: '2-digit'}];
        } else {
            a = [ {year: 'numeric'},{month: '2-digit'},{day: '2-digit'}];
        }
        return MyDate.join(date, a, '-');
    }
    static join(t, a, s) {
        function format(m) {
           let f = new Intl.DateTimeFormat('en', m);
           return f.format(t);
        }
        return a.map(format).join(s);
     }
}

// export class Graph {
class Graph {
    constructor(canvas,data,title){
        this.canv = canvas;
        this.ctx = canv.getContext("2d");
        this.data = data;
        this.title = title
        this.fillStyle = "rgb(46,46,46)";
        this.ctx.fillStyle = this.fillStyle;
        this.strokeStyle = "rgb(195,195,195)";
        this.ctx.strokeStyle = this.strokeStyle;
        this.yMarkCount = 5;
        this.xMarkCount = 6;
    }
    drawBase(){
        
        // clear canvas
        this.ctx.clearRect(0, 0, this.canv.width, this.canv.height);
        // this.ctx.fillRect(0,0,this.canv.width,this.canv.height);
        this.ctx.fillStyle = this.strokeStyle;
        //drawing Axis
        
        this.ctx.lineWidth = 1;
        //drawing y axis, vertical
        this.ctx.beginPath();
        this.ctx.moveTo(this.canv.width*0.08, this.canv.height*0.1);
        this.ctx.lineTo(this.canv.width*0.08, this.canv.height*0.9);
        this.ctx.stroke();
        //drawing x axis, horizontal
        this.ctx.beginPath();
        this.ctx.moveTo(this.canv.width*0.08, this.canv.height*0.9);
        this.ctx.lineTo(this.canv.width*0.94, this.canv.height*0.9);
        this.ctx.stroke();
        //declare axis positioning
        this.xAxisRange = [this.canv.width*0.08,this.canv.width*0.94];
        this.yAxisRange = [this.canv.height*0.1,this.canv.height*0.9];
        //insert title
        this.ctx.font = Math.floor(this.canv.width/41.6 ).toString() + "px Arial";
        this.ctx.textAlign = "center";
        // this.ctx.strokeText(this.title, this.canv.width*0.5, this.canv.height*0.05);
        
        
        
        this.ctx.fillText(this.title, this.canv.width*0.5, this.canv.height*0.05);
        // this.ctx.fillStyle = this.fillStyle;
    }
    drawPrices(){
        //drawing price indicators to y axis
        //static numbers for offsets/fonts are adjusted for canvas input ration 5:3
        this.ctx.font = Math.floor(this.canv.width/41.6 ).toString() + "px Arial";
        let xAxisOffSet = this.canv.width/25;
        
        let xCoor = this.xAxisRange[0]-xAxisOffSet;
        let diff = this.canv.height/5.17;

        this.priceIndicators = this.convertPriceData()
        for(var i = 0; i < this.yMarkCount; i++){
            this.ctx.fillText(this.priceIndicators[i], xCoor, this.yAxisRange[1]-diff*i);
        }
    }
    convertPriceData(){
        let values = [];
        let sum = 0
        for(var i = 0; i < this.data.length; i++) {
            values.push(this.data[i]['price']);
            sum += this.data[i]['price']
        }
        this.mean = sum/this.data.length
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
    drawDates(){
        //drawing date indicators to y axis
        //static divisor numbers for offsets/fonts are adjusted for canvas input ration 5:3
        let yAxisOffSet = canv.height/20;
        // let xAxisOffSet = canv.width/9.5;
        let xAxisOffSet = this.canv.width/25
        this.xMarkCount = (this.data.length < this.xMarkCount) ? this.data.length : this.xMarkCount;
        let pixelRange = Math.abs(this.xAxisRange[0]-this.xAxisRange[1]-xAxisOffSet);
        let pixelDiff = pixelRange/this.xMarkCount;
        this.daysRange = MyDate.getDiff([this.data[0]['date'],this.data[ this.data.length-1 ]['date']]);
        let dayDiff = Math.ceil(this.daysRange/(this.xMarkCount-1));
        this.finalDatesArray = []
        let currentX, text;
        for(var i = 0; i < this.xMarkCount; i++) {
            this.finalDatesArray.push( MyDate.addDays(this.data[ this.data.length-1 ]['date'],dayDiff*i,false) )
            
            text = MyDate.addDays(this.data[ this.data.length-1 ]['date'],dayDiff*i)
            currentX = i*pixelDiff+this.xAxisRange[0];
            currentX += xAxisOffSet;
            this.ctx.fillText(text, currentX, this.yAxisRange[1]+yAxisOffSet);
        }
    }
    drawData(){
        
        //draw 0 line + gradient
        let adjustedPrice, x,y
        // let maxPrice = Math.max(...this.priceIndicators);
        let pixelRange = Math.abs( this.yAxisRange[1]-this.yAxisRange[0] )
        let maxPrice = Math.max(...this.priceIndicators);
        let minPrice = Math.min(...this.priceIndicators);
        let priceRange = Math.abs( maxPrice-minPrice )
        // let adjustedPrice = price-minPrice
        let pixelPerAmount = pixelRange/priceRange
        // let y = adjustedPrice*pixelPerAmount
        adjustedPrice = this.mean-minPrice
        y = adjustedPrice*pixelPerAmount
        y = this.yAxisRange[1]-y
        // console.log(y)
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

        
        let pathing = []
        this.dataPointsCoor = []
        this.ctx.strokeStyle = "yellow";
        this.ctx.beginPath();
        for(var i = 0;i < this.data.length;i++){
            x = this.retreiveXforDataPoint(this.data[i]['date'])
            y = this.retreiveYforDataPoint(this.data[i]['price'])
            

            if (i == 0){
                this.ctx.moveTo(x, y);
            }else{
                this.ctx.lineTo(x, y);
            }
            
            this.dataPointsCoor.push({
                "x":x/this.canv.width,
                "y":y/this.canv.height,
                "date":this.data[i]['date'],
                "price":this.data[i]['price']
            })
            pathing.push({
                "x":x,
                "y":y
            })
        }
        this.ctx.stroke();
        this.ctx.closePath();
        // console.log(canv.width)
        
        // this.ctx.strokeStyle = "rgb(2, 230, 82)";
        // this.ctx.strokeStyle = "yellow";
        let radius, estimate, max
        estimate = canv.width/(this.data.length*3.2)
        max = canv.width/100
        radius = estimate > max ? max : estimate
        for(i = 0; i < pathing.length; i++){
            this.ctx.fillStyle = this.data[i]['active'] ? "rgba(31, 195, 245, 0.87)" : "rgba(245, 31, 138, 0.87)"
            this.ctx.strokeStyle = this.data[i]['active'] ? "rgba(31, 195, 245, 0.87)" : "rgba(245, 31, 138, 0.87)"
            // this.ctx.fillStyle = this.data[i]['active'] ? "rgba(31, 195, 245, 0.555)" : "rgba(245, 31, 138, 0.555)"
            // this.ctx.strokeStyle = this.data[i]['active'] ? "rgba(31, 195, 245, 0.555)" : "rgba(245, 31, 138, 0.555)"
            this.ctx.beginPath();
            
            // this.ctx.arc(pathing[i]['x'],pathing[i]['y'],canv.width/250,0, 2 * Math.PI)
            this.ctx.arc(pathing[i]['x'],pathing[i]['y'],radius,0, 2 * Math.PI)
            
            this.ctx.fill();
            this.ctx.stroke();
            
        }
        this.dataCoords = pathing
        this.ctx.strokeStyle = this.strokeStyle;
        
    }
    retreiveXforDataPoint(date){
        let pixelRange = Math.abs( this.xAxisRange[1]-this.xAxisRange[0] )
        let xAxisOffSet = this.canv.width/25
        pixelRange += -xAxisOffSet
        let daysRange = MyDate.getDiff([ this.finalDatesArray[0] , this.finalDatesArray[ this.finalDatesArray.length-1 ] ])
        let adjustedDate = MyDate.getDiff([ this.finalDatesArray[0] , date ])
        let pixelPerDay = pixelRange/(daysRange+1 )
        let x = adjustedDate*pixelPerDay
        // let xAxisOffSet = canv.width/18;
        // let xAxisOffSet = canv.width/9.5;
        x = this.yAxisRange[0]+x+xAxisOffSet
        return x*0.97
        // return this.yAxisRange[0]+x
    }
    retreiveYforDataPoint(price){
        let pixelRange = Math.abs( this.yAxisRange[1]-this.yAxisRange[0] )
        let maxPrice = Math.max(...this.priceIndicators);
        let minPrice = Math.min(...this.priceIndicators);
        let priceRange = Math.abs( maxPrice-minPrice )
        let adjustedPrice = price-minPrice
        let pixelPerAmount = pixelRange/priceRange
        let y = adjustedPrice*pixelPerAmount
        return this.yAxisRange[1]-y
    }
    markDataPoint(n){
        this.ctx.save();
        let xOffset, yOffset, w, h
        this.ctx.fillStyle = '#f50';
        this.ctx.strokeStyle = '#f50';
        xOffset = this.canv.width/40
        yOffset = this.canv.height/27
        this.ctx.beginPath();
        // this.ctx.moveTo(this.dataCoords[n].x, this.dataCoords[n].y);
        // this.ctx.lineTo(this.dataCoords[n].x, this.yAxisRange[1]);
        // this.ctx.moveTo(this.dataCoords[n].x, this.dataCoords[n].y);
        // this.ctx.lineTo(this.xAxisRange[0], this.dataCoords[n].y);
        this.ctx.moveTo(this.dataCoords[n].x, this.dataCoords[n].y);
        this.ctx.lineTo(this.dataCoords[n].x, this.yAxisRange[0]+yOffset);
        this.ctx.moveTo(this.dataCoords[n].x, this.dataCoords[n].y);
        this.ctx.lineTo(this.xAxisRange[1]-xOffset*2, this.dataCoords[n].y);
        this.ctx.stroke();
        this.ctx.closePath();
        
        // this.ctx.textBaseline = 'top';
        
        
        this.ctx.fillText(this.data[n]['date'], this.dataCoords[n].x, this.yAxisRange[0]+yOffset);
        this.ctx.fillText(this.data[n]['price'], this.xAxisRange[1]-xOffset, this.dataCoords[n].y);
        
        // w = this.canv.width/20
        // h = this.canv.height/10
        // this.ctx.fillStyle = 'white';
        // this.ctx.fillRect(this.dataCoords[n].x, this.yAxisRange[1]+yOffset,w,h)
        // this.ctx.fillStyle = '#f50';
        // this.ctx.fillText(this.data[n]['date'], this.dataCoords[n].x, this.yAxisRange[1]+yOffset);
        // w = this.canv.width/20
        // h = this.canv.height/10
        // this.ctx.fillStyle = 'white';
        // this.ctx.fillRect(this.xAxisRange[0]-xOffset, this.dataCoords[n].y,w,h)
        // this.ctx.fillStyle = '#f50';
        // this.ctx.fillText(this.data[n]['price'], this.xAxisRange[0]-xOffset, this.dataCoords[n].y);
        this.ctx.restore();
        
    }
}

