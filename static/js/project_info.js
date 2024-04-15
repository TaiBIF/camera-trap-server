// download
var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr('value');

let map = L.map("map", {tap: false});
L.tileLayer("https://{s}.tile.osm.org/{z}/{x}/{y}.png", {
  attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors',
}).addTo(map);


$( document ).ready(function() {
    let pk = $('input[name=pk]').val();

    $.ajax({
    type: 'GET',
    url: `/api/get_project_info_web/?pk=${pk}`,
    success: function (response) {
        getSaPoints(response.sa_list);
        setSpeciesPie(response.pie_data, response.other_data, []);

        window.sa_list = response.sa_list;
        window.other_data = response.other_data;
        window.pie_data = response.pie_data;
        window.species_count = response.species_count;
        window.species_last_updated = response.species_last_updated;
        map.setView(response.sa_point, response.zoom);

    }})

    $.ajax({
        type: 'GET',
        url: `/api/get_image_info/?pk=${pk}`,
        success: function (response) {  
            setImageLineChart(response.line_chart_data);

            window.line_chart_data = response.line_chart_data;
            window.image_counts = response.image_counts;
        }}
    )


    $('#updateSpeciesPie').on('click',function(){
        updateSpeciesPie()
        updateImageLineChart()
    })


    $("#show-woods").change(function() {
        if(this.checked) {
            if ($('.forestPoly').length){
                $('.forestPoly').removeClass('d-none')
            } else {
                $('.loading-pop').removeClass('d-none')
                
                $.getJSON("/static/map/forest_map.json", function(data, status){
                    $(data.features).each(function(key, data) {
                        L.geoJSON(data, {onEachFeature: onEachFeature, style: polystyle})
                        .bindPopup(`${data['properties']['DIST_C']}-${data['properties']['WKNG_C']}`)
                        .on("mouseover", function (e) {
                            this.openPopup();
                        })
                        .on("mouseout", function (e) {
                        this.closePopup();
                        })
                        .addTo(map);
                    });
                    $('.loading-pop').addClass('d-none')
                  });
            }
        } else {
            $('.forestPoly').addClass('d-none');
        }        
    });

    $('.filter').on('change', function(){
        updateSpeciesPie();
        updateImageLineChart()  
    });
        
    
    let date_locale = { days: ['周日', '周一', '周二', '周三', '周四', '周五', '周六'],
                    daysShort: ['日', '一', '二', '三', '四', '五', '六'],
                    daysMin: ['日', '一', '二', '三', '四', '五', '六'],
                    months: ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'],
                    monthsShort: ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'],
                    today: '今天',
                    clear: '清除',
                    dateFormat: 'yyyy-MM-dd',   
                    timeFormat: 'HH:mm',
                    firstDay: 1}
    
    let start_date_picker = new AirDatepicker('#start_date',
        { locale: date_locale,
            onSelect: function onSelect(fd, date, inst) {
                updateSpeciesPie();
            }
        });
    
    
    let end_date_picker = new AirDatepicker('#end_date',
        { locale: date_locale,
            onSelect: function onSelect(fd, date, inst) {
                updateSpeciesPie();
            } });
    
    
    $('.show_start').on('click', function(){
        if (start_date_picker.visible) {
            start_date_picker.hide();
        } else {
            start_date_picker.show();
        }
    })
    
    $('.show_end').on('click', function(){
        if (end_date_picker.visible) {
            end_date_picker.hide();
        } else {
            end_date_picker.show();
        }
    })
    

    $('.sa-select').on('change', function(){
        $('.subsa-select').html('<option value="all">全部</option>');
        let said = $(this).val();
        if (said != 'all'){
            $.ajax({
                data: {'said': said},            
                url: "/get_subsa",
                success: function(response){
                    response.subsas.forEach(
                        (i) =>
                          ($('.subsa-select').append(
                              `<option value='${i[0]}'>${i[1]}</option>`
                          ))
                      );
                },
            })
        } 
    })
    
    // download 
    $('#downloadButton').on('click', function () {
        $.ajax({
          type: "POST",
          url: "/api/check_login/",
          headers: { 'X-CSRFToken': $csrf_token },
          success: function (response) {
      
            if (response.redirect) {
              if (response.messages) {
                alert(response.messages);
                window.location.replace(window.location.origin + "/personal_info");
              } else {
                $('.down-pop').removeClass('d-none')
                //$('#downloadModal').fadeIn();
              }
            } else {
              if (response.messages) {
                alert(response.messages);
                $('#loginModal').modal('show')
              }
              else {
                // $('.down-pop').fadeIn();
                //$('#downloadModal').fadeIn();
                $('.down-pop').removeClass('d-none')
              }
            }
          },
          error: function () {
            alert('未知錯誤，請聯繫管理員');
          }
        })
      })
    
    
    $('.download').on('click', function(){
        // $("input[name=email]").val($("#download-email").val())
    
        $.ajax({
            data: {'email': $("#download-email").val()},            
            type: "POST",
            url: "/download/" + $('input[name=pk]').val(),
            headers:{'X-CSRFToken': $csrf_token},
            success: function(){
                alert('請求已送出');
                //$('#downloadModal').modal('hide')
                $('.down-pop').addClass('d-none')

                //$('.down-pop').fadeOut();
            },
            error:function(){
                alert('未知錯誤，請聯繫管理員');
                //$('#downloadModal').modal('hide')
                //$('.down-pop').fadeOut();
                $('.down-pop').addClass('d-none')

            }
        })
    })
    
    $('.down-pop .xx').on('click', function (event) {
        $('.down-pop').addClass('d-none');
    });

    $('#canceldownload').on('click', function (event) {
        $('.down-pop').addClass('d-none');
    });
    
    $("#download-email").keyup(function () {
        ValidateEmail($(this).val())
    });
    
    $('.clear-up').on('click', function (event) {
        location.reload();
    });
});


