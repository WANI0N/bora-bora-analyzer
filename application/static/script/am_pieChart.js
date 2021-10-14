am4core.ready(function() {
    
    // Themes begin
    // am4core.useTheme(am4themes_animated);
    am4core.useTheme(am4themes_dark);
    am4core.useTheme(am4themes_animated);
    // Themes end
    
    // Create chart instance
    var chart = am4core.create("pieChartdiv", am4charts.PieChart);
    
    // Add data
    chart.data = getChartData("top")
    // Add and configure Series
    var pieSeries = chart.series.push(new am4charts.PieSeries());
    pieSeries.dataFields.value = "value";
    pieSeries.dataFields.category = "category";
    pieSeries.slices.template.stroke = am4core.color("#fff");
    pieSeries.slices.template.strokeOpacity = 1;
    
    //test
    let gradient = new am4core.LinearGradient();
    gradient.addColor(am4core.color("red"));
    gradient.addColor(am4core.color("blue"));
    gradient.rotation = 90
    chart.background.fill = gradient
    chart.background.opacity = 0.2

    // This creates initial animation
    pieSeries.hiddenState.properties.opacity = 1;
    pieSeries.hiddenState.properties.endAngle = -90;
    pieSeries.hiddenState.properties.startAngle = -90;
    
    chart.hiddenState.properties.radius = am4core.percent(0);
    chart.innerRadius = am4core.percent(40);
    chart.legend = new am4charts.Legend();
    
}); // end am4core.ready()

function getChartData(targetKey){
    dataObj = {}
    let key, value
    for (var pkey in pieChartData){
        key = pieChartData[pkey][targetKey]
        value = pieChartData[pkey].count
        if (!dataObj.hasOwnProperty(key)){
            dataObj[key] = {
                category:key,
                value:0,
            }
        }else{
            dataObj[key].value += value
        }
    }
    let data = []
    for (key in dataObj){
        data.push(dataObj[key])
    }
    
    return data
}