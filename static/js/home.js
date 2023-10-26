$(function () {

    $.ajax({
        url: "/api/get_growth_data",
        success: function (data) {
        // plot
        data_growth_year = [];
        data.data_growth_image.forEach((i) => data_growth_year.push(i[0]));

        data_growth_image_count = [];
        data.data_growth_image.forEach((i) => data_growth_image_count.push(i[1] / 10000));

        data_growth_deployment_count = [];
        data.data_growth_deployment.forEach((i) => data_growth_deployment_count.push(i[1]));

        // plot - data_growth
        Highcharts.chart("data_growth", {
            chart: {
            marginTop: 40,
            backgroundColor: null,
            },
            exporting: { enabled: false },
            credits: { enabled: false },
            title: { text: "" },
            xAxis: [
            {
                categories: data_growth_year,
                crosshair: true,
            },
            ],
            legend: {
            itemStyle: {
                fontSize: "14px",
                fontWeight: "regular",
            },
            },
            yAxis: [
            {
                // Primary yAxis
                allowDecimals: false,
                labels: {
                format: "{value}",
                style: {
                    fontSize: "14px",
                },
                },
                title: {
                align: "high",
                offset: 0,
                text: "相機位置數",
                rotation: 0,
                y: -20,
                x: -10,
                style: {
                    fontSize: "14px",
                },
                },
                opposite: true,
            },
            {
                // Secondary yAxis
                allowDecimals: false,
                gridLineWidth: 0,
                title: {
                align: "high",
                offset: 0,
                text: "影像累積筆數(萬)",
                rotation: 0,
                y: -20,
                x: 30,
                style: {
                    fontSize: "14px",
                },
                },
                labels: {
                format: "{value}",
                style: {
                    fontSize: "14px",
                },
                },
            },
            ],
            tooltip: {
            shared: true,
            },
            series: [
            {
                name: "影像累積筆數(萬)",
                type: "column",
                yAxis: 1,
                data: data_growth_image_count,
                tooltip: {},
                color: "#AECC82",
            },
            {
                name: "相機位置數",
                type: "spline",
                data: data_growth_deployment_count,
                tooltip: {},
                marker: {
                lineWidth: 2,
                lineColor: "#AECC82",
                fillColor: "white",
                },
                color: "#AECC82",
                label: {
                enabled: false,
                },
            },
            ],
            responsive: {
            rules: [
                {
                condition: {
                    maxWidth: 500,
                },
                chartOptions: {
                    legend: {
                    floating: false,
                    layout: "horizontal",
                    align: "center",
                    verticalAlign: "bottom",
                    x: 0,
                    y: 0,
                    },
                    yAxis: [
                    {
                        labels: {
                        align: "right",
                        x: 0,
                        y: -6,
                        },
                        showLastLabel: false,
                    },
                    {
                        labels: {
                        align: "left",
                        x: 0,
                        y: -6,
                        },
                        showLastLabel: false,
                    },
                    {
                        visible: false,
                    },
                    ],
                },
                },
            ],
            },
        });
        },
    });

    $.ajax({
        url: "/api/get_species_data",
        success: function (data) {
        // plot - species
            species_data_name = [];
            data.species_data.forEach((i) => species_data_name.push(i[1]));
            species_data_count = [];
            data.species_data.forEach((i) => species_data_count.push(i[0] / 10000));

            // Select the top 10 species
            let xAxisCategories = species_data_name.slice(0, 10);
            // If the amount of species is more than 10, add '其他' as the last category
            if (species_data_name.length > 10) {
                xAxisCategories.push('其他');
            }

            // Accumulating the speceis number, except for the top 10 species
            const remainingCount = species_data_count.slice(10).reduce((a, b) => a + b, 0);
            const yAxisData = species_data_count.slice(0, 10);
            if (species_data_count.length > 10) {
                yAxisData.push(remainingCount);
            }
            // console.log(yAxisData);

            Highcharts.chart("species_data", {
                chart: {
                    type: "bar",
                    marginTop: 40,
                    backgroundColor: null,
                },
                exporting: { enabled: false },
                credits: { enabled: false },
                title: { text: "" },
                xAxis: {
                    categories: xAxisCategories,
                    tickInterval: 1,
                    title: {
                    text: null,
                    style: {
                        fontSize: "14px",
                    },
                    },
                    labels: {
                    step: 1,
                    style: {
                        fontSize: "14px",
                    },
                    },
                },
                yAxis: {
                    allowDecimals: false,
                    min: 0,
                    title: {
                    text: "資料累積筆數(萬)",
                    align: "high",
                    style: {
                        fontSize: "14px",
                    },
                    },
                    labels: {
                    overflow: "justify",
                    style: {
                        fontSize: "14px",
                    },
                    },
                },
                tooltip: {
                    pointFormatter: function () {
                    var string = this.series.name + ": " + this.y + "<br>";
                    return string;
                    },
                },
                series: [
                    {
                    name: "資料累積筆數(萬)",
                    data: yAxisData,
                    color: "#AECC82",
                    },
                ],
                legend: {
                    itemStyle: {
                    fontSize: "14px",
                    fontWeight: "regular",
                    },
                },
            });
        },
    });  
});

  // map
  
  const StudyAreaIcon = L.icon({
    iconUrl: '/static/icon/marker-icon-error.png',
    iconSize: [33, 60],
    iconAnchor: [33, 80],
    popupAnchor: [-3, -76],
    shadowSize: [33, 60],
    shadowAnchor: [31, 77],
    className: "myStudyAreaIcon",
  });
  
  const StudyAreaIconSelect = L.icon({
    iconUrl: '/static/icon/marker-icon-error-select.png',
    iconSize: [33, 60],
    iconAnchor: [33, 80],
    popupAnchor: [-3, -76],
    shadowSize: [33, 60],
    shadowAnchor: [31, 77],
    className: "myStudyAreaIcon",
  });


  const DeploymentIcon = L.icon({
    iconUrl: '/static/icon/marker-icon.png',
    iconSize: [66, 120],
    iconAnchor: [33, 80],
    popupAnchor: [-3, -76],
    shadowSize: [66, 120],
    shadowAnchor: [31, 77],
    className: "myDeploymentIcon",
  });
  
  const DeploymentIconSelect = L.icon({
    iconUrl: '/static/icon/marker-icon-select@2x.png',
    iconSize: [66, 120],
    iconAnchor: [33, 80],
    popupAnchor: [-3, -76],
    shadowSize: [66, 120],
    shadowAnchor: [31, 77],
    className: "myDeploymentIcon",
  });
  


  let map = L.map("map", {tap: false}).setView([23.5, 121.2], 7);
  L.tileLayer("https://{s}.tile.osm.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  function onEachFeature(feature, layer) {
        layer.on({
            mouseover: e => {
                e.target.setStyle({
                    fillColor: 'green',
                });
            },
            mouseout: e => {
                e.target.setStyle({
                    fillColor: '#7C9C2D',
                });
            },
            click: e => {
              $('.city-box').removeClass('d-none');
              $('.pin-chartbox').addClass('d-none')
              $('.inf-box').removeClass('d-block').addClass('d-none');
                let county = e.target.feature.properties.COUNTYNAME;
                countyOnClick(county);
            },
            
        })
    }


  function countyOnClick(county){
    $.ajax({
      url: '/api/stat_county',
      data: {"county": county},
      dataType: "json",
      success: function(response) {
        //map.removeLayer(marker);
        $('.myStudyAreaIcon').remove();

        response.studyarea.forEach(
          (i) =>
            (marker = new L.marker([i[1], i[0]], { icon: StudyAreaIcon })
              .bindPopup(
                `${i[3]}<small>${i[2]}</small>`
              )
              .on("mouseover", function (e) {
                this.openPopup();
                e.target.setIcon(StudyAreaIconSelect);                                 
              })
              .on("mouseout", function (e) {
                this.closePopup();
                e.target.setIcon(StudyAreaIcon);                                   
              })
              .on("click", function (e) {
                $('.loading-pop').removeClass('d-none')
                $.ajax({
                  url: '/api/stat_studyarea',
                  data: {"said": i[4]},
                  dataType: "json",
                  success: function(response) {
                    $('.loading-pop').addClass('d-none')
                    $('.city-box').addClass('d-none')
                    $('.pin-chartbox').removeClass('d-none')
                    // 返回鍵
                    //$('.map-explore').html(`<a class="link" onClick="resetMapExplore('${county}')">返回</a>`)
                    // 更換右側統計圖
                    $('.pin-chartbox').html(`

                    <h2>${i[3]}</h2>
                    <div class="mbscro">
                      <div class="chart-box">
                        <div id="deployment_data" class="mx-auto"></div>
                      </div>
                    </div>
                    <div class="mapiconbox">
                      <button class="resetMapExplore" data-county="${county}">< 返回</button>
                      <img src="/static/image/marker-icon.png" alt="">
                      <p>相機位置</p>
                    </div>
                      `);                                        
                    $('.resetMapExplore').off('click')
                    $('.resetMapExplore').on('click', function(){
                      resetMapExplore($(this).data('county'))
                    })

                    Highcharts.chart("deployment_data", {
                      chart: {
                        type: "column",
                        marginTop: 40,
                        backgroundColor: null,
                      },
                      exporting: { enabled: false },
                      credits: { enabled: false },
                      title: { text: "" },
                      xAxis: {
                        categories: response.name,
                        tickInterval: 1,
                        title: {
                          text: "相機位置",
                          style: {
                            fontSize: "14px",
                          },
                        },
                        labels: {
                          style: {
                            fontSize: "14px",
                          },
                        },
                      },
                      yAxis: {
                        allowDecimals: false,
                        min: 0,
                        title: {
                          align: "high",
                          offset: 0,
                          text: "影像累積筆數",
                          rotation: 0,
                          y: -20,
                          style: {
                            fontSize: "14px",
                          },                        
                        },
                        labels: {
                          format: "{value}",
                          overflow: "justify",
                          style: {
                            fontSize: "14px",
                          },
                        },
                      },
                      tooltip: {
                        pointFormatter: function () {
                          var string = this.series.name + "：" + this.y + "<br>";
                          return string;
                        },
                      },
                      series: [
                        {
                          name: "影像累積筆數",
                          data: response.count,
                          color: "#AECC82",
                        },
                      ],
                      legend:{ enabled:false },
                    });
                    // 更換左側地圖
                    // 重設縮放 & 移除其他icon
                    map.setView([response.center[1], response.center[0]], 10);
                    $('.myStudyAreaIcon').remove();
                    $('.countyPoly').addClass('d-none');
                    response.deployment_points.forEach(
                      (r) =>
                        (marker = new L.marker([r[2], r[1]], { icon: DeploymentIcon })
                          .on("mouseover", function (e) {
                            e.target.setIcon(DeploymentIconSelect);                                 
                          })
                          .on("mouseout", function (e) {
                            e.target.setIcon(DeploymentIcon);                                     
                          })                        
                          .bindTooltip(r[3], { permanent: true, direction: 'top' })
                          .addTo(map)));
                  },
                  error: function () {
                    $('.loading-pop').addClass('d-none')
                  }
                })
              })
              .addTo(map))
        );

        $('.city-box').html(
          `<h2>${county}</h2>
          <ul class="inflist">
          <li>
            <div class="left-title">計畫總數</div>
            <div class="right-cont">${response.num_project}</div>
          </li>
          <ul class="inflist">
          <li>
            <div class="left-title">計畫總數</div>
            <div class="right-cont">${response.num_deployment}</div>
          </li>
          <li>
            <div class="left-title">相機位置</div>
            <div class="right-cont">${response.num_deployment}</div>
          </li>
          <li>
            <div class="left-title">總辨識進度</div>
            <div class="right-cont">${response.identified} %</div>
          </li>
          <li>
            <div class="left-title">總影像數</div>
            <div class="right-cont">${response.num_image}</div>
          </li>
          <li>
            <div class="left-title">相機總工時</div>
            <div class="right-cont">${response.num_working_hour}</div>
          </li>
          <li>
            <div class="left-title">出現物種</div>
            <div class="right-cont">${response.species}</div>
          </li>
          </ul>
          <div class="mapiconbox">
            <img src="/static/image/marker-icon-error.png" alt="">
            <p>樣區</p>
          </div>
          `
        )
      }
  })
  }

  function polystyle(feature) {
    return {
      fillColor: "#7C9C2D",
      weight: 1.2,
      color: "white",
      className: "countyPoly",
    };
  }

  $.getJSON("/static/map/twCounty2010.geo.json", function (ret) {
    L.geoJSON(ret, {onEachFeature: onEachFeature, style: polystyle}).addTo(map);
    //L.geoJSON(ret, { style: polystyle }).addTo(map);
  });

    function resetMapExplore(county){
      $('.myDeploymentIcon').remove();
      $('.leaflet-tooltip').remove();
      map.setView([23.5, 121.2], 7);
      $('.countyPoly').removeClass('d-none');
      // trigger event
      $('.city-box').removeClass('d-none');
      $('.pin-chartbox').addClass('d-none')
      countyOnClick(county);
    
    }
  