function getSaPoints(sa_list){
    $.ajax({
        url: '/get_sa_points',
        data: {"sa": sa_list},
        dataType: "json",
        success: function(response) {
            response.sa_points.forEach(
                (i) =>
                  (marker = new L.marker([i[1], i[0]], { icon: StudyAreaIcon })
                    .bindTooltip(
                        `${i[2]}`, { permanent: true, direction: 'top' }
                    )
                    .on("mouseover", function (e) {
                        e.target.setIcon(StudyAreaIconSelect);                                 
                    })
                    .on("mouseout", function (e) {
                        e.target.setIcon(StudyAreaIcon);                                   
                    })
                    .on("click", function (e) {
                        // 如果是子樣區？
                        $('.sa-select').val(i[3]);
                        updateSpeciesPie();
                        updateImageLineChart()
                    })
                    .addTo(map))
              );
        }
    });  
}

//https://emailregex.com
function ValidateEmail(inputText){
    let mailformat = /(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])/
    if(inputText.match(mailformat)){
        $('#email-check').attr('fill', 'green');
        $('button.download').prop('disabled', false);
    } else {
        $('#email-check').attr('fill', 'lightgrey');
        $('button.download').prop('disabled', true);
    }
}


    

// map
  
function polystyle(feature) {
return {
    fillColor: "#7C9C2D",
    weight: 0.8,
    color: "white",
    className: "forestPoly",
};
}


function onEachFeature(feature, layer) {
    layer.on({
        mouseover: e => {
            e.target.setStyle({
                fillColor: '#8B0000',
            });
        },
        mouseout: e => {
            e.target.setStyle({
                fillColor: '#7C9C2D',
            });
        },        
    })
}


