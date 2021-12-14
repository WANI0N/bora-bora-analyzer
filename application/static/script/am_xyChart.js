function dynamicSort(property) {
    var sortOrder = 1;
    if(property[0] === "-") {
        sortOrder = -1;
        property = property.substr(1);
    }
    return function (a,b) {
        var result = (a[property] < b[property]) ? -1 : (a[property] > b[property]) ? 1 : 0;
        return result * sortOrder;
    }
}

// Create chart instance
am4core.ready(function() {

    // Themes begin
    am4core.useTheme(am4themes_dark);
    am4core.useTheme(am4themes_animated);
    // Themes end
    
    

    // Create chart instance
    var chart = am4core.create("xyChart", am4charts.XYChart);
    chart.numberFormatter.numberFormat = "#.##";
    

    // chart.maxPrecision = 1;
    
    
    chart.data = dbStatsData.sort(dynamicSort("date"));
    
    
    // Set input format for the dates
    chart.dateFormatter.inputDateFormat = "yyyy-MM-dd";
    
    // Create axes
    var dateAxis = chart.xAxes.push(new am4charts.DateAxis());
    var valueAxis = chart.yAxes.push(new am4charts.ValueAxis());
    
    valueAxis.numberFormatter.numberFormat = '#.####';
    valueAxis.maxPrecision = 5;
    valueAxis.renderer.minGridDistance = 15;
    
    
    // Create series
    var series = chart.series.push(new am4charts.LineSeries());
    series.dataFields.valueY = "diff_perc";
    
    series.dataFields.dateX = "date";
    series.tooltipText = "difference: {diff_perc}\n% of products: {perCent}%"
    series.strokeWidth = 2;
    series.minBulletDistance = 15;
    

    // Drop-shaped tooltips
    series.tooltip.background.cornerRadius = 20;
    series.tooltip.background.strokeOpacity = 0;
    series.tooltip.pointerOrientation = "vertical";
    series.tooltip.label.minWidth = 40;
    series.tooltip.label.minHeight = 40;
    series.tooltip.label.textAlign = "middle";
    series.tooltip.label.textValign = "middle";
    
    
    //test
    let gradient = new am4core.LinearGradient();
    gradient.addColor(am4core.color("red"));
    gradient.addColor(am4core.color("blue"));
    gradient.rotation = 90
    chart.background.fill = gradient
    chart.background.opacity = 0.2

    // Make bullets grow on hover
    var bullet = series.bullets.push(new am4charts.CircleBullet());
    bullet.circle.strokeWidth = 2;
    bullet.circle.radius = 4;
    bullet.circle.fill = am4core.color("#fff");

    var bullethover = bullet.states.create("hover");
    bullethover.properties.scale = 1.3;

    // bullet.circle.adapter.add("fill", function(fill, target) {
    //     // console.log(target.dataItem._dataContext.diff_perc)
    //     if (target.dataItem._dataContext.diff_perc < 0) {
    //       return am4core.color("#a55");
    //     }
    //     else {
    //       return fill;
    //     }
    //   });

    // Make a panning cursor
    chart.cursor = new am4charts.XYCursor();
    chart.cursor.behavior = "panXY";
    chart.cursor.xAxis = dateAxis;
    chart.cursor.snapToSeries = series;

    // Create vertical scrollbar and place it before the value axis
    chart.scrollbarY = new am4core.Scrollbar();
    chart.scrollbarY.parent = chart.leftAxesContainer;
    chart.scrollbarY.toBack();

    // Create a horizontal scrollbar with previe and place it underneath the date axis
    chart.scrollbarX = new am4charts.XYChartScrollbar();
    chart.scrollbarX.series.push(series);
    chart.scrollbarX.parent = chart.bottomAxesContainer;

    const maxRangeView = 100
    if (chart.data.length > maxRangeView){
        dateAxis.start = (chart.data.length-maxRangeView)/chart.data.length
    }
    
    dateAxis.keepSelection = true;
});