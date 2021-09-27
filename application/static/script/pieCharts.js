let previousI
anychart.onDocumentReady(function() {
    // let dataObj = {}
    // let key, value, i
    // for (var pkey in pieChartData){
    //     key = pieChartData[pkey].top
    //     value = pieChartData[pkey].count
    //     if (!dataObj.hasOwnProperty(key)){
    //         dataObj[key] = {
    //             x:key,
    //             value:0,
    //         }
    //     }else{
    //         dataObj[key].value += value
    //     }
        
    // }
    // let data = []
    // // console.log(data)
    // for (key in dataObj){
    //     data.push(dataObj[key])
    // }
    var data = getChartData()
    
  
    // create the chart
    var chart = anychart.pie();
    // var chart = anychart.pie3d(data);
    // set the chart title
    //chart.title("Population by Race for the United States: 2010 Census");
    chart.background('')
    // add the data
    chart.radius("50%")
    chart.data(data);
    chart.legend().position("right");
    // set items layout
    chart.legend().itemsLayout("vertical");
    
    
    chart.fill("aquastyle");
    var palette = anychart.palettes.provence
    
    chart.palette(palette);
    
    
    chart.selected().explode("3%");
    
    // display the chart in the container
    chart.container('container');
    chart.draw();
  
    var interactivity = chart.interactivity();
    // interactivity.selectionMode("none");
    // chart.hovered().markers(true);
    // chart.selected().markers(false);
    // chart.selected().labels(true);  
    interactivity.selectionMode("singleSelect");
    




    let data2
    data2 = getChartData(data[1]['x'])
    // create a chart and set the data
    chart2 = anychart.pie(data2);
    chart2.background('')
    chart2.fill("aquastyle");
    var palette = anychart.palettes.blue
    
    chart2.palette(palette);
    // set the container id
    chart2.container("container2");
    chart2.legend().position("right");
    // set items layout
    chart2.legend().itemsLayout("vertical");
    // initiate drawing the chart
    chart2.draw();

    
    chart.credits(false)
    chart2.credits(false)

    chart.legend().listen(
        "legendItemMouseDown",
        function(e){
            index = e.itemIndex
            if (Number.isInteger(previousI)){
                chart.select(previousI)
            }
            previousI = index
            secondaryChartData = getChartData(data[index]['x'])
            chart2.data(secondaryChartData);
        }
    )

    chart.listen(
        // click twice on any range bar to see the result
        // "pointClick",
        "pointMouseDown",
        function(e) {
            var index = e.iterator.getIndex();
            if (Number.isInteger(previousI)){
                chart.select(previousI)
            }
            previousI = index
            secondaryChartData = getChartData(data[index]['x'])
            chart2.data(secondaryChartData);
        }
        );
  });



function getChartData(targetKey = false){
    let targetKey2
    if (!targetKey){
        targetKey2 = 'top'
    }else{
        targetKey2 = 'mid'
    }
    dataObj = {}
    let key, value
    for (var pkey in pieChartData){
        if (targetKey){
            if (pieChartData[pkey].top != targetKey){
                continue
            }
        }

        key = pieChartData[pkey][targetKey2]
        value = pieChartData[pkey].count
        if (!dataObj.hasOwnProperty(key)){
            dataObj[key] = {
                x:key,
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