const StudyAreaIcon = L.icon({
    iconUrl: '/static/icon/marker-icon-error.png',
    iconSize: [66, 120],
    iconAnchor: [33, 80],
    popupAnchor: [-3, -76],
    shadowSize: [66, 120],
    shadowAnchor: [31, 77],
    className: "myStudyAreaIcon",
  });
  
  const StudyAreaIconSelect = L.icon({
    iconUrl: '/static/icon/marker-icon-error-select.png',
    iconSize: [66, 120],
    iconAnchor: [33, 80],
    popupAnchor: [-3, -76],
    shadowSize: [66, 120],
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
  


// species pie

let chartColors = [
    "#E8ECFB", 
    "#B997C7",
    "#824D99", 
    "#4E78C4", 
    "#57A2AC",
    "#7EB875", 
    "#D0B541",
    "#E67F33", 
    "#CE2220", 
    "#521A13" ];
  


function setSpeciesPie(pie_data, other_data, deployment_points){
    Highcharts.chart('species-pie', {
        chart: {
            backgroundColor: 'transparent',
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false,
            type: 'pie',
            height: 340,
          },
          colors: chartColors,
        title: { text: "" },
        exporting: { enabled: false },
        credits: { enabled: false },
        plotOptions: {
            pie: {
                name: 'speices',
                size: '80%',
                innerSize: '50%',
                allowPointSelect: true,
                cursor: 'pointer',
                dataLabels: {
                    enabled: false,
                },
                point: {
                    events: {
                        click: function(event) {
                            // 修改左側地圖成heatmap
                            if (this.name == '其他物種'){
                                alert('請由下方「其他物種」折疊選單選擇物種')
                            } else {
                                updateSpeciesMap(this.name)
                                console.log(this.name)
                                updateImageLineChart(this.name);
                            }
                            // 修改右側統計圖
                        }
                    }
                }        
            },
        },
        tooltip: {
            headerFormat: '',
            backgroundColor: 'rgba(70,70,70,.8)',
            pointFormatter() {
              return `<span class="white">${this.name} ${
                this.count
              } 筆辨識紀錄 (${this.y}%)</span>`;
            },
            style: {
              color: '#FFF',
            },
        },
        series: [{
            name: 'Speices',
            data: pie_data,
            size: '80%',
        }]
    });

    if (pie_data.length==0){
        $('#species-pie').html('')
    }

    // species percentage
    $('#species-percentage').html('');
    for (i = 0; i < pie_data.length; i++) {
        $('#species-percentage').append(
            ` <span class="species-percentage-list" data-species="${pie_data[i]['name']}"><i class="fa fa-circle chart-color-${i} w-12"></i> 
            ${pie_data[i]['name']} ${pie_data[i]['y']} % </span> <br>`
        )
        if (pie_data[i]['name'] == '其他物種'){
            $('#species-percentage').append(
                `<div class="collapse multi-collapse d-none" id="multiCollapseSpecies">
                </div>`
            )
        }
    }
    $('#multiCollapseSpecies').html('');
    for (i = 0; i < other_data.length; i++) {
        $('#multiCollapseSpecies').append(`
       <span class="species-percentage-list species-percentage-list-o" data-species="${other_data[i]['name']}">
            ${other_data[i]['name']} ${other_data[i]['y']} % </span><br>
        `)
    }

    $('.species-percentage-list').on('click', function(){
        if ($(this).data('species')=='其他物種'){
            $('#multiCollapseSpecies').toggleClass('d-none')
        } else {
            updateSpeciesMap($(this).data('species'))
            updateImageLineChart($(this).data('species'));
        }
    })

    // deployment
    $('.myDeploymentIcon').remove();
    $('.leaflet-tooltip').remove();
    $('.myStudyAreaIcon').remove();

    if (deployment_points.length > 0){
        map.setView([deployment_points[0][1],deployment_points[0][0]]);
        deployment_points.forEach(function(r){
                if (r[3] == false ){ // 不是子樣區, 是相機位置
                    marker = new L.marker([r[1], r[0]], { icon: DeploymentIcon })
                    .on("mouseover", function (e) {
                        e.target.setIcon(DeploymentIconSelect);                                 
                    })
                    .on("mouseout", function (e) {
                        e.target.setIcon(DeploymentIcon);                                     
                    })                        
                    .bindTooltip(r[2], { permanent: true, direction: 'top' })
                    .addTo(map)
                } else {
                    marker = new L.marker([r[1], r[0]], { icon: StudyAreaIcon })
                    .on("mouseover", function (e) {
                        e.target.setIcon(StudyAreaIconSelect);                                 
                    })
                    .on("mouseout", function (e) {
                        e.target.setIcon(StudyAreaIcon);                                     
                    })
                    .on("click", function (e) {
                        // 如果是子樣區？
                        $('.subsa-select').val(r[4]);
                        updateSpeciesPie();
                        updateImageLineChart()
                    })
                    .bindTooltip(r[2], { permanent: true, direction: 'top' })
                    .addTo(map)
                }
            
        }
        );
    }
}


function updateSpeciesPie(){
    // 地圖相關的移除
    $('.species-map-legend').addClass('d-none')
    $('.speciesMapIcon').remove()
    $('.species-pie,#species-pie,#species-percentage').removeClass('d-none')
    $('.species-map').addClass('d-none')
    // 樣區 子樣區 日期
    let said;
    // 子樣區優先
    let subsa_select = $('.subsa-select option:selected').val();
    let sa_select = $('.sa-select option:selected').val();
    let title;
    if ((subsa_select!='all') & (subsa_select!=undefined) ){
        said = subsa_select
        title = $( ".subsa-select option:selected" ).text()
    } else if ((sa_select!='all') & (sa_select!=undefined) ) {
        said = sa_select
        title = $( ".sa-select option:selected" ).text()
    } else {
        said = {'project': $('input[name=pk]').val()}
        title = '全部'
    }

    let start_date = $('input[name="start_date"]').val()
    let end_date = $('input[name="end_date"]').val()
    if ((!start_date) & (!end_date) & (title == '全部')){
        setSpeciesPie(window.pie_data, window.other_data, []);
        getSaPoints(window.sa_list)
        $('#pie-sa-title').text('全部樣區');
        $('#species-count-title').html(window.species_count);
        $('#species_last_updated').html(window.species_last_updated);
    } else {
        $('.loading-pop').removeClass('d-none')
        $.ajax({
            data: {'said': said, 'start_date': start_date, 'end_date': end_date},            
            url: "/update_species_pie",
            success: function(response){
                $('.loading-pop').addClass('d-none')
                $('#pie-sa-title').text(title);
                $('#species-count-title').html(response.species_count);
                $('#species_last_updated').html(response.species_last_updated);
                setSpeciesPie(response.pie_data, response.other_data, response.deployment_points)
                if (title=='全部'){
                    getSaPoints(window.sa_list)
                };
            },
            error: function(){
                alert('未知錯誤，請聯繫管理員');
                $('.loading-pop').addClass('d-none')

            }
        })
    }
}

function updateSpeciesMap(species){
    let pk = $('input[name=pk]').val();
    // 樣區 子樣區 日期
    let said;
    // 子樣區優先
    let subsa_select = $('.subsa-select option:selected').val();
    let sa_select = $('.sa-select option:selected').val();
    let title;
    if ((subsa_select!='all') & (subsa_select!=undefined) ){
        said = subsa_select
        title = $( ".subsa-select option:selected" ).text()
    } else if ((sa_select!='all') & (sa_select!=undefined) ) {
        said = sa_select
        title = $( ".sa-select option:selected" ).text()
    } else {
        said = {'project': $('input[name=pk]').val()}
        title = '全部'
    }

    let start_date = $('input[name="start_date"]').val()
    let end_date = $('input[name="end_date"]').val()

        $('.loading-pop').removeClass('d-none')
        $.ajax({
            data: {'said': said, 'start_date': start_date, 'end_date': end_date, 'species': species, 'pk': pk},            
            url: "/update_species_map",
            success: function(response){
                // 先把所有地圖上的移除
                $('.leaflet-marker-icon,.leaflet-tooltip,.speciesMapIcon').remove()
                $('.species-map-legend').removeClass('d-none');
                //$('#species-map-stat').html('<a class="text-gray link text-decoration-none mb-5" onClick="updateSpeciesPie()"><i class="fa fa-chevron-left"></i> 返回</a>')

                let pre
                if (response.type=='相機位置'){
                    pre = `<img class="marker-icon" src='/static/icon/marker-icon.png'>`
                } else {
                    pre = `<img class="marker-icon" src='/static/icon/marker-icon-error.png'>`
                }

                let pk = $('input[name=pk]').val();
                $('#species-map-stat').html('')
                //$('#species-map-stat').append(`<h5>${response.type}</h5>`)
                response.data.forEach(function(i) {
                    marker = pointToLayer(i[0], [i[2],i[1]])
                            .bindTooltip(pre+i[3],{className: 'species-map-tooltip'})
                            .addTo(map)
                    url = `/project/details/${pk}/?sa=${i[3]}&start_date=${start_date}&end_date=${end_date}&species=${species}`
                    $('#species-map-stat').append(
                        `
                        <div class="link-container">
                            <p><a href="${url}">${i[3]}：${i[0]}筆</a></p>
                            <div class="svg-container">
                                <svg class="icon02" xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 26.414 26.414">
                                    <g id="Group_771" data-name="Group 771" transform="translate(-966.586 -1128.083)">
                                        <g id="Group_719" data-name="Group 719" transform="translate(968 1128.083)">
                                            <g class="cir" id="Ellipse_5" data-name="Ellipse 5" transform="translate(3 0)" fill="none" stroke="#257455" stroke-width="2">
                                                <ellipse cx="11" cy="11" rx="11" ry="11" stroke="none"></ellipse>
                                                <ellipse cx="11" cy="11" rx="10" ry="10" fill="none"></ellipse>
                                            </g>
                                            <line id="Line_5" data-name="Line 5" x1="6" y2="6" transform="translate(0 19)" fill="none" stroke="#257455" stroke-linecap="round" stroke-width="2"></line>
                                        </g>
                                    </g>
                                </svg>
                            </div>
                        </div>
                        `
                    );
                    
                })                  

                // 右側統計
                $('.species-pie,#species-pie,#species-percentage').addClass('d-none')
                $('.species-map').removeClass('d-none')

                $('#species-map-title').html(species)
                $('#species-map-count-title').html(response.total_count)

                $('.loading-pop').addClass('d-none')
            },
            error: function(){
                alert('未知錯誤，請聯繫管理員');
                $('.loading-pop').addClass('d-none')
            }
        })
    //}

}

// species point color 
    /* marker style */
function getColor(d) {
    return  d > 10000  ? '#ED5564' :
            d > 5000   ? '#FFCE54' :
            d > 1000   ? '#A0D568' :
            d > 500   ? '#4FC1E8' :
                        '#AC92EB';
}

function getRadius(d) {
    return  d > 1000 ? 20 :
            d > 5000 ? 20 :
            d > 1000 ? 18 :
            d > 500  ? 16 :
                       14;
}  


function pointToLayer(count, latlng) {
    return L.circleMarker(latlng, {
        radius: getRadius(count),
        fillColor: getColor(count),
        color: 'transparent',
        weight: 1,
        opacity: 1,
        fillOpacity: 0.75,
        className: 'speciesMapIcon',
        }) // Change marker to circle
}

function setImageLineChart(line_chart_data){
    Highcharts.chart('line-chart', {
        chart: {
            backgroundColor: 'transparent',
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false,
            height: 340,
          },
        exporting: { enabled: false },
        credits: { enabled: false },
        legend: {
            enabled: false,
        },
        plotOptions:{
            series:{
                label:{
                    enabled: false,
                },
            },
        },
        title: { text: "" },
        xAxis:[{
            type:'datetime',
            labels: {
                format: '{value:%Y-%b}',
                rotation: -45,
                align: 'right',
              },
        }],
        yAxis:[{
            title: {
                text: '照片張數',
              },
        }],
        series: [{
            name: '照片張數',
            data: line_chart_data,
            size: '80%',
            color: '#257455', 
        }]
    });
}

function updateImageLineChart(species){
    // 地圖相關的移除
    $('.species-map-legend').addClass('d-none')
    $('.speciesMapIcon').remove()
    $('.species-pie,#species-pie,#species-percentage').removeClass('d-none')
    $('.species-map').addClass('d-none')
    // 樣區 子樣區 日期
    let pk = $('input[name=pk]').val();
    let said;
    // 子樣區優先
    let subsa_select = $('.subsa-select option:selected').val();
    let sa_select = $('.sa-select option:selected').val();
    let title;
    if ((subsa_select!='all') & (subsa_select!=undefined) ){
        said = subsa_select
        title = $( ".subsa-select option:selected" ).text()
    } else if ((sa_select!='all') & (sa_select!=undefined) ) {
        said = sa_select
        title = $( ".sa-select option:selected" ).text()
    } else {
        said = $('input[name=pk]').val()
        title = '全部'
    }

    let start_date = $('input[name="start_date"]').val()
    let end_date = $('input[name="end_date"]').val()

    // Reset the title of line chart
    $('#species_name').text('');
    if ((!start_date) && (!end_date) && (title == '全部') && (!species)){
        // If there is no selected filter, show the overview line chart
        setImageLineChart(window.line_chart_data)
        $('#sa-title').text('全部樣區');
        $('#image_counts').text(window.image_counts);
    } else {
        $('.loading-pop').removeClass('d-none')
        $.ajax({
            data: {'said': said, 'start_date': start_date, 'end_date': end_date, 'species': species, 'pk': pk},            
            url: "/update_line_chart",
            success: function(response){
                setImageLineChart(response.line_chart_data);
                var selectedSa = $('.sa-select').find("option:selected").text()
                $('#sa-title').text(selectedSa);
                $('#image_counts').text(response.image_counts);
                $('#species_name').text(species);

                // Reset species
                species = undefined;
            },
            error: function(){
                alert('未知錯誤，請聯繫管理員');
                $('.loading-pop').addClass('d-none')

            }
        })
    }
}